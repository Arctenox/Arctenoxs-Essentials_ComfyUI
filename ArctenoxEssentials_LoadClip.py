"""
Arctenox Essentials - Load Clip - SDXL
=======================================

A CLIP loader compatible with SDXL/Illustrious/NAI models.
Loads a single CLIP model with both clip_l and clip_g components.

Features:
- SDXL/Illustrious/NAI compatible
- Automatic clip_l and clip_g handling
- Simple dropdown selection
- Standard CLIP output

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""

import folder_paths
import comfy.sd


class ArcLoadClip:
    """
    Load a single CLIP model compatible with SDXL/Illustrious/NAI.
    Provides access to both clip_l and clip_g components.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip_name": (folder_paths.get_filename_list("clip"), {
                    "tooltip": "Select the CLIP model to load (SDXL/Illustrious/NAI compatible)"
                }),
            }
        }
    
    RETURN_TYPES = ("CLIP",)
    RETURN_NAMES = ("clip",)
    FUNCTION = "load_clip"
    CATEGORY = "Arctenox Essentials/Loaders"
    DESCRIPTION = "Loads a single CLIP model with clip_l and clip_g for SDXL/Illustrious/NAI"

    def load_clip(self, clip_name):
        """
        Load CLIP model from file.
        
        Args:
            clip_name: Name of the CLIP model file to load
        
        Returns:
            tuple: (clip,)
        """
        clip_path = folder_paths.get_full_path("clip", clip_name)
        clip = comfy.sd.load_clip(
            ckpt_paths=[clip_path], 
            embedding_directory=folder_paths.get_folder_paths("embeddings")
        )
        return (clip,)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ArcLoadClip": ArcLoadClip
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArcLoadClip": "Load Clip - SDXL (Arctenox's Essentials)"
}

__all__ = ["ArcLoadClip"]