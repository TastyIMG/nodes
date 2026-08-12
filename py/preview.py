import json
import os
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import folder_paths


class TastyPreviewImage:
    """Previews images in the ComfyUI UI without saving to the output folder."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE", "TASTY_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "json_result", "trigger")
    OUTPUT_NODE = True
    FUNCTION = "preview"
    CATEGORY = "Tasty/Image"

    def preview(self, images):
        results = []
        for batch_idx in range(images.shape[0]):
            i = 255.0 * images[batch_idx].cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            filename = f"tasty_preview_{batch_idx:05d}.png"
            subfolder = "tasty_temp"
            temp_dir = folder_paths.get_temp_directory()
            full_dir = os.path.join(temp_dir, subfolder)
            os.makedirs(full_dir, exist_ok=True)
            img.save(os.path.join(full_dir, filename), compress_level=1)

            results.append({
                "filename": filename,
                "subfolder": subfolder,
                "type": "temp",
            })

        json_result = json.dumps({"node": "TastyPreviewImage", "images": results, "count": len(results)})
        return {"ui": {"images": results}, "result": (images, json_result, "done")}


class TastySaveImage:
    """Saves images to the output folder with a customizable filename prefix."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "Tasty"}),
            },
        }

    RETURN_TYPES = ("TASTY_JSON", "TRIGGER")
    RETURN_NAMES = ("json_result", "trigger")
    OUTPUT_NODE = True
    FUNCTION = "save"
    CATEGORY = "Tasty/Image"

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.compress_level = 4

    def save(self, images, filename_prefix="Tasty"):
        full_output_folder, filename, counter, subfolder, filename_prefix = (
            folder_paths.get_save_image_path(
                filename_prefix, self.output_dir, images.shape[2], images.shape[1]
            )
        )

        results = []
        for batch_idx in range(images.shape[0]):
            i = 255.0 * images[batch_idx].cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            metadata = PngInfo()
            file = f"{filename}_{counter + batch_idx:05d}.png"
            img.save(
                os.path.join(full_output_folder, file),
                pnginfo=metadata,
                compress_level=self.compress_level,
            )

            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type,
            })

        json_result = json.dumps({"node": "TastySaveImage", "images": results, "count": len(results), "prefix": filename_prefix})
        return {"ui": {"images": results}, "result": (json_result, "done")}


class TastyPreviewAny:
    """Displays the string representation of any value in the ComfyUI UI."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "source": ("*", {"forceInput": True}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("*", "TASTY_JSON", "TRIGGER")
    RETURN_NAMES = ("value", "json_result", "trigger")
    OUTPUT_NODE = True
    FUNCTION = "preview"
    CATEGORY = "Tasty/Utils"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def preview(self, source=None, trigger=None):
        if isinstance(source, str):
            text = source
        elif isinstance(source, (int, float, bool)):
            text = str(source)
        elif source is None:
            text = "None"
        else:
            try:
                text = json.dumps(source, indent=2, default=str)
            except Exception:
                try:
                    text = str(source)
                except Exception:
                    text = "Value exists but could not be serialized"

        json_result = json.dumps({"node": "TastyPreviewAny", "value": text, "type": type(source).__name__})
        return {"ui": {"text": [text]}, "result": (source, json_result, "done")}
