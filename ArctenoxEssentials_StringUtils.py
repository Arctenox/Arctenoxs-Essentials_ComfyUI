"""
Arctenox Essentials - String Utilities
========================================

Lightweight string manipulation nodes for wiring text data through
workflows — especially useful when chaining the many STRING outputs
produced by other Arctenox nodes.

Nodes:
- StringConcatenate:  Join 2–4 strings with a configurable separator
- StringSwitch:       Toggle between two STRING inputs with a boolean

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""


# ─────────────────────────────────────────────────────────────────────────────
#  StringConcatenate
# ─────────────────────────────────────────────────────────────────────────────

class StringConcatenate:
    """
    Join up to four strings together with a configurable separator.

    Empty / unconnected inputs are silently skipped, so you can use
    this node with just two strings and leave the rest blank.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "separator": ("STRING", {
                    "default": ", ",
                    "multiline": False,
                    "tooltip": (
                        "String placed between each non-empty input.\n"
                        "Use '\\n' for newlines (type the two chars literally)."
                    )
                }),
            },
            "optional": {
                "string_a": ("STRING", {"forceInput": True}),
                "string_b": ("STRING", {"forceInput": True}),
                "string_c": ("STRING", {"forceInput": True}),
                "string_d": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES  = ("STRING",)
    RETURN_NAMES  = ("result",)
    FUNCTION      = "concatenate"
    CATEGORY      = "Arctenox Essentials/Text"

    DESCRIPTION = """
    Join up to four strings with a separator.

    Examples:
    • separator=", "  → "positive prompt, <lora:name:1.0>"
    • separator="\\n" → multi-line output
    • separator=""    → direct concatenation with no gap

    Empty/unconnected inputs are ignored — no trailing separators.
    """

    def concatenate(self, separator: str,
                    string_a: str = "", string_b: str = "",
                    string_c: str = "", string_d: str = ""):

        # Interpret literal \n in separator
        sep = separator.replace("\\n", "\n").replace("\\t", "\t")

        parts = [s for s in (string_a, string_b, string_c, string_d)
                 if s and s.strip()]

        result = sep.join(parts)
        return (result,)


# ─────────────────────────────────────────────────────────────────────────────
#  StringSwitch
# ─────────────────────────────────────────────────────────────────────────────

class StringSwitch:
    """
    Route one of two STRING inputs to the output based on a boolean toggle.

    Handy for quickly swapping between a positive and a fallback prompt,
    two LoRA lists, two model names, etc., without rewiring nodes.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "use_string_a": ("BOOLEAN", {
                    "default": True,
                    "label_on":  "String A",
                    "label_off": "String B",
                    "tooltip": "When ON, outputs string_a. When OFF, outputs string_b."
                }),
                "string_a": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Output when toggle is ON (String A)"
                }),
                "string_b": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Output when toggle is OFF (String B)"
                }),
            }
        }

    RETURN_TYPES  = ("STRING", "STRING")
    RETURN_NAMES  = ("selected", "discarded")
    FUNCTION      = "switch"
    CATEGORY      = "Arctenox Essentials/Text"

    DESCRIPTION = """
    Toggle between two STRING values.

    Outputs:
    • selected   – the active string (A or B depending on toggle)
    • discarded  – the inactive string (useful for logging/debugging)

    Use Cases:
    • Swap between two prompt variants without rewiring
    • Toggle a LoRA list on/off by switching between the list and ""
    • A/B compare different model names fed into Save Image With Metadata
    """

    def switch(self, use_string_a: bool, string_a: str, string_b: str):
        if use_string_a:
            return (string_a, string_b)
        else:
            return (string_b, string_a)


# ─────────────────────────────────────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "ArctenoxStringConcatenate": StringConcatenate,
    "ArctenoxStringSwitch":      StringSwitch,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArctenoxStringConcatenate": "String Concatenate (Arctenox's Essentials)",
    "ArctenoxStringSwitch":      "String Switch (Arctenox's Essentials)",
}

__all__ = ["StringConcatenate", "StringSwitch"]
