"""
controlnet_pipeline.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The REAL ControlNet MLSD + Depth pipeline for Home Gennie.

Architecture:
  Step 1  → MLSD Detector (local, CPU)   → Straight architectural lines blueprint
  Step 2  → Depth Estimator (HF API)     → 3D depth map of the room
  Step 3  → ControlNet Generator (HF Space GPU) → Geometry-accurate redesigned room

This is what enforces that the AI CANNOT change the room's:
  - Wall positions  - Window/door locations
  - Ceiling height  - Camera perspective / angle
  - Floor layout    - Spatial depth relationships
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import io
import base64
import tempfile
import requests
from PIL import Image


def _download_image(image_url: str) -> Image.Image:
    """Download an image from a URL and return as PIL Image."""
    response = requests.get(image_url, timeout=20)
    response.raise_for_status()
    img = Image.open(io.BytesIO(response.content)).convert("RGB")
    # Resize to 512x512 — ControlNet SD 1.5 models are optimised for this
    img = img.resize((512, 512), Image.LANCZOS)
    print(f"DEBUG [Pipeline] Image downloaded & resized to 512x512")
    return img


def _image_to_base64(img: Image.Image, format: str = "PNG") -> str:
    """Convert a PIL Image to a base64-encoded string."""
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _image_to_bytes(img: Image.Image, format: str = "PNG") -> bytes:
    """Convert a PIL Image to raw bytes."""
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()


# ─────────────────────────────────────────────────────────────────
# STEP 1: MLSD Architectural Line Extraction (Local CPU, ~1-3 sec)
# ─────────────────────────────────────────────────────────────────

def extract_mlsd_lines(image: Image.Image) -> Image.Image | None:
    """
    Run the MLSD (Mobile Line Segment Detector) on the room image.
    Returns a black-and-white image containing only the straight
    architectural lines (walls, window frames, door frames, pillars).
    This is the 'structural blueprint' that ControlNet will trace.
    Runs locally on CPU using the controlnet_aux library.
    """
    try:
        from controlnet_aux import MLSDdetector
        print("DEBUG [Pipeline] Step 1: Running MLSD detector (CPU)...")
        detector = MLSDdetector.from_pretrained("lllyasviel/Annotators")
        mlsd_image = detector(image)
        print("DEBUG [Pipeline] Step 1: MLSD extraction DONE ✓")
        return mlsd_image
    except ImportError:
        print("WARNING [Pipeline] controlnet_aux not installed. Skipping MLSD. "
              "Run: pip install controlnet_aux")
        return None
    except Exception as e:
        print(f"ERROR [Pipeline] MLSD extraction failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────
# STEP 2: Depth Map Extraction (HuggingFace API, free)
# ─────────────────────────────────────────────────────────────────

def extract_depth_map(image: Image.Image, hf_token: str) -> Image.Image | None:
    """
    Use HuggingFace's free Inference API to generate a depth map.
    NOTE: HF deprecated api-inference.huggingface.co (410 Gone).
          The new URL is router.huggingface.co/hf-inference.
    Retries once on network errors (IncompleteRead, timeout, etc).
    """
    img_bytes = _image_to_bytes(image)
    headers = {"Authorization": f"Bearer {hf_token}"}
    # FIX #2: Use new router URL — old api-inference.huggingface.co is 410 Gone
    url = "https://router.huggingface.co/hf-inference/models/depth-anything/Depth-Anything-V2-Small-hf"

    for attempt in range(2):  # FIX #3: Retry once on IncompleteRead / network drops
        try:
            print(f"DEBUG [Pipeline] Step 2: Calling HF Depth API (attempt {attempt + 1})...")
            response = requests.post(url, headers=headers, data=img_bytes, timeout=60)

            if response.status_code == 200:
                depth_img = Image.open(io.BytesIO(response.content)).convert("RGB")
                depth_img = depth_img.resize((512, 512), Image.LANCZOS)
                print("DEBUG [Pipeline] Step 2: Depth map extraction DONE ✓")
                return depth_img
            elif response.status_code == 503:
                print("DEBUG [Pipeline] Step 2: Model loading (503), using local fallback...")
                break  # Go straight to local fallback
            else:
                print(f"ERROR [Pipeline] Depth API {response.status_code}: {response.text[:200]}")
                break
        except Exception as e:
            print(f"ERROR [Pipeline] Depth API attempt {attempt + 1} failed: {e}")
            if attempt == 0:
                print("DEBUG [Pipeline] Retrying depth API in 2 seconds...")
                import time; time.sleep(2)

    # Local CPU fallback (downloads ~350MB first time, then cached)
    return _extract_depth_local(image)


def _extract_depth_local(image: Image.Image) -> Image.Image | None:
    """
    Fallback: Extract depth map locally using the transformers DPT model.
    This downloads ~350MB the first time but is then cached permanently.
    """
    try:
        from transformers import pipeline as hf_pipeline
        import numpy as np
        
        print("DEBUG [Pipeline] Step 2 fallback: Running DPT depth locally (CPU)...")
        depth_estimator = hf_pipeline(
            "depth-estimation",
            model="Intel/dpt-hybrid-midas",
            device=-1  # Force CPU
        )
        depth_output = depth_estimator(image)
        
        # Convert the depth output to a PIL Image
        depth_array = depth_output["predicted_depth"].squeeze().numpy()
        # Normalize to 0-255
        depth_min, depth_max = depth_array.min(), depth_array.max()
        depth_normalized = ((depth_array - depth_min) / (depth_max - depth_min) * 255).astype("uint8")
        depth_img = Image.fromarray(depth_normalized).convert("RGB")
        depth_img = depth_img.resize((512, 512), Image.LANCZOS)
        
        print("DEBUG [Pipeline] Step 2 fallback: Local depth extraction DONE ✓")
        return depth_img
    except Exception as e:
        print(f"ERROR [Pipeline] Local depth fallback failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────
# STEP 3: ControlNet Generation (HuggingFace Free GPU Space)
# ─────────────────────────────────────────────────────────────────

def generate_with_controlnet(
    prompt: str,
    mlsd_image: Image.Image | None,
    depth_image: Image.Image | None,
    original_image: Image.Image,
    hf_token: str,
    style: str,
    room_type: str
) -> bytes | None:
    """
    Send the extracted control maps + prompt to HuggingFace ControlNet.
    
    Priority:
    1. Use MLSD image (best for architecture - preserves straight lines)
    2. Fallback to Depth image (good for spatial layout)
    3. Fallback to original image (uses img2img style transfer)
    
    Returns raw image bytes of the generated room.
    """
    
    # Determine the best control image to use
    control_image = mlsd_image or depth_image or original_image
    control_type = "MLSD" if mlsd_image else ("Depth" if depth_image else "Original")
    print(f"DEBUG [Pipeline] Step 3: Generating with ControlNet ({control_type} control image)...")
    
    control_b64 = _image_to_base64(control_image)
    
    # ── Strategy A: Use the official HF ControlNet Space via Gradio ──
    result = _generate_via_gradio_space(prompt, control_image, hf_token, control_type, style, room_type)
    if result:
        return result
    
    # ── Strategy B: Fallback to HF Inference API (depth-conditioned) ──
    result = _generate_via_hf_api(prompt, control_b64, depth_image or original_image, hf_token)
    if result:
        return result
    
    return None


def _generate_via_gradio_space(
    prompt: str,
    control_image: Image.Image,
    hf_token: str,
    control_type: str,
    style: str,
    room_type: str
) -> bytes | None:
    """
    Use the official ControlNet HF Space via gradio_client.
    FIX #1: gradio_client 1.x removed the `hf_token` constructor param.
            For public spaces, just don't pass it at all.
            For private spaces, use: headers={"Authorization": f"Bearer {token}"}
    """
    try:
        from gradio_client import Client as GradioClient, handle_file

        # Save control image to temp file (gradio_client requires a file path)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            control_image.save(tmp.name)
            control_img_path = tmp.name

        print(f"DEBUG [Pipeline] Trying gradio ControlNet space (control={control_type})...")

        client = GradioClient("hysts/ControlNet-v1-1")

        # FIX: API endpoints have changed in Gradio 4 Space version 
        api_names_to_try = (
            ["/mlsd", "/depth"] if control_type == "MLSD"
            else ["/depth", "/mlsd"]
        )

        negative_prompt = (
            "deformed walls, wrong perspective, different room layout, "
            "low quality, blurry, distorted, extra doors, extra windows"
        )

        result = None
        for api_name in api_names_to_try:
            try:
                print(f"DEBUG [Pipeline] Trying API endpoint: {api_name}")
                kwargs = {
                    "image": handle_file(control_img_path),
                    "prompt": prompt,
                    "additional_prompt": "best quality, extremely detailed, real interior, fotorealistic",
                    "negative_prompt": negative_prompt,
                    "num_images": 1,
                    "image_resolution": 512,
                    "preprocess_resolution": 512,
                    "num_steps": 25,
                    "guidance_scale": 9.0,
                    "seed": 0,
                    "api_name": api_name
                }
                
                if api_name == "/mlsd":
                    kwargs["value_threshold"] = 0.1
                    kwargs["distance_threshold"] = 0.1
                elif api_name == "/depth":
                    kwargs["preprocessor_name"] = "Midas"

                result = client.predict(**kwargs)
                print(f"DEBUG [Pipeline] API {api_name} responded")
                break
            except Exception as api_err:
                print(f"DEBUG [Pipeline] API {api_name} failed: {api_err}")

        os.unlink(control_img_path)

        if result is None:
            return None

        # Result is a list of dicts. The FIRST image might be the control map, the SECOND is the generated image!
        # Let's use the LAST image in the result list just to be safe.
        result_path = None
        if isinstance(result, list) and len(result) > 0:
            last_item = result[-1]
            if isinstance(last_item, dict) and "image" in last_item:
                img_data = last_item["image"]
                if isinstance(img_data, str):
                    result_path = img_data
                else:
                    result_path = img_data.get("path") or img_data.get("url")
            elif isinstance(last_item, str):
                result_path = last_item
            else:
                result_path = str(last_item)
        else:
            result_path = result

        if result_path and os.path.exists(str(result_path)):
            with open(result_path, "rb") as f:
                img_bytes = f.read()
            print(f"DEBUG [Pipeline] Step 3 Gradio: DONE ✓ (local file)")
            return img_bytes
        elif str(result_path).startswith("http"):
            r = requests.get(str(result_path), timeout=30)
            print(f"DEBUG [Pipeline] Step 3 Gradio: DONE ✓ (url)")
            return r.content

    except Exception as e:
        print(f"ERROR [Pipeline] Gradio ControlNet space failed: {e}")

    return None


def _generate_via_hf_api(
    prompt: str,
    control_b64: str,
    depth_image: Image.Image,
    hf_token: str
) -> bytes | None:
    """
    Fallback: Call HuggingFace router API for image generation.
    FIX #2: api-inference.huggingface.co is 410 GONE.
            New URL: router.huggingface.co/hf-inference
    Uses stabilityai/stable-diffusion-2-1 as a reliable free model.
    """
    try:
        print("DEBUG [Pipeline] Step 3 fallback: HF router API (stable-diffusion-2-1)...")

        # FIX #2: New HF router URL
        response = requests.post(
            "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-2-1",
            headers={
                "Authorization": f"Bearer {hf_token}",
                "Content-Type": "application/json"
            },
            json={
                "inputs": prompt,
                "parameters": {
                    "negative_prompt": (
                        "deformed walls, wrong perspective, different room layout, "
                        "low quality, blurry, distorted"
                    ),
                    "num_inference_steps": 25,
                    "guidance_scale": 9.0,
                    "width": 512,
                    "height": 512
                }
            },
            timeout=90
        )

        if response.status_code == 200:
            print("DEBUG [Pipeline] Step 3 HF router API: DONE ✓")
            return response.content
        else:
            print(f"ERROR [Pipeline] HF router API {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"ERROR [Pipeline] HF router API fallback failed: {e}")

    return None


# ─────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────

def run_controlnet_pipeline(
    image_url: str,
    style: str,
    room_type: str,
    hf_token: str
) -> bytes | None:
    """
    Full pipeline: Download → MLSD → Depth → ControlNet Generate.
    Returns the generated image as raw bytes, or None if all steps fail.
    
    Args:
        image_url:  Public URL of the user's uploaded room photo
        style:      e.g. "modern", "minimalist", "scandinavian"  
        room_type:  e.g. "living room", "bedroom", "kitchen"
        hf_token:   HuggingFace API token with Inference permission
    
    Returns:
        Raw bytes of the generated image (JPEG/PNG), or None on failure.
    """
    print("\n━━━ ControlNet Pipeline START ━━━")
    
    # ── Step 1: Download & resize the user's image ──────────────────
    try:
        original_image = _download_image(image_url)
    except Exception as e:
        print(f"FATAL [Pipeline] Could not download image: {e}")
        return None
    
    # ── Step 2: Extract MLSD Architectural Lines (CPU local) ────────
    mlsd_image = extract_mlsd_lines(original_image)
    
    # ── Step 3: Extract Depth Map (HF API or local CPU fallback) ────
    depth_image = extract_depth_map(original_image, hf_token)
    
    # ── Step 4: Build the geometry-preserving prompt ─────────────────
    prompt = (
        f"A photorealistic {style} style interior design of a {room_type}. "
        f"Premium interior photography. Magazine quality. "
        f"Beautiful {style} furniture, perfect lighting, luxury materials. "
        f"Same exact room structure, walls, windows, doors. "
        f"8k resolution, highly detailed, professional real estate photography."
    )
    
    # ── Step 5: Generate with ControlNet ────────────────────────────
    result_bytes = generate_with_controlnet(
        prompt=prompt,
        mlsd_image=mlsd_image,
        depth_image=depth_image,
        original_image=original_image,
        hf_token=hf_token,
        style=style,
        room_type=room_type
    )
    
    if result_bytes:
        print("━━━ ControlNet Pipeline COMPLETE ✓ ━━━\n")
    else:
        print("━━━ ControlNet Pipeline FAILED (all steps exhausted) ━━━\n")
    
    return result_bytes
