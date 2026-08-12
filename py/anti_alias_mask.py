import torch
import torch.nn.functional as F
import json

class AntiAliasMaskNode:
    """
    An anti-aliasing mask node to smooth jagged edges of a mask.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
                "blur_radius": ("INT", {"default": 3, "min": 1, "max": 15, "step": 2}),
                "threshold": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("MASK", "TASTY_JSON", "TRIGGER")
    RETURN_NAMES = ("anti_aliased_mask", "json_result", "trigger")
    FUNCTION = "apply_anti_aliasing"
    CATEGORY = "Tasty/Masking"

    def apply_anti_aliasing(self, mask, blur_radius, threshold):
        # Ensure mask is float and has a channel dimension for blurring
        if mask.ndim == 3:  # [B, H, W]
            mask = mask.unsqueeze(1)  # [B, 1, H, W]
        elif mask.ndim == 2: # [H, W]
            mask = mask.unsqueeze(0).unsqueeze(0) # [1, 1, H, W]

        # Apply Gaussian blur
        # The blur_radius should be odd, so we ensure it
        if blur_radius % 2 == 0:
            blur_radius += 1
        
        # Calculate sigma for Gaussian blur. A common rule of thumb is sigma = radius / 3
        sigma = blur_radius / 3.0
        
        # Apply Gaussian blur using a convolution
        # We need to create a Gaussian kernel
        
        # Create a 1D Gaussian kernel
        kernel_1d = torch.exp(-torch.arange(-(blur_radius // 2), (blur_radius // 2) + 1).float()**2 / (2 * sigma**2))
        kernel_1d /= kernel_1d.sum()
        
        # Create a 2D Gaussian kernel by multiplying 1D kernels
        kernel_2d = kernel_1d.unsqueeze(0) * kernel_1d.unsqueeze(1)
        kernel_2d = kernel_2d.unsqueeze(0).unsqueeze(0) # [1, 1, H, W] for conv2d

        # Apply padding to handle edges
        padding = blur_radius // 2
        
        blurred_mask = F.conv2d(mask, kernel_2d.to(mask.device), padding=padding, groups=1)

        # Threshold the blurred mask to get a binary mask with smoothed edges
        anti_aliased_mask = (blurred_mask > threshold).float()

        # Remove the channel dimension if it was added
        if anti_aliased_mask.shape[1] == 1:
            anti_aliased_mask = anti_aliased_mask.squeeze(1) # [B, H, W]

        json_result = json.dumps({
            "node": "AntiAliasMaskNode",
            "blur_radius": blur_radius,
            "threshold": threshold
        })

        return (anti_aliased_mask, json_result, "done")
