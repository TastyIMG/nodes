import torch
import json


class InvertImageNode:
    """Invert an image's colors (1 - pixel value). No mask conversion needed."""

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

    RETURN_TYPES = ("IMAGE", "TASTY_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Tasty/Image"

    def execute(self, image, trigger=None):
        inverted = 1.0 - image
        json_result = json.dumps({"node": "InvertImageNode", "shape": list(image.shape)})
        return (inverted, json_result, "done")
