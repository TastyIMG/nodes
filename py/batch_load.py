"""Load staged batch images by index from public URLs (R2 / Worker)."""

import io
import os
import urllib.request

import numpy as np
import torch
from PIL import Image, ImageOps


class BatchLoadNode:
    """
    Fetch one image from a newline-separated URL list using an explicit index.
    Worker queues N jobs with index 0..N-1 — no shared counter (safe under concurrency).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "batch_id": ("STRING", {"default": ""}),
                "urls": ("STRING", {"multiline": True, "default": ""}),
                "index": ("INT", {"default": 0, "min": 0, "max": 150000, "step": 1}),
            },
            "optional": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "filename")
    FUNCTION = "load"
    CATEGORY = "Tasty/Batch"

    @staticmethod
    def _pil_to_tensor(pil_img):
        img_np = np.array(pil_img.convert("RGB")).astype(np.float32) / 255.0
        return torch.from_numpy(img_np).unsqueeze(0)

    def load(self, batch_id, urls, index, seed=0):
        if not batch_id:
            raise ValueError("batch_id is required")

        url_list = [u.strip() for u in urls.split("\n") if u.strip()]
        if not url_list:
            raise ValueError("urls must contain at least one URL")

        index = int(index)
        if index < 0 or index >= len(url_list):
            raise ValueError(f"index {index} out of range (0..{len(url_list) - 1})")

        url = url_list[index]
        with urllib.request.urlopen(url, timeout=120) as resp:
            data = resp.read()

        image = Image.open(io.BytesIO(data))
        image = ImageOps.exif_transpose(image)
        filename = os.path.basename(url.split("?")[0]) or f"image_{index}.png"

        return (self._pil_to_tensor(image), filename)

