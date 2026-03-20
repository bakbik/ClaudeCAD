#!/usr/bin/env python3
"""
mesh_generate.py — Generate a 3D mesh via Meshy AI API (text or image input).

Requires MESHY_API_KEY environment variable (Pro tier or above).
For development/testing, a dummy key is available:
    export MESHY_API_KEY=msy_dummy_api_key_for_test_mode_12345678

Meshy API docs: https://docs.meshy.ai/en/api/text-to-3d

Usage:
    python mesh_generate.py --prompt "a minimal phone stand, geometric, 3D printable"
    python mesh_generate.py --prompt "a decorative tree" --image ref.png --output designs/tree.glb
    python mesh_generate.py --prompt "..." --refine --output designs/out.glb
"""

import sys
import os
import time
import json
import argparse

import requests

MESHY_BASE_URL = "https://api.meshy.ai/openapi/v2"
TEST_API_KEY = "msy_dummy_api_key_for_test_mode_12345678"
POLL_INTERVAL_S = 5
TIMEOUT_S = 300


def get_api_key() -> str:
    key = os.environ.get("MESHY_API_KEY", TEST_API_KEY)
    if key == TEST_API_KEY:
        print(
            "ℹ️  Using Meshy test key — returns sample data, no credits consumed.\n"
            "   Set MESHY_API_KEY env var with a real key for actual generation.",
            file=sys.stderr,
        )
    return key


def auth_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def create_preview_task(prompt: str, negative_prompt: str, api_key: str,
                        image_path: str | None = None) -> str:
    """Submit a text-to-3D preview task. Returns task_id."""
    if image_path:
        # Image-to-3D: use image-to-3d endpoint
        return create_image_to_3d_task(image_path, prompt, api_key)

    payload = {
        "mode": "preview",
        "prompt": prompt,
        "negative_prompt": negative_prompt or "low quality, blurry, deformed",
        "should_remesh": True,
    }
    resp = requests.post(
        f"{MESHY_BASE_URL}/text-to-3d",
        headers=auth_headers(api_key),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    task_id = resp.json()["result"]
    print(f"Preview task created: {task_id}")
    return task_id


def create_image_to_3d_task(image_path: str, prompt: str, api_key: str) -> str:
    """Submit an image-to-3D task. Returns task_id."""
    import base64
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "webp": "image/webp"}.get(ext, "image/png")
    image_data_url = f"data:{mime};base64,{img_b64}"

    payload = {
        "image_url": image_data_url,
        "prompt": prompt or "",
        "should_remesh": True,
    }
    resp = requests.post(
        f"{MESHY_BASE_URL}/image-to-3d",
        headers=auth_headers(api_key),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    task_id = resp.json()["result"]
    print(f"Image-to-3D task created: {task_id}")
    return task_id


def create_refine_task(preview_task_id: str, api_key: str) -> str:
    """Submit a refine task from a completed preview. Returns task_id."""
    payload = {"mode": "refine", "preview_task_id": preview_task_id}
    resp = requests.post(
        f"{MESHY_BASE_URL}/text-to-3d",
        headers=auth_headers(api_key),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    task_id = resp.json()["result"]
    print(f"Refine task created: {task_id}")
    return task_id


def poll_task(task_id: str, api_key: str, endpoint: str = "text-to-3d") -> dict:
    """Poll until task SUCCEEDED or FAILED. Returns final task dict."""
    deadline = time.time() + TIMEOUT_S
    while time.time() < deadline:
        resp = requests.get(
            f"{MESHY_BASE_URL}/{endpoint}/{task_id}",
            headers=auth_headers(api_key),
            timeout=30,
        )
        resp.raise_for_status()
        task = resp.json()
        status = task.get("status", "UNKNOWN")
        progress = task.get("progress", 0)
        print(f"  Status: {status} ({progress}%)", end="\r", flush=True)

        if status == "SUCCEEDED":
            print(f"\n✅ Task complete: {task_id}")
            return task
        if status == "FAILED":
            print(f"\n❌ Task failed: {task.get('task_error', {}).get('message', 'unknown error')}")
            sys.exit(1)

        time.sleep(POLL_INTERVAL_S)

    print(f"\n⏰ Timeout after {TIMEOUT_S}s waiting for task {task_id}")
    sys.exit(1)


def download_model(task: dict, output_path: str, prefer_format: str = "glb"):
    """Download the generated model file."""
    model_urls = task.get("model_urls", {})

    # Try preferred format, then fallbacks
    for fmt in [prefer_format, "glb", "obj", "fbx"]:
        url = model_urls.get(fmt)
        if url:
            print(f"Downloading {fmt.upper()} from Meshy...")
            resp = requests.get(url, timeout=120, stream=True)
            resp.raise_for_status()
            # Adjust output extension to match format
            base, _ = os.path.splitext(output_path)
            actual_path = f"{base}.{fmt}"
            os.makedirs(os.path.dirname(actual_path) if os.path.dirname(actual_path) else ".", exist_ok=True)
            with open(actual_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            size_kb = os.path.getsize(actual_path) / 1024
            print(f"✅ Saved: {actual_path} ({size_kb:.1f} KB)")
            return actual_path

    print("❌ No downloadable model URL found in task response.", file=sys.stderr)
    print(f"   Available URLs: {list(model_urls.keys())}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate 3D mesh via Meshy AI API")
    parser.add_argument("--prompt", required=True, help="Text description of the 3D model")
    parser.add_argument("--negative-prompt", default="",
                        help="Describe what to avoid")
    parser.add_argument("--image", default=None,
                        help="Path to reference image (triggers image-to-3D)")
    parser.add_argument("--output", default="designs/model.glb",
                        help="Output file path (extension adjusted to actual format)")
    parser.add_argument("--refine", action="store_true",
                        help="Run refine stage after preview (adds texture detail)")
    parser.add_argument("--format", choices=["glb", "obj", "fbx"], default="glb",
                        help="Preferred output format")
    args = parser.parse_args()

    api_key = get_api_key()

    # Stage 1: Preview
    task_id = create_preview_task(
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        api_key=api_key,
        image_path=args.image,
    )
    endpoint = "image-to-3d" if args.image else "text-to-3d"
    task = poll_task(task_id, api_key, endpoint=endpoint)

    # Stage 2: Refine (optional)
    if args.refine and not args.image:
        print("Running refine stage...")
        refine_id = create_refine_task(task_id, api_key)
        task = poll_task(refine_id, api_key, endpoint="text-to-3d")

    # Download
    download_model(task, args.output, prefer_format=args.format)

    print(json.dumps({
        "task_id": task_id,
        "status": "SUCCEEDED",
        "output": args.output,
        "model_urls": task.get("model_urls", {}),
    }))


if __name__ == "__main__":
    main()
