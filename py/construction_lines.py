import numpy as np
import torch
import json
from PIL import Image, ImageDraw

from .utils import compute_all_edges


class ConstructionLineOverlay:
    """Draws bounding box and shape-derived construction lines on an image."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "x": ("INT", {"default": 0}),
                "y": ("INT", {"default": 0}),
                "width": ("INT", {"default": 100}),
                "height": ("INT", {"default": 100}),
            },
            "optional": {
                "edges": ("EDGE_DATA",),
                "line_weight": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
                "show_coords": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("IMAGE", "TASTY_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "json_result", "trigger")
    FUNCTION = "draw"
    CATEGORY = "Tasty/SuperCrop"

    def draw(self, image, x, y, width, height, edges=None, line_weight=1, show_coords=False):
        img_np = (image[0].cpu().numpy() * 255).astype(np.uint8)
        img_h, img_w = img_np.shape[:2]
        pil_img = Image.fromarray(img_np, "RGB")
        draw = ImageDraw.Draw(pil_img)

        x0, y0 = x, y
        x1, y1 = x + width - 1, y + height - 1
        lw = line_weight

        # --- Construction lines (full image extent, drawn behind the box) ---
        if edges is not None:
            h_color = (0, 229, 255)       # cyan
            v_color = (255, 145, 0)       # orange
            d45_color = (179, 136, 255)   # purple
            d135_color = (105, 240, 174)  # green

            for hy in edges.get("h_lines", []):
                _draw_dashed_line(draw, (0, hy), (img_w - 1, hy), h_color, line_width=lw)
                if show_coords:
                    _draw_label(draw, f"y:{hy}", (x0 - 4, hy + 3), h_color, align="right")

            for vx in edges.get("v_lines", []):
                _draw_dashed_line(draw, (vx, 0), (vx, img_h - 1), v_color, line_width=lw)
                if show_coords:
                    _draw_label(draw, f"x:{vx}", (vx, y0 - 4), v_color, align="center")

            for d in edges.get("d45_lines", []):
                _draw_diag45(draw, d, 0, 0, img_w - 1, img_h - 1, img_w, img_h, d45_color, lw)

            for s in edges.get("d135_lines", []):
                _draw_diag135(draw, s, 0, 0, img_w - 1, img_h - 1, img_w, img_h, d135_color, lw)

        # --- Bounding box (dashed red) ---
        box_color = (255, 68, 102)
        box_lw = max(lw, 2)
        for p1, p2, horiz in [
            ((x0, y0), (x1, y0), True),
            ((x0, y1), (x1, y1), True),
            ((x0, y0), (x0, y1), False),
            ((x1, y0), (x1, y1), False),
        ]:
            _draw_dashed_line(draw, p1, p2, box_color, dash=8, gap=5, line_width=box_lw)

        # --- Dimension labels ---
        if show_coords:
            _draw_label(draw, f"{width}px", (x0 + width // 2, y0 - 10), box_color, align="center")
            _draw_label(draw, f"{height}px", (x1 + 8, y0 + height // 2 + 4), box_color, align="left")

        result_np = np.array(pil_img).astype(np.float32) / 255.0
        result = torch.from_numpy(result_np).unsqueeze(0)
        
        edge_counts = {
            "h_lines": len(edges.get("h_lines", [])) if edges else 0,
            "v_lines": len(edges.get("v_lines", [])) if edges else 0,
            "d45_lines": len(edges.get("d45_lines", [])) if edges else 0,
            "d135_lines": len(edges.get("d135_lines", [])) if edges else 0,
        }
        json_result = json.dumps({
            "node": "ConstructionLineOverlay",
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "edges": edge_counts
        })
        
        return (result, json_result, "done")


def _draw_dashed_line(draw, p1, p2, color, dash=6, gap=3, line_width=1):
    """Draw a dashed line with round caps between two points (horizontal or vertical)."""
    x0, y0 = p1
    x1, y1 = p2
    step = dash + gap
    if line_width <= 1:
        if y0 == y1:
            pos = x0
            while pos <= x1:
                seg_end = min(pos + dash - 1, x1)
                draw.line([(pos, y0), (seg_end, y0)], fill=color, width=1)
                pos += step
        elif x0 == x1:
            pos = y0
            while pos <= y1:
                seg_end = min(pos + dash - 1, y1)
                draw.line([(x0, pos), (x0, seg_end)], fill=color, width=1)
                pos += step
    else:
        hw = line_width // 2
        if y0 == y1:
            pos = x0
            while pos <= x1:
                seg_end = min(pos + dash - 1, x1)
                draw.rounded_rectangle(
                    [pos, y0 - hw, seg_end, y0 + hw],
                    radius=hw, fill=color,
                )
                pos += step
        elif x0 == x1:
            pos = y0
            while pos <= y1:
                seg_end = min(pos + dash - 1, y1)
                draw.rounded_rectangle(
                    [x0 - hw, pos, x0 + hw, seg_end],
                    radius=hw, fill=color,
                )
                pos += step


def _clip_line_to_rect(x0, y0, x1, y1, xmin, ymin, xmax, ymax):
    """Cohen-Sutherland line clipping. Returns clipped endpoints or None."""
    INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8

    def code(x, y):
        c = INSIDE
        if x < xmin: c |= LEFT
        elif x > xmax: c |= RIGHT
        if y < ymin: c |= TOP
        elif y > ymax: c |= BOTTOM
        return c

    c0, c1 = code(x0, y0), code(x1, y1)
    for _ in range(20):
        if not (c0 | c1):
            return (x0, y0, x1, y1)
        if c0 & c1:
            return None
        c = c0 or c1
        if c & BOTTOM:
            x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0); y = ymax
        elif c & TOP:
            x = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0); y = ymin
        elif c & RIGHT:
            y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0); x = xmax
        else:
            y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0); x = xmin
        if c == c0:
            x0, y0, c0 = x, y, code(x, y)
        else:
            x1, y1, c1 = x, y, code(x, y)
    return None


def _draw_clipped_diag(draw, px0, py0, px1, py1, crop_x0, crop_y0, crop_x1, crop_y1, color, line_width=1):
    """Clip a diagonal line to a rect and draw it dashed."""
    clipped = _clip_line_to_rect(px0, py0, px1, py1, crop_x0, crop_y0, crop_x1, crop_y1)
    if clipped is None:
        return
    ax, ay, bx, by = clipped
    dx = bx - ax
    dy = by - ay
    length = (dx * dx + dy * dy) ** 0.5
    if length < 1:
        return
    dash, gap = 5, 4
    hw = max(line_width // 2, 0)
    radius = max(hw, 1)
    ux, uy = dx / length, dy / length
    pos = 0.0
    while pos < length:
        seg_end = min(pos + dash, length)
        sx, sy = ax + ux * pos, ay + uy * pos
        ex, ey = ax + ux * seg_end, ay + uy * seg_end
        x_lo = int(min(sx, ex)) - hw
        x_hi = int(max(sx, ex)) + hw
        y_lo = int(min(sy, ey)) - hw
        y_hi = int(max(sy, ey)) + hw
        draw.rounded_rectangle([x_lo, y_lo, x_hi, y_hi], radius=radius, fill=color)
        pos = seg_end + gap


def _draw_diag45(draw, d, crop_x0, crop_y0, crop_x1, crop_y1, img_w, img_h, color, line_width=1):
    """Draw a 45-degree diagonal (x - y = d) clipped to a rect."""
    if d >= 0:
        px0, py0 = d, 0
    else:
        px0, py0 = 0, -d
    px1 = min(img_w - 1, img_h - 1 + d)
    py1 = px1 - d
    _draw_clipped_diag(draw, px0, py0, px1, py1, crop_x0, crop_y0, crop_x1, crop_y1, color, line_width)


def _draw_diag135(draw, s, crop_x0, crop_y0, crop_x1, crop_y1, img_w, img_h, color, line_width=1):
    """Draw a 135-degree diagonal (x + y = s) clipped to a rect."""
    px0 = min(s, img_w - 1)
    py0 = s - px0
    px1 = max(0, s - (img_h - 1))
    py1 = s - px1
    _draw_clipped_diag(draw, px0, py0, px1, py1, crop_x0, crop_y0, crop_x1, crop_y1, color, line_width)


def _draw_label(draw, text, position, color, align="left"):
    """Draw a small coordinate label."""
    x, y = position
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
    except Exception:
        font = ImageFont.load_default()
    anchor = "rm" if align == "right" else ("mm" if align == "center" else "lm")
    draw.text((x, y), text, fill=color, font=font, anchor=anchor)
