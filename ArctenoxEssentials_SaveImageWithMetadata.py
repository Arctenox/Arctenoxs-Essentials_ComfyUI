"""
Arctenox Essentials - Save Image With Metadata (Enhanced + Civitai Compatible)
===============================================================================

A comprehensive image saving node that embeds full generation metadata
with proper resource hashes for automatic Civitai detection.

Features:
- Embeds ALL generation parameters with resource hashes
- Civitai-compatible metadata format (A1111 style)
- Optional workflow JSON embedding
- Automatic folder organization by date/workflow
- Multiple format support (PNG, JPEG, WEBP)
- Preserves quality while minimizing file size
- Professional workflow organization
- Built-in seed widget with full range support
- Dropdown menus for samplers and schedulers
- Simple text-based LoRA input (name:strength format)

Author: Arctenox
Version: 2.0.0 - uses FULL SHA256 hashes for LoRAs
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
import comfy.samplers


class SaveImageWithMetadata:
    """
    Save images with embedded metadata for full reproducibility and Civitai detection.
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
                "format": (["png", "jpeg", "webp"], {"default": "png"}),
                "quality": ("INT", {
                    "default": 95,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "Quality for JPEG/WEBP (1-100, higher is better)"
                }),
                "embed_workflow": (["disabled", "enabled"], {"default": "disabled"}),
                "positive_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "Positive prompt used for generation"
                }),
                "negative_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "Negative prompt used for generation"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": -0xffffffffffffffff,
                    "max": 0xffffffffffffffff,
                    "forceInput": True,
                    "tooltip": "Seed used for generation"
                }),
                "steps": ("INT", {
                    "default": 20,
                    "min": 1,
                    "max": 10000,
                    "tooltip": "Number of sampling steps"
                }),
                "cfg": ("FLOAT", {
                    "default": 7.0,
                    "min": 0.0,
                    "max": 100.0,
                    "step": 0.1,
                    "tooltip": "CFG scale value"
                }),
                "sampler_name": ("STRING", {
                    "default": "euler",
                    "multiline": False,
                    "forceInput": True,
                    "tooltip": "Sampler name - connect from KSampler or pass as string"
                }),
                "scheduler": ("STRING", {
                    "default": "normal",
                    "multiline": False,
                    "forceInput": True,
                    "tooltip": "Scheduler name - connect from KSampler or pass as string"
                }),
                "model_name": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "forceInput": True,
                    "tooltip": "Model/checkpoint name"
                }),
                "model_hash": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "forceInput": True,
                    "tooltip": "Model/checkpoint hash (for Civitai detection)"
                }),
                "vae": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "VAE filename (e.g. vae-ft-mse-840000-ema-pruned.safetensors)\nHash is calculated automatically for Civitai detection"
                }),
                "loras": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "LoRAs - Supports two formats:\n1. ComfyUI format: <lora:filename.safetensors:strength>\n2. Simple format: filename.safetensors:strength (one per line)\n\nFull SHA256 hashes are calculated automatically for Civitai detection"
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
                   format="png", quality=95, embed_workflow="disabled",
                   positive_prompt="", negative_prompt="", seed=None, steps=20,
                   cfg=7.0, sampler_name="", scheduler="", model_name="",
                   model_hash="", vae="", loras="",
                   prompt=None, extra_pnginfo=None):
        """
        Save images with comprehensive metadata including resource hashes.
        """
        # Apply safe default for seed if not connected
        if seed is None: seed = 0

        # Parse VAE info (name + AutoV2 hash)
        parsed_vae = self._parse_vae(vae)
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
        
        # Parse LoRA data from text input
        parsed_loras = self._parse_loras(loras)
        
        results = list()
        
        for batch_number, image in enumerate(images):
            # Convert tensor to PIL Image
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            # Prepare metadata
            metadata = None
            if format == "png":
                metadata = PngInfo()
                
                # Add generation parameters
                generation_params = {
                    "positive_prompt": positive_prompt,
                    "negative_prompt": negative_prompt,
                    "seed": seed,
                    "steps": steps,
                    "cfg_scale": cfg,
                    "sampler": sampler_name,
                    "scheduler": scheduler,
                    "model": model_name,
                    "model_hash": model_hash,
                    "vae": parsed_vae["name"],
                    "vae_hash": parsed_vae["hash"],
                }
                
                # Add LoRA information
                if parsed_loras:
                    generation_params["loras"] = parsed_loras
                
                # Add each parameter as separate metadata field
                for key, value in generation_params.items():
                    if value is not None and value != "":
                        if key == "loras":
                            metadata.add_text(key, json.dumps(value))
                        else:
                            metadata.add_text(key, str(value))
                
                # Add as combined JSON
                metadata.add_text("generation_parameters", json.dumps(generation_params))
                
                # Add workflow metadata (optional)
                if embed_workflow == "enabled" and prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                    metadata.add_text("workflow", json.dumps(prompt))
                
                # Add extra PNG info
                if extra_pnginfo is not None:
                    for key, value in extra_pnginfo.items():
                        metadata.add_text(key, json.dumps(value))
                
                # Add generation timestamp
                metadata.add_text("generation_time", datetime.now().isoformat())
                metadata.add_text("generator", "Arctenox Essentials for ComfyUI")
                metadata.add_text("software", "ComfyUI")
                
                # Add A1111-style parameters for Civitai compatibility
                a1111_params = self._format_a1111_params(
                    positive_prompt, negative_prompt, seed, steps,
                    cfg, sampler_name, scheduler, model_name, model_hash,
                    images[0].shape[1], images[0].shape[0], parsed_loras,
                    parsed_vae["name"], parsed_vae["hash"]
                )
                metadata.add_text("parameters", a1111_params)
                
                # Debug: Print the parameters being embedded
                print("[Arctenox] === A1111 Parameters ===")
                print(a1111_params)
                print("[Arctenox] ===========================")
            
            # Generate filename with counter
            file = f"{filename}_{counter:05}_.{format}"
            filepath = os.path.join(full_output_folder, file)
            
            # Save image with appropriate format and metadata
            if format == "png":
                img.save(filepath, pnginfo=metadata, compress_level=self.compress_level)
            elif format == "jpeg":
                img.save(filepath, quality=quality, optimize=True)
                if positive_prompt or negative_prompt or seed:
                    self._save_metadata_txt(filepath, positive_prompt, negative_prompt,
                                          seed, steps, cfg, sampler_name, scheduler,
                                          model_name, model_hash, parsed_loras,
                                          parsed_vae["name"], parsed_vae["hash"])
            elif format == "webp":
                img.save(filepath, quality=quality, method=6)
                if positive_prompt or negative_prompt or seed:
                    self._save_metadata_txt(filepath, positive_prompt, negative_prompt,
                                          seed, steps, cfg, sampler_name, scheduler,
                                          model_name, model_hash, parsed_loras,
                                          parsed_vae["name"], parsed_vae["hash"])
            
            # Prepare result info
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            
            counter += 1
        
        return {"ui": {"images": results}}
    
    def _parse_vae(self, vae_text):
        """
        Parse VAE text input — looks up the file and computes its AutoV2 hash.
        Returns a dict with 'name' (no extension) and 'hash' (AutoV2).
        """
        result = {"name": "", "hash": ""}

        if not vae_text or not vae_text.strip():
            return result

        vae_filename = vae_text.strip()
        clean_name = os.path.splitext(vae_filename)[0]
        result["name"] = clean_name

        # Calculate AutoV2 hash
        try:
            vae_path = folder_paths.get_full_path("vae", vae_filename)
            if not vae_path or not os.path.exists(vae_path):
                print(f"[Arctenox] Warning: VAE file not found: {vae_filename}")
                return result

            sha256 = hashlib.sha256()
            with open(vae_path, "rb") as f:
                sha256.update(f.read(0x100000))
            result["hash"] = sha256.hexdigest().upper()[:10]
            print(f"[Arctenox] VAE: {clean_name} | AutoV2: {result['hash']}")
        except Exception as e:
            print(f"[Arctenox] Warning: Could not calculate VAE hash: {e}")

        return result

    def _parse_loras(self, loras_text):
        """
        Parse LoRA text input into structured data.
        Supports both formats:
        - ComfyUI format: <lora:filename.safetensors:strength>
        - Simple format: filename.safetensors:strength
        """
        print(f"[Arctenox] === LoRA Parsing Debug ===")
        print(f"[Arctenox] Input text: '{loras_text}'")
        print(f"[Arctenox] Text is empty: {not loras_text or not loras_text.strip()}")
        
        if not loras_text or not loras_text.strip():
            print(f"[Arctenox] No LoRAs provided - skipping")
            return []
        
        parsed = []
        
        # Check if using ComfyUI format with <lora:...> tags
        if '<lora:' in loras_text:
            # Extract all <lora:...> tags using regex
            import re
            pattern = r'<lora:([^:>]+):([^>]+)>'
            matches = re.findall(pattern, loras_text)
            print(f"[Arctenox] Found {len(matches)} <lora:...> tag(s)")
            
            for match in matches:
                lora_name = match[0].strip()
                strength_str = match[1].strip()
                
                print(f"[Arctenox] Processing LoRA tag: <lora:{lora_name}:{strength_str}>")
                
                if not lora_name:
                    continue
                
                # Parse strength
                strength = 1.0
                try:
                    strength = float(strength_str)
                except ValueError:
                    print(f"[Arctenox] Warning: Invalid strength '{strength_str}' for {lora_name}, using 1.0")
                
                # Calculate hash
                lora_hash = self._calculate_lora_hash(lora_name)
                
                if lora_hash:
                    print(f"[Arctenox] ✓ LoRA detected: {lora_name}")
                    print(f"[Arctenox]   Hash (FULL SHA256): {lora_hash}")
                    print(f"[Arctenox]   Strength: {strength}")
                    parsed.append({
                        "name": lora_name,
                        "strength": strength,
                        "hash": lora_hash
                    })
                else:
                    print(f"[Arctenox] WARNING: Could not calculate hash for {lora_name}")
        else:
            # Use simple line-by-line format
            lines = loras_text.strip().split('\n')
            print(f"[Arctenox] Found {len(lines)} line(s) to parse")
            
            for line in lines:
                line = line.strip()
                print(f"[Arctenox] Processing line: '{line}'")
                if not line:
                    print(f"[Arctenox]   Line is empty, skipping")
                    continue
                
                # Parse format: filename:strength or just filename
                parts = line.split(':')
                lora_name = parts[0].strip()
                print(f"[Arctenox]   Parsed name: '{lora_name}'")
                
                if not lora_name:
                    print(f"[Arctenox]   Name is empty, skipping")
                    continue
                
                # Get strength (default to 1.0)
                strength = 1.0
                if len(parts) > 1:
                    try:
                        strength = float(parts[1].strip())
                    except ValueError:
                        print(f"[Arctenox] Warning: Invalid strength for {lora_name}, using 1.0")
                
                # Calculate hash
                lora_hash = self._calculate_lora_hash(lora_name)
                
                if lora_hash:
                    print(f"[Arctenox] LoRA detected: {lora_name}")
                    print(f"[Arctenox] LoRA hash (FULL SHA256): {lora_hash}")
                    parsed.append({
                        "name": lora_name,
                        "strength": strength,
                        "hash": lora_hash
                    })
                else:
                    print(f"[Arctenox] WARNING: Could not calculate hash for {lora_name}")
        
        print(f"[Arctenox] === Parsing Complete: {len(parsed)} LoRA(s) found ===")
        return parsed
    
    def _calculate_lora_hash(self, lora_name):
        """
        Calculate Civitai AutoV2 hash for a LoRA file.
        SHA256 of the first 1MB (0x100000 bytes) — matches Civitai's detection format.
        """
        try:
            lora_path = folder_paths.get_full_path("loras", lora_name)
            if not lora_path or not os.path.exists(lora_path):
                print(f"[Arctenox] Warning: LoRA file not found: {lora_name}")
                return ""

            sha256 = hashlib.sha256()
            with open(lora_path, "rb") as f:
                chunk = f.read(0x100000)  # Read exactly 1MB
                sha256.update(chunk)
            autov2_hash = sha256.hexdigest().upper()[:10]
            print(f"[Arctenox] Calculated AutoV2 hash for {lora_name}: {autov2_hash}")
            return autov2_hash
        except Exception as e:
            print(f"[Arctenox] Error calculating hash for {lora_name}: {e}")
            return ""
    
    def _format_a1111_params(self, positive, negative, seed, steps, cfg,
                            sampler, scheduler, model, model_hash, width, height, loras=None, vae_name=None, vae_hash=None):
        """
        Format metadata in A1111 style for Civitai compatibility.
        
        This is THE KEY FORMAT for Civitai resource detection!
        Matches the EXACT format from Automatic1111's output.
        """
        params_parts = []
        
        # Add prompt (without modifying it)
        if positive:
            params_parts.append(positive)
        
        if negative:
            params_parts.append(f"Negative prompt: {negative}")
        
        detail_parts = []
        detail_parts.append(f"Steps: {steps}")
        
        if sampler:
            sampler_full = sampler
            if scheduler:
                sampler_full += f" {scheduler}"
            detail_parts.append(f"Sampler: {sampler_full}")
        
        detail_parts.append(f"CFG scale: {cfg}")
        detail_parts.append(f"Seed: {seed}")
        detail_parts.append(f"Size: {width}x{height}")
        
        if model:
            detail_parts.append(f"Model: {model}")
        
        # CRITICAL: Add model hash in the format Civitai expects
        if model_hash:
            detail_parts.append(f"Model hash: {model_hash}")

        # VAE name - Civitai expects "VAE: name" (extension already stripped by LoadVAE node)
        if vae_name:
            detail_parts.append(f"VAE: {vae_name}")

        # VAE hash for Civitai resource detection
        if vae_hash:
            detail_parts.append(f"VAE hash: {vae_hash}")
        
        # CRITICAL: Add LoRA hashes in EXACT A1111 format
        # This is what Civitai parses to detect LoRAs!
        print(f"[Arctenox] Formatting A1111 params - LoRAs provided: {loras is not None}")
        if loras:
            print(f"[Arctenox] Number of LoRAs: {len(loras)}")
            lora_hashes = []
            for lora in loras:
                name = lora.get("name", "")
                hash_val = lora.get("hash", "")
                print(f"[Arctenox]   LoRA: {name}, Hash: {hash_val}")
                if name and hash_val:
                    # Remove file extension
                    name_clean = os.path.splitext(name)[0]
                    # Format MUST be: "name: hash" (no quotes around individual entries)
                    lora_hashes.append(f"{name_clean}: {hash_val}")
            
            # Add the Lora hashes line if we have any
            # Format: Lora hashes: "name1: hash1, name2: hash2, name3: hash3"
            if lora_hashes:
                hashes_str = ", ".join(lora_hashes)
                detail_parts.append(f"Lora hashes: \"{hashes_str}\"")
                print(f"[Arctenox] Added Lora hashes line: Lora hashes: \"{hashes_str}\"")
        
        params_parts.append(", ".join(detail_parts))
        
        return "\n".join(params_parts)
    
    def _save_metadata_txt(self, image_path, positive, negative, seed, steps,
                          cfg, sampler, scheduler, model, model_hash, loras=None, vae_name=None, vae_hash=None):
        """
        Save metadata as a text file alongside non-PNG images.
        """
        txt_path = os.path.splitext(image_path)[0] + ".txt"
        
        metadata_lines = []
        metadata_lines.append("=== Generation Parameters ===")
        metadata_lines.append(f"Positive Prompt: {positive}")
        metadata_lines.append(f"Negative Prompt: {negative}")
        metadata_lines.append(f"Seed: {seed}")
        metadata_lines.append(f"Steps: {steps}")
        metadata_lines.append(f"CFG Scale: {cfg}")
        
        if sampler:
            metadata_lines.append(f"Sampler: {sampler}")
        if scheduler:
            metadata_lines.append(f"Scheduler: {scheduler}")
        if model:
            metadata_lines.append(f"Model: {model}")
        if model_hash:
            metadata_lines.append(f"Model Hash: {model_hash}")
        if vae_name:
            metadata_lines.append(f"VAE: {vae_name}")
        if vae_hash:
            metadata_lines.append(f"VAE Hash: {vae_hash}")
        
        # Add LoRA information
        if loras:
            metadata_lines.append("\n=== LoRAs ===")
            for i, lora in enumerate(loras, 1):
                metadata_lines.append(f"LoRA {i}: {lora.get('name', '')}")
                metadata_lines.append(f"  Strength: {lora.get('strength', 0.0)}")
                if lora.get('hash'):
                    metadata_lines.append(f"  Hash: {lora.get('hash', '')}")
        
        metadata_lines.append(f"\nGenerated: {datetime.now().isoformat()}")
        
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(metadata_lines))
        except Exception as e:
            print(f"[Arctenox] Warning: Could not save metadata txt file: {e}")
    
    def _process_date_tokens(self, text):
        """
        Process date tokens in filename prefix.
        """
        now = datetime.now()
        
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


# Node registration
NODE_CLASS_MAPPINGS = {
    "SaveImageWithMetadata": SaveImageWithMetadata,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageWithMetadata": "Save Image With Metadata (Arctenox's Essentials)",
}
