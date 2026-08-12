import requests
import json
import numpy as np
from PIL import Image
import io


API_URL = "https://edgestinger.com/comfy"


class TastyApiNode:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"default": ""}),
                "image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE", "TASTY_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "status", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Tasty/API"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, api_key, image):
        img_array = (image[0].cpu().numpy() * 255).astype(np.uint8)
        img = Image.fromarray(img_array)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        try:
            r = requests.post(
                f"{API_URL}/process",
                files={"image": ("input.png", buf, "image/png")},
                headers={"x-api-key": api_key},
                timeout=60,
            )
        except requests.exceptions.RequestException as e:
            return (image, f"Error: {e}", "done")

        if r.status_code != 200:
            return (image, f"Error {r.status_code}: {r.text}", "done")

        content_type = r.headers.get("Content-Type", "")
        if "image" not in content_type:
            return (image, f"Unexpected response: {r.text[:200]}", "done")

        result_img = Image.open(io.BytesIO(r.content)).convert("RGB")
        result_array = np.array(result_img).astype(np.float32) / 255.0
        result_tensor = result_array[np.newaxis, :, :, :]

        return (result_tensor, json.dumps({"node": "TastyApiNode", "status": "ok"}), "done")


NODE_CLASS_MAPPINGS = {"TastyApiNode": TastyApiNode}
NODE_DISPLAY_NAME_MAPPINGS = {"TastyApiNode": "Tasty API"}
