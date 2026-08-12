import os
import json
import tempfile
import numpy as np
from io import BytesIO
from PIL import Image
import vtracer
from comfy_api.latest._util.image_types import SVG


class PNGToVectorNode:
    """Converts a PNG image to an SVG vector."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("SVG", "TASTY_JSON", "TRIGGER")
    RETURN_NAMES = ("svg", "json_result", "trigger")
    FUNCTION = "convert"
    CATEGORY = "Tasty/Utils"

    def convert(self, image, trigger=None):
        img_np = (image[0].cpu().numpy() * 255).astype(np.uint8)
        pil_img = Image.fromarray(img_np, mode="RGB")

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "input.png")
            out_path = os.path.join(tmpdir, "output.svg")

            pil_img.save(in_path)
            vtracer.convert_image_to_svg_py(in_path, out_path)

            with open(out_path, "rb") as f:
                svg_bytes = BytesIO(f.read())

        json_result = json.dumps({
            "node": "PNGToVectorNode",
            "size_bytes": svg_bytes.getbuffer().nbytes,
        })

        return (SVG([svg_bytes]), json_result, "done")
