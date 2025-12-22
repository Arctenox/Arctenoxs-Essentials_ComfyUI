"""
Arctenox Essentials - CLIP Text Encode with String Output
==========================================================

A CLIP Text Encode node that also outputs the text string for easy
connection to metadata savers and other text-based nodes.

Features:
- Standard CLIP text encoding (CONDITIONING output)
- Additional STRING output of the encoded text
- Perfect for connecting to SaveImageWithMetadata
- No functionality changes to encoding process

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""


class CLIPTextEncodeWithString:
    """
    Encode text using CLIP and output both conditioning and the text string.
    
    This is a wrapper around the standard CLIP Text Encode that adds a
    STRING output, making it easy to capture prompts for metadata.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Text to encode with CLIP"
                }),
                "clip": ("CLIP",),
            }
        }
    
    RETURN_TYPES = ("CONDITIONING", "STRING")
    RETURN_NAMES = ("conditioning", "text")
    FUNCTION = "encode"
    CATEGORY = "Arctenox Essentials/Conditioning"
    
    def encode(self, clip, text):
        """
        Encode text with CLIP and return both conditioning and text string.
        
        Args:
            clip: CLIP model
            text: Text to encode
        
        Returns:
            tuple: (conditioning, text_string)
        """
        # Encode the text using CLIP
        tokens = clip.tokenize(text)
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        
        # Return conditioning in the standard ComfyUI format
        conditioning = [[cond, {"pooled_output": pooled}]]
        
        return (conditioning, text)


# Node registration
NODE_CLASS_MAPPINGS = {
    "CLIPTextEncodeWithString": CLIPTextEncodeWithString,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CLIPTextEncodeWithString": "CLIP Text Encode + String (Arctenox's Essentials)",
}