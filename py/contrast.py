import json
import math


def srgb_to_linear(v):
    """Convert normalized sRGB (0-1) to linear RGB."""
    if v <= 0.04045:
        return v / 12.92
    return ((v + 0.055) / 1.055) ** 2.4


def linear_to_srgb(v):
    """Convert linear RGB back to normalized sRGB (0-1)."""
    if v <= 0.0031308:
        return v * 12.92
    return 1.055 * (v ** (1.0 / 2.4)) - 0.055


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


class WCAGContrastNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "R": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 255.0, "step": 1.0}),
                "G": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 255.0, "step": 1.0}),
                "B": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 255.0, "step": 1.0}),
            },
            "optional": {
                "hex_color": ("STRING", {"default": ""}),
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("JSON", "TRIGGER")
    RETURN_NAMES = ("results_json", "trigger")
    FUNCTION = "execute"
    CATEGORY = "utils/color"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, R, G, B, hex_color="", trigger=None):
        # --- If hex provided, override R/G/B ---
        h = hex_color.strip().lstrip("#")
        if len(h) == 6:
            try:
                R = float(int(h[0:2], 16))
                G = float(int(h[2:4], 16))
                B = float(int(h[4:6], 16))
            except ValueError:
                pass

        # --- Normalize 0-255 → 0-1 ---
        r_norm = R / 255.0
        g_norm = G / 255.0
        b_norm = B / 255.0

        # --- Linearize (remove sRGB gamma) ---
        r_lin = srgb_to_linear(r_norm)
        g_lin = srgb_to_linear(g_norm)
        b_lin = srgb_to_linear(b_norm)

        # --- Relative luminance (BT.709) ---
        L = 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

        # --- RGB contributions (percentage each channel contributes to luminance) ---
        r_contribution = (0.2126 * r_lin / L * 100) if L > 0 else 0.0
        g_contribution = (0.7152 * g_lin / L * 100) if L > 0 else 0.0
        b_contribution = (0.0722 * b_lin / L * 100) if L > 0 else 0.0

        # --- Contrast ratios against black and white ---
        # WCAG formula: (L1 + 0.05) / (L2 + 0.05) where L1 > L2
        contrast_on_white = (1.05) / (L + 0.05)
        contrast_on_black = (L + 0.05) / (0.0 + 0.05)

        white_pass = contrast_on_white >= 4.5
        black_pass = contrast_on_black >= 4.5

        # --- Scale factors ---
        # Darker: shift luminance down by 0.05
        scale_darker = (L - 0.05) / L if L > 0 else 0.0
        # Lighter: shift luminance up by 0.05
        scale_lighter = (L + 0.05) / L if L > 0 else 0.0
        # Minimum compliant against white (4.5:1 → target L = 0.1833)
        scale_min_white = 0.1833 / L if L > 0 else 0.0
        # Minimum compliant against black (4.5:1 → target L = 0.1750)
        # 4.5 = (L + 0.05) / 0.05 → L = 0.175
        scale_min_black = 0.175 / L if L > 0 else 0.0

        # --- Apply scales → new RGB values ---
        def apply_scale(r, g, b, scale):
            r_new = clamp(r * scale)
            g_new = clamp(g * scale)
            b_new = clamp(b * scale)
            # Convert back through gamma to sRGB 0-255
            return (
                round(linear_to_srgb(r_new) * 255),
                round(linear_to_srgb(g_new) * 255),
                round(linear_to_srgb(b_new) * 255),
            )

        darker_rgb = apply_scale(r_lin, g_lin, b_lin, scale_darker)
        lighter_rgb = apply_scale(r_lin, g_lin, b_lin, scale_lighter)
        min_white_rgb = apply_scale(r_lin, g_lin, b_lin, scale_min_white)
        min_black_rgb = apply_scale(r_lin, g_lin, b_lin, scale_min_black)

        # --- Hex values ---
        def to_hex(rgb_tuple):
            return "#{:02X}{:02X}{:02X}".format(*rgb_tuple)

        results = {
            "input_rgb": [int(R), int(G), int(B)],
            "input_hex": to_hex((int(R), int(G), int(B))),

            "r_normalized": round(r_norm, 6),
            "g_normalized": round(g_norm, 6),
            "b_normalized": round(b_norm, 6),

            "r_linearized": round(r_lin, 6),
            "g_linearized": round(g_lin, 6),
            "b_linearized": round(b_lin, 6),

            "luminance": round(L, 6),

            "r_contribution_pct": round(r_contribution, 2),
            "g_contribution_pct": round(g_contribution, 2),
            "b_contribution_pct": round(b_contribution, 2),

            "contrast_on_white": round(contrast_on_white, 2),
            "contrast_on_black": round(contrast_on_black, 2),
            "white_contrast_pass": white_pass,
            "black_contrast_pass": black_pass,

            "scale_darker": round(scale_darker, 6),
            "scale_lighter": round(scale_lighter, 6),
            "scale_min_white": round(scale_min_white, 6),
            "scale_min_black": round(scale_min_black, 6),

            "darker_rgb": list(darker_rgb),
            "darker_hex": to_hex(darker_rgb),
            "lighter_rgb": list(lighter_rgb),
            "lighter_hex": to_hex(lighter_rgb),
            "min_white_rgb": list(min_white_rgb),
            "min_white_hex": to_hex(min_white_rgb),
            "min_black_rgb": list(min_black_rgb),
            "min_black_hex": to_hex(min_black_rgb),
        }

        return (json.dumps(results, indent=2), "done")


NODE_CLASS_MAPPINGS = {
    "WCAGContrastNode": WCAGContrastNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WCAGContrastNode": "WCAG Contrast Calculator",
}