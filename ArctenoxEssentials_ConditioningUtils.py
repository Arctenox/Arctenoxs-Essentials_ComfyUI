"""
Arctenox Essentials - Conditioning Utilities
=============================================

Lightweight conditioning manipulation nodes.

Nodes:
- ConditioningStrengthScaler: Multiply conditioning influence by a float weight

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""

import torch


# ─────────────────────────────────────────────────────────────────────────────
#  ConditioningStrengthScaler
# ─────────────────────────────────────────────────────────────────────────────

class ConditioningStrengthScaler:
    """
    Scale the influence of a CONDITIONING tensor by multiplying it
    by a strength float before passing it to a sampler.

    Useful for:
    - Reducing negative prompt influence without editing the prompt
    - Boosting or dampening a phase prompt from PromptPhaseSplitter
    - A/B testing prompt weight globally without touching individual tokens

    A strength of 1.0 is a perfect pass-through.
    Values > 1.0 amplify; values < 1.0 dampen; 0.0 zeroes out the conditioning.
    Negative values invert the guidance direction (use with care).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "conditioning": ("CONDITIONING",),
                "strength": ("FLOAT", {
                    "default": 1.0,
                    "min": -4.0,
                    "max": 4.0,
                    "step": 0.05,
                    "tooltip": (
                        "Multiplier applied to the conditioning tensor.\n"
                        "1.0 = no change (pass-through)\n"
                        "0.5 = half strength\n"
                        "2.0 = double strength\n"
                        "0.0 = zero out (no guidance)\n"
                        "Negative values invert guidance direction"
                    )
                }),
            }
        }

    RETURN_TYPES  = ("CONDITIONING",)
    RETURN_NAMES  = ("conditioning",)
    FUNCTION      = "scale"
    CATEGORY      = "Arctenox Essentials/Conditioning"

    DESCRIPTION = """
    Multiply a CONDITIONING tensor by a scalar strength value.

    Practical uses:
    • Scale down negative prompt influence (e.g. 0.8) to soften it
      without rewriting prompts
    • Boost detail-phase conditioning from Prompt Phase Splitter
    • Global conditioning weight adjustment before samplers
    • Test how much a particular conditioning contributes to the result

    1.0 = exact pass-through, no computational cost in effect.
    """

    def scale(self, conditioning, strength: float):
        if strength == 1.0:
            # Perfect pass-through - no copy needed
            return (conditioning,)

        result = []
        for tensor, metadata in conditioning:
            scaled_tensor = tensor * strength
            result.append([scaled_tensor, metadata.copy()])

        return (result,)


# ─────────────────────────────────────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "ArctenoxConditioningStrengthScaler": ConditioningStrengthScaler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArctenoxConditioningStrengthScaler": "Conditioning Strength Scaler (Arctenox's Essentials)",
}

__all__ = ["ConditioningStrengthScaler"]
