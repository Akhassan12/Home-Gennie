import os
import time
import shutil
import base64
import tempfile
import requests
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import replicate
from gradio_client import Client as GradioClient, handle_file

load_dotenv()

app = FastAPI(title="Home Gennie API")

# ── Local static file server for GLB fallback ─────────────────────
# When Supabase upload fails, GLB files are served from here instead.
# Accessible at: http://localhost:8000/static/models/<filename>.glb
# On HuggingFace Spaces, SPACE_HOST is set automatically.
BACKEND_BASE_URL = os.environ.get("SPACE_HOST", "http://localhost:8000")
if BACKEND_BASE_URL and not BACKEND_BASE_URL.startswith("http"):
    BACKEND_BASE_URL = f"https://{BACKEND_BASE_URL}"

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_MODELS_DIR = os.path.join(_BACKEND_DIR, "static", "models")
os.makedirs(STATIC_MODELS_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=os.path.join(_BACKEND_DIR, "static")), name="static")

# Define allowed frontend origins
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
if os.environ.get("FRONTEND_URL"):
    origins.append(os.environ.get("FRONTEND_URL"))

# Enable CORS for the React frontend safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase Client settings
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

class GenerateRequest(BaseModel):
    userId: str
    originalImageUrl: str
    style: str
    roomType: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

def _update_supabase_record(design_id: str, generated_url: str, auth_header: str):
    """Helper to update database once background task finishes."""
    if not supabase_url or not supabase_key or not auth_header: return
    try:
        print(f"DEBUG: Updating database record {design_id}...")
        headers = {
            "apikey": supabase_key,
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        res = requests.patch(
            f"{supabase_url}/rest/v1/designs?id=eq.{design_id}",
            headers=headers,
            json={"generated_image_url": generated_url},
            timeout=10
        )
        res.raise_for_status()
        print("DEBUG: Database update successful!")
    except Exception as e:
        print(f"UPDATE ERROR: {str(e)}")

def _delete_supabase_record(design_id: str, auth_header: str):
    if not supabase_url or not supabase_key or not auth_header: return
    try:
        headers = { "apikey": supabase_key, "Authorization": auth_header }
        requests.delete(f"{supabase_url}/rest/v1/designs?id=eq.{design_id}", headers=headers, timeout=10)
    except: pass


def _upload_bytes_to_supabase(image_bytes: bytes, user_id: str, auth_header: str, label: str) -> str | None:
    """
    Upload raw image bytes to Supabase Storage and return the permanent public URL.
    This is the ONLY place images should be stored — never save expiring CDN URLs.

    Args:
        image_bytes:  Raw JPEG/PNG/WebP bytes of the generated image
        user_id:      The authenticated user's UUID (used as folder prefix)
        auth_header:  The "Bearer <jwt>" auth header from the original request
        label:        Short tag for the filename (e.g. 'controlnet', 'horde', 'replicate')

    Returns:
        Permanent Supabase public URL string, or None if upload fails.
    """
    if not supabase_url or not supabase_key:
        print(f"UPLOAD ERROR: Missing supabase_url or supabase_key")
        return None
    try:
        # Prefer service role key for uploads — bypasses RLS for server-side operations.
        # Fall back to user JWT if service key not configured.
        svc_key = os.environ.get("SUPABASE_SERVICE_KEY") or supabase_key
        upload_auth = f"Bearer {svc_key}" if svc_key != supabase_key else auth_header

        file_name = f"{user_id}/{int(time.time())}_{label}.jpg"
        print(f"DEBUG: Uploading {label} image to Supabase Storage ({len(image_bytes)} bytes)...")
        res = requests.post(
            f"{supabase_url}/storage/v1/object/designs/{file_name}",
            headers={"apikey": supabase_key, "Authorization": upload_auth},
            files={"file": (file_name, image_bytes, "image/jpeg")},
            timeout=30
        )
        if res.status_code in (200, 201):
            permanent_url = f"{supabase_url}/storage/v1/object/public/designs/{file_name}"
            print(f"DEBUG: Supabase upload SUCCESS -> {permanent_url}")
            return permanent_url
        else:
            print(f"UPLOAD ERROR [{res.status_code}]: {res.text[:300]}")
            return None
    except Exception as e:
        print(f"UPLOAD ERROR: {str(e)}")
        return None


def _download_image_bytes(url: str, timeout: int = 30) -> bytes | None:
    """Download raw bytes from any URL. Returns None on failure."""
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.content
    except Exception as e:
        print(f"DOWNLOAD ERROR: {str(e)}")
        return None

def _generate_with_fallbacks(req: GenerateRequest, prompt: str, design_id: str, auth_header: str):
    """Multi-Layer Zero-Fail Free Pipeline running in background."""
    print("DEBUG: Starting Background Generation Pipeline...")
    generated_url = None
    hf_token = os.environ.get("HF_TOKEN")
    replicate_key = os.environ.get("REPLICATE_API_TOKEN")
    # ══════════════════════════════════════════════════════════════
    # Layer 1: REAL ControlNet MLSD + Depth Pipeline (Primary)
    # ══════════════════════════════════════════════════════════════
    # This is the proper geometry-preserving pipeline:
    #   → Extract MLSD architectural lines from the room (CPU, local)
    #   → Extract 3D depth map (HF Inference API, free)
    #   → Generate with ControlNet conditioned on both maps (HF GPU Space, free)
    # The AI CANNOT change walls, windows, doors or camera angle.
    if hf_token:
        print("DEBUG: [Layer 1] Starting real ControlNet MLSD+Depth pipeline...")
        try:
            from controlnet_pipeline import run_controlnet_pipeline
            result_bytes = run_controlnet_pipeline(
                image_url=req.originalImageUrl,
                style=req.style,
                room_type=req.roomType,
                hf_token=hf_token
            )
            if result_bytes:
                generated_url = _upload_bytes_to_supabase(result_bytes, req.userId, auth_header, "controlnet")
                if generated_url:
                    print(f"DEBUG: [Layer 1] ControlNet Pipeline Success! URL: {generated_url}")
                else:
                    print(f"DEBUG: [Layer 1] Supabase upload failed after ControlNet generation")
        except Exception as e:
            print(f"DEBUG: [Layer 1] ControlNet Pipeline Error: {str(e)}")


    # Layer 2: Replicate API (Fallback if ControlNet fails)
    # IMPORTANT: Replicate returns a CDN URL that EXPIRES — must download + reupload to Supabase.
    if not generated_url and replicate_key:
        print("DEBUG: [Layer 2] Generating with Replicate (SDXL)...")
        try:
            output = replicate.run(
                "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                input={
                    "prompt": prompt,
                    "num_outputs": 1,
                    "scheduler": "K_EULER",
                    "num_inference_steps": 25,
                    "guidance_scale": 7.5
                }
            )
            if output and len(output) > 0:
                replicate_cdn_url = str(output[0])
                print(f"DEBUG: [Layer 2] Replicate generated image, downloading to re-upload...")
                # Download the image (expiring Replicate URL) and permanently store in Supabase
                img_bytes = _download_image_bytes(replicate_cdn_url)
                if img_bytes:
                    generated_url = _upload_bytes_to_supabase(img_bytes, req.userId, auth_header, "replicate")
                    if generated_url:
                        print(f"DEBUG: [Layer 2] Replicate+Supabase Success! URL: {generated_url}")
        except Exception as e:
            print(f"DEBUG: [Layer 2] Replicate Error: {str(e)}")

    # Layer 3: AI Horde (Free anonymous fallback)
    # IMPORTANT: AI Horde returns a signed Cloudflare R2 URL that EXPIRES IN 30 MINUTES.
    # We MUST download the image immediately and re-upload to Supabase for permanent storage.
    if not generated_url:
        print("DEBUG: [Layer 3] Generating with AI Horde...")
        try:
            horde_url = "https://stablehorde.net/api/v2/generate/async"
            horde_payload = {
                "prompt": prompt,
                "params": {"sampler_name": "k_euler", "height": 512, "width": 512, "steps": 20, "n": 1}
            }
            h_res = requests.post(horde_url, headers={"apikey": "0000000000"}, json=horde_payload, timeout=15)
            if h_res.status_code == 202:
                req_id = h_res.json()["id"]
                for i in range(120):
                    time.sleep(5)
                    s_res = requests.get(f"https://stablehorde.net/api/v2/generate/status/{req_id}", timeout=10)
                    if s_res.json().get("done"):
                        generations = s_res.json().get("generations", [])
                        if generations:
                            horde_signed_url = generations[0]["img"]
                            print(f"DEBUG: [Layer 3] AI Horde image ready (signed URL expires in 30min). Downloading...")
                            # Download immediately before the signed URL expires
                            img_bytes = _download_image_bytes(horde_signed_url, timeout=45)
                            if img_bytes:
                                # Re-upload to Supabase for permanent storage
                                generated_url = _upload_bytes_to_supabase(img_bytes, req.userId, auth_header, "horde")
                                if generated_url:
                                    print(f"DEBUG: [Layer 3] AI Horde+Supabase Success! Permanent URL: {generated_url}")
                            break
            else:
                print(f"DEBUG: [Layer 3] Horde rejected: {h_res.text}")
        except Exception as e:
            print(f"DEBUG: [Layer 3] AI Horde Error: {str(e)}")

    # Layer 4: HuggingFace Instruct-Pix2Pix (Secondary Fallback)
    if not generated_url and hf_token:
        print("DEBUG: [Layer 4] Falling back to HuggingFace Instruct-Pix2Pix...")
        try:
            # Download original image and encode as base64
            img_data = requests.get(req.originalImageUrl, timeout=15).content
            img_b64 = base64.b64encode(img_data).decode("utf-8")
            
            # Instruct-Pix2Pix: send image + text instruction as JSON
            pix2pix_prompt = (
                f"Redesign the interior of this exact room in {req.style} style. "
                f"Keep all walls, windows, doors and floor layout exactly the same. "
                f"Only change the furniture, colors, decor and materials."
            )
            # FIX: api-inference.huggingface.co is 410 Gone — use router.huggingface.co
            res = requests.post(
                "https://router.huggingface.co/hf-inference/models/timbrooks/instruct-pix2pix",
                headers={"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"},
                json={"inputs": img_b64, "parameters": {"prompt": pix2pix_prompt}},
                timeout=90
            )
            if res.status_code == 200:
                # Upload response bytes directly — no temp file needed
                generated_url = _upload_bytes_to_supabase(res.content, req.userId, auth_header, "pix2pix")
                if generated_url:
                    print(f"DEBUG: [Layer 4] Pix2Pix Success! URL: {generated_url}")
            else:
                print(f"DEBUG: [Layer 4] HF Pix2Pix Error ({res.status_code}): {res.text}")
        except Exception as e:
            print(f"DEBUG: [Layer 4] HF Secondary Error: {str(e)}")

    # Finalizer: Update record on success, or mark as failed (NEVER delete — user keeps their upload)
    if generated_url:
        _update_supabase_record(design_id, generated_url, auth_header)
    else:
        print("WARNING: All generation layers failed. Marking record as 'failed' (original image preserved).")
        _update_supabase_record(design_id, "failed", auth_header)


@app.post("/generate")
async def generate_design(req: GenerateRequest, request: Request, background_tasks: BackgroundTasks):
    print(f"\n--- NEW ASYNC GENERATION REQUEST ---")
    print(f"User ID: {req.userId}, Room: {req.roomType}, Style: {req.style}")
    
    auth_header = request.headers.get("Authorization")
    prompt = (
        f"Redesign this exact room as a {req.style} style {req.roomType}. "
        f"IMPORTANT: Keep the exact same room layout, wall positions, windows, doors, "
        f"ceiling height, and floor geometry. Only change the furniture, decor, colors, "
        f"materials and lighting. Same perspective and camera angle. "
        f"Photorealistic, interior design magazine quality, 8k, highly detailed."
    )
    design_id = None

    # 1. Insert pending record into Supabase instantly
    if supabase_url and supabase_key and auth_header:
        try:
            print(f"DEBUG: Inserting 'pending' record into 'designs' table...")
            headers = {
                "apikey": supabase_key,
                "Authorization": auth_header,
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
            payload = {
                "user_id": req.userId,
                "original_image_url": req.originalImageUrl,
                "generated_image_url": "pending",
                "style": req.style,
                "room_type": req.roomType,
                "prompt_used": prompt
            }
            res = requests.post(f"{supabase_url}/rest/v1/designs", headers=headers, json=payload, timeout=10)
            res.raise_for_status()
            data = res.json()
            if data and len(data) > 0:
                design_id = data[0]['id']
                print(f"DEBUG: Success! 'Pending' record created. ID: {design_id}")
            else:
                raise Exception("Database insert returned no data")
        except Exception as e:
            print(f"DATABASE ERROR: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database REST Error: {str(e)}")

    # 2. Dispatch Background Task to handle the 3-Layer Waterfall
    if design_id:
        background_tasks.add_task(_generate_with_fallbacks, req, prompt, design_id, auth_header)
    
    # 3. Return immediately so React frontend can navigate to Gallery without Timeout!
    return {
        "success": True,
        "designId": design_id,
        "status": "processing",
        "message": "Generation started in the background via Free AI Networks."
    }


class Generate3DRequest(BaseModel):
    imageUrl: str
    userId: str = ""

def _upload_glb_to_supabase(glb_path: str, user_id: str, auth_header: str, storage_auth: str = None) -> dict | None:
    """
    Upload a local .glb file to Supabase Storage and return the success response dict.
    Path format: {user_id}/3d_models/{timestamp}_{filename}
    The user_id prefix is REQUIRED to satisfy the bucket's RLS policy.
    storage_auth: use service role key if available to bypass RLS; defaults to auth_header.
    Returns a dict like {"success": True, "glbUrl": "<public_url>"} or None on failure.
    """
    upload_auth = storage_auth if storage_auth else auth_header
    if not supabase_url or not supabase_key:
        return None
    try:
        user_folder = user_id if user_id else "anonymous"
        file_name = f"{user_folder}/3d_models/{int(time.time())}_{os.path.basename(glb_path)}"
        print(f"DEBUG: Uploading GLB to Supabase Storage → models/{file_name}")
        with open(glb_path, "rb") as f:
            upload_headers = {"apikey": supabase_key, "Authorization": upload_auth}
            # Note: upload_auth must be a valid user JWT or service role key to pass RLS
            files = {"file": (file_name, f, "application/octet-stream")}
            res = requests.post(
                f"{supabase_url}/storage/v1/object/models/{file_name}",
                headers=upload_headers, files=files, timeout=300
            )
        if res.status_code in (200, 201):
            public_url = f"{supabase_url}/storage/v1/object/public/models/{file_name}"
            print(f"DEBUG: GLB Upload Success → {public_url}")
            return {"success": True, "glbUrl": public_url}
        else:
            print(f"DEBUG: GLB Upload Failed [{res.status_code}]: {res.text}")
            return None
    except Exception as e:
        print(f"GLB UPLOAD ERROR: {str(e)}")
        return None

@app.post("/generate-3d")
async def generate_3d_model(req: Generate3DRequest, request: Request):
    print(f"\n--- NEW 3D GENERATION REQUEST ---")
    print(f"Image URL: {req.imageUrl}")
    
    hf_token = os.environ.get("HF_TOKEN")
    meshy_key = os.environ.get("MESHY_API_KEY")
    tripo_key = os.environ.get("TRIPO_API_KEY")
    replicate_key = os.environ.get("REPLICATE_API_TOKEN")
    auth_header = request.headers.get("Authorization", f"Bearer {supabase_key}")
    # `or supabase_key` handles the case where SUPABASE_SERVICE_KEY= is blank in .env
    service_key = os.environ.get("SUPABASE_SERVICE_KEY") or supabase_key
    # Prefer service role key (bypasses RLS); fall back to user JWT from request
    storage_auth = f"Bearer {service_key}" if service_key != supabase_key else auth_header
    is_service = service_key != supabase_key
    is_jwt = auth_header and auth_header != f"Bearer {supabase_key}"
    print(f"DEBUG: storage_auth = {'SERVICE_ROLE KEY' if is_service else ('USER JWT' if is_jwt else 'ANON KEY (will fail RLS)')}")


    # 1. Replicate (Prioritized as requested)
    if replicate_key:
        print(f"DEBUG: Calling Replicate API for Image-to-3D (firtoz/trellis)...")
        try:
            output = replicate.run(
                "firtoz/trellis:e8f6c45206993f297372f5436b90350817bd9b4a0d52d2a76df50c1c8afa2b3c",
                input={
                    "images": [req.imageUrl],  # API takes a list of image URLs
                    "generate_model": True,     # CRITICAL: must be True to get the .glb file
                    "generate_color": True,
                    "texture_size": 1024,
                    "mesh_simplify": 0.95,
                    "randomize_seed": True,
                }
            )
            
            generated_glb_url = None
            if isinstance(output, dict) and "model_file" in output:
                 generated_glb_url = str(output["model_file"])
            elif isinstance(output, str):
                 generated_glb_url = str(output)
            elif isinstance(output, list) and len(output) > 0:
                 generated_glb_url = str(output[0])
                
            if not generated_glb_url:
                raise Exception(f"Unrecognized output format from Replicate: {output}")

            print(f"DEBUG: Replicate Image-to-3D Success. GLB URL: {generated_glb_url}")
            return {
                "success": True,
                "glbUrl": generated_glb_url
            }
        except Exception as e:
            print(f"REPLICATE 3D ERROR: {str(e)}")
            print("Replicate Failed, falling back to other providers...")

    # 2. HuggingFace Free Alternative — Official Microsoft TRELLIS Space
    if hf_token or os.environ.get("USE_FREE_MODE", "false").lower() == "true":
        print("DEBUG: Using HuggingFace TRELLIS (Free) for Image-to-3D...")
        try:
            import tempfile, urllib.request
            from gradio_client import Client as GradioClient, handle_file
            
            # Download the image to a temp file (Gradio needs a local filepath)
            print("DEBUG: Downloading source image for HF TRELLIS...")
            tmp_img = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            urllib.request.urlretrieve(req.imageUrl, tmp_img.name)
            tmp_img.close()
            print(f"DEBUG: Image saved to {tmp_img.name}")

            client = GradioClient("JeffreyXiang/TRELLIS")

            print("DEBUG: TRELLIS - Starting session...")
            client.predict(api_name="/start_session")

            print("DEBUG: TRELLIS - Preprocessing image...")
            processed = client.predict(
                image=handle_file(tmp_img.name),
                api_name="/preprocess_image"
            )
            preprocessed_path = processed if isinstance(processed, str) else tmp_img.name
            print(f"DEBUG: TRELLIS - Preprocessed image at: {preprocessed_path}")

            print("DEBUG: TRELLIS - Running image_to_3d generation...")
            client.predict(
                image=handle_file(preprocessed_path),
                multiimages=[],
                seed=0,
                ss_guidance_strength=7.5,
                ss_sampling_steps=12,
                slat_guidance_strength=3.0,
                slat_sampling_steps=12,
                multiimage_algo="stochastic",
                api_name="/image_to_3d"
            )

            print("DEBUG: TRELLIS - Extracting GLB mesh...")
            glb_result = client.predict(
                mesh_simplify=0.95,
                texture_size=1024,
                api_name="/extract_glb"
            )

            glb_path = None
            if isinstance(glb_result, (list, tuple)) and len(glb_result) >= 2:
                glb_path = glb_result[1]
            elif isinstance(glb_result, str):
                glb_path = glb_result

            if not glb_path or not os.path.exists(str(glb_path)):
                raise Exception(f"Failed to extract GLB from TRELLIS output: {glb_result}")

            print(f"DEBUG: TRELLIS Success. Local Path: {glb_path}")
            result = _upload_glb_to_supabase(str(glb_path), req.userId, auth_header, storage_auth)
            if result:
                return result

        except Exception as e:
            print(f"HF TRELLIS ERROR: {str(e)}")
            print("TRELLIS Failed, trying InstantMesh...")

    # 2.5. InstantMesh (TencentARC) — separate ZeroGPU quota from TRELLIS
    if hf_token or os.environ.get("USE_FREE_MODE", "false").lower() == "true":
        print("DEBUG: Using HuggingFace InstantMesh (Free) for Image-to-3D...")
        try:
            import tempfile, urllib.request
            from gradio_client import Client as GradioClient, handle_file

            tmp_img2 = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            urllib.request.urlretrieve(req.imageUrl, tmp_img2.name)
            tmp_img2.close()
            print(f"DEBUG: InstantMesh - Image saved to {tmp_img2.name}")

            client = GradioClient("TencentARC/InstantMesh")

            # Step 1: Preprocess (background removal)
            print("DEBUG: InstantMesh - Preprocessing image...")
            processed = client.predict(
                image=handle_file(tmp_img2.name),
                do_rembg=True,
                api_name="/preprocess"
            )
            proc_path = processed if isinstance(processed, str) else tmp_img2.name
            print(f"DEBUG: InstantMesh - Preprocessed at: {proc_path}")

            # Step 2: Generate multi-view images
            print("DEBUG: InstantMesh - Generating multi-view images...")
            mv_result = client.predict(
                image=handle_file(proc_path),
                sample_steps=75,
                sample_seed=42,
                api_name="/generate_mvs"
            )
            mv_path = mv_result if isinstance(mv_result, str) else (mv_result[0] if isinstance(mv_result, (list, tuple)) else None)
            if not mv_path:
                raise Exception(f"InstantMesh: no multi-view output: {mv_result}")
            print(f"DEBUG: InstantMesh - Multi-view at: {mv_path}")

            # Step 3: Reconstruct 3D mesh
            print("DEBUG: InstantMesh - Reconstructing 3D mesh...")
            mesh_result = client.predict(api_name="/make3d")

            glb_path = None
            if isinstance(mesh_result, (list, tuple)):
                # Returns (obj_path, glb_path)
                for item in mesh_result:
                    if isinstance(item, str) and item.endswith(".glb"):
                        glb_path = item
                        break
                if not glb_path and len(mesh_result) > 0:
                    glb_path = mesh_result[-1]
            elif isinstance(mesh_result, str):
                glb_path = mesh_result

            if not glb_path or not os.path.exists(str(glb_path)):
                raise Exception(f"InstantMesh: no GLB output: {mesh_result}")

            print(f"DEBUG: InstantMesh Success. Local Path: {glb_path}")
            result = _upload_glb_to_supabase(str(glb_path), req.userId, auth_header, storage_auth)
            if result:
                return result

        except Exception as e:
            print(f"HF InstantMesh ERROR: {str(e)}")
            print("InstantMesh Failed, falling back to other providers...")

    if meshy_key:
        print("DEBUG: Using Meshy.ai API for Image-to-3D...")
        try:
            import asyncio
            headers = {"Authorization": f"Bearer {meshy_key}"}
            payload = {"image_url": req.imageUrl, "enable_pbr": True}
            res = requests.post("https://api.meshy.ai/openapi/v1/image-to-3d", headers=headers, json=payload, timeout=30)
            res.raise_for_status()
            task_id = res.json()["result"]
            print(f"DEBUG: Meshy task started: {task_id}. Polling...")
            
            for _ in range(60): # 2 mins max
                await asyncio.sleep(2)
                p_res = requests.get(f"https://api.meshy.ai/openapi/v1/image-to-3d/{task_id}", headers=headers, timeout=20)
                p_res.raise_for_status()
                data = p_res.json()
                status = data.get("status")
                if status == "SUCCEEDED":
                    glb_url = data.get("model_urls", {}).get("glb")
                    print(f"DEBUG: Meshy Image-to-3D Success. GLB URL: {glb_url}")
                    return {"success": True, "glbUrl": glb_url}
                elif status in ["FAILED", "EXPIRED"]:
                    raise Exception(f"Meshy generation failed: {data}")
                
            raise Exception("Meshy generation timed out after 2 minutes")
        except Exception as e:
            print(f"MESHY 3D ERROR: {str(e)}")
            print("Meshy failed, falling back to Tripo3D...")
            
    if tripo_key:
        print("DEBUG: Using Tripo3D API for Image-to-3D...")
        try:
            import asyncio
            headers = {"Authorization": f"Bearer {tripo_key}", "Content-Type": "application/json"}
            # For URL-based input, Tripo3D expects the 'url' field (not 'file_token')
            payload = {"type": "image_to_model", "file": {"type": "url", "url": req.imageUrl}}
            res = requests.post("https://api.tripo3d.ai/v2/openapi/task", headers=headers, json=payload, timeout=30)
            res.raise_for_status()
            task_id = res.json()["data"]["task_id"]
            print(f"DEBUG: Tripo task started: {task_id}. Polling...")
            
            for _ in range(90):  # 3 mins max (Tripo can be slow)
                await asyncio.sleep(2)
                p_res = requests.get(f"https://api.tripo3d.ai/v2/openapi/task/{task_id}", headers=headers, timeout=20)
                p_res.raise_for_status()
                data = p_res.json()
                status = data.get("data", {}).get("status")
                if status == "success":
                    output = data.get("data", {}).get("output", {})
                    print(f"DEBUG: Tripo output keys: {list(output.keys())}")  # log for debugging
                    # Try all known output key names (API version differences)
                    glb_url = (
                        output.get("model") or
                        output.get("pbr_model") or
                        output.get("glb") or
                        output.get("base_model") or
                        next(iter(output.values()), None)  # fallback: first value
                    )
                    if not glb_url:
                        raise Exception(f"Tripo succeeded but output has no model URL: {output}")
                    print(f"DEBUG: Tripo Image-to-3D Success. URL: {glb_url}")
                    # Try to download + re-upload to Supabase for permanent storage.
                    # If this fails for any reason (network reset, size limit, etc.),
                    # fall back to the Tripo CDN URL — it's signed and valid for ~1 year.
                    try:
                        glb_bytes = _download_image_bytes(glb_url, timeout=90)
                        if glb_bytes and supabase_url and supabase_key:
                            user_folder = req.userId if req.userId else "anonymous"
                            file_name = f"{user_folder}/3d_models/{int(time.time())}_tripo.glb"
                            upload_headers = {"apikey": supabase_key, "Authorization": storage_auth}
                            up_res = requests.post(
                                f"{supabase_url}/storage/v1/object/models/{file_name}",
                                headers=upload_headers,
                                files={"file": (file_name, glb_bytes, "application/octet-stream")},
                                timeout=300
                            )
                            if up_res.status_code in (200, 201):
                                public_url = f"{supabase_url}/storage/v1/object/public/models/{file_name}"
                                print(f"DEBUG: Tripo GLB uploaded to Supabase: {public_url}")
                                return {"success": True, "glbUrl": public_url}
                            else:
                                print(f"DEBUG: Supabase upload failed [{up_res.status_code}], using CDN URL")
                    except Exception as upload_err:
                        print(f"DEBUG: Tripo upload to Supabase failed ({upload_err}), using CDN URL as fallback")
                    # Fallback: Tripo CDN URL (signed, valid ~1 year)
                    return {"success": True, "glbUrl": glb_url}
                elif status in ["failed", "cancelled", "unknown"]:
                    raise Exception(f"Tripo generation failed with status '{status}': {data.get('data', {}).get('message', '')}")
                    
            raise Exception("Tripo generation timed out after 3 minutes")
        except Exception as e:
            print(f"TRIPO 3D ERROR: {str(e)}")
            print("Tripo3D failed.")
            
    # All providers exhausted — report a clear, actionable error
    print("ERROR: All 3D generation providers failed or no API keys configured.")
    raise HTTPException(
        status_code=500,
        detail=(
            "All 3D generation providers failed. "
            "To fix: (1) Add billing to Replicate at replicate.com/account/billing, "
            "(2) Renew your TRIPO_API_KEY at platform.tripo3d.ai if you see 403 errors, "
            "or (3) Ensure HF_TOKEN is valid (HF TRELLIS space may be queued — try again in a minute)."
        )
    )


# ══════════════════════════════════════════════════════════════════
# FULL-ROOM 3D RECONSTRUCTION (Depth → Mesh)
# ══════════════════════════════════════════════════════════════════

class Generate3DRoomRequest(BaseModel):
    imageUrl: str
    userId: str = ""
    designId: str = ""  # optional — when set, glb_url is saved to the designs table


@app.post("/generate-3d-room")
async def generate_3d_room(req: Generate3DRoomRequest, request: Request):
    """
    Generate a complete 3D room mesh from an interior design image.

    Unlike /generate-3d (which reconstructs a SINGLE object using TRELLIS),
    this endpoint captures the ENTIRE room — walls, floor, ceiling, all
    furniture — by converting a monocular depth map into a textured GLB mesh.

    Free 3-Layer Depth Waterfall (no Replicate credits needed):
      Layer 1 → HuggingFace Inference API (free serverless, fastest)
      Layer 2 → HuggingFace Gradio Space  (free ZeroGPU, queue-based)
      Layer 3 → Local CPU model           (offline fallback, always works)

    The depth → GLB conversion runs on the local CPU using numpy + trimesh.

    Returns: { success: true, glbUrl: "<permanent Supabase URL>" }
    """
    print(f"\n--- NEW ROOM 3D REQUEST ---")
    print(f"Image URL: {req.imageUrl}")

    hf_token = os.environ.get("HF_TOKEN")
    auth_header = request.headers.get("Authorization", f"Bearer {supabase_key}")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY") or supabase_key
    storage_auth = f"Bearer {service_key}" if service_key != supabase_key else auth_header

    # ── Run the depth-to-mesh pipeline ───────────────────────────────
    try:
        from depth_room_pipeline import run_room_pipeline

        print("DEBUG: Starting depth-to-mesh room pipeline...")
        glb_path = run_room_pipeline(
            image_url=req.imageUrl,
            hf_token=hf_token,
        )
    except Exception as exc:
        print(f"ROOM PIPELINE IMPORT/RUNTIME ERROR: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Room pipeline error: {str(exc)}"
        )

    if not glb_path:
        raise HTTPException(
            status_code=500,
            detail=(
                "All depth estimation layers failed. "
                "Ensure HF_TOKEN is set in .env, or install torch for local fallback: "
                "pip install torch --index-url https://download.pytorch.org/whl/cpu"
            )
        )

    # ── Upload GLB to Supabase ────────────────────────────────────────
    result = _upload_glb_to_supabase(
        glb_path=glb_path,
        user_id=req.userId,
        auth_header=auth_header,
        storage_auth=storage_auth,
    )

    if result:
        # Supabase upload succeeded — persist the URL in the designs table
        try: os.unlink(glb_path)
        except OSError: pass
        public_glb_url = result['glbUrl']
        print(f"DEBUG: Room 3D pipeline complete. GLB URL: {public_glb_url}")
        # Save glb_url back to the designs row so Gallery can load it directly next time
        if req.designId and supabase_url and supabase_key:
            try:
                patch_headers = {
                    "apikey": supabase_key,
                    "Authorization": auth_header,
                    "Content-Type": "application/json",
                }
                patch_res = requests.patch(
                    f"{supabase_url}/rest/v1/designs?id=eq.{req.designId}",
                    headers=patch_headers,
                    json={"glb_url": public_glb_url},
                    timeout=10,
                )
                if patch_res.status_code in (200, 204):
                    print(f"DEBUG: glb_url saved to designs table for design {req.designId}")
                else:
                    print(f"WARNING: Could not save glb_url to DB [{patch_res.status_code}]: {patch_res.text[:200]}")
            except Exception as db_err:
                print(f"WARNING: DB glb_url update failed: {db_err}")
        return result

    # ── Supabase upload failed → local static fallback ────────────────
    # Move (not copy) the GLB into backend/static/models/ so FastAPI can
    # serve it at http://localhost:8000/static/models/<file>.glb
    # The model-viewer component loads from any URL, including localhost.
    print("WARNING: Supabase upload failed. Falling back to local static serving.")
    try:
        filename = f"{int(time.time())}_{os.path.basename(glb_path)}"
        dest_path = os.path.join(STATIC_MODELS_DIR, filename)
        shutil.move(glb_path, dest_path)

        # Build the localhost URL — works as long as backend is running
        # (which it always is during development / on-device use)
        local_url = f"{BACKEND_BASE_URL}/static/models/{filename}"
        print(f"DEBUG: GLB served locally at {local_url}")
        return {"success": True, "glbUrl": local_url, "source": "local"}
    except Exception as fallback_err:
        # Last resort — clean up and raise a clear error
        try: os.unlink(glb_path)
        except OSError: pass
        raise HTTPException(
            status_code=500,
            detail=(
                f"GLB generated but could not be saved: {fallback_err}. "
                "Check SUPABASE_SERVICE_KEY in .env and storage bucket permissions."
            )
        )


