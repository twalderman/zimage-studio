# Zimage Studio

A web-based interface for ZImageCLI with generation history, SVG support, and MCP integration.

![Platform](https://img.shields.io/badge/platform-macOS-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

- **Web UI** - Modern browser-based interface for image generation
- **Generation History** - SQLite-backed history with search
- **SVG Export** - Automatic vector conversion with multiple presets
- **MCP Server** - AI agent integration via Model Context Protocol
- **LoRA Support** - Upload and manage LoRA models

## Requirements

- macOS 14.0+ with Apple Silicon
- [ZImageCLI](https://github.com/mzbac/Z-Image.swift) installed
- Python 3.10+
- vtracer (for SVG conversion): `cargo install vtracer`

## Installation

```bash
# Clone the repository
git clone https://github.com/twalderman/zimage-studio.git
cd zimage-studio

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Activate virtual environment
source .venv/bin/activate

# Start the server
python app.py
```

Open http://localhost:8000 in your browser.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/generate` | POST | Generate image |
| `/history` | GET | List generation history |
| `/models` | GET | List available models |
| `/loras` | GET/POST | Manage LoRA files |
| `/mcp` | POST | MCP JSON-RPC endpoint |

### Generate Image

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a beautiful sunset over mountains",
    "width": 1024,
    "height": 1024,
    "steps": 16,
    "svg": true,
    "svg_preset": "default"
  }'
```

### SVG Presets

| Preset | Use Case | Output |
|--------|----------|--------|
| `default` | Balanced quality/size | Medium |
| `logo` | Flat colors, icons | Smallest |
| `detailed` | Complex images | Largest |
| `simplified` | Clean output | Small |
| `bw` | Black and white | Varies |

## MCP Integration

The server includes an MCP endpoint for AI agent integration. Add to your Claude configuration:

```json
{
  "mcpServers": {
    "zimage-studio": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Available tools:
- `generate` - Generate images from text prompts
- `list_history` - List recent generations

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ZIMAGE_DATA_DIR` | Data directory | `~/.zimage-server` |

## Credits

- Inspired by [z-image-studio](https://github.com/iconben/z-image-studio)
- Powered by [ZImageCLI](https://github.com/mzbac/Z-Image.swift) and [Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
- SVG conversion via [vtracer](https://github.com/visioncortex/vtracer)

## License

MIT License
