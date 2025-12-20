"""
Arctenox Essentials - Passthrough Nodes
========================================

Utility nodes for passing through inputs with optional notes
for workflow documentation and organization.

Universal passthrough uses ComfyUI's wildcard type system properly.

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""

class ArctenoxBox:
    """Box."""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "execute"
    CATEGORY = "Arctenox Essentials/Utilities"
    OUTPUT_NODE = True
    DESCRIPTION = ""

    def execute(self):
        return {}
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")


class ArctenoxCheckpointPassthrough:
    """
    Specialized passthrough for MODEL, CLIP, and VAE together.
    Useful for checkpoint-specific workflow organization.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "vae": ("VAE",)
            },
            "optional": {
                "notes": ("STRING", {
                    "default": "", 
                    "multiline": True,
                    "tooltip": "Optional notes for workflow documentation"
                })
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE")
    RETURN_NAMES = ("model", "clip", "vae")
    FUNCTION = "execute"
    CATEGORY = "Arctenox Essentials/Utilities"
    OUTPUT_NODE = False
    
    DESCRIPTION = """
    Passes through checkpoint components (MODEL, CLIP, VAE) with optional documentation.
    
    Features:
    • Pass-through routing for MODEL, CLIP, and VAE together
    • Optional notes field for workflow documentation
    • Maintains full compatibility with all checkpoint types
    • Zero processing overhead - direct passthrough
    
    Use Cases:
    • Organizing checkpoint flows in complex workflows
    • Adding documentation to checkpoint sections
    • Creating clean connection points for checkpoints
    • Workflow readability improvements
    """

    def execute(self, model, clip, vae, notes=""):
        """Pass through checkpoint components"""
        if notes and notes.strip():
            print(f"[Arctenox Checkpoint Passthrough] {notes.strip()}")
        
        return (model, clip, vae)
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")


# Node registration for ComfyUI
NODE_CLASS_MAPPINGS = {
    "ArctenoxBox": ArctenoxBox,
    "ArctenoxCheckpointPassthrough": ArctenoxCheckpointPassthrough,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArctenoxBox": " ",
    "ArctenoxCheckpointPassthrough": "Checkpoint Passthrough + Notes (Arctenox's Essentials)",
}

# Export the classes for import
__all__ = [
    "ArctenoxBox",
    "ArctenoxCheckpointPassthrough",
]
