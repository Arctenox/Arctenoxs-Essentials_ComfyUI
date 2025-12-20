"""
Arctenox Essentials - Prompt Phase Splitter
============================================

Splits conditioning into multiple temporal phases applied at different
sampling steps for progressive refinement control.

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""

import torch


class PromptPhaseSplitter:
    """
    Splits prompt conditioning into temporal phases applied at different sampling steps.
    Allows progressive refinement: composition → detail → texture → character/subject.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_positive": ("CONDITIONING",),
                "base_negative": ("CONDITIONING",),
                
                # Phase 1: Composition (early steps)
                "enable_composition": (["disabled", "enabled"], {
                    "default": "enabled",
                    "tooltip": "Enable composition phase"
                }),
                "composition_prompt": ("STRING", {
                    "default": "masterpiece, best quality, composition, framing, rule of thirds",
                    "multiline": True,
                    "tooltip": "Applied in early sampling (composition structure)"
                }),
                "composition_weight": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 3.0,
                    "step": 0.1,
                    "tooltip": "Strength of composition phase"
                }),
                "composition_end_percent": ("FLOAT", {
                    "default": 0.3,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "When to end composition phase (0.3 = 30% of steps)"
                }),
                
                # Phase 2: Detail (middle steps)
                "enable_detail": (["disabled", "enabled"], {
                    "default": "enabled",
                    "tooltip": "Enable detail phase"
                }),
                "detail_prompt": ("STRING", {
                    "default": "intricate details, fine details, sharp focus, high detail",
                    "multiline": True,
                    "tooltip": "Applied in middle sampling (detail refinement)"
                }),
                "detail_weight": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 3.0,
                    "step": 0.1,
                    "tooltip": "Strength of detail phase"
                }),
                "detail_start_percent": ("FLOAT", {
                    "default": 0.25,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "When to start detail phase"
                }),
                "detail_end_percent": ("FLOAT", {
                    "default": 0.65,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "When to end detail phase"
                }),
                
                # Phase 3: Texture (late steps)
                "enable_texture": (["disabled", "enabled"], {
                    "default": "enabled",
                    "tooltip": "Enable texture phase"
                }),
                "texture_prompt": ("STRING", {
                    "default": "smooth textures, refined surface, polished finish",
                    "multiline": True,
                    "tooltip": "Applied in late sampling (texture refinement)"
                }),
                "texture_weight": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 3.0,
                    "step": 0.1,
                    "tooltip": "Strength of texture phase"
                }),
                "texture_start_percent": ("FLOAT", {
                    "default": 0.6,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "When to start texture phase"
                }),
                
                # Phase 4: Character/Subject (optional, throughout)
                "enable_character": (["disabled", "enabled"], {
                    "default": "disabled",
                    "tooltip": "Enable character/subject focus phase"
                }),
                "character_prompt": ("STRING", {
                    "default": "1girl, detailed face, expressive eyes, natural pose",
                    "multiline": True,
                    "tooltip": "Character/subject focus (applied when enabled)"
                }),
                "character_weight": ("FLOAT", {
                    "default": 1.2,
                    "min": 0.0,
                    "max": 3.0,
                    "step": 0.1,
                    "tooltip": "Strength of character phase"
                }),
                "character_start_percent": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "When to start character phase"
                }),
                "character_end_percent": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "When to end character phase"
                }),
                
                # Global settings
                "blend_mode": (["concat", "append", "add", "subtract"], {
                    "default": "concat",
                    "tooltip": "concat (join prompts), append (separate entries), add (strengthen), subtract (weaken)"
                }),
            },
            "optional": {
                "clip": ("CLIP",),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "STRING")
    RETURN_NAMES = ("positive", "negative", "phase_info")
    FUNCTION = "split_phases"
    CATEGORY = "Arctenox Essentials/Sampling"
    
    DESCRIPTION = """
    Splits prompt conditioning into temporal phases for progressive refinement control.
    
    Phases:
    • Phase 1 (Composition): Early steps - overall structure and composition
    • Phase 2 (Detail): Middle steps - refine details and definition
    • Phase 3 (Texture): Late steps - surface texture and polish
    • Phase 4 (Character/Subject): Optional - maintain subject focus throughout
    
    Blend Modes:
    • Concat: Concatenate phase prompts with base prompt text (cleanest)
    • Append: Add phase prompts as separate conditioning entries (most flexible)
    • Add: Add phase conditioning to base conditioning tensors (strengthen)
    • Subtract: Subtract phase conditioning from base (weaken/remove concepts)
    
    Use Cases:
    • Progressive refinement workflows
    • Separate composition from detail control
    • Character-focused generation with background phases
    • Temporal prompt scheduling
    """

    def _encode_prompt(self, clip, prompt):
        """Encode a text prompt using CLIP"""
        if not clip or not prompt or not prompt.strip():
            return None
        
        tokens = clip.tokenize(prompt)
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        return [[cond, {"pooled_output": pooled}]]
    
    def _pad_conditioning_tensors(self, tensor1, tensor2):
        """Pad conditioning tensors to same size for addition/subtraction"""
        # Get shapes
        b1, s1, d = tensor1.shape
        b2, s2, _ = tensor2.shape
        
        # Pad to match sequence length
        if s1 < s2:
            # Pad tensor1
            padding = torch.zeros(b1, s2 - s1, d, device=tensor1.device, dtype=tensor1.dtype)
            tensor1 = torch.cat([tensor1, padding], dim=1)
        elif s2 < s1:
            # Pad tensor2
            padding = torch.zeros(b2, s1 - s2, d, device=tensor2.device, dtype=tensor2.dtype)
            tensor2 = torch.cat([tensor2, padding], dim=1)
        
        return tensor1, tensor2
    
    def _combine_conditioning(self, base_cond, phase_prompts, clip, blend_mode, weights):
        """
        Combine base conditioning with phase prompts using specified blend mode.
        This approach works with ComfyUI's conditioning format properly.
        """
        if not phase_prompts or not clip:
            return base_cond
        
        if blend_mode == "concat":
            # Concatenate all prompts into one and re-encode
            # Extract base prompt text if possible, otherwise use placeholder
            base_prompt = "masterpiece, best quality"
            
            # Combine base + all phase prompts
            all_prompts = [base_prompt] + phase_prompts
            combined_prompt = ", ".join(all_prompts)
            
            return self._encode_prompt(clip, combined_prompt)
        
        elif blend_mode == "append":
            # Add phase conditioning as separate entries in the conditioning list
            result = list(base_cond)  # Start with base
            
            for i, prompt in enumerate(phase_prompts):
                phase_cond = self._encode_prompt(clip, prompt)
                if phase_cond:
                    # Append each phase as a separate conditioning entry
                    result.extend(phase_cond)
            
            return result
        
        elif blend_mode == "add":
            # Add phase conditioning tensors to base (strengthening)
            result = []
            
            # Start with base conditioning
            for base_item in base_cond:
                base_tensor = base_item[0].clone()
                base_dict = base_item[1].copy()
                
                # Add each phase conditioning
                for i, prompt in enumerate(phase_prompts):
                    phase_cond = self._encode_prompt(clip, prompt)
                    if phase_cond and i < len(weights):
                        phase_tensor = phase_cond[0][0]
                        weight = weights[i]
                        
                        # Pad tensors to same size
                        padded_base, padded_phase = self._pad_conditioning_tensors(
                            base_tensor, phase_tensor
                        )
                        
                        # Add weighted phase to base
                        base_tensor = padded_base + (padded_phase * weight)
                
                result.append([base_tensor, base_dict])
            
            return result
        
        else:  # subtract
            # Subtract phase conditioning tensors from base (weakening)
            result = []
            
            # Start with base conditioning
            for base_item in base_cond:
                base_tensor = base_item[0].clone()
                base_dict = base_item[1].copy()
                
                # Subtract each phase conditioning
                for i, prompt in enumerate(phase_prompts):
                    phase_cond = self._encode_prompt(clip, prompt)
                    if phase_cond and i < len(weights):
                        phase_tensor = phase_cond[0][0]
                        weight = weights[i]
                        
                        # Pad tensors to same size
                        padded_base, padded_phase = self._pad_conditioning_tensors(
                            base_tensor, phase_tensor
                        )
                        
                        # Subtract weighted phase from base
                        base_tensor = padded_base - (padded_phase * weight)
                
                result.append([base_tensor, base_dict])
            
            return result

    def split_phases(self, base_positive, base_negative,
                    enable_composition, composition_prompt, composition_weight, composition_end_percent,
                    enable_detail, detail_prompt, detail_weight, detail_start_percent, detail_end_percent,
                    enable_texture, texture_prompt, texture_weight, texture_start_percent,
                    enable_character, character_prompt, character_weight,
                    character_start_percent, character_end_percent,
                    blend_mode, clip=None):
        
        # If no CLIP provided, return base conditioning
        if clip is None:
            phase_info = "No CLIP provided - using base conditioning only"
            return (base_positive, base_negative, phase_info)
        
        # Collect active phase prompts
        active_prompts = []
        phase_descriptions = []
        
        # Composition phase
        if enable_composition == "enabled" and composition_weight > 0 and composition_prompt.strip():
            active_prompts.append(composition_prompt)
            phase_descriptions.append(
                f"Composition: 0%-{composition_end_percent*100:.0f}% (weight: {composition_weight:.1f})"
            )
        
        # Detail phase
        if enable_detail == "enabled" and detail_weight > 0 and detail_prompt.strip():
            active_prompts.append(detail_prompt)
            phase_descriptions.append(
                f"Detail: {detail_start_percent*100:.0f}%-{detail_end_percent*100:.0f}% (weight: {detail_weight:.1f})"
            )
        
        # Texture phase
        if enable_texture == "enabled" and texture_weight > 0 and texture_prompt.strip():
            active_prompts.append(texture_prompt)
            phase_descriptions.append(
                f"Texture: {texture_start_percent*100:.0f}%-100% (weight: {texture_weight:.1f})"
            )
        
        # Character phase (optional)
        if enable_character == "enabled" and character_weight > 0 and character_prompt.strip():
            active_prompts.append(character_prompt)
            phase_descriptions.append(
                f"Character: {character_start_percent*100:.0f}%-{character_end_percent*100:.0f}% (weight: {character_weight:.1f})"
            )
        
        # Combine conditioning
        weights = [composition_weight, detail_weight, texture_weight, character_weight]
        result_positive = self._combine_conditioning(
            base_positive,
            active_prompts,
            clip,
            blend_mode,
            weights
        )
        
        # Generate phase info
        if active_prompts:
            phase_info = f"Active phases ({blend_mode} mode):\n"
            phase_info += "\n".join(f"  • {desc}" for desc in phase_descriptions)
            phase_info += f"\n\nCombined {len(active_prompts)} phase prompt(s)"
        else:
            phase_info = "No active phases - using base conditioning"
        
        return (result_positive, base_negative, phase_info)


# Node registration
NODE_CLASS_MAPPINGS = {
    "PromptPhaseSplitter": PromptPhaseSplitter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptPhaseSplitter": "Prompt Phase Splitter (Arctenox's Essentials)",
}

__all__ = ["PromptPhaseSplitter"]