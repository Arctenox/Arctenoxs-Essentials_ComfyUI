"""
Arctenox Essentials - Execution Cost Estimator
===============================================

Estimates VRAM usage, runtime, and resource costs before execution.
Provides detailed breakdowns and warnings for resource-intensive operations.

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""

import torch
import comfy.model_management
import math


class ExecutionCostEstimator:
    """
    Estimates execution costs including VRAM, time, and batch processing overhead.
    Helps optimize workflows and prevent OOM errors.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {
                    "default": 960,
                    "min": 64,
                    "max": 8192,
                    "step": 8,
                    "tooltip": "Image width"
                }),
                "height": ("INT", {
                    "default": 1280,
                    "min": 64,
                    "max": 8192,
                    "step": 8,
                    "tooltip": "Image height"
                }),
                "batch_size": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 64,
                    "tooltip": "Number of images per batch"
                }),
                "steps": ("INT", {
                    "default": 25,
                    "min": 1,
                    "max": 10000,
                    "tooltip": "Sampling steps"
                }),
                "model_type": ([
                    "SDXL (8GB)",
                    "SD 1.5 (4GB)",
                    "SD 2.1 (6GB)",
                    "Flux.1 Dev (24GB)",
                    "Flux.1 Schnell (12GB)",
                    "Custom Model"
                ], {
                    "default": "SDXL (8B)",
                    "tooltip": "Model architecture type"
                }),
                "custom_model_size_gb": ("FLOAT", {
                    "default": 6.45,
                    "min": 0.01,
                    "max": 64.0,
                    "step": 0.01,
                    "tooltip": "Custom model size in GB (if Custom Model selected)"
                }),
                "precision": (["fp32", "fp16", "bf16", "fp8"], {
                    "default": "fp16",
                    "tooltip": "Model precision"
                }),
                "enable_vae": (["true", "false"], {
                    "default": "true",
                    "tooltip": "Include VAE decode in estimate"
                }),
                "device": (["auto", "cuda", "mps", "cpu"], {
                    "default": "auto",
                    "tooltip": "Target device for estimation"
                })
            },
            "optional": {
                "model": ("MODEL",),
                "vae": ("VAE",),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("cost_report",)
    FUNCTION = "estimate_cost"
    CATEGORY = "Arctenox Essentials/Utilities"
    OUTPUT_NODE = True
    
    DESCRIPTION = """
    Estimates execution costs before running generation:
    
    Estimates:
    • VRAM usage breakdown (model + latents + overhead)
    • Expected runtime (per step and total)
    • Batch processing efficiency
    • Memory pressure warnings
    • Device-specific optimizations
    
    Features:
    • Supports major model architectures
    • Precision-aware calculations
    • Device-specific estimates (CUDA/MPS/CPU)
    • Batch efficiency analysis
    • OOM risk warnings
    
    Use Cases:
    • Preview resource requirements
    • Optimize batch sizes
    • Prevent out-of-memory errors
    • Compare workflow efficiency
    • Plan hardware upgrades
    """

    def _get_device_info(self, device="auto"):
        """Get available device and its memory"""
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        
        total_memory = 0
        free_memory = 0
        device_name = "Unknown"
        
        if device == "cuda" and torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            free_memory = (torch.cuda.get_device_properties(0).total_memory - 
                          torch.cuda.memory_allocated(0)) / (1024**3)
        elif device == "mps":
            device_name = "Apple Silicon (MPS)"
            # MPS shares system memory, estimate conservatively
            total_memory = 16.0  # Conservative estimate
            free_memory = 12.0
        else:
            device_name = "CPU"
            import psutil
            vm = psutil.virtual_memory()
            total_memory = vm.total / (1024**3)
            free_memory = vm.available / (1024**3)
        
        return device, device_name, total_memory, free_memory

    def _get_model_size(self, model_type, custom_size):
        """Get model size in GB"""
        model_sizes = {
            "SDXL (6.6GB)": 6.6,
            "SD 1.5 (2GB)": 2.0,
            "SD 2.1 (2.5GB)": 2.5,
            "Flux.1 Dev (23GB)": 23.0,
            "Flux.1 Schnell (23GB)": 23.0,
            "Custom Model": custom_size
        }
        return model_sizes.get(model_type, custom_size)

    def _get_precision_multiplier(self, precision):
        """Get memory multiplier for precision"""
        multipliers = {
            "fp32": 1.0,
            "fp16": 0.5,
            "bf16": 0.5,
            "fp8": 0.25
        }
        return multipliers.get(precision, 0.5)

    def _estimate_latent_memory(self, width, height, batch_size, precision):
        """Estimate latent tensor memory usage"""
        # Latent space is width/8 x height/8 x 4 channels
        latent_w = width // 8
        latent_h = height // 8
        channels = 4
        
        # Calculate tensor size in GB
        elements = batch_size * channels * latent_h * latent_w
        bytes_per_element = 4 * self._get_precision_multiplier(precision)  # fp32 base
        size_gb = (elements * bytes_per_element) / (1024**3)
        
        return size_gb

    def _estimate_unet_memory(self, width, height, model_size_gb, precision):
        """Estimate U-Net forward pass memory"""
        # U-Net requires intermediate activations
        # Scales with resolution but not linearly
        resolution_factor = (width * height) / (1024 * 1024)  # Normalize to 1024x1024
        
        # Base activation memory scales with resolution
        activation_base = 2.0  # GB for 1024x1024
        activation_memory = activation_base * math.sqrt(resolution_factor)
        
        # Apply precision multiplier
        activation_memory *= self._get_precision_multiplier(precision)
        
        return activation_memory

    def _estimate_vae_memory(self, width, height, batch_size, precision):
        """Estimate VAE decode memory"""
        # VAE processes full resolution
        pixels = width * height * batch_size * 3  # RGB
        bytes_per_pixel = 4 * self._get_precision_multiplier(precision)
        size_gb = (pixels * bytes_per_pixel) / (1024**3)
        
        # VAE model overhead (~330MB for SDXL)
        vae_model = 0.33
        
        return size_gb + vae_model

    def _estimate_overhead(self, batch_size):
        """Estimate system overhead (PyTorch, ComfyUI, etc.)"""
        base_overhead = 1.5  # GB
        batch_overhead = 0.2 * batch_size  # Additional per batch
        return base_overhead + batch_overhead

    def _estimate_step_time(self, width, height, steps, model_type, device):
        """Estimate time per step in seconds"""
        # Base times (seconds per step for 1024x1024 on RTX 3090)
        base_times = {
            "SDXL (8GB)": 0.15,
            "SD 1.5 (4GB)": 0.05,
            "SD 2.1 (6GB)": 0.06,
            "Flux.1 Dev (24GB)": 0.8,
            "Flux.1 Schnell (12GB)": 0.4,
            "Custom Model": 0.15
        }
        
        base_time = base_times.get(model_type, 0.15)
        
        # Resolution scaling (approximately quadratic for attention)
        resolution_factor = (width * height) / (1024 * 1024)
        time_per_step = base_time * math.pow(resolution_factor, 1.5)
        
        # Device multipliers
        device_multipliers = {
            "cuda": 1.0,
            "mps": 2.5,    # MPS is slower than CUDA
            "cpu": 20.0    # CPU is much slower
        }
        time_per_step *= device_multipliers.get(device, 1.0)
        
        return time_per_step

    def _calculate_efficiency_score(self, vram_usage, available_vram, batch_size):
        """Calculate efficiency score (0-100)"""
        # Penalize memory pressure
        memory_usage_ratio = vram_usage / available_vram if available_vram > 0 else 1.0
        memory_score = max(0, 100 - (memory_usage_ratio * 100))
        
        # Reward batching
        batch_score = min(100, 50 + (batch_size * 10))
        
        # Combined score
        efficiency = (memory_score * 0.6) + (batch_score * 0.4)
        return max(0, min(100, efficiency))

    def _generate_warnings(self, vram_usage, available_vram, time_seconds, batch_size):
        """Generate warnings and recommendations"""
        warnings = []
        
        # Memory warnings
        usage_ratio = vram_usage / available_vram if available_vram > 0 else 1.0
        
        if usage_ratio > 0.95:
            warnings.append("⚠️ CRITICAL: High OOM risk! Reduce batch size or resolution.")
        elif usage_ratio > 0.85:
            warnings.append("⚠️ WARNING: High memory pressure. May cause OOM errors.")
        elif usage_ratio > 0.75:
            warnings.append("⚠️ CAUTION: Moderate memory usage. Monitor for stability.")
        
        # Time warnings
        if time_seconds > 300:  # 5 minutes
            warnings.append(f"⏱️ Long execution time: {time_seconds/60:.1f} minutes")
        
        # Batch recommendations
        if batch_size == 1 and usage_ratio < 0.5:
            warnings.append("💡 TIP: Low memory usage - consider increasing batch size.")
        elif batch_size > 4 and usage_ratio > 0.7:
            warnings.append("💡 TIP: Consider reducing batch size for stability.")
        
        if not warnings:
            warnings.append("✅ Execution parameters look good!")
        
        return "\n".join(warnings)

    def estimate_cost(self, width, height, batch_size, steps, model_type,
                     custom_model_size_gb, precision, enable_vae, device,
                     model=None, vae=None):
        """Generate comprehensive cost estimate"""
        
        # Get device info
        device, device_name, total_memory, free_memory = self._get_device_info(device)
        
        # Get model size
        model_size = self._get_model_size(model_type, custom_model_size_gb)
        
        # Apply precision multiplier to model
        model_memory = model_size * self._get_precision_multiplier(precision)
        
        # Calculate component memory
        latent_memory = self._estimate_latent_memory(width, height, batch_size, precision)
        unet_memory = self._estimate_unet_memory(width, height, model_size, precision)
        vae_memory = self._estimate_vae_memory(width, height, batch_size, precision) if enable_vae == "true" else 0
        overhead = self._estimate_overhead(batch_size)
        
        # Total VRAM
        total_vram = model_memory + latent_memory + unet_memory + vae_memory + overhead
        
        # Estimate time
        time_per_step = self._estimate_step_time(width, height, steps, model_type, device)
        total_time = time_per_step * steps
        
        # VAE decode time (if enabled)
        vae_time = 0
        if enable_vae == "true":
            vae_time = 0.5 * batch_size  # ~0.5s per image
            total_time += vae_time
        
        # Calculate efficiency
        efficiency = self._calculate_efficiency_score(total_vram, free_memory, batch_size)
        
        # Generate warnings
        warnings = self._generate_warnings(total_vram, free_memory, total_time, batch_size)
        
        # Build report
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    EXECUTION COST ESTIMATE                   ║
                                                                       
  📊 CONFIGURATION                                             
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
   Resolution:       {width}x{height} ({width*height/1_000_000:.1f}MP)                                       
   Batch Size:       {batch_size}                                       
   Steps:            {steps}                                            
   Model:            {model_type}                                       
   Precision:        {precision}                                        
   VAE Decode:       {enable_vae}                                       
   Device:           {device_name} ({device.upper()})                   

  💾 VRAM BREAKDOWN - MAY NOT BE 100% ACCURATE                
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
   Model:            {model_memory:.2f} GB  
   Latent Tensors:   {latent_memory:.2f} GB 
   U-Net Forward:    {unet_memory:.2f} GB   
   VAE Decode:       {vae_memory:.2f} GB    
   System Overhead:  {overhead:.2f} GB      
   ─────────────────────────────────
   TOTAL ESTIMATED:  {total_vram:.2f} GB
 
  📈 MEMORY STATUS - MAY NOT BE 100% ACCURATE                  
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
   Available:        {free_memory:.2f} GB / {total_memory:.2f} GB
   Usage:            {(total_vram/free_memory*100) if free_memory > 0 else 0:.1f}%
   Efficiency:       {efficiency:.0f}/100
 
  ⏱️ TIME ESTIMATE - MAY NOT BE 100% ACCURATE                 
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
   Per Step:         {time_per_step:.3f} seconds
   Sampling:         {time_per_step * steps:.1f} seconds
   VAE Decode:       {vae_time:.1f} seconds
   ──────────────────────────────────────────
   TOTAL:            {total_time:.1f} seconds ({total_time/60:.1f} min)
 
  🔍 BATCH ANALYSIS - MAY NOT BE 100% ACCURATE                 
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
   Images:           {batch_size}
   Time per Image:   {total_time/batch_size:.1f} seconds
   VRAM per Image:   {latent_memory/batch_size:.2f} GB
 
  {warnings}                                                     
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        
        return (report,)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ExecutionCostEstimator": ExecutionCostEstimator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExecutionCostEstimator": "Execution Cost Estimator (Arctenox's Essentials)",
}

__all__ = ["ExecutionCostEstimator"]