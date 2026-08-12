import json
import numpy as np
import torch
import cv2
import os

class FaceMask:
    """Generates a skin-region mask from detected face area using HSV thresholding."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "expand": ("INT", {"default": 10, "min": 0, "max": 100, "step": 5}),
                "smooth": ("INT", {"default": 5, "min": 0, "max": 20, "step": 1}),
                "face_index": ("INT", {"default": 0, "min": 0, "max": 31, "step": 1}),
            },
        }

    RETURN_TYPES = ("MASK", "INT", "INT", "INT", "INT", "TASTY_JSON", "TRIGGER")
    RETURN_NAMES = ("mask", "x", "y", "width", "height", "json_result", "trigger")
    OUTPUT_NODE = False
    FUNCTION = "generate_mask"
    CATEGORY = "Tasty/SuperCrop"

    def generate_mask(self, image, expand=10, smooth=5, face_index=0):
        img_np = (image[0].cpu().numpy() * 255).astype(np.uint8)
        img_h, img_w = img_np.shape[:2]

        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
        # Try multiple paths to find the Haar cascade file
        cascade_file = None
        
        # Try cv2.data path first (if available)
        if hasattr(cv2, 'data'):
            try:
                cascade_file = cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
                if os.path.exists(cascade_file):
                    pass  # Found it
                else:
                    cascade_file = None
            except:
                cascade_file = None
        
        # Try other common paths
        if not cascade_file:
            cascade_paths = [
                os.path.join(cv2.__path__[0], "data", "haarcascade_frontalface_alt2.xml"),
                "/usr/share/opencv4/haarcascades/haarcascade_frontalface_alt2.xml",
                "/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_alt2.xml",
                "haarcascade_frontalface_alt2.xml",  # System path fallback
            ]
            
            for path in cascade_paths:
                if os.path.exists(path):
                    cascade_file = path
                    break
        
        if not cascade_file:
            cascade_file = "haarcascade_frontalface_alt2.xml"
        
        cascade = cv2.CascadeClassifier(cascade_file)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))

        face_count = len(faces) if isinstance(faces, np.ndarray) else 0
        mask = np.zeros((img_h, img_w), dtype=np.uint8)

        if face_count == 0:
            print("[tasty] FaceMask: no faces detected")
            result = torch.from_numpy(mask.astype(np.float32)).unsqueeze(0)
            result_json = json.dumps({"node": "FaceMask", "x": 0, "y": 0, "width": img_w, "height": img_h, "face_count": 0})
            return (result, 0, 0, img_w, img_h, result_json, "done")

        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        idx = min(face_index, face_count - 1)
        fx, fy, fw, fh = [int(v) for v in faces[idx]]

        ex = max(0, fx - expand)
        ey = max(0, fy - expand)
        ew = min(img_w, fx + fw + expand) - ex
        eh = min(img_h, fy + fh + expand) - ey

        face_roi = img_np[ey:ey + eh, ex:ex + ew]
        hsv = cv2.cvtColor(face_roi, cv2.COLOR_RGB2HSV)

        lower1 = np.array([0, 30, 60])
        upper1 = np.array([25, 180, 255])
        lower2 = np.array([160, 30, 60])
        upper2 = np.array([180, 180, 255])

        mask1 = cv2.inRange(hsv, lower1, upper1)
        mask2 = cv2.inRange(hsv, lower2, upper2)
        skin = cv2.bitwise_or(mask1, mask2)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, kernel, iterations=2)
        skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, kernel, iterations=1)

        if smooth > 0:
            k = smooth * 2 + 1
            skin = cv2.GaussianBlur(skin, (k, k), 0)
            _, skin = cv2.threshold(skin, 127, 255, cv2.THRESH_BINARY)

        mask[ey:ey + eh, ex:ex + ew] = skin

        out_x, out_y, out_w, out_h = int(ex), int(ey), int(ew), int(eh)
        print(f"[tasty] FaceMask: face region x={out_x} y={out_y} w={out_w} h={out_h}")

        result = torch.from_numpy(mask.astype(np.float32) / 255.0).unsqueeze(0)
        result_json = json.dumps({"node": "FaceMask", "x": out_x, "y": out_y, "width": out_w, "height": out_h, "face_count": face_count})
        return (result, out_x, out_y, out_w, out_h, result_json, "done")
