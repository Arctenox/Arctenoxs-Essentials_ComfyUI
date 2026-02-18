"""
Arctenox Essentials - KSampler Refiner
========================================

A dedicated hi-res fix / refiner pass node designed to pair with the
existing KSampler (Arctenox's Essentials).

Workflow:
  [KSampler] --> LATENT --> [KSampler Refiner] --> refined LATENT / IMAGE

Features:
- Accepts LATENT from any KSampler for a second-pass refine
- Optional upscale before refining (nearest, bilinear, bicubic, lanczos)
- Upscale by factor OR target width/height (whichever is used)
- denoise controls how much the refiner changes the latent
  (0.4-0.6 = hi-res fix sweet spot; lower = subtle, higher = rework)
- Inherits golden ratio sonar transformation from the main KSampler
- Optional VAE decode output so the node is self-contained
- Outputs MODEL, CONDITIONING+/- pass-through for easy chaining

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""

import math
import torch
import torch.nn.functional as F
import comfy.samplers
import comfy.sample
import comfy.model_management


# ─────────────────────────────────────────────────────────────────────────────
#  Golden-ratio sonar (identical logic to the main KSampler)
# ─────────────────────────────────────────────────────────────────────────────

PHI_INVERSE = 0.618033988749895


def _sonar_transform(seed: int, sonar: int) -> int:
    """Apply the same golden-ratio sonar seed transformation as the main KSampler."""
    if sonar == 0:
        return seed

    max_seed = 0xFFFFFFFF
    offset_hash = (sonar * 0x9E3779B9) ^ (sonar << 13) ^ (sonar >> 7)
    base = ((seed ^ offset_hash) * 1103515245 + 12345) & 0xFFFFFFFF

    abs_sonar = abs(sonar)
    if abs_sonar > 10:
        golden_influence = (abs_sonar * PHI_INVERSE * 0.1) % 1.0
        adjustment = int(base * golden_influence * 0.05)
        result = (base + adjustment) & 0xFFFFFFFF
    else:
        result = base

    if sonar < 0:
        result = (max_seed - result) & 0xFFFFFFFF

    return result


# ─────────────────────────────────────────────────────────────────────────────
#  Latent upscaler
# ─────────────────────────────────────────────────────────────────────────────

_UPSCALE_MODES = ["None", "nearest", "bilinear", "bicubic", "bislerp"]


def _upscale_latent(latent_tensor: torch.Tensor, scale_factor: float,
                    target_width: int, target_height: int,
                    mode: str) -> torch.Tensor:
    """
    Upscale a latent tensor.
    - If target_width/height > 0, those take priority over scale_factor.
    - mode "bislerp" falls back to bilinear (true bislerp needs more scaffolding).
    """
    if mode == "None" or (scale_factor == 1.0 and target_width == 0 and target_height == 0):
        return latent_tensor

    _, _, h, w = latent_tensor.shape

    if target_width > 0 and target_height > 0:
        new_w = target_width  // 8
        new_h = target_height // 8
    else:
        new_w = max(1, int(w * scale_factor))
        new_h = max(1, int(h * scale_factor))

    interp_mode = "bilinear" if mode == "bislerp" else mode
    align = False if interp_mode == "nearest" else True

    upscaled = F.interpolate(
        latent_tensor.float(),
        size=(new_h, new_w),
        mode=interp_mode,
        align_corners=align if interp_mode not in ("nearest", "bilinear") else None
    )
    return upscaled.to(latent_tensor.dtype)


# ─────────────────────────────────────────────────────────────────────────────
#  Node
# ─────────────────────────────────────────────────────────────────────────────

class KSamplerRefiner:
    """
    KSampler Refiner (Arctenox's Essentials)

    Performs a second-pass refinement on an existing LATENT.
    Perfect for hi-res fix workflows: run the main KSampler at half
    resolution, upscale here, then refine at full resolution with a
    low denoise (0.4–0.6) to add detail without changing composition.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Pass-through inputs (from main KSampler outputs)
                "model":     ("MODEL",),
                "positive":  ("CONDITIONING",),
                "negative":  ("CONDITIONING",),
                "latent":    ("LATENT",),

                # Upscale settings
                "upscale_method": (_UPSCALE_MODES, {
                    "default": "bilinear",
                    "tooltip": "Latent upscale interpolation method. 'None' skips upscaling."
                }),
                "scale_factor": ("FLOAT", {
                    "default": 1.5,
                    "min": 0.25,
                    "max": 8.0,
                    "step": 0.05,
                    "tooltip": "Upscale multiplier. Ignored if target_width/height > 0."
                }),
                "target_width": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 8192,
                    "step": 8,
                    "tooltip": "Target pixel width after upscale. 0 = use scale_factor instead."
                }),
                "target_height": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 8192,
                    "step": 8,
                    "tooltip": "Target pixel height after upscale. 0 = use scale_factor instead."
                }),

                # Refiner sampler settings
                "seed": ("INT", {
                    "default": 0,
                    "min": -0x7fffffffffffffff,
                    "max": 0xffffffffffffffff,
                    "tooltip": "Seed for refiner pass. Use the same seed as the main KSampler for consistency."
                }),
                "sonar": ("INT", {
                    "default": 0,
                    "min": -18446744073709552000,
                    "max": 18446744073709552000,
                    "tooltip": "Golden-ratio sonar offset. Match to main KSampler for coherent variation."
                }),
                "steps": ("INT", {
                    "default": 20,
                    "min": 1,
                    "max": 10000,
                    "tooltip": "Refiner sampling steps."
                }),
                "cfg": ("FLOAT", {
                    "default": 4.0,
                    "min": 0.0,
                    "max": 100.0,
                    "step": 0.01,
                    "tooltip": "CFG scale for refiner pass."
                }),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler":    (comfy.samplers.KSampler.SCHEDULERS,),
                "denoise": ("FLOAT", {
                    "default": 0.45,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "tooltip": (
                        "How much the refiner changes the latent.\n"
                        "0.3–0.5 = subtle hi-res fix (adds detail, preserves composition)\n"
                        "0.5–0.7 = moderate rework\n"
                        "0.7–1.0 = heavy rework (similar to full generation)"
                    )
                }),

                # Output
                "vae_decode": (["true", "false"], {
                    "default": "true",
                    "tooltip": "Decode the refined latent to an IMAGE inside this node."
                }),
            },
            "optional": {
                "vae": ("VAE",),
            }
        }

    RETURN_TYPES  = ("MODEL", "CONDITIONING", "CONDITIONING", "LATENT", "VAE", "IMAGE")
    RETURN_NAMES  = ("model", "positive", "negative", "latent", "vae", "image")
    FUNCTION      = "refine"
    CATEGORY      = "Arctenox Essentials/Sampling"

    DESCRIPTION = """
    Second-pass refiner / hi-res fix node.

    Typical hi-res fix workflow:
      1. KSampler (Arctenox's Essentials) at 512x768, denoise=1.0
            --> LATENT
      2. KSampler Refiner, upscale_method=bilinear, scale_factor=1.5,
         denoise=0.45, same seed/sonar
            --> refined LATENT + IMAGE at 768x1152

    Denoise guide:
      0.30-0.50  Subtle hi-res fix  (adds crisp detail, keeps composition)
      0.50-0.70  Moderate rework    (allows layout shifts)
      0.70-1.00  Heavy rework       (treats it almost like a fresh generation)
    """

    # ------------------------------------------------------------------
    def refine(self, model, positive, negative, latent,
               upscale_method, scale_factor, target_width, target_height,
               seed, sonar, steps, cfg, sampler_name, scheduler, denoise,
               vae_decode, vae=None):

        # ── 1. Extract latent tensor ──────────────────────────────────
        if isinstance(latent, dict) and "samples" in latent:
            latent_tensor = latent["samples"]
        elif isinstance(latent, torch.Tensor):
            latent_tensor = latent
        else:
            raise ValueError(f"[Arctenox Refiner] Invalid latent format: {type(latent)}")

        # ── 2. Upscale ────────────────────────────────────────────────
        if upscale_method != "None":
            latent_tensor = _upscale_latent(
                latent_tensor, scale_factor, target_width, target_height, upscale_method
            )
            _, _, h, w = latent_tensor.shape
            print(f"[Arctenox Refiner] Upscaled latent to {w*8}x{h*8} px  ({w}x{h} latent)")

        # Ensure correct device
        target_device = comfy.model_management.intermediate_device()
        latent_tensor = latent_tensor.to(target_device)

        # ── 3. Seed / sonar ───────────────────────────────────────────
        if seed < 0:
            abs_s = abs(seed)
            abs_s = ((abs_s ^ 0xDEADBEEF) * 0x45d9f3b) & 0xFFFFFFFF
            abs_s = ((abs_s ^ (abs_s >> 16)) * 0x45d9f3b) & 0xFFFFFFFF
            noise_seed = (abs_s ^ (abs_s >> 16)) & 0xFFFFFFFF
        else:
            noise_seed = int(seed) & 0xFFFFFFFF

        if sonar != 0:
            noise_seed = _sonar_transform(noise_seed, sonar)

        # ── 4. Prepare noise ──────────────────────────────────────────
        noise = comfy.sample.prepare_noise(latent_tensor, noise_seed, None)

        # ── 5. Sample ─────────────────────────────────────────────────
        try:
            samples = comfy.sample.sample(
                model=model,
                noise=noise,
                steps=steps,
                positive=positive,
                negative=negative,
                cfg=cfg,
                sampler_name=sampler_name,
                scheduler=scheduler,
                sigmas=None,
                latent_image=latent_tensor,
                denoise=denoise,
                disable_noise=False,
                start_step=None,
                last_step=None,
                force_full_denoise=True,
                seed=noise_seed,
            )
        except Exception as exc:
            raise RuntimeError(f"[Arctenox Refiner] Sampling failed: {exc}")

        # ── 6. Extract output tensor ──────────────────────────────────
        if isinstance(samples, dict) and "samples" in samples:
            out_tensor = samples["samples"]
        elif isinstance(samples, torch.Tensor):
            out_tensor = samples
        else:
            raise RuntimeError(f"[Arctenox Refiner] Unexpected sample format: {type(samples)}")

        # ── 7. Optional VAE decode ────────────────────────────────────
        image = None
        if vae_decode == "true" and vae is not None:
            try:
                decoded = vae.decode(out_tensor)
                image = decoded if isinstance(decoded, torch.Tensor) else decoded.get("samples")
            except Exception as exc:
                print(f"[Arctenox Refiner] VAE decode failed: {exc}")
                image = torch.zeros(
                    (out_tensor.shape[0], 64, 64, 3),
                    dtype=torch.float32, device=out_tensor.device
                )
        else:
            image = torch.zeros(
                (out_tensor.shape[0], 64, 64, 3),
                dtype=torch.float32, device=out_tensor.device
            )

        return (model, positive, negative, {"samples": out_tensor}, vae, image)


# ─────────────────────────────────────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "KSamplerRefiner": KSamplerRefiner,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "KSamplerRefiner": "KSampler Refiner (Arctenox's Essentials)",
}

__all__ = ["KSamplerRefiner"]
