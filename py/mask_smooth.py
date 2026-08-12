import cv2
import numpy as np
import torch
import json


class MaskSmoothNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
                "mode": (["anti_alias", "median"], {}),
            },
            "optional": {
                "strength": ("INT", {"default": 3, "min": 1, "max": 15, "step": 1}),
                "iterations": ("INT", {"default": 3, "min": 1, "max": 20, "step": 1}),
            },
        }

    RETURN_TYPES = ("MASK", "TASTY_JSON", "TRIGGER")
    RETURN_NAMES = ("mask", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Tasty/Masking"

    def execute(self, mask, mode="anti_alias", strength=3, iterations=3):
        m = (mask[0].cpu().numpy() * 255).astype(np.uint8)

        if mode == "anti_alias":
            # Extract contours, redraw with LINE_AA
            # Same exact geometry, just anti-aliased edge rendering
            contours, hierarchy = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
            aa_mask = np.zeros_like(m)

            if hierarchy is not None:
                # Draw outer contours filled
                for i, cnt in enumerate(contours):
                    if hierarchy[0][i][3] == -1:
                        cv2.drawContours(aa_mask, [cnt], 0, 255, cv2.FILLED, lineType=cv2.LINE_AA)
                # Punch out inner contours (holes)
                for i, cnt in enumerate(contours):
                    if hierarchy[0][i][3] >= 0:
                        cv2.drawContours(aa_mask, [cnt], 0, 0, cv2.FILLED, lineType=cv2.LINE_AA)

            result = torch.from_numpy(aa_mask.astype(np.float32) / 255.0).unsqueeze(0)

        elif mode == "median":
            # pyrUp → medianBlur → pyrDown
            # Removes staircase jaggies but will round sharp corners
            up = cv2.pyrUp(m)
            k = strength * 2 + 1
            for _ in range(iterations):
                up = cv2.medianBlur(up, k)
            down = cv2.pyrDown(up)
            down = cv2.resize(down, (m.shape[1], m.shape[0]), interpolation=cv2.INTER_LINEAR)
            _, down = cv2.threshold(down, 127, 255, cv2.THRESH_BINARY)
            result = torch.from_numpy(down.astype(np.float32) / 255.0).unsqueeze(0)

        json_result = json.dumps({
            "node": "MaskSmoothNode",
            "mode": mode,
            "strength": strength,
            "iterations": iterations
        })

        return (result, json_result, "done")


NODE_CLASS_MAPPINGS = {
    "MaskSmoothNode": MaskSmoothNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskSmoothNode": "Mask Smooth",
}