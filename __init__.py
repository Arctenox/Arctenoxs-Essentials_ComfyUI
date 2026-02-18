"""
Arctenox's Essentials
=============================

A collection of efficient workflow nodes for ComfyUI.

Author: Arctenox
Version: 1.4.0
License: GPL-3.0

New in v1.3.0:
- CLIP Text Encode (Positive + Wildcards) — positive-only encode with wildcard support
- CLIP Text Encode (Prompt Gen) — positive encode with direct PromptGenerator hookup
- Prompt Generator now includes a filter_tags input to exclude unwanted tags
- Wildcard Nodes: Processor, Picker, Stack (fixed + stable)
"""

import os
import sys
import importlib.util
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

__version__     = "1.4.0"
__author__      = "Arctenox"
__description__ = "Arctenox Workflow Essentials — Efficient workflow nodes for ComfyUI"

# ─────────────────────────────────────────────────────────────────────────────
#  Imports
# ─────────────────────────────────────────────────────────────────────────────

# KSampler
try:
    from .ArctenoxEssentials_KSampler import KSamplerWithLatent
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import KSampler: {e}")
    KSamplerWithLatent = None

# KSampler Refiner
try:
    from .ArctenoxEssentials_KSamplerRefiner import KSamplerRefiner
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import KSampler Refiner: {e}")
    KSamplerRefiner = None

# Passthrough nodes
try:
    from .ArctenoxEssentials_Passthrough import (
        ArctenoxBox,
        ArctenoxCheckpointPassthrough,
    )
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Passthrough nodes: {e}")
    ArctenoxBox = None
    ArctenoxCheckpointPassthrough = None

# Seed Topology Mapper
try:
    from .ArctenoxEssentials_SeedTopology import SeedTopologyMapper
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Seed Topology Mapper: {e}")
    SeedTopologyMapper = None

# Prompt Phase Splitter
try:
    from .ArctenoxEssentials_PromptPhaseSplitter import PromptPhaseSplitter
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Prompt Phase Splitter: {e}")
    PromptPhaseSplitter = None

# Artifact Risk Predictor
try:
    from .ArctenoxEssentials_ArtifactRiskPredictor import ArtifactRiskPredictor
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Artifact Risk Predictor: {e}")
    ArtifactRiskPredictor = None

# Execution Cost Estimator
try:
    from .ArctenoxEssentials_CostEstimator import ExecutionCostEstimator
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Cost Estimator: {e}")
    ExecutionCostEstimator = None

# Save Image With Metadata
try:
    from .ArctenoxEssentials_SaveImageWithMetadata import SaveImageWithMetadata
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Save Image With Metadata: {e}")
    SaveImageWithMetadata = None

# Prompt Styler
try:
    from .ArctenoxEssentials_PromptStyler import PromptStyler, PromptStylerAdvanced
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Prompt Styler: {e}")
    PromptStyler = None
    PromptStylerAdvanced = None

# CLIP Text Encode nodes
try:
    from .ArctenoxEssentials_CLIPTextEncode import (
        CLIPTextEncodeWithString,
        CLIPTextEncodeWithPromptGen,
    )
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import CLIP Text Encode nodes: {e}")
    CLIPTextEncodeWithString   = None
    CLIPTextEncodeWithPromptGen = None

# Prompt Generator + Tag Normalizer
try:
    from .ArctenoxEssentials_PromptGenerator import PromptGenerator, TagNormalizer
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Prompt Generator: {e}")
    PromptGenerator = None
    TagNormalizer   = None

# Prompt Finalizer
try:
    from .ArctenoxEssentials_PromptFinalizer import PromptFinalizer
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Prompt Finalizer: {e}")
    PromptFinalizer = None

# Load Checkpoint
try:
    from .ArctenoxEssentials_LoadCheckpoint import LoadCheckpointWithString
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Load Checkpoint: {e}")
    LoadCheckpointWithString = None

# LoRA Stack Manager
try:
    from .ArctenoxEssentials_LoraStackManager import LoraStackManager
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import LoRA Stack Manager: {e}")
    LoraStackManager = None

# Image Utilities
try:
    from .ArctenoxEssentials_ImageUtils import ImageResize, ImageDimensions
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Image Utilities: {e}")
    ImageResize = None
    ImageDimensions = None

# VAE Encode + Dimensions
try:
    from .ArctenoxEssentials_VAEEncode import VAEEncodeWithDimensions
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import VAE Encode: {e}")
    VAEEncodeWithDimensions = None

# String Utilities
try:
    from .ArctenoxEssentials_StringUtils import StringConcatenate, StringSwitch
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import String Utilities: {e}")
    StringConcatenate = None
    StringSwitch = None

# Conditioning Utilities
try:
    from .ArctenoxEssentials_ConditioningUtils import ConditioningStrengthScaler
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Conditioning Utilities: {e}")
    ConditioningStrengthScaler = None

# Wildcard Nodes
try:
    from .ArctenoxEssentials_WildcardNodes import (
        ArctenoxWildcardProcessor,
        ArctenoxWildcardPicker,
        ArctenoxWildcardStack,
    )
except ImportError as e:
    print(f"[Arctenox Essentials] Warning: Could not import Wildcard Nodes: {e}")
    ArctenoxWildcardProcessor = None
    ArctenoxWildcardPicker    = None
    ArctenoxWildcardStack     = None

# ─────────────────────────────────────────────────────────────────────────────
#  Node Mappings
# ─────────────────────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    # Sampling
    "KSamplerWithLatent":                   KSamplerWithLatent,
    "KSamplerRefiner":                      KSamplerRefiner,
    "SeedTopologyMapper":                   SeedTopologyMapper,
    # Conditioning
    "CLIPTextEncodeWithString":             CLIPTextEncodeWithString,
    "CLIPTextEncodeWithPromptGen":          CLIPTextEncodeWithPromptGen,
    "PromptPhaseSplitter":                  PromptPhaseSplitter,
    "ArctenoxConditioningStrengthScaler":   ConditioningStrengthScaler,
    # Prompting
    "PromptStyler":                         PromptStyler,
    "PromptStylerAdvanced":                 PromptStylerAdvanced,
    "ArctenoxPromptGenerator":              PromptGenerator,
    "ArctenoxTagNormalizer":                TagNormalizer,
    "ArctenoxPromptFinalizer":              PromptFinalizer,
    # Wildcards
    "ArctenoxWildcardProcessor":            ArctenoxWildcardProcessor,
    "ArctenoxWildcardPicker":               ArctenoxWildcardPicker,
    "ArctenoxWildcardStack":                ArctenoxWildcardStack,
    # Loaders
    "ArctenoxLoadCheckpoint":               LoadCheckpointWithString,
    "LoraStackManager":                     LoraStackManager,
    # Latent
    "ArctenoxVAEEncode":                    VAEEncodeWithDimensions,
    # Image
    "ArctenoxImageResize":                  ImageResize,
    "ArctenoxImageDimensions":              ImageDimensions,
    # Text
    "ArctenoxStringConcatenate":            StringConcatenate,
    "ArctenoxStringSwitch":                 StringSwitch,
    # Output
    "SaveImageWithMetadata":                SaveImageWithMetadata,
    # Utilities
    "ArctenoxBox":                          ArctenoxBox,
    "ArctenoxCheckpointPassthrough":        ArctenoxCheckpointPassthrough,
    "ArtifactRiskPredictor":                ArtifactRiskPredictor,
    "ExecutionCostEstimator":               ExecutionCostEstimator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    # Sampling
    "KSamplerWithLatent":                   "KSampler (Arctenox's Essentials)",
    "KSamplerRefiner":                      "KSampler Refiner (Arctenox's Essentials)",
    "SeedTopologyMapper":                   "Seed Topology Mapper (Arctenox's Essentials)",
    # Conditioning
    "CLIPTextEncodeWithString":             "CLIP Text Encode [Positive + Wildcards] (Arctenox's Essentials)",
    "CLIPTextEncodeWithPromptGen":          "CLIP Text Encode [Prompt Gen] (Arctenox's Essentials)",
    "PromptPhaseSplitter":                  "Prompt Phase Splitter (Arctenox's Essentials)",
    "ArctenoxConditioningStrengthScaler":   "Conditioning Strength Scaler (Arctenox's Essentials)",
    # Prompting
    "PromptStyler":                         "Prompt Styler (Arctenox's Essentials)",
    "PromptStylerAdvanced":                 "Prompt Styler [Advanced] (Arctenox's Essentials)",
    "ArctenoxPromptGenerator":              "Prompt Generator (Arctenox's Essentials)",
    "ArctenoxTagNormalizer":                "Tag Normalizer (Arctenox's Essentials)",
    "ArctenoxPromptFinalizer":              "Prompt Finalizer (Arctenox's Essentials)",
    # Wildcards
    "ArctenoxWildcardProcessor":            "Wildcard Processor (Arctenox's Essentials)",
    "ArctenoxWildcardPicker":               "Wildcard Picker (Arctenox's Essentials)",
    "ArctenoxWildcardStack":                "Wildcard Stack (Arctenox's Essentials)",
    # Loaders
    "ArctenoxLoadCheckpoint":               "Load Checkpoint (Arctenox's Essentials)",
    "LoraStackManager":                     "LoRA Stack Manager (Arctenox's Essentials)",
    # Latent
    "ArctenoxVAEEncode":                    "VAE Encode + Dimensions (Arctenox's Essentials)",
    # Image
    "ArctenoxImageResize":                  "Image Resize (Arctenox's Essentials)",
    "ArctenoxImageDimensions":              "Image Dimensions (Arctenox's Essentials)",
    # Text
    "ArctenoxStringConcatenate":            "String Concatenate (Arctenox's Essentials)",
    "ArctenoxStringSwitch":                 "String Switch (Arctenox's Essentials)",
    # Output
    "SaveImageWithMetadata":                "Save Image With Metadata (Arctenox's Essentials)",
    # Utilities
    "ArctenoxBox":                          " ",
    "ArctenoxCheckpointPassthrough":        "Checkpoint Passthrough + Notes (Arctenox's Essentials)",
    "ArtifactRiskPredictor":                "Artifact Risk Predictor (Arctenox's Essentials)",
    "ExecutionCostEstimator":               "Execution Cost Estimator (Arctenox's Essentials)",
}

# Strip None entries from failed imports
NODE_CLASS_MAPPINGS        = {k: v for k, v in NODE_CLASS_MAPPINGS.items() if v is not None}
NODE_DISPLAY_NAME_MAPPINGS = {k: v for k, v in NODE_DISPLAY_NAME_MAPPINGS.items()
                               if k in NODE_CLASS_MAPPINGS}

# ─────────────────────────────────────────────────────────────────────────────
#  Startup
# ─────────────────────────────────────────────────────────────────────────────

def _check_dependencies():
    missing = []
    for pkg, label in [("torch", "PyTorch"), ("comfy", "ComfyUI"), ("numpy", "NumPy")]:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(label)
    if missing:
        print(f"[Arctenox Essentials] Warning: Missing dependencies: {', '.join(missing)}")
    return not missing


def _get_system_info():
    try:
        import torch
        info = {
            "torch": torch.__version__,
            "cuda":  torch.cuda.is_available(),
            "mps":   hasattr(torch.backends, "mps") and torch.backends.mps.is_available(),
        }
        if info["cuda"]:
            info["cuda_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 1
            )
        return info
    except Exception:
        return {}


def _print_welcome():
    info = _get_system_info()
    print("\n" + "=" * 62)
    print(f"  Arctenox Workflow Essentials  v{__version__}")
    print("=" * 62)
    if info:
        dev = (f"CUDA ({info.get('cuda_gb', '?')}GB)" if info.get("cuda")
               else "MPS" if info.get("mps") else "CPU")
        print(f"  PyTorch {info['torch']}  |  Device: {dev}")

    categories: dict = {}
    for key, cls in NODE_CLASS_MAPPINGS.items():
        cat = getattr(cls, "CATEGORY", "Arctenox Essentials/Utilities")
        categories.setdefault(cat, []).append(
            NODE_DISPLAY_NAME_MAPPINGS.get(key, key)
        )

    print(f"\n  {len(NODE_CLASS_MAPPINGS)} nodes loaded:\n")
    for cat in sorted(categories):
        short = cat.replace("Arctenox Essentials/", "")
        print(f"    [{short}]")
        for name in sorted(categories[cat]):
            if name.strip():
                print(f"      • {name}")

    print(f"\n  New in v1.4.0:")
    for item in [
        "Tag Normalizer  — deduplicates tags, escapes parentheses, underscore→space",
        "Prompt Generator  — exclude artist/copyright tags toggles, min_post_count steps by 1",
        "Prompt Generator  — parenthesis escaping now built-in",
    ]:
        print(f"    + {item}")
    print("=" * 62 + "\n")


def _init():
    try:
        _check_dependencies()
        wc_dir = current_dir / "wildcards"
        wc_dir.mkdir(exist_ok=True)
        example = wc_dir / "hair_color.txt"
        if not example.exists():
            example.write_text(
                "# Example wildcard file — one option per line\n"
                "red\nblonde\nbrown\nblack\nsilver\npink\nblue\n",
                encoding="utf-8",
            )
        # Ensure data dir exists for CSV autocomplete files
        (current_dir / "data").mkdir(exist_ok=True)
        _print_welcome()
    except Exception as e:
        print(f"[Arctenox Essentials] Error during init: {e}")


_init()

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "__version__"]

# ─────────────────────────────────────────────────────────────────────────────
#  API registration  (Wildcard API + Full Autocomplete API)
# ─────────────────────────────────────────────────────────────────────────────

def _register_all_routes(aiohttp_app):
    """Register all HTTP routes for browser-side features."""
    # Wildcard API  (GET /arctenox/wildcards, GET /arctenox/e621_tags)
    try:
        from .ArctenoxEssentials_WildcardAPI import register_routes as wc_reg
        wc_reg(aiohttp_app)
    except Exception as e:
        print(f"[Arctenox Essentials] Wildcard API error: {e}")

    # Full Autocomplete API  (GET /arctenox/ac/*)
    try:
        from .ArctenoxEssentials_AutocompleteAPI import register_routes as ac_reg
        ac_reg(aiohttp_app)
    except Exception as e:
        print(f"[Arctenox Essentials] Autocomplete API error: {e}")


try:
    from server import PromptServer
    _register_all_routes(PromptServer.instance.app)
except Exception as _err:
    print(f"[Arctenox Essentials] API registration deferred (server not ready): {_err}")

# Tell ComfyUI to serve ./web so the browser can load all JS extensions
WEB_DIRECTORY = "./web"
