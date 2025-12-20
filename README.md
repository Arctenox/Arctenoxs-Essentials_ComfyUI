[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-Compatible-brightgreen.svg)](https://github.com/comfyanonymous/ComfyUI)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
# Arctenox's Essentials
A collection of efficient workflow nodes for ComfyUI, designed to streamline and optimize your generation process with combined functionality and improved performance.

### Developer Note
My second node pack, which I originally made to help streamline my workflows when I make a new one.

## 🎯 Overview

Arctenox's Essentials provides a suite of powerful workflow nodes that enhance ComfyUI with advanced sampling techniques, intelligent seed management, temporal prompt processing, and workflow optimization tools. Each node is designed to integrate seamlessly into your existing workflows while adding sophisticated functionality.

## ✨ Features

- **🎲 Advanced KSampler**: Combined empty latent, base ksampler, vae decoding and sampling with golden ratio sonar seed transformation - This does not save Metadata.
- **🗺️ Seed Topology Mapping**: Generate mathematically related seed families for structured exploration
- **⏱️ Temporal Prompt Splitting**: Progressive refinement through composition → detail → texture phases
- **⚠️ Artifact Risk Prediction**: Detect potential issues before VAE decoding
- **💰 Cost Estimation**: Real-time VRAM, time, and efficiency metrics
- **📦 Workflow Utilities**: Checkpoint passthrough, organization boxes, and more
- **🚀 Performance Optimized**: Memory-efficient processing across CUDA/MPS/CPU
- **🎨 Professional Quality**: Built with production workflows in mind

## 📦 Installation

### Via ComfyUI Manager (Recommended)

1. Open ComfyUI Manager
2. Search for "Arctenoxs-Essentials_ComfyUI" or "Arctenox's Essentials"
4. If It Is In The Manager -> Click Install -> If It Is Not In The Manager Do The Manual Install Method.
6. Restart ComfyUI

### Manual Installation

1. Navigate to your ComfyUI custom nodes directory:
   ```bash
   cd ComfyUI/custom_nodes/
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/Arctenox/Arctenoxs-Essentials_ComfyUI
   ```

3. Restart ComfyUI

### Requirements

- ComfyUI (latest version recommended)
- PyTorch >= 1.12.0
- Python >= 3.8
- Optional: `psutil` for CPU memory monitoring

## 🎨 Node Catalog

### 🎲 KSampler (Arctenox's Essentials)

An enhanced sampler that combines latent generation with advanced sampling features.

**Key Features:**
- Built-in empty latent generation
- **Golden Ratio Sonar Transformation**: Deterministic seed transformation using golden ratio patterns
- **Intelligent CFG Handling**: Logarithmic scaling for extreme CFG values
- **Large Step Support**: Handles astronomical step counts intelligently
- **Negative Seed Support**: Deterministic hashing for negative seed values
- Optional VAE decoding in a single node

**Parameters:**
- `width/height`: Image dimensions (64-8192, step 8)
- `batch_size`: Number of images to generate (1-64)
- `seed`: Base random seed
- `sonar`: Golden ratio transformation offset (-18446744073709552000 to 18446744073709552000)
- `steps`: Sampling steps (1-10000+)
- `cfg`: Classifier-free guidance scale (0.0-100.0+)
- `sampler_name`: Sampling algorithm
- `scheduler`: Noise schedule
- `denoise`: Denoising strength (0.0-1.0)
- `vae_decode`: Enable/disable automatic decoding

**Use Cases:**
- Exploring seed variations systematically with sonar
- Batch generation with consistent quality
- Streamlined workflows without separate latent nodes
- Experimenting with extreme CFG values

---

### 🗺️ Seed Topology Mapper

Generate families of mathematically related seeds for structured exploration of the latent space.

**Topology Types:**

| Type | Description | Best For |
|------|-------------|----------|
| **Golden Angle** | Seeds spaced by 137.5° golden angle | Natural, organic variations |
| **Harmonic** | Musical harmony ratios (1:2:3:4...) | Rhythmic, balanced sets |
| **Fibonacci** | Fibonacci sequence spacing | Natural progression patterns |
| **Chaos Neighbors** | Controlled chaotic spacing | Unpredictable but related results |
| **Prime Spiral** | Prime number spiral distribution | Mathematical exploration |
| **Phi Spacing** | Golden ratio (φ) based intervals | Aesthetically pleasing variations |

**Parameters:**
- `base_seed`: Starting seed for topology generation
- `topology_type`: Mathematical spacing method
- `num_seeds`: Number of seeds to generate (1-16)
- `spread`: Spacing multiplier (0.1-10.0)

**Outputs:** 16 deterministically related seeds

**Use Cases:**
- Create seed families with related characteristics
- Systematic exploration of variations
- Reproducible batch processing workflows
- Finding "neighboring" results in latent space

---

### ⏱️ Prompt Phase Splitter

Split your generation into temporal phases for progressive refinement and enhanced control.

**Phase System:**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ COMPOSITION │ ──> │   DETAIL    │ ──> │   TEXTURE   │
│   Phase     │     │   Phase     │     │   Phase     │
│  (Early)    │     │  (Middle)   │     │   (Late)    │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Parameters:**
- `composition_prompt`: Early phase - overall composition and layout
- `detail_prompt`: Middle phase - subject details and refinement  
- `texture_prompt`: Late phase - surface qualities and fine details
- `composition_weight`: Strength of composition phase (0.0-2.0)
- `detail_weight`: Strength of detail phase (0.0-2.0)
- `texture_weight`: Strength of texture phase (0.0-2.0)
- `phase_1_steps`: Steps for composition phase
- `phase_2_steps`: Steps for detail phase
- `phase_3_steps`: Steps for texture phase
- `enable_character_focus`: Optional character/subject emphasis
- `character_focus_prompt`: Subject-specific refinement
- `character_weight`: Character focus strength (0.0-2.0)

**Use Cases:**
- Separate composition from detail refinement
- Better control over generation progression
- Prevent early detail interference with composition
- Character-focused image generation
- Architectural and landscape rendering with distinct phases

---

### ⚠️ Artifact Risk Predictor

Analyze latent samples before VAE decoding to predict potential artifacts and quality issues.

**Detection Capabilities:**
- High-frequency noise patterns
- Extreme value spikes
- Abnormal distribution patterns
- Channel inconsistencies
- Statistical anomalies
- Overbakedness/Artifacts

**Risk Levels:**
- 🟢 **Low** (0.0-0.3): Clean generation expected
- 🟡 **Medium** (0.3-0.6): Minor artifacts possible
- 🔴 **High** (0.6-1.0): Significant issues likely

**Outputs:**
- `risk_score`: Numerical risk assessment (0.0-1.0)
- `risk_level`: Categorized risk level
- `latent_passthrough`: Original latent for downstream processing

**Use Cases:**
- Quality control, tells you before VAE decoding
- Before you publish an image, incase you don't know if an image has artifacts, overbakedness, etc
- Automatic bad sample filtering
- Debugging problematic generations
- Batch processing optimization

---

### 💰 Execution Cost Estimator

Real-time performance metrics and resource usage estimation for your workflows. Not 100% accurate but can help.

**Metrics Provided:**
- **VRAM Usage**: GPU memory consumption
- **Execution Time**: Expected generation duration
- **Efficiency Score**: Performance optimization rating
- **Bottleneck Analysis**: Identify performance limiters

**Parameters:**
- `model`: Model to analyze
- `width/height`: Target dimensions
- `batch_size`: Number of samples
- `steps`: Sampling steps
- Enable various analysis features

**Outputs:**
- Detailed cost breakdown
- Performance recommendations
- Resource usage predictions

**Use Cases:**
- Workflow optimization
- Hardware upgrade planning
- Batch size optimization
- Performance debugging

---

### 📦 Checkpoint Passthrough + Notes

Organize checkpoint flows with inline documentation.

**Features:**
- Pass-through routing for MODEL, CLIP, and VAE together
- Optional multiline notes field
- Zero processing overhead
- Workflow readability enhancement

**Use Cases:**
- Document your main checkpoints or whatever else you can use it for
- Create clean connection points
- Organize complex multi-checkpoint setups
- Improve workflow maintainability

---

### 📦 Box (Empty Node)

Simple organizational box for workflow documentation and structure.

**Features:**
- No inputs or outputs
- Pure visual organization
- Workflow sectioning
- Documentation anchor points

**Use Cases:**
- Visually separate workflow sections
- Add structure to complex graphs
- Create workflow "chapters"
- Improve readability

## 🔬 Technical Details

### Golden Ratio Sonar Transformation

The sonar parameter applies a sophisticated seed transformation based on the golden ratio (φ ≈ 1.618):

```
φ⁻¹ ≈ 0.618033988749895
```

**How It Works:**
1. Base hash transformation for deterministic offset
2. Golden ratio influence for values > 10
3. Conservative 10% influence factor
4. Sign preservation for negative sonar values
5. 32-bit seed space normalization

**Benefits:**
- Aesthetically pleasing variation patterns
- Deterministic and reproducible
- Smooth transitions between related seeds
- Natural-feeling exploration of latent space

### Seed Topology Mathematics

Each topology type uses distinct mathematical spacing:

- **Golden Angle**: `137.5077°` rotation spacing
- **Harmonic**: Multiply by integer ratios
- **Fibonacci**: Add Fibonacci sequence values
- **Chaos**: Logistic map with `r=3.9`
- **Prime Spiral**: Prime number intervals
- **Phi Spacing**: Exponential golden ratio growth

### Prompt Phase Timing

The temporal phase system divides the sampling process into three cognitive stages:

```
Total Steps = Phase1 + Phase2 + Phase3

Phase 1 (Composition): Steps 0 → N₁
  └─ Global structure, layout, composition

Phase 2 (Detail): Steps N₁ → N₂  
  └─ Subject refinement, feature details

Phase 3 (Texture): Steps N₂ → Total
  └─ Surface qualities, fine textures
```

## 🎓 Usage Examples

### Example 1: Systematic Seed Exploration

```
Base Seed: 42
Sonar Range: -100 to +100
Result: 200 deterministically related variations
```

Use the Seed Topology Mapper with golden_angle topology to explore a seed's neighborhood systematically.

### Example 2: Temporal Portrait Generation

```
Phase 1 (10 steps): "portrait of a person, professional photography"
Phase 2 (10 steps): "detailed facial features, expressive eyes, natural skin"  
Phase 3 (5 steps): "fine skin texture, hair detail, fabric texture"
Character Focus: "the subject's face and expression"
```

### Example 3: Quality Control Pipeline - To help see if the Image is Overbaked or has Artifacts

```
[Generate Latent] → [Artifact Risk Predictor] → [Conditional VAE Decode]
                           ↓
                    [Filter High Risk]
```

Only decode latents with acceptable risk scores.

## 🔧 Advanced Configuration

### Custom Sonar Curves

For advanced users, the sonar transformation can be tuned by modifying the influence factor in the code:

```python
golden_influence = (abs_sonar * PHI_INVERSE * 0.1) % 1.0  # 0.1 = 10% influence
golden_adjustment = int(base_noise_seed * golden_influence * 0.05)  # 5% max change
```

### Topology Spread Optimization

Different topology types respond differently to spread values:

- **Golden Angle**: 0.5-2.0 for subtle to extreme variations
- **Harmonic**: 1.0-5.0 for musical spacing
- **Fibonacci**: 0.1-1.0 for natural progressions
- **Chaos**: 0.5-1.5 for controlled chaos
- **Prime Spiral**: 1.0-3.0 for mathematical spacing
- **Phi Spacing**: 0.5-2.0 for aesthetic distributions

## 🐛 Troubleshooting

### Node Not Appearing

1. Verify installation in `ComfyUI/custom_nodes/`
2. Check console for import errors
3. Ensure PyTorch is properly installed
4. Restart ComfyUI completely

### Import Errors

Missing dependencies? Install with:
```bash
pip install torch numpy psutil
```

### Performance Issues

- Reduce batch size for VRAM constraints
- Use Cost Estimator to help identify bottlenecks
- Enable CPU offloading in ComfyUI settings
- Consider lower resolution for testing

### Unexpected Results

- Verify seed values are within valid range
- Check sonar values aren't too extreme
- Ensure prompt weights are reasonable
- Review phase step distributions
- You may get get a error while cancelling with KSampler (Arctenox's Essentials) that is expected for now and you can ignore it does nothing except cancel the KSampler like usual.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Installation

```bash
git clone https://github.com/Arctenox/Arctenoxs-Essentials_ComfyU
cd Arctenoxs-Essentials_ComfyUI
# Make your changes
# Test in ComfyUI
# Submit PR
```

## 📝 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.


## 📧 Contact
- Discord: https://discord.gg/UVXPdkgedh
- GitHub: [@Arctenox](https://github.com/Arctenox)
- Issues: [GitHub Issues](https://github.com/Arctenox/Arctenoxs-Essentials_ComfyUI/issues)

## 🗺️ Roadmap

- [ ] Additional nodes

---

**Made with ❤️ by Claude Sonnet 3.5 and Arctenox**
