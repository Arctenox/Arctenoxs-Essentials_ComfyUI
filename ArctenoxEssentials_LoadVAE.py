"""
Arctenox Essentials - Load VAE With Metadata
=============================================

Loads a VAE and outputs the VAE object, its filename, and its SHA256 hash
for use with the Save Image With Metadata node (Civitai-compatible).

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""

import os
import hashlib
import folder_paths
import comfy.sd
import comfy.utils


class LoadVAEWithMetadata:
    """
    Load a VAE and expose its name and SHA256 hash for Civitai-compatible metadata.
    Outputs: VAE object, vae_name (string), vae_hash (string)
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "vae_name": (folder_paths.get_filename_list("vae"),),
            }
        }

    RETURN_TYPES = ("VAE", "STRING", "STRING")
    RETURN_NAMES = ("VAE", "vae_name", "vae_hash")
    FUNCTION = "load_vae"
    CATEGORY = "Arctenox Essentials/Loaders"

    def load_vae(self, vae_name):
        # Load the VAE using ComfyUI's correct method
        vae_path = folder_paths.get_full_path("vae", vae_name)
        sd = comfy.utils.load_torch_file(vae_path)
        vae = comfy.sd.VAE(sd=sd)

        # Strip extension for clean display name (Civitai style)
        clean_name = os.path.splitext(vae_name)[0]

        # Calculate SHA256 hash
        vae_hash = self._calculate_hash(vae_path)

        print(f"[Arctenox] Loaded VAE: {vae_name}")
        print(f"[Arctenox] VAE clean name: {clean_name}")
        print(f"[Arctenox] VAE SHA256: {vae_hash}")

        return (vae, clean_name, vae_hash)

    def _calculate_hash(self, file_path):
        """Calculate full SHA256 hash of a file."""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            full_hash = sha256.hexdigest().upper()
            return full_hash
        except Exception as e:
            print(f"[Arctenox] Warning: Could not calculate VAE hash: {e}")
            return ""


# Node registration
NODE_CLASS_MAPPINGS = {
    "LoadVAEWithMetadata": LoadVAEWithMetadata,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadVAEWithMetadata": "Load VAE (Arctenox's Essentials)",
}

__version__ = "1.0.0"
__author__ = "Arctenox"
