"""
Arctenox Essentials - LoRA Stack Manager
=========================================

Stack up to 10 LoRAs in a single node with individual enable toggles
and separate model/clip strength sliders, inspired by rgthree's Power Lora Loader.

Features:
- 10 LoRA slots in one node (no more chaining 10 separate Load LoRA nodes)
- Per-slot enable/disable toggle
- Separate model_strength and clip_strength per slot
- Outputs STRING list of active LoRAs for metadata embedding
- Hash caching so repeated loads don't rehash large files
- Safe: skips missing/empty slots silently

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""

import os
import hashlib
import folder_paths
import comfy.utils
import comfy.lora


# ─────────────────────────────────────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

_HASH_CACHE: dict = {}   # (path, mtime, size) → full sha256 hex string


def _sha256(filepath: str) -> str:
    """Return full SHA-256 hex digest, cached by (path, mtime, size)."""
    try:
        stat = os.stat(filepath)
        key = (filepath, stat.st_mtime, stat.st_size)
        if key in _HASH_CACHE:
            return _HASH_CACHE[key]
        h = hashlib.sha256()
        with open(filepath, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        digest = h.hexdigest().upper()
        _HASH_CACHE[key] = digest
        return digest
    except Exception as exc:
        print(f"[Arctenox LoRA Stack] Hash error for {filepath}: {exc}")
        return ""


def _apply_lora(model, clip, lora_name: str, model_str: float, clip_str: float):
    """Load and apply a single LoRA, returning (model, clip)."""
    lora_path = folder_paths.get_full_path("loras", lora_name)
    if not lora_path or not os.path.exists(lora_path):
        print(f"[Arctenox LoRA Stack] WARNING - LoRA not found: {lora_name}")
        return model, clip
    lora_weights = comfy.utils.load_torch_file(lora_path, safe_load=True)
    model, clip = comfy.lora.load_lora_for_models(model, clip, lora_weights, model_str, clip_str)
    return model, clip


# ─────────────────────────────────────────────────────────────────────────────
#  Node
# ─────────────────────────────────────────────────────────────────────────────

_SLOT_COUNT = 10


class LoraStackManager:
    """
    LoRA Stack Manager (Arctenox's Essentials)

    Load up to 10 LoRAs in a single node.  Each slot has:
      - A dropdown to pick the LoRA file (or "None" to skip)
      - An enable/disable toggle
      - A model_strength slider
      - A clip_strength slider

    Outputs the patched MODEL and CLIP plus a STRING summary of active LoRAs
    that can be wired straight into Save Image With Metadata.
    """

    @classmethod
    def INPUT_TYPES(cls):
        # Refresh the list every time INPUT_TYPES is called so new LoRAs appear
        lora_list = ["None"] + folder_paths.get_filename_list("loras")

        required = {
            "model": ("MODEL",),
            "clip":  ("CLIP",),
        }

        for i in range(1, _SLOT_COUNT + 1):
            required[f"lora_{i}"]           = (lora_list, {"default": "None"})
            required[f"lora_{i}_enabled"]   = ("BOOLEAN", {
                "default": True,
                "label_on":  "Enabled",
                "label_off": "Disabled"
            })
            required[f"lora_{i}_model_str"] = ("FLOAT", {
                "default": 1.0,
                "min": -10.0,
                "max": 10.0,
                "step": 0.01,
                "tooltip": f"Slot {i} - model (UNet) strength"
            })
            required[f"lora_{i}_clip_str"]  = ("FLOAT", {
                "default": 1.0,
                "min": -10.0,
                "max": 10.0,
                "step": 0.01,
                "tooltip": f"Slot {i} - CLIP (text encoder) strength"
            })

        return {"required": required}

    RETURN_TYPES  = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES  = ("model", "clip", "active_loras")
    FUNCTION      = "apply_stack"
    CATEGORY      = "Arctenox Essentials/Loaders"

    DESCRIPTION = """
    Stack up to 10 LoRAs in one node - no more long chains of Load LoRA nodes.

    Each slot:
      - Dropdown: choose a LoRA file (or leave as "None" to skip)
      - Enabled toggle: quickly mute/unmute a slot without removing it
      - model_strength: how strongly the LoRA affects the UNet
      - clip_strength:  how strongly the LoRA affects the text encoder

    The active_loras STRING output uses the ComfyUI <lora:name:strength> format
    and can be connected directly to Save Image With Metadata's loras input
    for automatic Civitai hash embedding.
    """

    def apply_stack(self, model, clip, **kwargs):
        active_lora_entries = []

        for i in range(1, _SLOT_COUNT + 1):
            lora_name = kwargs.get(f"lora_{i}", "None")
            enabled   = kwargs.get(f"lora_{i}_enabled", True)
            model_str = kwargs.get(f"lora_{i}_model_str", 1.0)
            clip_str  = kwargs.get(f"lora_{i}_clip_str",  1.0)

            # Skip empty / disabled / zero-strength slots
            if lora_name == "None" or not lora_name:
                continue
            if not enabled:
                print(f"[Arctenox LoRA Stack] Slot {i} ({lora_name}): disabled, skipping.")
                continue
            if model_str == 0.0 and clip_str == 0.0:
                print(f"[Arctenox LoRA Stack] Slot {i} ({lora_name}): both strengths are 0, skipping.")
                continue

            print(f"[Arctenox LoRA Stack] Slot {i}: applying {lora_name}  "
                  f"model={model_str:.2f}  clip={clip_str:.2f}")

            model, clip = _apply_lora(model, clip, lora_name, model_str, clip_str)

            # Build metadata string entry in ComfyUI/A1111 lora syntax
            lora_stem = os.path.splitext(lora_name)[0]
            active_lora_entries.append(f"<lora:{lora_stem}:{model_str}>")

        if active_lora_entries:
            active_loras_str = "\n".join(active_lora_entries)
            print(f"[Arctenox LoRA Stack] Active LoRAs:\n{active_loras_str}")
        else:
            active_loras_str = ""
            print("[Arctenox LoRA Stack] No LoRAs active in this stack.")

        return (model, clip, active_loras_str)


# ─────────────────────────────────────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "LoraStackManager": LoraStackManager,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoraStackManager": "LoRA Stack Manager (Arctenox's Essentials)",
}

__all__ = ["LoraStackManager"]
