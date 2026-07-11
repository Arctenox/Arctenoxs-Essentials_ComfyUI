# Arctenox's Essentials (DEPRECATED)
Note: I'll be remastering some of this with my other node pack into a new node pack.
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-Compatible-brightgreen.svg)](https://github.com/comfyanonymous/ComfyUI)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-1.3.0-orange.svg)]()

A collection of efficient workflow nodes for ComfyUI designed to streamline your generation process — covering sampling, prompting, image utilities, wildcards, metadata, and workflow organization.

---

## 📧 Contact & Support

- **Discord**: https://discord.gg/UVXPdkgedh
- **GitHub**: [@Arctenox](https://github.com/Arctenox)
- **Issues**: [GitHub Issues](https://github.com/Arctenox/Arctenoxs-Essentials_ComfyUI/issues)
- **CivitAI**: https://civitai.com/user/Arctenox

---

## 📦 Installation

### Via ComfyUI Manager (Recommended)

1. Open ComfyUI Manager
2. Search for `Arctenoxs-Essentials_ComfyUI` or `Arctenox's Essentials`
3. Click Install
4. Restart ComfyUI

### Manual Installation

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/Arctenox/Arctenoxs-Essentials_ComfyUI
```

Then restart ComfyUI.

### Requirements

- ComfyUI (latest version recommended)
- PyTorch >= 1.12.0
- Python >= 3.8
- Optional: `psutil` for CPU memory monitoring

```bash
pip install torch numpy psutil
```

---

## 🎯 Overview

Arctenox's Essentials provides a suite of nodes that integrate seamlessly into existing workflows while adding genuinely useful functionality. The pack is organized into logical categories:

- 🎲 **Sampling** — KSampler, KSampler Refiner, Seed Topology Mapper
- 🎨 **Prompting** — Prompt Styler, Wildcard nodes, CLIP Text Encode variants
- 🖼️ **Image** — Image Resize, Image Dimensions, VAE Encode + Dimensions
- ⚙️ **Conditioning** — Conditioning Strength Scaler
- 💾 **Output** — Save Image With Metadata
- 🔧 **Loaders** — Load Checkpoint, LoRA Stack Manager
- 📝 **Text** — String Concatenate, String Switch
- 🛠️ **Utilities** — Artifact Risk Predictor, Execution Cost Estimator, Checkpoint Passthrough, Box

> **Note:** If you see `"Sampling failed: . Check that all inputs are valid tensors."` when cancelling a running KSampler, this is expected and safe to ignore. It cannot be suppressed.

---

## 📚 Node Reference

---

### 🎲 KSampler (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Sampling`

A combined empty latent + KSampler node with golden ratio sonar seed transformation and intelligent handling of extreme CFG and step values. Eliminates the need for a separate empty latent node.

**Inputs**

| Input | Type | Description |
|---|---|---|
| `model` | MODEL | Model to use for sampling |
| `positive` | CONDITIONING | Positive conditioning |
| `negative` | CONDITIONING | Negative conditioning |
| `width` | INT | Image width (64–8192, step 8) |
| `height` | INT | Image height (64–8192, step 8) |
| `batch_size` | INT | Number of images (1–64) |
| `seed` | INT | Base random seed (supports negative values) |
| `sonar` | INT | Golden ratio seed transformation offset |
| `steps` | INT | Sampling steps |
| `cfg` | FLOAT | CFG scale (0.0–100.0+) |
| `sampler_name` | STRING | Sampling algorithm |
| `scheduler` | STRING | Noise schedule |
| `denoise` | FLOAT | Denoising strength (0.0–1.0) |
| `vae_decode` | BOOLEAN | Decode latent to image automatically |
| `latent_image` | LATENT *(optional)* | Input latent for img2img |
| `optional_vae` | VAE *(optional)* | VAE for decoding |

**Outputs**

| Output | Type | Description |
|---|---|---|
| `MODEL` | MODEL | Pass-through |
| `CONDITIONING+` | CONDITIONING | Pass-through |
| `CONDITIONING-` | CONDITIONING | Pass-through |
| `LATENT` | LATENT | Generated latent samples |
| `VAE` | VAE | Pass-through |
| `IMAGE` | IMAGE | Decoded image (if vae_decode enabled) |
| `seed_used` | INT | Actual seed used (post-sonar if applicable) |

**Golden Ratio Sonar**

The `sonar` parameter applies a seed transformation using the golden ratio inverse (φ⁻¹ ≈ 0.618). It produces aesthetically related seed variations in a deterministic and reproducible way. A sonar of `0` is a perfect pass-through with no effect.

- `sonar: 0` — standard generation, seed unchanged
- `sonar: 100` — subtle golden ratio influenced variation
- `sonar: -100` — variation in the opposite direction

Very large sonar values (> 1,000,000) may produce unpredictable results.

**Other Features**

- CFG values above 100 are logarithmically scaled to prevent sampling instability
- Step counts above 10,000 are intelligently capped
- Negative seeds are handled via deterministic hashing for reproducibility

---

### 🔁 KSampler Refiner (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Sampling`

A dedicated second-pass refinement node designed to pair directly with the KSampler above. Accepts an existing LATENT, optionally upscales it, then runs a refiner pass — perfect for hi-res fix workflows.

**Inputs**

| Input | Type | Description |
|---|---|---|
| `model` | MODEL | Model (pass-through from KSampler) |
| `positive` | CONDITIONING | Positive conditioning |
| `negative` | CONDITIONING | Negative conditioning |
| `latent` | LATENT | Latent from first-pass KSampler |
| `upscale_method` | SELECT | None, nearest, bilinear, bicubic, bislerp |
| `scale_factor` | FLOAT | Upscale multiplier (ignored if target W/H > 0) |
| `target_width` | INT | Target pixel width (0 = use scale_factor) |
| `target_height` | INT | Target pixel height (0 = use scale_factor) |
| `seed` | INT | Seed for refiner pass |
| `sonar` | INT | Same golden ratio sonar as main KSampler |
| `steps` | INT | Refiner sampling steps |
| `cfg` | FLOAT | CFG scale |
| `sampler_name` | STRING | Sampling algorithm |
| `scheduler` | STRING | Noise schedule |
| `denoise` | FLOAT | How much the refiner changes the latent |
| `vae_decode` | BOOLEAN | Decode inside this node |
| `vae` | VAE *(optional)* | VAE for decoding |

**Outputs:** `MODEL`, `CONDITIONING+`, `CONDITIONING-`, `LATENT`, `VAE`, `IMAGE`

**Denoise Guide**

| Range | Effect |
|---|---|
| 0.30–0.50 | Subtle hi-res fix — adds crisp detail, preserves composition |
| 0.50–0.70 | Moderate rework — allows some layout shift |
| 0.70–1.00 | Heavy rework — treats it almost like a fresh generation |

**Example Hi-Res Fix Workflow**

```
KSampler at 512×768, denoise=1.0
  └─ LATENT ──▶ KSampler Refiner
                  upscale_method=bilinear
                  scale_factor=1.5
                  denoise=0.45
                  same seed + sonar as above
                ──▶ refined image at 768×1152
```

---

### 🗺️ Seed Topology Mapper (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Sampling`

Generates up to 16 deterministically related seeds from a single base seed using mathematical spacing methods, enabling structured exploration of the latent space.

**Inputs**

| Input | Type | Description |
|---|---|---|
| `base_seed` | INT | Starting seed |
| `topology_type` | SELECT | Spacing method (see below) |
| `num_seeds` | INT | Number of seeds to generate (1–16) |
| `spread` | FLOAT | Spacing multiplier (0.1–10.0) |

**Outputs:** `seed_1` through `seed_16` (INT)

Slots beyond `num_seeds` output the base seed unchanged.

**Topology Types**

| Type | Description | Recommended Spread |
|---|---|---|
| `golden_angle` | Seeds spaced by the 137.5° golden angle | 0.5–2.0 |
| `harmonic` | Musical harmony ratios (1:2:3:4…) | 1.0–5.0 |
| `fibonacci` | Fibonacci sequence spacing | 0.1–1.0 |
| `chaos_neighbors` | Logistic map chaos (r=3.9), deterministic | 0.5–1.5 |
| `prime_spiral` | Prime number interval spacing | 1.0–3.0 |
| `phi_spacing` | Exponential golden ratio (φ) growth | 0.5–2.0 |

---

### ⏱️ Prompt Phase Splitter

**Category:** `Arctenox Essentials/Sampling`

Splits generation into three temporal phases — Composition → Detail → Texture — each with its own prompt, weight, and step count. All phases are combined into a single weighted conditioning output.

**Inputs**

| Input | Type | Default | Description |
|---|---|---|---|
| `clip` | CLIP | — | CLIP model |
| `composition_prompt` | STRING | "" | Overall layout and structure |
| `detail_prompt` | STRING | "" | Subject refinement and features |
| `texture_prompt` | STRING | "" | Surface qualities and fine detail |
| `composition_weight` | FLOAT | 1.0 | Phase 1 influence (0.0–2.0) |
| `detail_weight` | FLOAT | 1.0 | Phase 2 influence (0.0–2.0) |
| `texture_weight` | FLOAT | 1.0 | Phase 3 influence (0.0–2.0) |
| `phase_1_steps` | INT | 10 | Steps allocated to composition |
| `phase_2_steps` | INT | 10 | Steps allocated to detail |
| `phase_3_steps` | INT | 5 | Steps allocated to texture |
| `enable_character_focus` | BOOLEAN | false | Optional subject emphasis |
| `character_focus_prompt` | STRING | "" | Subject-specific addition |
| `character_weight` | FLOAT | 1.0 | Character emphasis strength |

**Outputs:** `combined_conditioning` (CONDITIONING), `total_steps` (INT)

---

### 🎨 Prompt Styler (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Prompting`

Apply one of 40+ built-in style presets to your prompt. Each preset appends positive style keywords and optional negative modifiers. Wildcard syntax (`{a|b}` and `__filename__`) is fully supported in the input prompt.

Style categories include Photography (cinematic, portrait, landscape, macro, street, fashion, product, documentary), Artistic (oil painting, watercolor, digital art, anime, sketch, comic book, concept art, abstract), Technical (photorealistic, hyperrealistic, studio lighting, natural light, dramatic lighting, soft focus, high contrast, vintage), and more.

---

### 📝 CLIP Text Encode [Prompt] (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Conditioning`

Standard CLIP text encode with wildcard support and a text pass-through for metadata wiring.

**Inputs:** `text` (STRING, multiline), `clip` (CLIP), `wildcard_seed` (INT, -1 = random)

**Outputs:** `conditioning` (CONDITIONING), `text` (STRING — original), `resolved_text` (STRING — after wildcard resolution)

Wildcard syntax supported: `{a|b|c}` picks one option, `__filename__` picks a random line from `wildcards/filename.txt`.

---

### 📝 CLIP Text Encode [Prompt + Gen] (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Conditioning`

Same as above but accepts an optional `prompt_gen_output` STRING (e.g. from a prompt generator node) and appends it to the hand-written text before encoding. Automatically deduplicates tags that already appear in the hand-written portion.

**Inputs:** `text`, `clip`, `wildcard_seed`, `prompt_gen_output` *(optional)*

**Outputs:** `conditioning`, `text` (original), `resolved_text` (final encoded text)

---

### ⚙️ Conditioning Strength Scaler (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Conditioning`

Multiply a CONDITIONING tensor by a scalar weight before passing it to a sampler. Useful for dampening or boosting prompts globally without editing the prompt text.

**Inputs:** `conditioning` (CONDITIONING), `strength` (FLOAT, -4.0–4.0, default 1.0)

**Output:** `conditioning` (CONDITIONING)

A strength of `1.0` is a perfect pass-through with no computational overhead. Values above 1.0 amplify; below 1.0 dampen; 0.0 removes guidance; negative values invert guidance direction.

---

### 🃏 Wildcard Processor (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Wildcards`

Resolve `__wildcard__` file tokens and `{a|b|c}` inline groups in any prompt string.

**Inputs:** `prompt` (STRING), `seed` (INT, -1 = random)

**Outputs:** `resolved_prompt` (STRING), `original_prompt` (STRING), `seed_used` (INT)

---

### 🃏 Wildcard Picker (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Wildcards`

Pick a single random entry from a wildcard file. The dropdown is populated automatically from all `.txt` files found in your wildcard directories.

**Inputs:** `wildcard_name` (dropdown), `seed` (INT, -1 = random)

**Outputs:** `picked_value` (STRING), `seed_used` (INT)

---

### 🃏 Wildcard Stack (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Wildcards`

Stack up to four wildcard-aware prompt segments, resolve all tokens in each, and join the non-empty results with a configurable separator.

**Inputs:** `prompt_1` (required), `prompt_2`–`prompt_4` *(optional)*, `seed` (INT), `separator` (STRING, default `", "`)

**Outputs:** `resolved_prompt` (STRING), `seed_used` (INT)

---

### 🔧 String Concatenate (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Text`

Join up to four STRING inputs with a configurable separator. Empty or unconnected inputs are silently skipped — no trailing separators. Use `\n` in the separator field for newlines.

**Inputs:** `separator` (STRING), `string_a`–`string_d` *(optional)*

**Output:** `result` (STRING)

---

### 🔧 String Switch (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Text`

Toggle between two STRING inputs with a boolean. Useful for swapping prompt variants, LoRA lists, or model names without rewiring nodes.

**Inputs:** `use_string_a` (BOOLEAN), `string_a` (STRING), `string_b` (STRING)

**Outputs:** `selected` (STRING), `discarded` (STRING)

---

### 🖼️ Image Resize (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Image`

Resize an image with four fit modes. Outputs the resized image and its actual pixel dimensions as INT values for easy downstream wiring.

**Inputs:** `image` (IMAGE), `width` (INT), `height` (INT), `mode` (SELECT), `interpolation` (SELECT)

**Outputs:** `image` (IMAGE), `width` (INT), `height` (INT)

**Modes**

| Mode | Behaviour |
|---|---|
| `stretch` | Exact target size, ignores aspect ratio |
| `fit` | Maintains aspect ratio, fits within target (may letterbox) |
| `fill` | Maintains aspect ratio, covers target (may crop edges) |
| `pad` | Same as fit, then pads to exact target size with black |

**Interpolation options:** `bilinear`, `bicubic`, `nearest`, `lanczos` (implemented as bicubic)

---

### 🖼️ Image Dimensions (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Image`

Read width, height, and batch size from any IMAGE tensor and output them as INT values. Eliminates the need to hardcode dimensions in downstream nodes.

**Input:** `image` (IMAGE)

**Outputs:** `image` (IMAGE, pass-through), `width` (INT), `height` (INT), `batch_size` (INT), `dimensions_str` (STRING, e.g. `"1024x1280 (batch: 1)"`)

---

### 🔷 VAE Encode + Dimensions (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Latent`

A VAE encode wrapper that also outputs the source image's pixel width and height as INT values, eliminating the need for a separate Image Dimensions node when feeding into a KSampler Refiner or Cost Estimator.

**Inputs:** `image` (IMAGE), `vae` (VAE), `tile_encode` (BOOLEAN, optional — tiled encode for large images to reduce VRAM)

**Outputs:** `latent` (LATENT), `width` (INT), `height` (INT)

---

### ⚠️ Artifact Risk Predictor (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Utilities`

Analyze a latent before VAE decoding to predict potential quality issues. Useful for filtering bad samples in batch workflows without paying the cost of a full decode.

**Input:** `latent` (LATENT)

**Outputs:** `risk_score` (FLOAT, 0.0–1.0), `risk_level` (STRING), `latent_passthrough` (LATENT)

**Risk Levels**

| Level | Range | Meaning |
|---|---|---|
| Low | 0.0–0.3 | Clean generation expected |
| Medium | 0.3–0.6 | Minor artifacts possible, generally acceptable |
| High | 0.6–1.0 | Significant issues likely, consider regenerating |

Detects high-frequency noise, extreme value spikes, abnormal distributions, channel inconsistencies, and signs of overprocessing. This is a heuristic — not 100% accurate.

---

### 💰 Execution Cost Estimator (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Utilities`

Estimate VRAM usage, generation time, and workflow efficiency before running a full generation. Useful for planning batch sizes and avoiding OOM errors.

**Inputs:** `model` (MODEL), `width` (INT), `height` (INT), `batch_size` (INT), `steps` (INT), plus optional analysis toggles (BOOLEAN)

**Outputs:** `cost_info` (STRING), `vram_estimate` (FLOAT, GB), `time_estimate` (FLOAT, seconds), `efficiency_score` (FLOAT)

Note: Estimates are approximate and intended as guidance, not guarantees.

---

### 💾 Save Image With Metadata (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Output`

Save images with complete generation parameters embedded in metadata. Compatible with the A1111/Automatic1111 metadata format for Civitai automatic resource detection.

**Inputs:** `images` (IMAGE), `filename_prefix` (STRING), plus optional fields for `subfolder`, `format` (png/jpeg/webp), `quality`, `embed_workflow`, `positive_prompt`, `negative_prompt`, `seed`, `steps`, `cfg`, `sampler`, `scheduler`, `model_name`, `model_hash`, and `loras`

Features date tokens in filename prefix (e.g. `%date:yyyy-MM-dd%`), subfolder organization, and full SHA256 hash embedding for Civitai LoRA resource linking.

---

### 🔄 Load Checkpoint (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Loaders`

Standard checkpoint loader with additional STRING outputs for the model name and a SHA256 AutoHash — ready to wire directly into Save Image With Metadata for Civitai resource detection.

**Input:** `ckpt_name` (dropdown)

**Outputs:** `model` (MODEL), `clip` (CLIP), `vae` (VAE), `model_name` (STRING), `model_hash` (STRING — first 10 chars of SHA256, AutoHash format)

Hash results are cached by file path, mtime, and size to avoid recalculating on every run.

---

### 🗂️ LoRA Stack Manager (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Loaders`

> ⚠️ **Work in Progress** — This node is functional but not yet complete. Additional features and polish are planned for a future release.

Stack up to 10 LoRAs in a single node. Each slot has an enable/disable toggle and separate `model_strength` and `clip_strength` sliders. Eliminates the need to chain 10 individual Load LoRA nodes.

**Inputs:** `model` (MODEL), `clip` (CLIP), then for each of the 10 slots: a LoRA dropdown, an enabled toggle, `model_strength` (FLOAT), `clip_strength` (FLOAT)

**Outputs:** `model` (MODEL), `clip` (CLIP), `active_loras` (STRING — formatted as `<lora:name:strength>` entries for wiring into Save Image With Metadata)

Slots set to `"None"` or disabled are silently skipped. Slots where both strengths are `0.0` are also skipped.

---

### 📦 Checkpoint Passthrough + Notes (Arctenox's Essentials)

**Category:** `Arctenox Essentials/Utilities`

Pass MODEL, CLIP, and VAE together through a single node with an optional notes field for workflow documentation. Zero processing overhead.

**Inputs:** `model` (MODEL), `clip` (CLIP), `vae` (VAE), `notes` (STRING, optional)

**Outputs:** `model` (MODEL), `clip` (CLIP), `vae` (VAE)

---

### 📦 Box (Empty Node)

**Category:** `Arctenox Essentials/Utilities`

A visual organization node with no inputs or outputs. Use it to section off parts of your workflow, add labels, or create visual groupings.

---

## 🃏 Wildcards System

Wildcards are supported in the CLIP Text Encode nodes, Prompt Styler, and the dedicated Wildcard nodes. Place `.txt` files in either of these directories:

```
ComfyUI/custom_nodes/Arctenoxs-Essentials_ComfyUI/wildcards/
ComfyUI/wildcards/
```

**Syntax:**

- `{cat|dog|bird}` — picks one option at random
- `__hair_color__` — picks a random line from `wildcards/hair_color.txt`
- Both can be nested and combined freely
- Lines starting with `#` in wildcard files are treated as comments and ignored

Use `wildcard_seed = -1` for a different result each run, or set a fixed integer for reproducible outputs.

The autocomplete API (`/arctenox/wildcards`) serves all available wildcards as JSON to the browser, and the e621 tag proxy (`/arctenox/e621_tags?q=<query>`) provides tag autocomplete with a 30-minute server-side cache.

---

## 🛠️ Advanced Configuration

### Sonar Influence Factor

The golden ratio influence applied by the sonar parameter can be tuned in `ArctenoxEssentials_KSampler.py`:

```python
golden_influence  = (abs_sonar * PHI_INVERSE * 0.1) % 1.0   # 10% influence
golden_adjustment = int(base_noise_seed * golden_influence * 0.05)  # 5% max change
```

Increase these percentages for stronger sonar effects, decrease for subtler ones.

### Topology Spread Optimization

| Topology | Optimal Spread | Notes |
|---|---|---|
| golden_angle | 0.5–2.0 | Subtle to significant variation |
| harmonic | 1.0–5.0 | Musical spacing |
| fibonacci | 0.1–1.0 | Natural progressions |
| chaos | 0.5–1.5 | Controlled unpredictability |
| prime_spiral | 1.0–3.0 | Mathematical distribution |
| phi_spacing | 0.5–2.0 | Aesthetic distribution |

---

## 🛟 Troubleshooting

**Node not appearing after install** — Verify the folder is in `ComfyUI/custom_nodes/`, check the ComfyUI console for import errors, and try clearing your browser cache.

**Import errors** — Run `pip install torch numpy psutil`.

**Sampling cancel error** — The `"Sampling failed: ."` message on cancel is expected and harmless.

**Unexpected results from sonar** — Avoid sonar values above `±1,000,000`.

**LoRA Stack not loading a LoRA** — Check that the file exists in your LoRA directory. A slot is silently skipped if the file is missing, disabled, or both strengths are zero.

**Wildcard Picker showing no options** — Ensure `.txt` files exist in one of the two supported wildcard directories and contain at least one non-comment line.

---

## 🤝 Contributing

Pull requests are welcome. For major changes please open an issue first to discuss what you'd like to change.

```bash
git clone https://github.com/Arctenox/Arctenoxs-Essentials_ComfyUI
cd Arctenoxs-Essentials_ComfyUI
# Make your changes and test in ComfyUI
# Submit PR
```

---

## 📄 License

GNU General Public License v3.0 — see [LICENSE](LICENSE) for details.

---

## 🗺️ Roadmap

- [ ] Complete LoRA Stack Manager
- [ ] Additional nodes as ideas arise
- [ ] Workflow templates

---

*Version 1.3.0 — Made with ❤️ by Arctenox*
