"""
Arctenox Essentials - CLIP Text Encode nodes
=============================================

CLIPTextEncodeWithString  (Positive + Wildcards)
    Positive-only CLIP encode with wildcard support.
    Outputs conditioning, the original text, and the resolved text.

CLIPTextEncodeWithPromptGen  (Prompt Gen)
    Same as above but accepts an optional prompt_gen_output STRING
    (from ArctenoxPromptGenerator) and appends it to the positive
    prompt before wildcard resolution and encoding.

Wildcard syntax supported in all text inputs:
    {a|b|c}      – pick one option at random
    __filename__ – pick a random line from wildcards/filename.txt

Author: Arctenox
Version: 1.3.0
License: GPL-3.0
"""

import os
import re
import random
import folder_paths


# ─────────────────────────────────────────────────────────────────────────────
#  Wildcard resolver  (shared by both nodes)
# ─────────────────────────────────────────────────────────────────────────────

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_WILDCARD_DIRS = [
    os.path.join(_THIS_DIR, "wildcards"),
    os.path.join(folder_paths.base_path, "wildcards"),
]


def _load_wildcard_file(name: str) -> list:
    """Load options from a .txt wildcard file. Returns [] if not found."""
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
    """Recursively resolve __file__ and {a|b|c} wildcard tokens."""
    max_passes = 20

    file_wc_re = re.compile(r"__([a-zA-Z0-9][a-zA-Z0-9_/.-]*?)__")
    inline_re  = re.compile(r"\{([^{}]+)\}")

    for _ in range(max_passes):
        changed = False

        def _replace_file(m):
            options = _load_wildcard_file(m.group(1).strip())
            if options:
                return rng.choice(options)
            print(f"[Arctenox Wildcards] Wildcard file not found: {m.group(1)}")
            return m.group(0)

        new_text, n = file_wc_re.subn(_replace_file, text)
        if n:
            text    = new_text
            changed = True

        def _replace_inline(m):
            options = [o.strip() for o in m.group(1).split("|")]
            options = [o for o in options if o]
            return rng.choice(options) if options else ""

        new_text, n = inline_re.subn(_replace_inline, text)
        if n:
            text    = new_text
            changed = True

        if not changed:
            break

    return text


# ─────────────────────────────────────────────────────────────────────────────
#  Shared encoding helper
# ─────────────────────────────────────────────────────────────────────────────

def _encode(clip, text: str):
    """Tokenise and encode a single text string. Returns a conditioning list."""
    tokens = clip.tokenize(text)
    cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
    return [[cond, {"pooled_output": pooled}]]


def _resolve_and_log(label: str, text: str, rng: random.Random) -> str:
    resolved = _resolve_wildcards(text, rng)
    if resolved != text:
        print(f"[Arctenox CLIP Encode] Wildcards resolved ({label}):")
        print(f"  Original : {text[:120]}{'...' if len(text) > 120 else ''}")
        print(f"  Resolved : {resolved[:120]}{'...' if len(resolved) > 120 else ''}")
    return resolved


# ─────────────────────────────────────────────────────────────────────────────
#  Node 1 — CLIPTextEncodeWithString
#           Positive prompt with wildcard support
# ─────────────────────────────────────────────────────────────────────────────

class CLIPTextEncodeWithString:
    """
    Positive-only CLIP encode with wildcard support.
    Outputs conditioning, the original text string, and the resolved text string.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default":   "",
                    "tooltip":   (
                        "Positive prompt. Supports wildcards:\n"
                        "  {a|b|c}      → picks one option\n"
                        "  __filename__ → picks a random line from wildcards/filename.txt"
                    ),
                }),
                "clip": ("CLIP",),
                "wildcard_seed": ("INT", {
                    "default": 0,
                    "min":     -1,
                    "max":     0xffffffffffffffff,
                    "tooltip": (
                        "Seed for wildcard resolution.\n"
                        "-1 = new random picks every run\n"
                        " 0+ = locked / reproducible"
                    ),
                }),
            },
        }

    RETURN_TYPES  = ("CONDITIONING", "STRING", "STRING")
    RETURN_NAMES  = ("conditioning", "text", "resolved_text")
    FUNCTION  = "encode"
    CATEGORY  = "Arctenox Essentials/Conditioning"

    DESCRIPTION = "CLIP Text Encode (positive only) with wildcard support and string pass-throughs."

    @classmethod
    def IS_CHANGED(cls, text, clip, wildcard_seed=0):
        if wildcard_seed == -1:
            return float("NaN")
        return wildcard_seed

    def encode(self, text: str, clip, wildcard_seed: int = 0):
        rng = random.Random() if wildcard_seed == -1 else random.Random(wildcard_seed)
        resolved = _resolve_and_log("positive", text, rng)
        conditioning = _encode(clip, resolved)
        return (conditioning, text, resolved)


# ─────────────────────────────────────────────────────────────────────────────
#  Node 2 — CLIPTextEncodeWithPromptGen
#           Appends PromptGenerator output to the positive prompt
# ─────────────────────────────────────────────────────────────────────────────

class CLIPTextEncodeWithPromptGen:
    """
    Positive CLIP encode that accepts an optional prompt_gen_output STRING
    (from ArctenoxPromptGenerator) and appends it to the prompt text before
    wildcard resolution and encoding.

    Typical wiring:
        PromptGenerator.prompt  →  prompt_gen_output
        Your hand-written text  →  text  (optional prefix)
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default":   "",
                    "tooltip":   (
                        "Hand-written positive prompt prefix. "
                        "The PromptGenerator output will be appended after this. "
                        "Wildcards supported."
                    ),
                }),
                "clip": ("CLIP",),
                "wildcard_seed": ("INT", {
                    "default": 0,
                    "min":     -1,
                    "max":     0xffffffffffffffff,
                    "tooltip": (
                        "Seed for wildcard resolution.\n"
                        "-1 = new random picks every run\n"
                        " 0+ = locked / reproducible"
                    ),
                }),
            },
            "optional": {
                "prompt_gen_output": ("STRING", {
                    "multiline": False,
                    "default":   "",
                    "tooltip":   (
                        "Connect the 'prompt' output of ArctenoxPromptGenerator here. "
                        "It will be appended to text with ', ' as a separator."
                    ),
                }),
            },
        }

    RETURN_TYPES  = ("CONDITIONING", "STRING", "STRING")
    RETURN_NAMES  = ("conditioning", "text", "resolved_text")
    FUNCTION  = "encode"
    CATEGORY  = "Arctenox Essentials/Conditioning"

    DESCRIPTION = (
        "CLIP Text Encode that hooks directly into ArctenoxPromptGenerator. "
        "Appends the generator's output to your prompt text before encoding."
    )

    @classmethod
    def IS_CHANGED(cls, text, clip, wildcard_seed=0, prompt_gen_output=""):
        if wildcard_seed == -1:
            return float("NaN")
        return hash((wildcard_seed, text, prompt_gen_output))

    def encode(
        self,
        text:              str,
        clip,
        wildcard_seed:     int = 0,
        prompt_gen_output: str = "",
    ):
        rng = random.Random() if wildcard_seed == -1 else random.Random(wildcard_seed)

        # Build a set of tags already present in the hand-written text so we can
        # strip duplicates from the generator output before appending.
        # Normalise to lowercase + underscores for comparison only.
        def _normalise(tag: str) -> str:
            return tag.strip().lower().replace(" ", "_")

        existing = {_normalise(t) for t in text.replace("\n", ",").split(",") if t.strip()}

        # Filter generator tags that are already covered by the hand-written text
        if prompt_gen_output.strip():
            filtered_gen_tags = [
                t.strip() for t in prompt_gen_output.split(",")
                if t.strip() and _normalise(t) not in existing
            ]
            filtered_gen = ", ".join(filtered_gen_tags)
        else:
            filtered_gen = ""

        parts    = [p.strip() for p in [text, filtered_gen] if p.strip()]
        combined = ", ".join(parts)

        resolved     = _resolve_and_log("positive", combined, rng)
        conditioning = _encode(clip, resolved)

        return (conditioning, text, resolved)


# ─────────────────────────────────────────────────────────────────────────────
#  Node 3 — WildcardString
#           Multiline string primitive with wildcard resolution
# ─────────────────────────────────────────────────────────────────────────────

class WildcardString:
    """
    A multiline string node that resolves wildcards before outputting.
    Use anywhere you need a plain STRING with {a|b|c} or __file__ support.
    Outputs both the original text and the resolved text.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default":   "",
                    "tooltip":   (
                        "Any text. Wildcards are resolved on output:\n"
                        "  {a|b|c}      → picks one option at random\n"
                        "  __filename__ → picks a random line from wildcards/filename.txt"
                    ),
                }),
                "wildcard_seed": ("INT", {
                    "default": 0,
                    "min":     -1,
                    "max":     0xffffffffffffffff,
                    "tooltip": (
                        "Seed for wildcard resolution.\n"
                        "-1 = new random picks every run\n"
                        " 0+ = locked / reproducible"
                    ),
                }),
            },
        }

    RETURN_TYPES  = ("STRING", "STRING")
    RETURN_NAMES  = ("text",   "resolved_text")
    FUNCTION      = "resolve"
    CATEGORY      = "Arctenox Essentials/Prompting"

    DESCRIPTION = (
        "Multiline string primitive with wildcard support. "
        "Resolves {a|b|c} and __filename__ wildcards before passing the string downstream. "
        "Outputs both the original and resolved text."
    )

    @classmethod
    def IS_CHANGED(cls, text, wildcard_seed=0):
        if wildcard_seed == -1:
            return float("NaN")
        return hash((wildcard_seed, text))

    def resolve(self, text: str, wildcard_seed: int = 0):
        rng = random.Random() if wildcard_seed == -1 else random.Random(wildcard_seed)
        resolved = _resolve_and_log("wildcard_string", text, rng)
        return (text, resolved)


# ─────────────────────────────────────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "CLIPTextEncodeWithString":    CLIPTextEncodeWithString,
    "CLIPTextEncodeWithPromptGen": CLIPTextEncodeWithPromptGen,
    "ArctenoxWildcardString":      WildcardString,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CLIPTextEncodeWithString":    "CLIP Text Encode [Prompt] (Arctenox's Essentials)",
    "CLIPTextEncodeWithPromptGen": "CLIP Text Encode [Prompt + Gen] (Arctenox's Essentials)",
    "ArctenoxWildcardString":      "Wildcard String (Arctenox's Essentials)",
}
