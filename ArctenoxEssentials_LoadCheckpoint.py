"""
Arctenox Essentials - Load Checkpoint with String Output and Hash
==================================================================

A Load Checkpoint node that outputs the model name AND hash for Civitai
resource detection and metadata tracking.

Features:
- Standard checkpoint loading (MODEL, CLIP, VAE outputs)
- STRING output of checkpoint name
- STRING output of SHA256 hash (for Civitai detection)
- Efficient hash caching to avoid recalculation
- Perfect for connecting to SaveImageWithMetadata

Author: Arctenox
Version: 1.1.0
License: GPL-3.0
"""

import os
import hashlib
import folder_paths
import comfy.sd


class LoadCheckpointWithString:
    """
    Load a checkpoint and output model components, name, and SHA256 hash.
    
    The hash output enables automatic resource detection on platforms like
    Civitai when embedded in image metadata.
    """
    
    # Cache for computed hashes to avoid recalculating
    _hash_cache = {}
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ckpt_name": (folder_paths.get_filename_list("checkpoints"),),
            }
        }
    
    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "model_name", "model_hash")
    FUNCTION = "load_checkpoint"
    CATEGORY = "Arctenox Essentials/Loaders"
    
    def load_checkpoint(self, ckpt_name):
        """
        Load checkpoint and return model components, name, and hash.
        
        Args:
            ckpt_name: Name of the checkpoint file to load
        
        Returns:
            tuple: (model, clip, vae, checkpoint_name, checkpoint_hash)
        """
        # Get the full path to the checkpoint
        ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
        
        # Load the checkpoint using ComfyUI's standard loader
        out = comfy.sd.load_checkpoint_guess_config(
            ckpt_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings")
        )
        
        # Extract model, clip, and vae from the loaded checkpoint
        model = out[0]
        clip = out[1]
        vae = out[2]
        
        # Calculate SHA256 hash for Civitai detection
        model_hash = self._calculate_file_hash(ckpt_path)
        
        # Debug output
        print(f"[Arctenox] Loaded checkpoint: {ckpt_name}")
        print(f"[Arctenox] Checkpoint hash: {model_hash}")
        
        # Return model components, name, and hash
        return (model, clip, vae, ckpt_name, model_hash)
    
    def _calculate_file_hash(self, filepath):
        """
        Calculate SHA256 hash of a file with caching.
        
        Args:
            filepath: Full path to the file
        
        Returns:
            str: First 10 characters of SHA256 hash (AutoHash format)
        """
        # Check cache first
        file_stat = os.stat(filepath)
        cache_key = (filepath, file_stat.st_mtime, file_stat.st_size)
        
        if cache_key in self._hash_cache:
            return self._hash_cache[cache_key]
        
        # Calculate hash
        sha256_hash = hashlib.sha256()
        
        try:
            with open(filepath, "rb") as f:
                # Read in chunks to handle large files efficiently
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            
            # Get first 10 chars (AutoHash format used by A1111/Civitai)
            hash_str = sha256_hash.hexdigest()[:10].upper()
            
            # Cache the result
            self._hash_cache[cache_key] = hash_str
            
            return hash_str
            
        except Exception as e:
            print(f"[Arctenox] Error calculating hash for {filepath}: {e}")
            return "UNKNOWN"


# Node registration
NODE_CLASS_MAPPINGS = {
    "ArctenoxLoadCheckpoint": LoadCheckpointWithString,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArctenoxLoadCheckpoint": "Load Checkpoint (Arctenox's Essentials)",
}