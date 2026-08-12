import requests
import json
import time
import numpy as np
import torch
from PIL import Image
import io


class SvgToPngApiNode:
    """
    Tasty API node: sends an image to the cloud SVG-to-PNG worker,
    polls for completion, fetches the processed image.
    """

    NODE_ID = "svg_to_png"
    API_URL = "https://tastystudio.app/api"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "api_key": ("STRING", {"default": ""}),
            },
            "optional": {
                "trigger": ("*",),
            },
        }

    RETURN_TYPES = ("IMAGE", "*")
    RETURN_NAMES = ("image", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Tasty/API"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, image, api_key, trigger=None):
        api_url = self.API_URL.rstrip("/")
        node_id = self.NODE_ID
        auth = {"Authorization": f"Bearer {api_key}"}

        img_array = (image[0].numpy() * 255).astype(np.uint8)
        img = Image.fromarray(img_array, "RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

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
            return (image, None)

        if r.status_code != 200:
            print(f"[Tasty API] Submit error {r.status_code}: {r.text[:500]}")
            return (image, None)

        try:
            submit_result = r.json()
        except ValueError:
            print(f"[Tasty API] Invalid submit response")
            return (image, None)

        request_id = submit_result.get("request_id")
        if not request_id:
            print(f"[Tasty API] No request_id: {submit_result}")
            return (image, None)

        print(f"[Tasty API] Job submitted: {request_id}")

        max_wait = 60
        poll_interval = 1
        elapsed = 0
        job_status = "unknown"

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
                return (image, None)

        if job_status != "done":
            print(f"[Tasty API] Timed out after {max_wait}s")
            return (image, None)

        print(f"[Tasty API] Fetching image...")
        try:
            img_r = requests.get(
                f"{api_url}/job/{request_id}/image",
                headers=auth,
                timeout=60,
            )
        except requests.exceptions.RequestException as e:
            print(f"[Tasty API] Image fetch failed: {e}")
            return (image, None)

        if img_r.status_code != 200:
            print(f"[Tasty API] Image fetch error: {img_r.status_code}")
            return (image, None)

        out_img = Image.open(io.BytesIO(img_r.content)).convert("RGB")
        out_tensor = np.array(out_img).astype(np.float32) / 255.0
        print(f"[Tasty API] Done! Output: {out_img.size}")
        return (torch.from_numpy(out_tensor).unsqueeze(0), True)


NODE_CLASS_MAPPINGS = {"SvgToPngApiNode": SvgToPngApiNode}
NODE_DISPLAY_NAME_MAPPINGS = {"SvgToPngApiNode": "SVG to PNG (API)"}
