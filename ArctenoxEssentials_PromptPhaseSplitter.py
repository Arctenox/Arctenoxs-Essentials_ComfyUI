"""
Arctenox Essentials - Prompt Phase Splitter (with Wildcards)
=============================================================

Splits conditioning into multiple temporal phases applied at different
sampling steps for progressive refinement control.

NEW in this version: Wildcard Prompt support
  - Each phase prompt box (and a dedicated standalone wildcard field)
    supports {option1|option2|option3} inline wildcard syntax
  - A separate wildcard file can be loaded from
    ComfyUI/custom_nodes/Arctenoxs-Essentials_ComfyUI/wildcards/
  - Seed-locked: same seed always picks the same options (reproducible)
  - Wildcards resolve before encoding, so the resolved text is also
    returned as a STRING for metadata / debugging

Author: Arctenox
Version: 2.0.1 (Patched for caching)
License: GPL-3.0
"""

import os
import re
import random
import torch
import folder_paths


# ─────────────────────────────────────────────────────────────────────────────
#  Wildcard resolver
# ─────────────────────────────────────────────────────────────────────────────

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_WILDCARD_DIRS = [
    os.path.join(_THIS_DIR, "wildcards"),
    os.path.join(folder_paths.base_path, "wildcards"),
]


def _load_wildcard_file(name: str) -> list[str]:
    """
    Load options from a .txt wildcard file.
    'name' can be 'hair_color', 'hair_color.txt', or a relative subfolder path.
    """
    candidates = [name, name + ".txt"]
    for base_dir in _WILDCARD_DIRS:
        for candidate in candidates:
            path = os.path.join(base_dir, candidate)
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        lines = [l.strip() for l in fh.readlines()]
                    return [l for l in lines if l and not l.startswith("#")]
                except Exception as exc:
                    print(f"[Arctenox Wildcards] Could not read {path}: {exc}")
    return []


def _resolve_wildcards(text: str, rng: random.Random) -> str:
    """
    Recursively resolve all wildcard tokens in *text*.
    """
    max_passes = 20   # guard against infinite recursion

    for _ in range(max_passes):
        changed = False

        # ── file wildcards __name__ ──────────────────────────────────
        file_wc_re = re.compile(r"__([a-zA-Z0-9][a-zA-Z0-9_/.-]*?)__")
        def _replace_file(m):
            options = _load_wildcard_file(m.group(1).strip())
            if options:
                return rng.choice(options)
            print(f"[Arctenox Wildcards] Wildcard file not found: {m.group(1)}")
            return m.group(0)

        new_text, n = file_wc_re.subn(_replace_file, text)
        if n:
            text = new_text
            changed = True

        # ── inline wildcards {a|b|c} ─────────────────────────────────
        inline_re = re.compile(r"\{([^{}]+)\}")
        def _replace_inline(m):
            options = [o.strip() for o in m.group(1).split("|")]
            options = [o for o in options if o]
            return rng.choice(options) if options else ""

        new_text, n = inline_re.subn(_replace_inline, text)
        if n:
            text = new_text
            changed = True

        if not changed:
            break

    return text


# ─────────────────────────────────────────────────────────────────────────────
#  Node
# ─────────────────────────────────────────────────────────────────────────────

class PromptPhaseSplitter:
    """
    Splits prompt conditioning into temporal phases applied at different sampling steps.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_positive": ("CONDITIONING",),
                "base_negative": ("CONDITIONING",),

                # ── Phase 1: Composition ──────────────────────────────
                "enable_composition": (["disabled", "enabled"], {
                    "default": "enabled",
                    "tooltip": "Enable composition phase"
                }),
                "composition_prompt": ("STRING", {
                    "default": "masterpiece, best quality, composition, framing, rule of thirds",
                    "multiline": True,
                    "tooltip": "Applied in early sampling (composition structure). Supports wildcards."
                }),
                "composition_weight": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1,
                    "tooltip": "Strength of composition phase"
                }),
                "composition_end_percent": ("FLOAT", {
                    "default": 0.3, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": "When to end composition phase (0.3 = 30% of steps)"
                }),

                # ── Phase 2: Detail ───────────────────────────────────
                "enable_detail": (["disabled", "enabled"], {
                    "default": "enabled",
                    "tooltip": "Enable detail phase"
                }),
                "detail_prompt": ("STRING", {
                    "default": "intricate details, fine details, sharp focus, high detail",
                    "multiline": True,
                    "tooltip": "Applied in middle sampling (detail refinement). Supports wildcards."
                }),
                "detail_weight": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1,
                    "tooltip": "Strength of detail phase"
                }),
                "detail_start_percent": ("FLOAT", {
                    "default": 0.25, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": "When to start detail phase"
                }),
                "detail_end_percent": ("FLOAT", {
                    "default": 0.65, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": "When to end detail phase"
                }),

                # ── Phase 3: Texture ──────────────────────────────────
                "enable_texture": (["disabled", "enabled"], {
                    "default": "enabled",
                    "tooltip": "Enable texture phase"
                }),
                "texture_prompt": ("STRING", {
                    "default": "smooth textures, refined surface, polished finish",
                    "multiline": True,
                    "tooltip": "Applied in late sampling (texture refinement). Supports wildcards."
                }),
                "texture_weight": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1,
                    "tooltip": "Strength of texture phase"
                }),
                "texture_start_percent": ("FLOAT", {
                    "default": 0.6, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": "When to start texture phase"
                }),

                # ── Phase 4: Character/Subject ────────────────────────
                "enable_character": (["disabled", "enabled"], {
                    "default": "disabled",
                    "tooltip": "Enable character/subject focus phase"
                }),
                "character_prompt": ("STRING", {
                    "default": "1girl, detailed face, expressive eyes, natural pose",
                    "multiline": True,
                    "tooltip": "Character/subject focus (applied when enabled). Supports wildcards."
                }),
                "character_weight": ("FLOAT", {
                    "default": 1.2, "min": 0.0, "max": 3.0, "step": 0.1,
                    "tooltip": "Strength of character phase"
                }),
                "character_start_percent": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": "When to start character phase"
                }),
                "character_end_percent": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": "When to end character phase"
                }),

                # ── Global settings ───────────────────────────────────
                "blend_mode": (["concat", "append", "add", "subtract"], {
                    "default": "concat",
                    "tooltip": "concat (join prompts), append (separate entries), add (strengthen), subtract (weaken)"
                }),

                # ── Wildcard settings ─────────────────────────────────
                "wildcard_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Standalone wildcard prompt. Appended to composition or base."
                }),
                "wildcard_seed": ("INT", {
                    "default": 0,
                    "min": -1,
                    "max": 0xffffffffffffffff,
                    "tooltip": "Seed for wildcards. -1 = Randomize every run. 0+ = Fixed."
                }),
            },
            "optional": {
                "clip": ("CLIP",),
            }
        }

    RETURN_TYPES  = ("CONDITIONING", "CONDITIONING", "STRING", "STRING")
    RETURN_NAMES  = ("positive", "negative", "phase_info", "resolved_wildcards")
    FUNCTION      = "split_phases"
    CATEGORY      = "Arctenox Essentials/Sampling"

    DESCRIPTION = """
    Splits prompt conditioning into temporal phases for progressive refinement.
    Supports wildcards and internal seed control.
    """

    # ------------------------------------------------------------------
    #  Cache Busting for seed=-1
    # ------------------------------------------------------------------
    @classmethod
    def IS_CHANGED(cls, wildcard_seed, **kwargs):
        # If seed is -1, return NaN to force a re-run every time
        if wildcard_seed == -1:
            return float("NaN")
        # Otherwise, the output is deterministic based on the seed
        return wildcard_seed

    # ------------------------------------------------------------------
    #  Wildcard resolution
    # ------------------------------------------------------------------

    def _make_rng(self, seed: int) -> random.Random:
        if seed == -1:
            return random.Random()
        return random.Random(seed)

    def _resolve(self, text: str, rng: random.Random) -> str:
        return _resolve_wildcards(text, rng)

    # ------------------------------------------------------------------
    #  CLIP encoding helpers
    # ------------------------------------------------------------------

    def _encode_prompt(self, clip, prompt):
        if not clip or not prompt or not prompt.strip():
            return None
        tokens = clip.tokenize(prompt)
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        return [[cond, {"pooled_output": pooled}]]

    def _pad_conditioning_tensors(self, tensor1, tensor2):
        b1, s1, d = tensor1.shape
        b2, s2, _ = tensor2.shape
        if s1 < s2:
            padding = torch.zeros(b1, s2 - s1, d, device=tensor1.device, dtype=tensor1.dtype)
            tensor1 = torch.cat([tensor1, padding], dim=1)
        elif s2 < s1:
            padding = torch.zeros(b2, s1 - s2, d, device=tensor2.device, dtype=tensor2.dtype)
            tensor2 = torch.cat([tensor2, padding], dim=1)
        return tensor1, tensor2

    def _combine_conditioning(self, base_cond, phase_prompts, clip, blend_mode, weights):
        if not phase_prompts or not clip:
            return base_cond

        if blend_mode == "concat":
            base_prompt = "masterpiece, best quality"
            combined_prompt = ", ".join([base_prompt] + phase_prompts)
            return self._encode_prompt(clip, combined_prompt)

        elif blend_mode == "append":
            result = list(base_cond)
            for prompt in phase_prompts:
                phase_cond = self._encode_prompt(clip, prompt)
                if phase_cond:
                    result.extend(phase_cond)
            return result

        elif blend_mode == "add":
            result = []
            for base_item in base_cond:
                base_tensor = base_item[0].clone()
                base_dict = base_item[1].copy()
                for i, prompt in enumerate(phase_prompts):
                    phase_cond = self._encode_prompt(clip, prompt)
                    if phase_cond and i < len(weights):
                        phase_tensor = phase_cond[0][0]
                        padded_base, padded_phase = self._pad_conditioning_tensors(
                            base_tensor, phase_tensor
                        )
                        base_tensor = padded_base + (padded_phase * weights[i])
                result.append([base_tensor, base_dict])
            return result

        else:  # subtract
            result = []
            for base_item in base_cond:
                base_tensor = base_item[0].clone()
                base_dict = base_item[1].copy()
                for i, prompt in enumerate(phase_prompts):
                    phase_cond = self._encode_prompt(clip, prompt)
                    if phase_cond and i < len(weights):
                        phase_tensor = phase_cond[0][0]
                        padded_base, padded_phase = self._pad_conditioning_tensors(
                            base_tensor, phase_tensor
                        )
                        base_tensor = padded_base - (padded_phase * weights[i])
                result.append([base_tensor, base_dict])
            return result

    # ------------------------------------------------------------------
    #  Main function
    # ------------------------------------------------------------------

    def split_phases(self,
                     base_positive, base_negative,
                     enable_composition, composition_prompt, composition_weight, composition_end_percent,
                     enable_detail, detail_prompt, detail_weight, detail_start_percent, detail_end_percent,
                     enable_texture, texture_prompt, texture_weight, texture_start_percent,
                     enable_character, character_prompt, character_weight,
                     character_start_percent, character_end_percent,
                     blend_mode,
                     wildcard_prompt, wildcard_seed,
                     clip=None):

        if clip is None:
            return (base_positive, base_negative, "No CLIP provided", "")

        rng = self._make_rng(wildcard_seed)

        r_composition = self._resolve(composition_prompt, rng)
        r_detail      = self._resolve(detail_prompt,      rng)
        r_texture     = self._resolve(texture_prompt,     rng)
        r_character   = self._resolve(character_prompt,   rng)
        r_wildcard    = self._resolve(wildcard_prompt,    rng)

        resolved_parts = []
        if r_composition != composition_prompt: resolved_parts.append(f"[Composition] {r_composition}")
        if r_detail != detail_prompt:           resolved_parts.append(f"[Detail] {r_detail}")
        if r_texture != texture_prompt:         resolved_parts.append(f"[Texture] {r_texture}")
        if r_character != character_prompt:     resolved_parts.append(f"[Character] {r_character}")
        if r_wildcard:                          resolved_parts.append(f"[Wildcard] {r_wildcard}")

        resolved_wildcards_str = "\n".join(resolved_parts) if resolved_parts else "(no wildcards resolved)"

        active_prompts = []
        phase_descriptions = []

        if enable_composition == "enabled" and composition_weight > 0 and r_composition.strip():
            prompt_to_use = r_composition
            if r_wildcard.strip():
                prompt_to_use = r_composition + ", " + r_wildcard
            active_prompts.append(prompt_to_use)
            phase_descriptions.append(f"Composition: 0%-{composition_end_percent*100:.0f}% ({composition_weight:.1f})")
        elif r_wildcard.strip():
            active_prompts.append(r_wildcard)
            phase_descriptions.append("Wildcard (standalone): appended to positive")

        if enable_detail == "enabled" and detail_weight > 0 and r_detail.strip():
            active_prompts.append(r_detail)
            phase_descriptions.append(f"Detail: {detail_start_percent*100:.0f}%-{detail_end_percent*100:.0f}% ({detail_weight:.1f})")

        if enable_texture == "enabled" and texture_weight > 0 and r_texture.strip():
            active_prompts.append(r_texture)
            phase_descriptions.append(f"Texture: {texture_start_percent*100:.0f}%-100% ({texture_weight:.1f})")

        if enable_character == "enabled" and character_weight > 0 and r_character.strip():
            active_prompts.append(r_character)
            phase_descriptions.append(f"Character: {character_start_percent*100:.0f}%-{character_end_percent*100:.0f}% ({character_weight:.1f})")

        weights = [composition_weight, detail_weight, texture_weight, character_weight]
        result_positive = self._combine_conditioning(
            base_positive, active_prompts, clip, blend_mode, weights
        )

        if active_prompts:
            phase_info = f"Active phases ({blend_mode} mode):\n"
            phase_info += "\n".join(f"  - {desc}" for desc in phase_descriptions)
            phase_info += f"\n\nCombined {len(active_prompts)} phase prompt(s)"
            phase_info += f"\nWildcard seed: {wildcard_seed}"
        else:
            phase_info = "No active phases - using base conditioning"

        return (result_positive, base_negative, phase_info, resolved_wildcards_str)


# ─────────────────────────────────────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "PromptPhaseSplitter": PromptPhaseSplitter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptPhaseSplitter": "Prompt Phase Splitter (Arctenox's Essentials)",
}

__all__ = ["PromptPhaseSplitter"]
