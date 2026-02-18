"""
Arctenox Essentials - VAE Encode
==================================

A VAE Encode wrapper that outputs the LATENT plus the source image
dimensions as INT values — making it easy to wire width/height into
a KSampler Refiner or Cost Estimator without a separate Image Dimensions node.

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""

import torch


class VAEEncodeWithDimensions:
    """
    Encode an IMAGE to a LATENT using a VAE, and additionally output
    the source pixel width and height as INT values.

    This is a thin wrapper around ComfyUI's VAE encode that eliminates
    the need to add a separate Image Dimensions node when you want to
    know the resolution after encoding (e.g. for feeding into a Refiner
    or Cost Estimator).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "vae":   ("VAE",),
            },
            "optional": {
                "tile_encode": ("BOOLEAN", {
                    "default": False,
                    "label_on":  "Tiled (VRAM saver)",
                    "label_off": "Standard",
                    "tooltip": (
                        "Use tiled VAE encoding to reduce VRAM usage.\n"
                        "Useful for very large images. May produce subtle\n"
                        "tile seams on high-contrast edges at extreme sizes."
                    )
                }),
            }
        }

    RETURN_TYPES  = ("LATENT", "INT", "INT")
    RETURN_NAMES  = ("latent", "width", "height")
    FUNCTION      = "encode"
    CATEGORY      = "Arctenox Essentials/Latent"

    DESCRIPTION = """
    Encode an IMAGE to a LATENT via VAE, with dimension pass-through.

    Outputs:
    • latent  – encoded latent (ready for KSampler / Refiner)
    • width   – source image pixel width (INT)
    • height  – source image pixel height (INT)

    The dimension outputs let you wire resolution directly into nodes
    like KSampler Refiner (target_width / target_height) or Cost
    Estimator without adding a separate Image Dimensions node.

    Tiled encode reduces peak VRAM for large images at the cost of
    potentially very subtle seam artifacts at extreme resolutions.
    """

    def encode(self, image: torch.Tensor, vae, tile_encode: bool = False):
        # ComfyUI IMAGE tensors are BHWC
        _, h, w, _ = image.shape

        if tile_encode:
            # ComfyUI's VAE has encode_tiled method
            try:
                encoded = vae.encode_tiled(image[:, :, :, :3])
            except AttributeError:
                print("[Arctenox VAE Encode] Warning: encode_tiled not available, "
                      "falling back to standard encode.")
                encoded = vae.encode(image[:, :, :, :3])
        else:
            encoded = vae.encode(image[:, :, :, :3])

        # ComfyUI VAE.encode returns a tensor directly
        if isinstance(encoded, dict) and "samples" in encoded:
            latent = encoded
        else:
            latent = {"samples": encoded}

        print(f"[Arctenox VAE Encode] {w}x{h} → latent "
              f"{latent['samples'].shape}  tiled={tile_encode}")

        return (latent, w, h)


# ─────────────────────────────────────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "ArctenoxVAEEncode": VAEEncodeWithDimensions,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArctenoxVAEEncode": "VAE Encode + Dimensions (Arctenox's Essentials)",
}

__all__ = ["VAEEncodeWithDimensions"]
