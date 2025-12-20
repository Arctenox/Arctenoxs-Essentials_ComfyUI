"""
Arctenox Workflow Essentials
=============================

A collection of efficient workflow nodes for ComfyUI, designed to streamline
and optimize your generation process with combined functionality and 
improved performance.

Author: Arctenox
Version: 1.0.0
License: GPL-3.0

Features:
- Efficient combined sampler with built-in latent generation
- Seed topology mapping for structured exploration
- Temporal prompt phase splitting for progressive refinement
- Artifact risk prediction before decoding
- Execution cost estimation (VRAM, time, efficiency)
- Streamlined workflow nodes
- Memory-optimized processing
- Cross-platform compatibility (CUDA/MPS/CPU)
"""

import os
import sys
import importlib.util
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import KSampler nodes
try:
    from .ArctenoxEssentials_KSampler import KSamplerWithLatent
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import KSampler nodes: {e}")
    KSamplerWithLatent = None

# Import Passthrough nodes
try:
    from .ArctenoxEssentials_Passthrough import (
        ArctenoxBox,
        ArctenoxCheckpointPassthrough,
    )
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Passthrough nodes: {e}")
    ArctenoxBox = None
    ArctenoxCheckpointPassthrough = None

# Import Seed Topology Mapper
try:
    from .ArctenoxEssentials_SeedTopology import SeedTopologyMapper
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Seed Topology Mapper: {e}")
    SeedTopologyMapper = None

# Import Prompt Phase Splitter
try:
    from .ArctenoxEssentials_PromptPhaseSplitter import PromptPhaseSplitter
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Prompt Phase Splitter: {e}")
    PromptPhaseSplitter = None

# Import Artifact Risk Predictor
try:
    from .ArctenoxEssentials_ArtifactRiskPredictor import ArtifactRiskPredictor
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Artifact Risk Predictor: {e}")
    ArtifactRiskPredictor = None

# Import Execution Cost Estimator
try:
    from .ArctenoxEssentials_CostEstimator import ExecutionCostEstimator
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Cost Estimator: {e}")
    ExecutionCostEstimator = None

# Version info
__version__ = "1.0.0"
__author__ = "Arctenox"
__description__ = "Arctenox Workflow Essentials - Efficient workflow nodes for ComfyUI"

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# KSampler nodes
if KSamplerWithLatent:
    NODE_CLASS_MAPPINGS["KSamplerWithLatent"] = KSamplerWithLatent
    NODE_DISPLAY_NAME_MAPPINGS["KSamplerWithLatent"] = "KSampler (Arctenox's Essentials)"

# Passthrough nodes
if ArctenoxBox:
    NODE_CLASS_MAPPINGS["ArctenoxBox"] = ArctenoxBox
    NODE_DISPLAY_NAME_MAPPINGS["ArctenoxBox"] = " "

if ArctenoxCheckpointPassthrough:
    NODE_CLASS_MAPPINGS["ArctenoxCheckpointPassthrough"] = ArctenoxCheckpointPassthrough
    NODE_DISPLAY_NAME_MAPPINGS["ArctenoxCheckpointPassthrough"] = "Checkpoint Passthrough + Notes (Arctenox's Essentials)"

# Seed Topology Mapper
if SeedTopologyMapper:
    NODE_CLASS_MAPPINGS["SeedTopologyMapper"] = SeedTopologyMapper
    NODE_DISPLAY_NAME_MAPPINGS["SeedTopologyMapper"] = "Seed Topology Mapper (Arctenox's Essentials)"

# Prompt Phase Splitter
if PromptPhaseSplitter:
    NODE_CLASS_MAPPINGS["PromptPhaseSplitter"] = PromptPhaseSplitter
    NODE_DISPLAY_NAME_MAPPINGS["PromptPhaseSplitter"] = "Prompt Phase Splitter (Arctenox's Essentials)"

# Artifact Risk Predictor
if ArtifactRiskPredictor:
    NODE_CLASS_MAPPINGS["ArtifactRiskPredictor"] = ArtifactRiskPredictor
    NODE_DISPLAY_NAME_MAPPINGS["ArtifactRiskPredictor"] = "Artifact Risk Predictor (Arctenox's Essentials)"

# Execution Cost Estimator
if ExecutionCostEstimator:
    NODE_CLASS_MAPPINGS["ExecutionCostEstimator"] = ExecutionCostEstimator
    NODE_DISPLAY_NAME_MAPPINGS["ExecutionCostEstimator"] = "Execution Cost Estimator (Arctenox's Essentials)"

# Node categories
NODE_CATEGORIES = {}
for node_key in NODE_CLASS_MAPPINGS.keys():
    if "Sampler" in node_key or "Seed" in node_key or "Topology" in node_key or "Phase" in node_key or "Prompt" in node_key:
        NODE_CATEGORIES[node_key] = "Arctenox Essentials/Sampling"
    elif "Latent" in node_key:
        NODE_CATEGORIES[node_key] = "Arctenox Essentials/Latent"
    elif "Checkpoint" in node_key or "Passthrough" in node_key or "Box" in node_key or "Estimator" in node_key or "Cost" in node_key or "Predictor" in node_key or "Risk" in node_key or "Artifact" in node_key:
        NODE_CATEGORIES[node_key] = "Arctenox Essentials/Utilities"
    else:
        NODE_CATEGORIES[node_key] = "Arctenox Essentials/Core"

def check_dependencies():
    """Check if required dependencies are available."""
    required_packages = [
        ("torch", "PyTorch >= 1.12.0"),
        ("comfy", "ComfyUI"),
        ("numpy", "NumPy"),
    ]
    
    optional_packages = [
        ("psutil", "psutil (for CPU memory info)"),
    ]
    
    missing_packages = []
    missing_optional = []
    
    for package_name, description in required_packages:
        try:
            importlib.import_module(package_name)
        except ImportError:
            missing_packages.append(description)
    
    for package_name, description in optional_packages:
        try:
            importlib.import_module(package_name)
        except ImportError:
            missing_optional.append(description)
    
    if missing_packages:
        print(f"[Arctenox Essentials] Warning: Missing dependencies:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("[Arctenox Essentials] Some features may not work properly.")
    
    if missing_optional:
        print(f"[Arctenox Essentials] Optional dependencies not found:")
        for pkg in missing_optional:
            print(f"  - {pkg}")
    
    return len(missing_packages) == 0

def get_system_info():
    """Get system information for optimization."""
    try:
        import torch
        
        info = {
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "mps_available": hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(),
        }
        
        if info["cuda_available"]:
            info["cuda_device_count"] = torch.cuda.device_count()
            info["cuda_memory"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 1)
        
        return info
    except Exception as e:
        print(f"[Arctenox Essentials] Could not get system info: {e}")
        return {}

def print_welcome_message():
    """Print welcome message with system information."""
    print("\n" + "="*60)
    print("🔮 Arctenox Workflow Essentials Loaded")
    print("="*60)
    print(f"Version: {__version__}")
    print(f"Author: {__author__}")
    print(f"Nodes: {len(NODE_CLASS_MAPPINGS)}")
    
    # System info
    sys_info = get_system_info()
    if sys_info:
        print(f"\n📊 System Information:")
        print(f"  PyTorch: {sys_info.get('torch_version', 'Unknown')}")
        
        if sys_info.get("cuda_available"):
            print(f"  CUDA: Available ({sys_info.get('cuda_device_count', 0)} device(s))")
            if sys_info.get('cuda_memory'):
                print(f"  GPU Memory: {sys_info.get('cuda_memory')}GB")
        elif sys_info.get("mps_available"):
            print(f"  MPS: Available (Apple Silicon)")
        else:
            print(f"  GPU: CPU fallback mode")
    
    print(f"\n🚀 Available Nodes:")
    for category in sorted(set(NODE_CATEGORIES.values())):
        print(f"\n  {category}:")
        for node_class, node_category in NODE_CATEGORIES.items():
            if node_category == category:
                display_name = NODE_DISPLAY_NAME_MAPPINGS.get(node_class, node_class)
                print(f"    • {display_name}")
    
    print(f"\n💡 Features:")
    print("    • Golden ratio sonar seed transformation")
    print("    • Seed topology mapping for structured exploration")
    print("    • Temporal prompt phase splitting (composition→detail→texture)")
    print("    • Artifact risk prediction before decoding")
    print("    • Optional character/subject focus phase")
    print("    • Execution cost estimation (VRAM, time, efficiency)")
    print("    • Efficient latent generation")
    print("    • Empty box for workflow organization")
    print("    • Checkpoint passthrough for complete checkpoint routing")
    
    print("="*60 + "\n")

# Initialize the package
def __init_package():
    """Initialize the package and perform startup checks."""
    try:
        # Check dependencies
        deps_ok = check_dependencies()
        
        # Print welcome message
        print_welcome_message()
        
        if not deps_ok:
            print("[Arctenox Essentials] Warning: Some dependencies are missing. Please install them for full functionality.")
        
        print("[Arctenox Essentials] Package initialized successfully!")
        
    except Exception as e:
        print(f"[Arctenox Essentials] Error during initialization: {e}")
        print("[Arctenox Essentials] Package may not function correctly.")

# Run initialization
__init_package()

# Export for ComfyUI
__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS", 
    "__version__",
    "__author__",
    "__description__"
]