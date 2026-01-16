# ZImage Vector Studio

AI-powered vector graphics generator for macOS. Create production-ready SVG files, edge maps, and depth maps from text prompts.

![Platform](https://img.shields.io/badge/platform-macOS-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## What It Does

ZImage Vector Studio generates **clean, scalable SVG files** and auxiliary maps directly from text descriptions. The system is optimized end-to-end for vector output:

1. **Prompt Enhancement** - Automatically optimizes prompts for flat colors, hard edges, and clean paths
2. **AI Generation** - Z-Image-Turbo creates images optimized for vectorization
3. **FFmpeg Preprocessing** - Contrast, levels, and edge enhancement for cleaner paths
4. **Smart Conversion** - VTracer converts to SVG with preset-tuned parameters
5. **Auxiliary Outputs** - Generate Canny edges, depth maps, and heat maps

## Use Cases

- **Logos** - Minimalist brand marks, wordmarks, icon logos
- **Icons** - App icons, UI elements, pictograms
- **Illustrations** - Flat vector art, infographics, diagrams
- **Silhouettes** - Bold shapes, stencil-ready designs
- **Badges** - Emblems, stamps, certification marks
- **Patterns** - Seamless geometric and abstract patterns

## Requirements

- macOS 14.0+ with Apple Silicon (M1/M2/M3)
- [ZImageCLI](https://github.com/mzbac/Z-Image.swift) installed
- Python 3.10+
- vtracer: `cargo install vtracer`
- FFmpeg: `brew install ffmpeg` (for preprocessing and auxiliary outputs)

## Quick Start

```bash
git clone https://github.com/twalderman/zimage-studio.git
cd zimage-studio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:8000

## Vector Generation

### Basic SVG Generation

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "minimalist coffee cup logo",
    "width": 512,
    "height": 512,
    "steps": 16,
    "svg": true,
    "svg_preset": "logo"
  }'
```

### SVG Presets

| Preset | Best For | Characteristics |
|--------|----------|-----------------|
| `logo` | Logos, icons, flat graphics | Cutout paths, polygon mode, aggressive simplification |
| `default` | General purpose | Balanced quality and file size |
| `detailed` | Complex illustrations | High fidelity, more paths |
| `simplified` | Clean minimal output | Reduced detail, small files |
| `bw` | Black and white designs | Binary color mode |

### Image Preprocessing

FFmpeg-based preprocessing improves vectorization quality:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "geometric abstract logo",
    "svg": true,
    "preprocess": {
      "contrast": 1.3,
      "brightness": 0.05,
      "saturation": 1.2,
      "sharpen": true
    }
  }'
```

| Option | Range | Effect |
|--------|-------|--------|
| `contrast` | 0.5-2.0 | Separates colors for cleaner paths |
| `brightness` | -0.5-0.5 | Adjusts overall luminance |
| `saturation` | 0.0-2.0 | Intensifies color distinction |
| `sharpen` | true/false | Enhances edges before vectorization |
| `posterize` | 2-8 | Reduces color levels (great for logos) |

## Auxiliary Outputs

Generate control maps for advanced workflows:

### Canny Edge Detection

Extract clean edge maps for ControlNet or vector tracing:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "architectural blueprint building",
    "outputs": ["png", "svg", "canny"]
  }'
```

### Depth Maps

Generate depth estimation for 3D workflows and parallax effects:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "layered mountain landscape",
    "outputs": ["png", "depth"]
  }'
```

### Heat Maps

Visualize attention/saliency for design analysis:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "product showcase",
    "outputs": ["png", "heat"]
  }'
```

### Output Types Reference

| Output | Format | Use Case |
|--------|--------|----------|
| `png` | Raster | Base generated image |
| `svg` | Vector | Scalable graphics, print, web |
| `canny` | PNG | Edge detection, ControlNet input |
| `depth` | PNG | 3D compositing, parallax, occlusion |
| `heat` | PNG | Attention analysis, design critique |

### Prompt Enhancement

Transform any idea into a vector-optimized prompt:

```bash
curl -X POST http://localhost:8000/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "phoenix bird",
    "style": "logo"
  }'
```

**Enhancement Styles:**

| Style | Output Description |
|-------|-------------------|
| `logo` | Minimalist logo, clean edges, single mark |
| `icon` | Simple pictogram, single color, UI-ready |
| `illustration` | Flat vector art, limited palette |
| `silhouette` | Bold black shape, white background |
| `badge` | Circular emblem, vintage style |

The enhancer automatically adds:
- `HIGH CONTRAST, bold distinct colors, solid fills`
- `flat vector illustration, hard edges`
- `no gradients, no shadows, no soft edges`
- Style-specific optimizations

## Vector Templates

Pre-configured templates for common vector formats:

```bash
# List all templates
curl http://localhost:8000/templates

# Apply template to subject
curl -X POST "http://localhost:8000/templates/logo_template/apply?subject=mountain"
```

| Template | Size | Description |
|----------|------|-------------|
| `logo_template` | 512x512 | Minimalist logo mark |
| `icon_template` | 256x256 | Simple app/UI icon |
| `illustration_template` | 1024x1024 | Flat vector illustration |
| `silhouette_template` | 512x512 | Black silhouette shape |
| `badge_template` | 512x512 | Circular badge/emblem |
| `infographic_template` | 800x600 | Data visualization element |

## Prompt Library

Curated prompts optimized for vector output:

```bash
# Browse categories
curl http://localhost:8000/prompts

# Get prompts by category
curl http://localhost:8000/prompts/vector_logos
```

**Categories:**
- `vector_logos` - Tech, startup, medical, eco, finance logos
- `vector_icons` - App icons, UI elements, emoji-style
- `vector_illustrations` - Characters, isometric, infographic elements
- `vector_patterns` - Geometric, abstract seamless patterns
- `vector_symbols` - Monograms, abstract marks, badges

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/generate` | POST | Generate image with SVG, preprocessing, and auxiliary outputs |
| `/preprocess` | POST | Apply FFmpeg filters to existing image |
| `/extract/canny` | POST | Extract Canny edges from image |
| `/extract/depth` | POST | Generate depth map from image |
| `/extract/heat` | POST | Generate heat/saliency map from image |
| `/enhance` | POST | Optimize prompt for vector output |
| `/enhance/styles` | GET | List enhancement styles |
| `/templates` | GET | List vector templates |
| `/templates/{id}/apply` | POST | Apply template to subject |
| `/prompts` | GET | List prompt categories |
| `/prompts/{category}` | GET | Get prompts in category |
| `/history` | GET | Generation history |
| `/loras` | GET/POST | Manage LoRA files |
| `/mcp` | POST | MCP JSON-RPC endpoint |

## MCP Integration

Connect to Claude or other AI agents:

```json
{
  "mcpServers": {
    "zimage-vector": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**Tools:**
- `generate` - Generate vector graphics from prompts
- `list_history` - Browse recent generations

## Tips for Best Results

1. **Use specific style keywords** - "minimalist", "flat", "geometric", "simple"
2. **Limit colors** - "3-color palette", "monochrome", "two-tone"
3. **Describe shapes** - "circular", "angular", "organic curves"
4. **Avoid photorealism** - Skip "realistic", "photograph", "3D render"
5. **Match preset to content** - Use `logo` for simple marks, `detailed` for illustrations

## How It Works

```
Text Prompt
    │
    ▼
┌─────────────────┐
│ Prompt Enhancer │ ← Adds vector-optimized keywords
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Z-Image-Turbo  │ ← 6B parameter diffusion model
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     FFmpeg      │ ← Contrast, levels, edge enhancement
└────────┬────────┘
         │
    ┌────┴────┬─────────┬─────────┐
    ▼         ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│VTracer│ │ Canny │ │ Depth │ │ Heat  │
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
    │         │         │         │
    ▼         ▼         ▼         ▼
   SVG      Edges      Depth    Saliency
            (PNG)      (PNG)     (PNG)
```

## Credits

- [ZImageCLI](https://github.com/mzbac/Z-Image.swift) - Fast image generation on Apple Silicon
- [Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo) - Distilled FLUX model
- [VTracer](https://github.com/visioncortex/vtracer) - Raster to vector conversion
- [FFmpeg](https://ffmpeg.org/) - Image preprocessing and filtering
- Inspired by [z-image-studio](https://github.com/iconben/z-image-studio)

## License

MIT License
