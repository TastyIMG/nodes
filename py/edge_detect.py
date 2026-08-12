import numpy as np
import torch
import json
from PIL import Image, ImageDraw

from .utils import compute_all_edges

class ShapeEdgeDetect:
    """Detects shape-derived construction line positions from a mask's boundary geometry."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
                "edge_min": ("INT", {"default": 50, "min": 1, "max": 500, "step": 5}),
                "merge_tol": ("INT", {"default": 5, "min": 1, "max": 50, "step": 1}),
            },
        }

    RETURN_TYPES = ("EDGE_DATA", "TASTY_JSON", "TRIGGER")
    RETURN_NAMES = ("edges", "json_result", "trigger")
    FUNCTION = "detect"
    CATEGORY = "Tasty/SuperCrop"

    def detect(self, mask, edge_min, merge_tol):
        m = mask[0].cpu().numpy()
        edges = compute_all_edges(m, edge_min, merge_tol)
        h_count = len(edges["h_lines"])
        v_count = len(edges["v_lines"])
        d45_count = len(edges["d45_lines"])
        d135_count = len(edges["d135_lines"])
        print(f"[tasty] edges: {h_count}H / {v_count}V / {d45_count}d45 / {d135_count}d135")
        
        json_result = json.dumps({
            "node": "ShapeEdgeDetect",
            "h_lines": h_count,
            "v_lines": v_count,
            "d45_lines": d45_count,
            "d135_lines": d135_count,
            "edge_min": edge_min,
            "merge_tol": merge_tol
        })
        
        return (edges, json_result, "done")