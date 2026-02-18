"""
Arctenox Essentials - Wildcard Nodes
======================================

Provides ComfyUI nodes for working with wildcard prompts:

  ArctenoxWildcardProcessor  — resolves __wildcard__ tokens and {a|b|c} inline
                               groups in a prompt string, returning the final text.

  ArctenoxWildcardPicker     — picks a single random entry from a named wildcard
                               file and outputs it as a STRING.

  ArctenoxWildcardStack      — stacks up to 4 wildcard-aware prompt segments,
                               resolves all tokens, and joins them with a separator.

Author: Arctenox
Version: 1.0.1
License: GPL-3.0
"""

import os
import re
import random
from pathlib import Path
from typing import Optional

try:
    import folder_paths
    _BASE_PATH = Path(folder_paths.base_path)
except Exception:
    _BASE_PATH = Path(__file__).parent.parent.parent   # fallback: comfyui root

_THIS_DIR = Path(__file__).parent

_WILDCARD_DIRS = [
    _THIS_DIR / "wildcards",
    _BASE_PATH / "wildcards",
]


# ─────────────────────────────────────────────────────────────────────────────
#  Wildcard resolution helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_wildcard(stem: str) -> list:
    """
    Search all wildcard directories for <stem>.txt and return its non-empty,
    non-comment lines.  Returns an empty list if not found.
    """
    for base in _WILDCARD_DIRS:
        candidate = (base / stem).with_suffix(".txt")
        if candidate.is_file():
            try:
                lines = candidate.read_text(encoding="utf-8").splitlines()
                return [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
            except Exception as exc:
                print(f"[Arctenox WildcardNodes] Could not read {candidate}: {exc}")
    return []


def _resolve_inline(text: str, seed: Optional[int] = None) -> str:
    """
    Replace every  {option1|option2|...}  group with a randomly chosen option.
    Supports nested groups (inner resolved first).
    """
    rng = random.Random(seed) if seed is not None else random.Random()

    # Iteratively resolve innermost {} groups (no nested {})
    pattern = re.compile(r"\{([^{}]+)\}")
    for _ in range(64):   # safety limit for deep nesting
        match = pattern.search(text)
        if not match:
            break
        options = [o.strip() for o in match.group(1).split("|")]
        choice  = rng.choice(options) if options else ""
        text    = text[:match.start()] + choice + text[match.end():]
    return text


def _resolve_wildcards(text: str, seed: Optional[int] = None) -> str:
    """
    Replace every  __stem__  token with a random line from that wildcard file.
    Falls back to the original token if the file is missing.
    """
    rng = random.Random(seed) if seed is not None else random.Random()

    def replacer(m: re.Match) -> str:
        stem    = m.group(1)
        options = _load_wildcard(stem)
        if not options:
            print(f"[Arctenox WildcardNodes] No options found for wildcard: {stem}")
            return m.group(0)   # keep token unchanged
        return rng.choice(options)

    return re.sub(r"__([a-zA-Z0-9_/.-]+)__", replacer, text)


def resolve_prompt(text: str, seed: Optional[int] = None) -> str:
    """Full resolution pass: wildcards first, then inline groups."""
    text = _resolve_wildcards(text, seed)
    text = _resolve_inline(text, seed)
    return text


# ─────────────────────────────────────────────────────────────────────────────
#  Helper: discover wildcard stems (for dropdown population)
#  FIX: moved above the node classes so it is defined before first use.
# ─────────────────────────────────────────────────────────────────────────────

def _discover_wildcard_stems() -> list:
    stems = set()
    for base_dir in _WILDCARD_DIRS:
        if not base_dir.is_dir():
            continue
        for txt_file in base_dir.rglob("*.txt"):
            rel  = txt_file.relative_to(base_dir).with_suffix("")
            stems.add(rel.as_posix())
    return list(stems)


# ─────────────────────────────────────────────────────────────────────────────
#  Node: Wildcard Processor
# ─────────────────────────────────────────────────────────────────────────────

class ArctenoxWildcardProcessor:
    """
    Resolves __wildcard__ tokens and {a|b|c} inline groups in a prompt string.

    Inputs:
        prompt  (STRING, multiline) — the raw prompt text
        seed    (INT)               — random seed for reproducibility (-1 = random each run)

    Outputs:
        resolved_prompt  (STRING) — the resolved text
        original_prompt  (STRING) — the input text, unchanged (pass-through for wiring)
        seed_used        (INT)    — the actual seed that was used
    """

    CATEGORY    = "Arctenox Essentials/Wildcards"
    FUNCTION    = "process"
    RETURN_TYPES  = ("STRING", "STRING", "INT")
    RETURN_NAMES  = ("resolved_prompt", "original_prompt", "seed_used")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default":   "",
                    "tooltip":   "Prompt with __wildcards__ and {inline|options}",
                }),
                "seed": ("INT", {
                    "default":  -1,
                    "min":      -1,
                    "max":      0x7FFF_FFFF,
                    "step":     1,
                    "tooltip":  "-1 = random each execution",
                }),
            },
        }

    def process(self, prompt: str, seed: int):
        actual_seed = seed if seed >= 0 else random.randint(0, 0x7FFF_FFFF)
        resolved    = resolve_prompt(prompt, actual_seed)
        return (resolved, prompt, actual_seed)


# ─────────────────────────────────────────────────────────────────────────────
#  Node: Wildcard Picker
# ─────────────────────────────────────────────────────────────────────────────

class ArctenoxWildcardPicker:
    """
    Picks a single random entry from a named wildcard file.

    Inputs:
        wildcard_name  (STRING) — stem of the wildcard file (e.g. "hair_color")
        seed           (INT)    — random seed (-1 = random each run)

    Outputs:
        picked_value  (STRING) — the randomly chosen option
        seed_used     (INT)
    """

    CATEGORY    = "Arctenox Essentials/Wildcards"
    FUNCTION    = "pick"
    RETURN_TYPES  = ("STRING", "INT")
    RETURN_NAMES  = ("picked_value", "seed_used")

    @classmethod
    def INPUT_TYPES(cls):
        # Dynamically list available wildcard stems for the dropdown
        stems = _discover_wildcard_stems()
        stem_list = sorted(stems) if stems else ["(no wildcards found)"]

        return {
            "required": {
                "wildcard_name": (stem_list, {
                    "tooltip": "Select a wildcard file to pick from",
                }),
                "seed": ("INT", {
                    "default":  -1,
                    "min":      -1,
                    "max":      0x7FFF_FFFF,
                    "step":     1,
                    "tooltip":  "-1 = random each execution",
                }),
            },
        }

    def pick(self, wildcard_name: str, seed: int):
        actual_seed = seed if seed >= 0 else random.randint(0, 0x7FFF_FFFF)
        # FIX: guard against the placeholder value when no wildcard files exist
        if not wildcard_name or wildcard_name == "(no wildcards found)":
            print("[Arctenox WildcardPicker] No wildcard files available.")
            return ("", actual_seed)
        options = _load_wildcard(wildcard_name)
        if not options:
            print(f"[Arctenox WildcardPicker] No options for: {wildcard_name}")
            return ("", actual_seed)
        rng   = random.Random(actual_seed)
        value = rng.choice(options)
        return (value, actual_seed)


# ─────────────────────────────────────────────────────────────────────────────
#  Node: Wildcard Stack
# ─────────────────────────────────────────────────────────────────────────────

class ArctenoxWildcardStack:
    """
    Stacks up to 4 wildcard-aware prompt segments, resolves all tokens in each,
    then joins the non-empty results with a configurable separator.

    Inputs:
        prompt_1..4  (STRING, multiline) — prompt segments (empty segments skipped)
        seed         (INT)               — shared seed for all segments
        separator    (STRING)            — text to place between segments (default ", ")

    Outputs:
        resolved_prompt  (STRING)
        seed_used        (INT)
    """

    CATEGORY    = "Arctenox Essentials/Wildcards"
    FUNCTION    = "stack"
    RETURN_TYPES  = ("STRING", "INT")
    RETURN_NAMES  = ("resolved_prompt", "seed_used")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt_1":  ("STRING", {"multiline": True, "default": "", "tooltip": "First prompt segment"}),
                "seed":      ("INT",    {"default": -1, "min": -1, "max": 0x7FFF_FFFF, "step": 1}),
                "separator": ("STRING", {"default": ", ", "tooltip": "Separator between segments"}),
            },
            "optional": {
                "prompt_2": ("STRING", {"multiline": True, "default": ""}),
                "prompt_3": ("STRING", {"multiline": True, "default": ""}),
                "prompt_4": ("STRING", {"multiline": True, "default": ""}),
            },
        }

    def stack(
        self,
        prompt_1:  str,
        seed:      int,
        separator: str,
        prompt_2:  str = "",
        prompt_3:  str = "",
        prompt_4:  str = "",
    ):
        actual_seed = seed if seed >= 0 else random.randint(0, 0x7FFF_FFFF)
        segments    = [prompt_1, prompt_2, prompt_3, prompt_4]
        resolved    = [resolve_prompt(s, actual_seed) for s in segments if s and s.strip()]
        joined      = separator.join(resolved)
        return (joined, actual_seed)


# ─────────────────────────────────────────────────────────────────────────────
#  Exports
# ─────────────────────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "ArctenoxWildcardProcessor": ArctenoxWildcardProcessor,
    "ArctenoxWildcardPicker":    ArctenoxWildcardPicker,
    "ArctenoxWildcardStack":     ArctenoxWildcardStack,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArctenoxWildcardProcessor": "Wildcard Processor (Arctenox's Essentials)",
    "ArctenoxWildcardPicker":    "Wildcard Picker (Arctenox's Essentials)",
    "ArctenoxWildcardStack":     "Wildcard Stack (Arctenox's Essentials)",
}
