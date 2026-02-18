"""
Arctenox Essentials - Image Utilities
======================================

Practical image manipulation nodes that slot naturally into any workflow.

Nodes:
- ImageResize:      Resize with multiple fit modes, outputs new dimensions
- ImageDimensions:  Read width/height from any IMAGE tensor

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""

import torch
import torch.nn.functional as F


# ─────────────────────────────────────────────────────────────────────────────
#  ImageResize
# ─────────────────────────────────────────────────────────────────────────────

_RESIZE_MODES = ["stretch", "fit", "fill", "pad"]
_INTERP_MODES = ["bilinear", "bicubic", "nearest", "lanczos"]


class ImageResize:
    """
    Resize an image to a target resolution.

    Modes:
      stretch  – Ignore aspect ratio, fill exact dimensions.
      fit      – Maintain aspect ratio, fit entirely within target (may have blank bars).
      fill     – Maintain aspect ratio, cover target entirely (may crop edges).
      pad      – Same as fit but adds black padding to reach exact target size.

    Outputs the resized IMAGE plus the actual output width and height as INT,
    making it easy to wire dimensions into KSampler or Cost Estimator.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "width": ("INT", {
                    "default": 1024,
                    "min": 8,
                    "max": 8192,
                    "step": 8,
                    "tooltip": "Target width in pixels"
                }),
                "height": ("INT", {
                    "default": 1024,
                    "min": 8,
                    "max": 8192,
                    "step": 8,
                    "tooltip": "Target height in pixels"
                }),
                "mode": (_RESIZE_MODES, {
                    "default": "fit",
                    "tooltip": (
                        "stretch = exact size, ignore aspect ratio\n"
                        "fit     = keep aspect, fit within target (may letterbox)\n"
                        "fill    = keep aspect, cover target (may crop)\n"
                        "pad     = keep aspect, fit then pad with black to exact size"
                    )
                }),
                "interpolation": (_INTERP_MODES, {
                    "default": "lanczos",
                    "tooltip": "Resampling filter. lanczos/bicubic are sharpest for downscaling."
                }),
            }
        }

    RETURN_TYPES  = ("IMAGE", "INT", "INT")
    RETURN_NAMES  = ("image", "width", "height")
    FUNCTION      = "resize"
    CATEGORY      = "Arctenox Essentials/Image"

    DESCRIPTION = """
    Resize an image with multiple fit modes.

    Mode guide:
    • stretch – exact target size, no aspect ratio preservation
    • fit     – letterbox/pillarbox, whole image visible
    • fill    – zoom/crop to fully cover target area
    • pad     – fit then pad edges with black to reach exact size

    Outputs actual width & height as INT for wiring downstream.
    """

    # ------------------------------------------------------------------

    def _to_bchw(self, image: torch.Tensor) -> torch.Tensor:
        """Convert ComfyUI BHWC float tensor to BCHW float."""
        return image.permute(0, 3, 1, 2)

    def _to_bhwc(self, tensor: torch.Tensor) -> torch.Tensor:
        """Convert BCHW tensor back to ComfyUI BHWC format."""
        return tensor.permute(0, 2, 3, 1)

    def _interpolate(self, tensor: torch.Tensor, h: int, w: int, interp: str) -> torch.Tensor:
        """Interpolate a BCHW tensor to (h, w)."""
        if interp == "lanczos":
            # PyTorch has no native lanczos; bicubic is visually very close
            mode, align = "bicubic", True
        elif interp == "nearest":
            mode, align = "nearest", None
        else:
            mode, align = interp, True

        kwargs = {"mode": mode, "size": (h, w)}
        if align is not None:
            kwargs["align_corners"] = align

        return F.interpolate(tensor.float(), **kwargs).clamp(0.0, 1.0)

    def resize(self, image: torch.Tensor, width: int, height: int,
               mode: str, interpolation: str):

        bchw = self._to_bchw(image)
        _, c, src_h, src_w = bchw.shape
        tw, th = width, height

        if mode == "stretch":
            out = self._interpolate(bchw, th, tw, interpolation)
            out_w, out_h = tw, th

        elif mode == "fit":
            scale = min(tw / src_w, th / src_h)
            new_w = max(8, round(src_w * scale))
            new_h = max(8, round(src_h * scale))
            out = self._interpolate(bchw, new_h, new_w, interpolation)
            out_w, out_h = new_w, new_h

        elif mode == "fill":
            scale = max(tw / src_w, th / src_h)
            scaled_w = max(8, round(src_w * scale))
            scaled_h = max(8, round(src_h * scale))
            scaled = self._interpolate(bchw, scaled_h, scaled_w, interpolation)
            # Center crop
            x0 = (scaled_w - tw) // 2
            y0 = (scaled_h - th) // 2
            out = scaled[:, :, y0:y0 + th, x0:x0 + tw]
            out_w, out_h = tw, th

        else:  # pad
            scale = min(tw / src_w, th / src_h)
            fit_w = max(8, round(src_w * scale))
            fit_h = max(8, round(src_h * scale))
            fitted = self._interpolate(bchw, fit_h, fit_w, interpolation)
            # Create black canvas
            canvas = torch.zeros(
                (fitted.shape[0], c, th, tw),
                dtype=fitted.dtype, device=fitted.device
            )
            x0 = (tw - fit_w) // 2
            y0 = (th - fit_h) // 2
            canvas[:, :, y0:y0 + fit_h, x0:x0 + fit_w] = fitted
            out = canvas
            out_w, out_h = tw, th

        result = self._to_bhwc(out)
        print(f"[Arctenox ImageResize] {src_w}x{src_h} → {out_w}x{out_h}  "
              f"mode={mode}  interp={interpolation}")
        return (result, out_w, out_h)


# ─────────────────────────────────────────────────────────────────────────────
#  ImageDimensions
# ─────────────────────────────────────────────────────────────────────────────

class ImageDimensions:
    """
    Read width, height, and batch size from any IMAGE tensor.

    Useful for wiring real image dimensions into nodes that need explicit
    numbers (KSampler, Cost Estimator, resize targets, etc.) without
    hardcoding them.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            }
        }

    RETURN_TYPES  = ("IMAGE", "INT", "INT", "INT", "STRING")
    RETURN_NAMES  = ("image", "width", "height", "batch_size", "dimensions_str")
    FUNCTION      = "get_dimensions"
    CATEGORY      = "Arctenox Essentials/Image"

    DESCRIPTION = """
    Read dimensions from an IMAGE tensor and output them as INT values.

    Outputs:
    • image          – pass-through (unchanged)
    • width          – pixel width
    • height         – pixel height
    • batch_size     – number of images in the batch
    • dimensions_str – e.g. "1024x1280 (batch: 1)" for display/metadata
    """

    def get_dimensions(self, image: torch.Tensor):
        # ComfyUI IMAGE tensors are BHWC
        b, h, w, c = image.shape
        dims_str = f"{w}x{h} (batch: {b})"
        print(f"[Arctenox ImageDimensions] {dims_str}")
        return (image, w, h, b, dims_str)


# ─────────────────────────────────────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "ArctenoxImageResize":     ImageResize,
    "ArctenoxImageDimensions": ImageDimensions,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArctenoxImageResize":     "Image Resize (Arctenox's Essentials)",
    "ArctenoxImageDimensions": "Image Dimensions (Arctenox's Essentials)",
}

__all__ = ["ImageResize", "ImageDimensions"]
