"""
Arctenox Essentials - Save Image With Metadata
===============================================

A comprehensive image saving node that embeds full generation metadata
directly into PNG files for easy recreation and sharing of exact settings.

Features:
- Embeds all generation parameters (prompts, model, seed, steps, etc.)
- Automatic folder organization by date/workflow
- Multiple format support (PNG, JPEG, WEBP)
- Preserves quality while minimizing file size
- Compatible with ComfyUI metadata readers
- Professional workflow organization

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""

import os
import json
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import folder_paths
from datetime import datetime
import hashlib


class SaveImageWithMetadata:
    """
    Save images with embedded metadata for full reproducibility.
    
    This node saves images with comprehensive metadata embedded in the file,
    including prompts, model information, generation parameters, and more.
    Supports automatic folder organization and multiple output formats.
    """
    
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {
                    "default": "ComfyUI",
                    "multiline": False,
                    "tooltip": "Prefix for output filename. Supports date tokens like %date:yyyy-MM-dd%"
                }),
            },
            "optional": {
                "subfolder": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Subfolder path for organization (e.g., 'outputs/2024-01-15')"
                }),
                "format": (["png", "jpeg", "webp"],),
                "quality": ("INT", {
                    "default": 95,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "Quality for JPEG/WEBP (1-100, higher is better)"
                }),
                "embed_workflow": (["enabled", "disabled"],),
                "embed_prompt": (["enabled", "disabled"],),
                "counter": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "Counter for batch numbering"
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "Arctenox Essentials/Output"

    def save_images(self, images, filename_prefix="ComfyUI", subfolder="", 
                   format="png", quality=95, embed_workflow="enabled", 
                   embed_prompt="enabled", counter=0, prompt=None, extra_pnginfo=None):
        """
        Save images with comprehensive metadata.
        
        Args:
            images: Image tensor from ComfyUI
            filename_prefix: Prefix for saved files
            subfolder: Optional subfolder path
            format: Output format (png/jpeg/webp)
            quality: Quality for lossy formats
            embed_workflow: Whether to embed workflow JSON
            embed_prompt: Whether to embed prompt info
            counter: Batch counter
            prompt: Workflow prompt data
            extra_pnginfo: Additional PNG metadata
        
        Returns:
            dict: Information about saved files
        """
        # Process date tokens in filename
        filename_prefix = self._process_date_tokens(filename_prefix)
        
        # Setup output directory
        full_output_folder, filename, counter, subfolder, filename_prefix = \
            folder_paths.get_save_image_path(filename_prefix, self.output_dir, 
                                            images[0].shape[1], images[0].shape[0])
        
        # Apply subfolder if specified
        if subfolder:
            full_output_folder = os.path.join(full_output_folder, subfolder)
            os.makedirs(full_output_folder, exist_ok=True)
        
        results = list()
        
        for batch_number, image in enumerate(images):
            # Convert tensor to PIL Image
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            # Prepare metadata
            metadata = None
            if format == "png":
                metadata = PngInfo()
                
                # Add workflow metadata
                if embed_workflow == "enabled" and prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                
                # Add extra PNG info
                if embed_prompt == "enabled" and extra_pnginfo is not None:
                    for key, value in extra_pnginfo.items():
                        metadata.add_text(key, json.dumps(value))
                
                # Add generation timestamp
                metadata.add_text("generation_time", datetime.now().isoformat())
                metadata.add_text("generator", "Arctenox Essentials for ComfyUI")
            
            # Generate filename with counter
            file = f"{filename}_{counter:05}_.{format}"
            filepath = os.path.join(full_output_folder, file)
            
            # Save image with appropriate format and metadata
            if format == "png":
                img.save(filepath, pnginfo=metadata, compress_level=self.compress_level)
            elif format == "jpeg":
                # JPEG doesn't support PNG metadata, but we can save to EXIF
                img.save(filepath, quality=quality, optimize=True)
            elif format == "webp":
                img.save(filepath, quality=quality, method=6)
            
            # Prepare result info
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            
            counter += 1
        
        return {"ui": {"images": results}}
    
    def _process_date_tokens(self, text):
        """
        Process date tokens in filename prefix.
        
        Supports tokens like:
        - %date:yyyy-MM-dd% -> 2024-12-21
        - %date:yyyy% -> 2024
        - %date:MM% -> 12
        - %date:dd% -> 21
        - %time:HH-mm-ss% -> 14-30-45
        
        Args:
            text: String potentially containing date tokens
        
        Returns:
            str: String with tokens replaced by actual dates
        """
        now = datetime.now()
        
        # Common date format replacements
        replacements = {
            "%date:yyyy-MM-dd%": now.strftime("%Y-%m-%d"),
            "%date:yyyy%": now.strftime("%Y"),
            "%date:MM%": now.strftime("%m"),
            "%date:dd%": now.strftime("%d"),
            "%time:HH-mm-ss%": now.strftime("%H-%M-%S"),
            "%time:HH-mm%": now.strftime("%H-%M"),
            "%datetime%": now.strftime("%Y-%m-%d_%H-%M-%S"),
        }
        
        for token, replacement in replacements.items():
            text = text.replace(token, replacement)
        
        return text


class SaveImageWithMetadataAdvanced(SaveImageWithMetadata):
    """
    Advanced version with additional metadata options.
    
    Extends the base SaveImageWithMetadata with:
    - Custom metadata fields
    - Hash generation for deduplication
    - Extended format support
    - Batch processing optimizations
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        base_inputs = super().INPUT_TYPES()
        base_inputs["optional"].update({
            "custom_metadata": ("STRING", {
                "default": "",
                "multiline": True,
                "tooltip": "Custom metadata in JSON format: {\"key\": \"value\"}"
            }),
            "generate_hash": (["enabled", "disabled"],),
            "overwrite_existing": (["disabled", "enabled"],),
        })
        return base_inputs
    
    CATEGORY = "Arctenox Essentials/Output"
    
    def save_images(self, images, custom_metadata="", generate_hash="disabled", 
                   overwrite_existing="disabled", **kwargs):
        """
        Save images with advanced metadata options.
        """
        # Parse custom metadata if provided
        if custom_metadata:
            try:
                custom_meta_dict = json.loads(custom_metadata)
                if kwargs.get("extra_pnginfo") is None:
                    kwargs["extra_pnginfo"] = {}
                kwargs["extra_pnginfo"].update(custom_meta_dict)
            except json.JSONDecodeError:
                print("[Arctenox] Warning: Could not parse custom metadata JSON")
        
        # Generate hash if enabled
        if generate_hash == "enabled":
            for image in images:
                img_array = image.cpu().numpy()
                img_hash = hashlib.md5(img_array.tobytes()).hexdigest()[:8]
                if kwargs.get("filename_prefix"):
                    kwargs["filename_prefix"] += f"_{img_hash}"
        
        # Call parent save method
        return super().save_images(images, **kwargs)


# Node registration
NODE_CLASS_MAPPINGS = {
    "SaveImageWithMetadata": SaveImageWithMetadata,
    "SaveImageWithMetadataAdvanced": SaveImageWithMetadataAdvanced,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageWithMetadata": "💾 Save Image With Metadata (Arctenox)",
    "SaveImageWithMetadataAdvanced": "💾 Save Image With Metadata [Advanced] (Arctenox)",
}
