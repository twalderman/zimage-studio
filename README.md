# AIbstraction Studio

AI-powered vector graphics generator for macOS. Create production-ready SVG files, edge maps, and depth maps from text prompts or images.

![Platform](https://img.shields.io/badge/platform-macOS-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## What It Does

AIbstraction Studio generates **clean, scalable SVG files** and auxiliary maps from text prompts or image inputs. Built on mflux for native Apple Silicon performance:

1. **FLUX.1 Models** - schnell (fast), dev (quality), dev-krea (face consistency)
2. **Image Input** - Vectorize photos, img2img refinement, face references
3. **Kontext Transform** - Edit images with natural language
4. **Prompt Enhancement** - Automatically optimizes prompts for vector output
5. **FFmpeg Preprocessing** - Contrast, levels, and edge enhancement
6. **Smart Conversion** - VTracer converts to SVG with preset-tuned parameters
7. **Auxiliary Outputs** - Canny edges, depth maps, heat maps

## Use Cases

### Vector Graphics
- **Logos** - Minimalist brand marks, wordmarks, icon logos
- **Icons** - App icons, UI elements, pictograms
- **Illustrations** - Flat vector art, infographics, diagrams
- **Silhouettes** - Bold shapes, stencil-ready designs
- **Badges** - Emblems, stamps, certification marks
- **Patterns** - Seamless geometric and abstract patterns

### Control Maps
- **Canny Edges** - Clean line extraction for ControlNet, tracing templates, coloring books
- **Depth Maps** - 3D compositing, parallax effects, occlusion masks, AR/VR assets
- **Heat Maps** - Attention analysis, design critique, visual hierarchy validation

### Image Transformation
- **Style Transfer** - Convert photos to illustrations, paintings, sketches
- **Character Consistency** - Generate multiple poses with same face (dev-krea)
- **Image Editing** - Natural language edits via Kontext ("add sunset lighting")
- **Batch Processing** - Apply consistent style across image sets

### Creative Workflows
- **Concept Art** - Rapid iteration with schnell (2 steps), polish with dev
- **Asset Generation** - Game sprites, UI components, marketing materials
- **Photo to Vector** - Vectorize logos, traced artwork, scanned drawings
- **Preprocessing** - Enhance images before vectorization (contrast, posterize)

## Requirements

- macOS 14.0+ with Apple Silicon (M1/M2/M3)
- Python 3.10+
- [mflux](https://github.com/filipstrand/mflux) - FLUX.1 models for Apple Silicon
- vtracer: `cargo install vtracer`
- FFmpeg: `brew install ffmpeg`

**Optional:**
- [ZImageCLI](https://github.com/mzbac/Z-Image.swift) - Ultra-fast generation (4 steps)

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

## Generation Models

Choose the right model for your task:

| Model | Steps | Time | Quality | Best For |
|-------|-------|------|---------|----------|
| `zimage` | 4 | ~30 sec | Good | Ultra-fast vectors, logos |
| `schnell` | 2-4 | ~30 sec | Good | Fast iterations, concepts |
| `dev` | 20-30 | ~7 min | Excellent | Final renders, complex scenes |
| `dev-krea` | 20 | ~7 min | Excellent | Face consistency, character work |

**For vector work:** `zimage` (4 steps) and `schnell` (2 steps) both produce excellent results with minimal generation time.

### Text-to-Image

```bash
# Ultra-fast with ZImage (4 steps)
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "minimalist mountain logo, flat vector style",
    "model": "zimage",
    "steps": 4,
    "width": 1024,
    "height": 1024,
    "svg": true,
    "svg_preset": "logo"
  }'

# Fast with schnell (2 steps for vectors)
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "geometric icon, simple shapes, bold colors",
    "model": "schnell",
    "steps": 2,
    "width": 1024,
    "height": 1024,
    "svg": true,
    "svg_preset": "logo"
  }'

# High quality with dev
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "detailed phoenix illustration, bold colors, clean lines",
    "model": "dev",
    "steps": 25,
    "width": 1024,
    "height": 1024,
    "svg": true,
    "svg_preset": "detailed"
  }'
```

### Image-to-Image

Use an existing image as a starting point:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "convert to flat vector illustration style, limited color palette",
    "model": "dev",
    "image": "/path/to/photo.png",
    "image_strength": 0.6,
    "steps": 20,
    "svg": true
  }'
```

| Strength | Effect |
|----------|--------|
| 0.3-0.4 | Light guidance, more creative freedom |
| 0.5-0.6 | Balanced (recommended for style transfer) |
| 0.7-0.8 | Strong adherence to input |
| 0.9-1.0 | Minimal changes, refinement only |

### Face-Consistent Generation

Generate images with consistent facial features using dev-krea:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "portrait in flat illustration style, bold outlines",
    "model": "dev-krea",
    "face_reference": "/path/to/face.png",
    "image_strength": 0.7,
    "steps": 20,
    "width": 1024,
    "height": 1536,
    "svg": true,
    "svg_preset": "detailed"
  }'
```

### LoRA Support

Apply style LoRAs to any generation:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "corporate logo design",
    "model": "dev",
    "lora": "/path/to/style.safetensors",
    "lora_scale": 0.8,
    "steps": 25,
    "svg": true
  }'
```

## Image Transformation (Kontext)

Transform existing images with natural language using mflux-generate-kontext:

```bash
curl -X POST http://localhost:8000/transform \
  -H "Content-Type: application/json" \
  -d '{
    "image": "/path/to/input.png",
    "prompt": "convert to woodcut print style",
    "strength": 0.7,
    "steps": 8,
    "svg": true
  }'
```

**Transformation Examples:**
- "convert to line art with clean edges"
- "make it look like a vintage poster"
- "simplify to 3 flat colors"
- "transform to isometric illustration"
- "add bold black outlines"
- "change to sunset lighting"

## Vectorize Existing Images

Convert any raster image directly to SVG:

```bash
# Basic conversion
curl -X POST http://localhost:8000/vectorize \
  -F "image=@artwork.png" \
  -F "preset=detailed"

# With preprocessing for cleaner results
curl -X POST http://localhost:8000/vectorize \
  -F "image=@logo_scan.jpg" \
  -F "preset=logo" \
  -F "preprocess[contrast]=1.4" \
  -F "preprocess[posterize]=4"
```

### SVG Presets

| Preset | Best For | Characteristics |
|--------|----------|-----------------|
| `logo` | Logos, icons, flat graphics | Cutout paths, aggressive simplification |
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
    "model": "schnell",
    "svg": true,
    "preprocess": {
      "contrast": 1.3,
      "brightness": 0.05,
      "saturation": 1.2,
      "sharpen": true,
      "posterize": 6
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

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "architectural blueprint",
    "model": "schnell",
    "outputs": ["png", "svg", "canny"]
  }'
```

### Depth Maps

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "layered mountain landscape",
    "model": "dev",
    "outputs": ["png", "depth"]
  }'
```

### Heat Maps

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "product showcase",
    "model": "schnell",
    "outputs": ["png", "heat"]
  }'
```

| Output | Format | Use Case |
|--------|--------|----------|
| `png` | Raster | Base generated image |
| `svg` | Vector | Scalable graphics, print, web |
| `canny` | PNG | Edge detection, ControlNet input |
| `depth` | PNG | 3D compositing, parallax, occlusion |
| `heat` | PNG | Attention analysis, design critique |

## Prompt Enhancement

Automatically optimize any prompt for vector output:

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

### Generation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/generate` | POST | Generate from prompt with FLUX models |
| `/vectorize` | POST | Convert raster image to SVG |
| `/transform` | POST | Transform image with Kontext |

### Processing

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/preprocess` | POST | Apply FFmpeg filters to image |
| `/extract/canny` | POST | Extract Canny edge map |
| `/extract/depth` | POST | Generate depth map |
| `/extract/heat` | POST | Generate heat/saliency map |

### Prompts & Templates

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/enhance` | POST | Optimize prompt for vector output |
| `/enhance/styles` | GET | List enhancement styles |
| `/templates` | GET | List vector templates |
| `/templates/{id}/apply` | POST | Apply template to subject |
| `/prompts` | GET | List prompt categories |
| `/prompts/{category}` | GET | Get prompts in category |

### Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/history` | GET | Generation history |
| `/loras` | GET/POST | Manage LoRA files |
| `/models` | GET | List available FLUX models |
| `/mcp` | POST | MCP JSON-RPC endpoint |

## MCP Integration

Connect to Claude or other AI agents:

```json
{
  "mcpServers": {
    "aibstraction": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**Tools:**
- `generate` - Generate vector graphics from prompts
- `vectorize` - Convert raster images to SVG
- `transform` - Transform images with natural language
- `list_history` - Browse recent generations

## Tips for Best Results

1. **Use specific style keywords** - "minimalist", "flat", "geometric", "simple"
2. **Limit colors** - "3-color palette", "monochrome", "two-tone"
3. **Describe shapes** - "circular", "angular", "organic curves"
4. **Avoid photorealism** - Skip "realistic", "photograph", "3D render"
5. **Match preset to content** - Use `logo` for simple marks, `detailed` for illustrations
6. **Use schnell for drafts** - Iterate quickly, then render final with dev
7. **Preprocess for logos** - Posterize (4-6) + high contrast for cleanest paths

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                        INPUT                                 │
├─────────────────────────────────────────────────────────────┤
│  Text Prompt          Image File           Face Reference   │
│       │                    │                     │          │
│       ▼                    │                     │          │
│  ┌─────────────┐           │                     │          │
│  │   Enhance   │           │                     │          │
│  └──────┬──────┘           │                     │          │
└─────────┼──────────────────┼─────────────────────┼──────────┘
          │                  │                     │
          ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    GENERATION BACKEND                        │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│   ZImage    │   schnell   │     dev     │     dev-krea      │
│   4 steps   │  2-4 steps  │  20-30 steps│     20 steps      │
│   ~30 sec   │   ~30 sec   │    ~7 min   │      ~7 min       │
│ (ultra-fast)│   (fast)    │  (quality)  │ (face consistent) │
└──────┬──────┴──────┬──────┴──────┬──────┴─────────┬─────────┘
          │                  │                    │
          └──────────────────┼────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    PREPROCESSING                             │
├─────────────────────────────────────────────────────────────┤
│  FFmpeg: contrast, brightness, saturation, sharpen, posterize│
└────────────────────────────┬────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    VTracer      │ │  Canny / Depth  │ │    Kontext      │
│  (Vectorize)    │ │  / Heat Extract │ │  (Transform)    │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                        OUTPUT                                │
├─────────────────────────────────────────────────────────────┤
│      SVG         PNG        Canny       Depth       Heat    │
│    (vector)    (raster)    (edges)     (3D)      (saliency) │
└─────────────────────────────────────────────────────────────┘
```

## Performance

| Model | Steps | 1024x1024 | 1024x1536 | Memory |
|-------|-------|-----------|-----------|--------|
| zimage | 4 | ~30 sec | ~45 sec | ~8 GB |
| schnell | 2 | ~30 sec | ~45 sec | ~16 GB |
| schnell | 4 | ~1 min | ~1.5 min | ~16 GB |
| dev | 25 | ~5 min | ~7 min | ~24 GB |
| dev-krea | 20 | ~5 min | ~7 min | ~24 GB |

*Benchmarks on M3 Max*

## Credits

- [mflux](https://github.com/filipstrand/mflux) - FLUX.1 models for Apple Silicon
- [ZImageCLI](https://github.com/mzbac/Z-Image.swift) - Ultra-fast generation on Apple Silicon
- [FLUX.1](https://blackforestlabs.ai/) - Black Forest Labs diffusion models
- [VTracer](https://github.com/visioncortex/vtracer) - Raster to vector conversion
- [FFmpeg](https://ffmpeg.org/) - Image preprocessing and filtering

## License

MIT License
