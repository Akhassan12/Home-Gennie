"""
depth_room_pipeline.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full-Room 3D Reconstruction Pipeline for Home Gennie.

Converts an AI-generated interior design image into a complete
3D room mesh (GLB) using metric depth estimation.

Architecture (3-Layer Free Waterfall):
  Layer 1 → HuggingFace Inference API (serverless, free, fastest)
             Model: depth-anything/Depth-Anything-V2-Small-hf
             URL:   router.huggingface.co/hf-inference
  Layer 2 → HuggingFace Gradio Space (ZeroGPU, free GPU)
             Space: depth-anything/Depth-Anything-V2
  Layer 3 → Local CPU Inference (offline fallback, always works)
             Model: depth-anything/Depth-Anything-V2-Small-hf (94 MB, cached)

After depth is obtained (from any layer), the depth → GLB conversion
runs entirely on the local CPU using numpy + trimesh. No paid API needed.

Output: A .glb file containing the full room as a textured 3D mesh,
        viewable in model-viewer with AR support.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import io
import time
import tempfile
import requests
import numpy as np
from PIL import Image


# ─────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────

# Model for local & HF API depth estimation
DEPTH_MODEL_ID = "depth-anything/Depth-Anything-V2-Small-hf"

# HF Inference API endpoint (new router URL — old api-inference is 410 Gone)
# NOTE: Not all models are supported via hf-inference serverless provider.
# depth-anything/Depth-Anything-V2-Small-hf returns 400 "not supported".
# The Large model IS supported. We try Large first, fall to local Small.
HF_DEPTH_API_URL = (
    "https://router.huggingface.co/hf-inference/models/"
    "depth-anything/Depth-Anything-V2-Large-hf"
)

# HuggingFace Gradio Space for depth estimation (ZeroGPU, free)
HF_DEPTH_SPACE = "depth-anything/Depth-Anything-V2"

# Target resolution for depth + mesh (512 is the sweet spot for speed/quality)
TARGET_SIZE = 512

# Room max-depth assumption (meters). Interior rooms are typically 3–8m deep.
ROOM_MAX_DEPTH = 8.0

# Focal length multiplier (approximates a standard smartphone camera)
FOCAL_LENGTH_FACTOR = 0.8

# Edge-stretch threshold: removes polygons that span across depth discontinuities
# Higher = fewer holes but more stretching; lower = cleaner edges but holes
EDGE_STRETCH_MULTIPLIER = 4.0

# Module-level cache for the local depth model (loaded once, reused)
_local_depth_pipeline = None


# ─────────────────────────────────────────────────────────────────
# IMAGE UTILITIES
# ─────────────────────────────────────────────────────────────────

def _download_image(image_url: str) -> Image.Image:
    """Download an image from a URL and return as a 512×512 PIL Image (RGB)."""
    print(f"DEBUG [RoomPipeline] Downloading image from URL...")
    response = requests.get(image_url, timeout=30)
    response.raise_for_status()
    img = Image.open(io.BytesIO(response.content)).convert("RGB")
    img = img.resize((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)
    print(f"DEBUG [RoomPipeline] Image downloaded and resized to {TARGET_SIZE}×{TARGET_SIZE}")
    return img


def _image_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    """Serialize a PIL Image to raw bytes."""
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────
# LAYER 1: HuggingFace Serverless Inference API
# ─────────────────────────────────────────────────────────────────

def _depth_via_hf_api(image: Image.Image, hf_token: str) -> np.ndarray | None:
    """
    Layer 1: Call the HuggingFace free serverless Inference API.

    Returns a numpy float32 depth array (shape: H×W), values in [0, 1],
    or None if the call fails (rate-limited, cold-start timeout, etc).

    Retries once on transient network errors.
    """
    img_bytes = _image_to_bytes(image, fmt="PNG")
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "image/png",
    }

    for attempt in range(2):
        try:
            print(f"DEBUG [RoomPipeline] Layer 1: HF Inference API (attempt {attempt + 1})...")
            response = requests.post(
                HF_DEPTH_API_URL,
                headers=headers,
                data=img_bytes,
                timeout=45,
            )
            if response.status_code == 200:
                # Response is a grayscale depth-map PNG image
                depth_img = Image.open(io.BytesIO(response.content)).convert("L")
                depth_img = depth_img.resize((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)
                depth_arr = np.array(depth_img, dtype=np.float32) / 255.0
                print("DEBUG [RoomPipeline] Layer 1: HF Inference API SUCCESS ✓")
                return depth_arr
            elif response.status_code == 503:
                print("DEBUG [RoomPipeline] Layer 1: Model loading (503) — falling to Layer 2")
                return None
            elif response.status_code == 429:
                print("DEBUG [RoomPipeline] Layer 1: Rate limited (429) — falling to Layer 2")
                return None
            else:
                print(
                    f"DEBUG [RoomPipeline] Layer 1: HTTP {response.status_code} "
                    f"— {response.text[:150]}"
                )
                return None
        except Exception as exc:
            print(f"DEBUG [RoomPipeline] Layer 1 attempt {attempt + 1} failed: {exc}")
            if attempt == 0:
                time.sleep(2)

    return None


# ─────────────────────────────────────────────────────────────────
# LAYER 2: HuggingFace Gradio Space (ZeroGPU, free GPU)
# ─────────────────────────────────────────────────────────────────

def _depth_via_gradio_space(image: Image.Image) -> np.ndarray | None:
    """
    Layer 2: Use a public HuggingFace Gradio Space running on ZeroGPU.

    The Depth-Anything-V2 space accepts an image and returns a grayscale
    depth map. We save the input image to a temp file (gradio_client
    requires a filepath), call the space, and load the result.

    Returns a numpy float32 depth array (H×W, values in [0, 1]),
    or None on queue timeout / space unavailability.
    """
    try:
        from gradio_client import Client as GradioClient, handle_file

        print("DEBUG [RoomPipeline] Layer 2: HF Gradio Space (ZeroGPU)...")

        # Save input image to temp file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image.save(tmp.name, format="PNG")
            tmp_input_path = tmp.name

        try:
            client = GradioClient(HF_DEPTH_SPACE)

            # The official Depth-Anything-V2 space API name is /predict
            # It accepts an image and returns the depth map image path
            result = client.predict(
                image=handle_file(tmp_input_path),
                api_name="/predict",
            )
        finally:
            try:
                os.unlink(tmp_input_path)
            except OSError:
                pass

        # Result can be a file path (string), a dict, or a list
        depth_path = None
        if isinstance(result, str):
            depth_path = result
        elif isinstance(result, (list, tuple)) and len(result) > 0:
            # Some versions return (raw_depth, colored_depth) — take first
            item = result[0]
            depth_path = item if isinstance(item, str) else str(item)
        elif isinstance(result, dict):
            depth_path = result.get("path") or result.get("value")

        if depth_path and os.path.exists(str(depth_path)):
            depth_img = Image.open(str(depth_path)).convert("L")
            depth_img = depth_img.resize((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)
            depth_arr = np.array(depth_img, dtype=np.float32) / 255.0
            print("DEBUG [RoomPipeline] Layer 2: Gradio Space SUCCESS ✓")
            return depth_arr

        print(f"DEBUG [RoomPipeline] Layer 2: Unexpected result format: {type(result)}")
        return None

    except Exception as exc:
        print(f"DEBUG [RoomPipeline] Layer 2: Gradio Space failed: {exc}")
        return None


# ─────────────────────────────────────────────────────────────────
# LAYER 3: Local CPU Inference (offline, always works)
# ─────────────────────────────────────────────────────────────────

def _depth_via_local_cpu(image: Image.Image) -> np.ndarray | None:
    """
    Layer 3: Run Depth-Anything-V2-Small locally on the CPU.

    The model is 94 MB and is downloaded once to ~/.cache/huggingface/.
    On your i5-1155G7 with 8 GB RAM it takes ~3–8 seconds per image.
    Uses ~1.5 GB RAM — well within your 8 GB budget.

    Returns a numpy float32 depth array (H×W, values in [0, 1]),
    or None if transformers / torch are not installed.
    """
    global _local_depth_pipeline

    try:
        # Lazy import — only pulls in torch/transformers when actually needed
        from transformers import pipeline as hf_pipeline

        if _local_depth_pipeline is None:
            print(
                "DEBUG [RoomPipeline] Layer 3: Loading Depth-Anything-V2-Small on CPU...\n"
                "         (First run downloads ~94 MB — this is a one-time operation)"
            )
            _local_depth_pipeline = hf_pipeline(
                task="depth-estimation",
                model=DEPTH_MODEL_ID,
                device=-1,  # Force CPU (-1 means CPU in HF pipelines)
            )
            print("DEBUG [RoomPipeline] Layer 3: Model loaded and cached ✓")

        print("DEBUG [RoomPipeline] Layer 3: Running local CPU depth inference...")
        result = _local_depth_pipeline(image)

        # result["depth"] is a PIL grayscale Image from the transformers pipeline
        depth_img = result["depth"]
        if not isinstance(depth_img, Image.Image):
            # Older versions return a tensor; handle both
            import torch
            depth_tensor = result.get("predicted_depth", depth_img)
            if hasattr(depth_tensor, "squeeze"):
                arr = depth_tensor.squeeze().numpy().astype(np.float32)
            else:
                arr = np.array(depth_img, dtype=np.float32)
        else:
            depth_img = depth_img.resize((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)
            arr = np.array(depth_img.convert("L"), dtype=np.float32)

        # Normalize to [0, 1]
        dmin, dmax = arr.min(), arr.max()
        if dmax > dmin:
            arr = (arr - dmin) / (dmax - dmin)
        arr = np.clip(arr.reshape(TARGET_SIZE, TARGET_SIZE), 0.0, 1.0)

        print("DEBUG [RoomPipeline] Layer 3: Local CPU depth inference SUCCESS ✓")
        return arr

    except ImportError:
        print(
            "ERROR [RoomPipeline] Layer 3: torch/transformers not installed.\n"
            "       Install with: pip install transformers torch --index-url "
            "https://download.pytorch.org/whl/cpu"
        )
        return None
    except Exception as exc:
        print(f"ERROR [RoomPipeline] Layer 3: Local CPU inference failed: {exc}")
        return None


# ─────────────────────────────────────────────────────────────────
# DEPTH WATERFALL ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────

def get_depth_map(image: Image.Image, hf_token: str | None) -> np.ndarray | None:
    """
    3-Layer waterfall: try each depth provider in order until one succeeds.

    Returns a float32 numpy array of shape (TARGET_SIZE, TARGET_SIZE),
    values in [0, 1] where 1 = closest to camera, 0 = furthest.
    Returns None only if ALL three layers fail.
    """
    # Layer 1: HF Inference API (fastest, uses remote GPU)
    if hf_token:
        depth = _depth_via_hf_api(image, hf_token)
        if depth is not None:
            return depth

    # Layer 2: HF Gradio Space (ZeroGPU, free GPU, may queue)
    depth = _depth_via_gradio_space(image)
    if depth is not None:
        return depth

    # Layer 3: Local CPU (offline fallback — always works if torch installed)
    depth = _depth_via_local_cpu(image)
    return depth  # May be None if torch not installed


# ─────────────────────────────────────────────────────────────────
# DEPTH → 3D MESH CONVERSION (Pure CPU, numpy + trimesh)
# ─────────────────────────────────────────────────────────────────

def depth_to_glb(
    depth_map: np.ndarray,
    color_image: Image.Image,
    max_depth: float = ROOM_MAX_DEPTH,
) -> str:
    """
    Convert a depth map + color image into a textured 3D room mesh (GLB).

    Algorithm:
      1. Scale depth values to real-world range [0, max_depth] meters
      2. Back-project every pixel to a 3D point using pinhole camera model
      3. Connect adjacent pixels into triangles (2 triangles per quad)
      4. Remove degenerate triangles (depth discontinuities / stretched polys)
      5. Assign per-vertex RGB colors from the original image
      6. Export as .GLB binary using trimesh

    This runs entirely on CPU using numpy. No GPU, no paid API.
    Performance on i5-1155G7: ~1–3 seconds for 512×512.

    Returns:
        Absolute path to the generated .glb temporary file.

    Raises:
        RuntimeError if trimesh is not installed.
        RuntimeError if mesh generation produces 0 valid faces.
    """
    try:
        import trimesh
    except ImportError:
        raise RuntimeError(
            "trimesh is required for GLB export. "
            "Install with: pip install trimesh"
        )

    h, w = depth_map.shape
    print(f"DEBUG [RoomPipeline] Building 3D mesh from {w}×{h} depth map...")

    # ── 1. Scale depth to metric range ─────────────────────────────
    # depth_map values are in [0, 1]; we map to [0.1, max_depth]
    # Invert: brighter = closer to camera, so z = (1 - depth) * max_depth
    z = (1.0 - depth_map.astype(np.float32)) * max_depth + 0.1

    # ── 2. Back-project pixels to 3D ───────────────────────────────
    # Pinhole camera model:
    #   X = (u - cx) * Z / fx
    #   Y = (v - cy) * Z / fy
    #   Z = depth
    fx = fy = w * FOCAL_LENGTH_FACTOR
    cx, cy = w / 2.0, h / 2.0

    u, v = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    x = (u - cx) * z / fx
    y = -(v - cy) * z / fy   # Negate Y so +Y is up in 3D space

    # Stack into (H×W, 3) vertex array
    vertices = np.stack([x, y, -z], axis=-1).reshape(-1, 3)

    # ── 3. Per-vertex colors from the original image ────────────────
    color_resized = np.array(color_image.resize((w, h)), dtype=np.uint8)  # (H, W, 3)
    vertex_colors = color_resized.reshape(-1, 3)

    # ── 4. Build triangle faces from the pixel grid ─────────────────
    # For each 2×2 pixel quad, create 2 triangles:
    #   [top-left, bottom-left, top-right]  +  [top-right, bottom-left, bottom-right]
    row_idx = np.arange(h - 1, dtype=np.int32)
    col_idx = np.arange(w - 1, dtype=np.int32)
    rr, cc = np.meshgrid(row_idx, col_idx, indexing="ij")

    tl = (rr * w + cc).ravel()           # top-left
    bl = ((rr + 1) * w + cc).ravel()     # bottom-left
    tr = (rr * w + (cc + 1)).ravel()     # top-right
    br = ((rr + 1) * w + (cc + 1)).ravel()  # bottom-right

    tri_a = np.stack([tl, bl, tr], axis=1)  # triangle A
    tri_b = np.stack([tr, bl, br], axis=1)  # triangle B
    faces = np.vstack([tri_a, tri_b]).astype(np.int32)

    # ── 5. Remove depth-discontinuity triangles (stretched polys) ───
    # Compute the max edge length for each triangle
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]

    e01 = np.linalg.norm(v1 - v0, axis=1)
    e12 = np.linalg.norm(v2 - v1, axis=1)
    e20 = np.linalg.norm(v0 - v2, axis=1)
    max_edge = np.maximum(np.maximum(e01, e12), e20)

    # Threshold: triangles with edges > median × multiplier are discarded
    median_edge = np.median(max_edge)
    valid_mask = max_edge < (median_edge * EDGE_STRETCH_MULTIPLIER)
    faces = faces[valid_mask]

    n_faces = len(faces)
    print(
        f"DEBUG [RoomPipeline] Mesh: {len(vertices):,} vertices, "
        f"{n_faces:,} faces after edge filtering"
    )

    if n_faces == 0:
        raise RuntimeError("Mesh generation produced 0 valid faces — depth map may be uniform")

    # ── 6. Build trimesh and export as GLB ──────────────────────────
    # Add alpha=255 to vertex colors (trimesh expects RGBA)
    alpha = np.full((len(vertex_colors), 1), 255, dtype=np.uint8)
    vertex_colors_rgba = np.hstack([vertex_colors, alpha])

    mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=faces,
        vertex_colors=vertex_colors_rgba,
        process=False,  # Skip expensive processing for speed
    )

    # Write to a temp file
    glb_tmp = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
    glb_path = glb_tmp.name
    glb_tmp.close()

    mesh.export(glb_path, file_type="glb")
    glb_size_mb = os.path.getsize(glb_path) / (1024 * 1024)
    print(f"DEBUG [RoomPipeline] GLB exported: {glb_path} ({glb_size_mb:.1f} MB)")

    return glb_path


# ─────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────

def run_room_pipeline(
    image_url: str,
    hf_token: str | None = None,
) -> str | None:
    """
    Full pipeline: Download → Depth (3-layer waterfall) → GLB Mesh.

    Args:
        image_url:  Public URL of the AI-generated room design image
        hf_token:   HuggingFace API token (used in Layer 1; optional
                    but strongly recommended for faster response)

    Returns:
        Absolute path to the generated .glb file, or None on failure.
    """
    print("\n━━━ Room 3D Pipeline START ━━━")
    t_start = time.time()

    # Step 1: Download the image
    try:
        image = _download_image(image_url)
    except Exception as exc:
        print(f"FATAL [RoomPipeline] Could not download image: {exc}")
        return None

    # Step 2: Get depth map via 3-layer waterfall
    depth_map = get_depth_map(image, hf_token)
    if depth_map is None:
        print("FATAL [RoomPipeline] All depth layers failed. Cannot generate 3D room.")
        return None

    # Step 3: Convert depth + color → GLB mesh
    try:
        glb_path = depth_to_glb(depth_map, image)
    except Exception as exc:
        print(f"FATAL [RoomPipeline] Mesh generation failed: {exc}")
        return None

    elapsed = time.time() - t_start
    print(f"━━━ Room 3D Pipeline COMPLETE ✓  ({elapsed:.1f}s) ━━━\n")
    return glb_path
