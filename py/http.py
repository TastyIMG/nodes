import requests
import json
import time
import numpy as np
import torch
from PIL import Image
import io


class HttpRequestNode:
    """
    Tasty API node: sends an image + node_id to the Worker,
    polls for completion, fetches the processed image.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "api_key": ("STRING", {"default": ""}),
                "node_id": ("STRING", {"default": "hsl_colorize"}),
            },
            "optional": {
                "api_url": ("STRING", {"default": "https://tastystudio.app/api"}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "execute"
    CATEGORY = "Tasty/API"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, image, api_key, node_id, api_url="https://tastystudio.app/api"):
        api_url = api_url.rstrip("/")
        auth = {"Authorization": f"Bearer {api_key}"}

        img_array = (image[0].numpy() * 255).astype(np.uint8)
        img = Image.fromarray(img_array, "RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        # Step 1: Submit job
        print(f"[Tasty API] Submitting job: node_id={node_id}, image_size={len(png_bytes)} bytes")
        try:
            r = requests.post(
                f"{api_url}/process",
                files={"image": ("input.png", png_bytes, "image/png")},
                data={"node_id": node_id},
                headers=auth,
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            print(f"[Tasty API] Submit failed: {e}")
            return (image,)

        if r.status_code != 200:
            print(f"[Tasty API] Submit error {r.status_code}: {r.text[:500]}")
            return (image,)

        try:
            submit_result = r.json()
        except ValueError:
            print(f"[Tasty API] Invalid submit response")
            return (image,)

        request_id = submit_result.get("request_id")
        if not request_id:
            print(f"[Tasty API] No request_id: {submit_result}")
            return (image,)

        print(f"[Tasty API] Job submitted: {request_id}")

        # Step 2: Poll for completion
        max_wait = 60
        poll_interval = 1
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            try:
                status_r = requests.get(
                    f"{api_url}/job/{request_id}/status",
                    headers=auth,
                    timeout=10,
                )
                status = status_r.json()
            except Exception as e:
                print(f"[Tasty API] Poll error: {e}")
                continue

            job_status = status.get("status", "unknown")
            print(f"[Tasty API] Status: {job_status} ({elapsed}s)")

            if job_status == "done":
                break
            elif job_status == "error":
                print(f"[Tasty API] Job failed: {status.get('error')}")
                return (image,)

        if job_status != "done":
            print(f"[Tasty API] Timed out after {max_wait}s")
            return (image,)

        # Step 3: Fetch image
        print(f"[Tasty API] Fetching image...")
        try:
            img_r = requests.get(
                f"{api_url}/job/{request_id}/image",
                headers=auth,
                timeout=60,
            )
        except requests.exceptions.RequestException as e:
            print(f"[Tasty API] Image fetch failed: {e}")
            return (image,)

        if img_r.status_code != 200:
            print(f"[Tasty API] Image fetch error: {img_r.status_code}")
            return (image,)

        out_img = Image.open(io.BytesIO(img_r.content)).convert("RGB")
        out_tensor = np.array(out_img).astype(np.float32) / 255.0
        print(f"[Tasty API] Done! Output: {out_img.size}")
        return (torch.from_numpy(out_tensor).unsqueeze(0),)


NODE_CLASS_MAPPINGS = {"HttpRequestNode": HttpRequestNode}
NODE_DISPLAY_NAME_MAPPINGS = {"HttpRequestNode": "Tasty API"}
