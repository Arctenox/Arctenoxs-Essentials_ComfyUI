import torch
import comfy.samplers
import comfy.sample
import comfy.model_management
import folder_paths
import nodes
import math

class KSamplerWithLatent:
    """
    A combined node that creates an empty latent image and performs efficient sampling
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "width": ("INT", {"default": 960, "min": 64, "max": 8192, "step": 8}),
                "height": ("INT", {"default": 1280, "min": 64, "max": 8192, "step": 8}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 64}),
                "seed": ("INT", {"default": 0, "min": -0x7fffffffffffffff, "max": 0xffffffffffffffff}),
                "sonar": ("INT", {"default": 0, "min": -18446744073709552000, "max": 18446744073709552000}),
                "steps": ("INT", {"default": 25, "min": 1, "max": 10000}),
                "cfg": ("FLOAT", {"default": 4.0, "min": 0.0, "max": 100.0, "step": 0.01}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "vae_decode": (["true", "false"],),
            },
            "optional": {
                "latent_image": ("LATENT",),
                "optional_vae": ("VAE",),
                "script": ("SCRIPT",),
                "vae_name": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "forceInput": True,
                    "tooltip": "VAE filename for metadata (e.g. vae-ft-mse-840000-ema-pruned)"
                }),
            }
        }

    RETURN_TYPES = ("MODEL", "CONDITIONING", "CONDITIONING", "LATENT", "VAE", "IMAGE", "INT", "INT", "FLOAT", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("MODEL", "CONDITIONING+", "CONDITIONING-", "LATENT", "VAE", "IMAGE", "seed_used", "steps", "cfg", "sampler_name", "scheduler", "vae_name")
    FUNCTION = "sample"
    CATEGORY = "Arctenox Essentials/Sampling"

    def _golden_ratio_sonar_transform(self, seed, sonar):
        """
        Conservative sonar transformation that gently guides toward golden ratio patterns
        while maintaining stable, predictable behavior
        """
        if sonar == 0:
            return seed
            
        max_seed = 0xFFFFFFFF
        
        # Original sonar-style hash transformation (main behavior)
        offset_hash = (sonar * 0x9E3779B9) ^ (sonar << 13) ^ (sonar >> 7)
        base_noise_seed = ((seed ^ offset_hash) * 1103515245 + 12345) & 0xFFFFFFFF
        
        # Gentle golden ratio influence - only apply subtle adjustments
        abs_sonar = abs(sonar)
        
        # Conservative approach: only apply golden ratio for larger sonar values
        if abs_sonar > 10:
            # Golden ratio constant
            PHI_INVERSE = 0.618033988749895  # 1 / PHI
            
            # Very gentle golden ratio nudge - scale down the effect significantly
            golden_influence = (abs_sonar * PHI_INVERSE * 0.1) % 1.0  # 0.1 = 10% influence
            
            # Apply minimal golden ratio adjustment
            golden_adjustment = int(base_noise_seed * golden_influence * 0.05)  # 5% max change
            final_seed = (base_noise_seed + golden_adjustment) & 0xFFFFFFFF
        else:
            # For small sonar values, use original behavior only
            final_seed = base_noise_seed
        
        # Preserve original sonar sign behavior
        if sonar < 0:
            final_seed = (max_seed - final_seed) & 0xFFFFFFFF
            
        return final_seed
                
    def _handle_large_cfg(self, cfg):
        """
        Handle extremely large CFG values (including massive decimals) by applying intelligent scaling
        while maintaining sampling stability
        """
        if cfg <= 100.0:
            # Normal CFG range, return as-is
            return float(cfg)
        elif cfg <= 1000.0:
            # Moderate scaling for large but reasonable values
            return float(cfg)
        else:
            # For extremely large CFG values, apply logarithmic scaling
            # to prevent sampling instability while still allowing exploration
            
            # Logarithmic compression for very large values
            # Maps large numbers to a more reasonable range while preserving differences
            if cfg > 1e10:  # For truly massive values
                # Take log base 10, scale, and add offset to keep it in workable range
                log_val = math.log10(cfg)
                # Scale to reasonable CFG range (10-50) based on log magnitude
                scaled_cfg = 10.0 + (log_val - 10.0) * 5.0  # Maps log10(1e10) to log10(max) -> 10 to 50
                return max(10.0, min(50.0, scaled_cfg))
            else:
                # For large but not astronomical values, use gentler scaling
                # Square root scaling to compress large values
                sqrt_scale = math.sqrt(cfg / 100.0)  # Normalize by 100, then sqrt
                scaled_cfg = 10.0 + sqrt_scale * 2.0  # Scale to 10+ range
                return max(10.0, min(30.0, scaled_cfg))
    
    def _handle_large_steps(self, steps):
        """
        Handle extremely large step values intelligently
        """
        if steps <= 10000:
            # Normal step range, return as-is
            return int(steps)
        elif steps <= 100000:
            # Cap at reasonable maximum
            return min(steps, 50000)
        else:
            # For astronomical step values, use logarithmic scaling
            log_val = math.log10(steps)
            # Map large step counts to reasonable range (1000-10000)
            scaled_steps = int(1000 + (log_val - 5.0) * 1000)  # log10(100000) = 5
            return max(1000, min(10000, scaled_steps))

    def sample(self, model, positive, negative, width, height, batch_size, seed, sonar, steps, cfg, 
               sampler_name, scheduler, denoise, vae_decode,
               latent_image=None, optional_vae=None, script=None, vae_name=""):
        
        # Extract tensor from latent_image or create new one
        latent_tensor = None
        
        if latent_image is None:
            # Create empty latent tensor
            latent_tensor = torch.zeros(
                [batch_size, 4, height // 8, width // 8],
                device=comfy.model_management.intermediate_device()
            )
        else:
            # Safely extract tensor from latent_image
            if isinstance(latent_image, dict) and "samples" in latent_image:
                latent_tensor = latent_image["samples"]
            elif isinstance(latent_image, torch.Tensor):
                latent_tensor = latent_image
            else:
                raise ValueError(f"Invalid latent_image format. Expected dict with 'samples' key or tensor, got {type(latent_image)}")
            
            # Ensure it's actually a tensor
            if not isinstance(latent_tensor, torch.Tensor):
                raise ValueError(f"latent_image['samples'] must be a tensor, got {type(latent_tensor)}")

        # Validate tensor shape and device
        if not isinstance(latent_tensor, torch.Tensor):
            raise ValueError(f"Failed to extract valid tensor from latent_image")
            
        # Ensure tensor is on correct device
        target_device = comfy.model_management.intermediate_device()
        if latent_tensor.device != target_device:
            latent_tensor = latent_tensor.to(target_device)

        # Handle seed - standard behavior for positive, deterministic transform for negative
        if seed < 0:
            # Deterministic transformation for negative seeds
            # Use a hash to map negative seeds to positive space
            abs_seed = abs(seed)
            # Simple but effective hash mixing
            hashed = abs_seed
            hashed = ((hashed ^ 0xDEADBEEF) * 0x45d9f3b) & 0xFFFFFFFF
            hashed = ((hashed ^ (hashed >> 16)) * 0x45d9f3b) & 0xFFFFFFFF
            hashed = (hashed ^ (hashed >> 16)) & 0xFFFFFFFF
            noise_seed = hashed
        else:
            # Standard behavior for positive seeds - just mask to 32-bit
            noise_seed = int(seed) & 0xFFFFFFFF
        
        # Apply sonar transformation if sonar is non-zero
        if sonar != 0:
            noise_seed = self._golden_ratio_sonar_transform(noise_seed, sonar)

        # seed_used: return the original input seed when sonar is inactive so the
        # user sees exactly what they typed in; return the transformed noise_seed
        # only when sonar has modified it (so they know what was actually sampled).
        seed_used = noise_seed if sonar != 0 else seed
        
        # Generate noise using ComfyUI's standard method
        batch_inds = latent_image.get("batch_index") if isinstance(latent_image, dict) else None
        
        # Use comfy's prepare_noise
        noise = comfy.sample.prepare_noise(latent_tensor, noise_seed, batch_inds)
        
        # Use processed values for sampling
        processed_cfg = self._handle_large_cfg(cfg)
        processed_steps = self._handle_large_steps(steps)
        
        # Define sampling parameters
        disable_noise = False
        start_step = None
        last_step = None
        force_full_denoise = True
        
        # Pass to comfy.sample.sample
        try:
            samples = comfy.sample.sample(
                model=model,
                noise=noise,                 # TENSOR - random noise for sampling
                steps=processed_steps,       # Use processed steps
                positive=positive,
                negative=negative,
                cfg=processed_cfg,           # Use processed CFG
                sampler_name=sampler_name,
                scheduler=scheduler,
                sigmas=None,
                latent_image=latent_tensor,  # TENSOR - starting latent (can be zeros or existing)
                denoise=denoise,
                disable_noise=disable_noise,
                start_step=start_step,
                last_step=last_step,
                force_full_denoise=force_full_denoise,
                seed=noise_seed,  # Use the final seed (with sonar if applied)
            )
        except Exception as e:
            raise RuntimeError(f"Sampling failed: {str(e)}. Check that all inputs are valid tensors.")
        
        # Safely extract samples tensor from result
        output_tensor = None
        if isinstance(samples, dict) and "samples" in samples:
            output_tensor = samples["samples"]
        elif isinstance(samples, torch.Tensor):
            output_tensor = samples
        else:
            raise RuntimeError(f"Sampling returned unexpected format: {type(samples)}")
            
        if not isinstance(output_tensor, torch.Tensor):
            raise RuntimeError(f"Failed to extract tensor from sampling result")

        # Handle VAE and image output safely
        vae = optional_vae
        image = None
        
        if vae_decode == "true" and vae is not None:
            try:
                # Decode latent to image
                decoded = vae.decode(output_tensor)
                # Handle various return formats from VAE decode
                if isinstance(decoded, dict) and "samples" in decoded:
                    image = decoded["samples"]
                elif isinstance(decoded, torch.Tensor):
                    image = decoded
                else:
                    # Fallback if decode fails
                    image = torch.zeros((batch_size, 64, 64, 3), dtype=torch.float32, device=output_tensor.device)
            except Exception as e:
                print(f"VAE decode failed: {e}, returning empty image")
                image = torch.zeros((batch_size, 64, 64, 3), dtype=torch.float32, device=output_tensor.device)
        else:
            # Return empty image tensor if no decoding
            image = torch.zeros((batch_size, 64, 64, 3), dtype=torch.float32, device=output_tensor.device)
        
        # Ensure we return the latent in the correct dict format
        return (
            model,                           # MODEL
            positive,                        # CONDITIONING+
            negative,                        # CONDITIONING-
            {"samples": output_tensor},      # LATENT (dict format for ComfyUI)
            vae,                             # VAE
            image,                           # IMAGE
            seed_used,                       # seed_used
            steps,                           # steps
            cfg,                             # cfg
            sampler_name,                    # sampler_name
            scheduler,                       # scheduler
            vae_name,                        # vae_name
        )


class EfficientLatentImage:
    """
    Simple empty latent image generator
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 960, "min": 64, "max": 8192, "step": 8}),
                "height": ("INT", {"default": 1280, "min": 64, "max": 8192, "step": 8}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 64})
            }
        }
    
    RETURN_TYPES = ("LATENT",)
    FUNCTION = "generate"
    CATEGORY = "latent"

    def generate(self, width, height, batch_size):
        # Always return tensor wrapped in dict
        latent = torch.zeros(
            [batch_size, 4, height // 8, width // 8],
            device=comfy.model_management.intermediate_device()
        )
        return ({"samples": latent},)


# Node mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "KSamplerWithLatent": KSamplerWithLatent,
    "EfficientLatentImage": EfficientLatentImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "KSamplerWithLatent": "KSampler (Arctenox's Essentials)",
    "EfficientLatentImage": "Efficient Empty Latent (Arctenox's Essentials)",
}

# Package info
__version__ = "1.0.0"
__author__ = "Arctenox"
__description__ = "Arctenox Workflow Essentials - Efficient sampling nodes with optimized golden ratio sonar"
__package_name__ = "arctenox_workflow-essentials"
