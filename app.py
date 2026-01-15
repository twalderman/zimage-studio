#!/usr/bin/env python3
"""
ZImageCLI Web Server
A FastAPI-based web interface for ZImageCLI with generation history and MCP support.
Inspired by z-image-studio (https://github.com/iconben/z-image-studio)
"""

import asyncio
import json
import os
import re
import sqlite3
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


# =============================================================================
# PROMPT LIBRARY - Curated prompts organized by category
# =============================================================================

PROMPT_LIBRARY = {
    "vector_logos": {
        "name": "Vector Logos",
        "description": "Logo designs optimized for SVG conversion",
        "svg_preset": "logo",
        "prompts": [
            {
                "id": "tech_logo",
                "name": "Tech Company Logo",
                "prompt": "minimalist tech company logo, geometric shapes, HIGH CONTRAST, bold solid colors on pure white background, flat vector design, clean sharp edges, no gradients, no shadows, professional corporate identity",
                "negative_prompt": "gradients, shadows, soft edges, photorealistic, 3d, texture, noise, blurry, complex details"
            },
            {
                "id": "startup_logo",
                "name": "Startup Logo",
                "prompt": "modern startup logo, abstract geometric symbol, HIGH CONTRAST, 2-3 bold colors maximum, pure white background, flat design, sharp clean lines, minimalist, scalable vector style",
                "negative_prompt": "gradients, shadows, realistic, complex, detailed, textured, 3d effects, soft edges"
            },
            {
                "id": "medical_logo",
                "name": "Medical/Healthcare Logo",
                "prompt": "professional medical healthcare logo, clean geometric design, HIGH CONTRAST, blue and white color scheme, pure white background, flat vector style, sharp edges, minimalist symbol, corporate medical identity",
                "negative_prompt": "gradients, shadows, photorealistic, complex details, soft edges, textured"
            },
            {
                "id": "eco_logo",
                "name": "Eco/Nature Logo",
                "prompt": "eco-friendly nature logo, leaf or tree symbol, HIGH CONTRAST, green and white, pure white background, flat vector design, clean geometric shapes, minimalist environmental branding",
                "negative_prompt": "gradients, shadows, realistic leaves, complex details, photorealistic, 3d"
            },
            {
                "id": "finance_logo",
                "name": "Finance Logo",
                "prompt": "professional finance banking logo, abstract geometric symbol, HIGH CONTRAST, navy blue and gold, pure white background, flat vector design, sharp clean lines, trustworthy corporate identity",
                "negative_prompt": "gradients, shadows, complex details, photorealistic, 3d effects"
            }
        ]
    },
    "vector_icons": {
        "name": "Vector Icons",
        "description": "Simple icons for UI/UX and applications",
        "svg_preset": "logo",
        "prompts": [
            {
                "id": "app_icon",
                "name": "App Icon",
                "prompt": "simple app icon, single bold symbol, HIGH CONTRAST, solid flat color on white background, clean geometric shape, minimal design, vector style, sharp edges",
                "negative_prompt": "gradients, shadows, realistic, detailed, textured, 3d, complex"
            },
            {
                "id": "ui_icon_set",
                "name": "UI Icon",
                "prompt": "UI interface icon, simple geometric symbol, HIGH CONTRAST, single solid color, white background, flat design, clean lines, pixel-perfect vector style",
                "negative_prompt": "gradients, shadows, realistic, complex, detailed, 3d effects"
            },
            {
                "id": "emoji_style",
                "name": "Emoji Style Icon",
                "prompt": "cute emoji style icon, simple round design, HIGH CONTRAST, bold flat colors, white background, cartoon vector style, clean outlines, friendly expression",
                "negative_prompt": "gradients, shadows, realistic, complex shading, 3d, photorealistic"
            }
        ]
    },
    "vector_illustrations": {
        "name": "Vector Illustrations",
        "description": "Flat illustrations suitable for vectorization",
        "svg_preset": "default",
        "prompts": [
            {
                "id": "flat_character",
                "name": "Flat Character",
                "prompt": "flat design character illustration, simple geometric shapes, HIGH CONTRAST, bold distinct colors, solid color fills, white background, clean vector art style, no gradients, cartoon style",
                "negative_prompt": "gradients, shadows, realistic, photorealistic, complex shading, soft edges, 3d"
            },
            {
                "id": "isometric_scene",
                "name": "Isometric Scene",
                "prompt": "isometric illustration, geometric buildings and objects, HIGH CONTRAST, flat bold colors, clean sharp edges, white background, vector art style, no gradients, architectural diagram style",
                "negative_prompt": "gradients, shadows, realistic, complex details, soft lighting, 3d render"
            },
            {
                "id": "infographic",
                "name": "Infographic Element",
                "prompt": "infographic illustration element, simple geometric shapes, HIGH CONTRAST, bold flat colors, white background, clean vector design, data visualization style, sharp edges",
                "negative_prompt": "gradients, shadows, photorealistic, complex details, soft edges"
            },
            {
                "id": "spot_illustration",
                "name": "Spot Illustration",
                "prompt": "editorial spot illustration, simple bold shapes, HIGH CONTRAST, limited color palette 3-4 colors, white background, flat vector style, clean geometric design",
                "negative_prompt": "gradients, shadows, photorealistic, complex shading, detailed textures"
            }
        ]
    },
    "vector_patterns": {
        "name": "Vector Patterns",
        "description": "Seamless patterns for backgrounds and textures",
        "svg_preset": "simplified",
        "prompts": [
            {
                "id": "geometric_pattern",
                "name": "Geometric Pattern",
                "prompt": "seamless geometric pattern, repeating shapes, HIGH CONTRAST, bold two-tone colors, flat design, clean sharp edges, vector tile pattern, no gradients",
                "negative_prompt": "gradients, shadows, realistic, complex, soft edges, 3d"
            },
            {
                "id": "abstract_pattern",
                "name": "Abstract Pattern",
                "prompt": "abstract seamless pattern, organic shapes, HIGH CONTRAST, limited color palette, flat bold colors, vector art style, clean edges, repeating design",
                "negative_prompt": "gradients, shadows, photorealistic, complex details, soft blending"
            }
        ]
    },
    "vector_symbols": {
        "name": "Vector Symbols",
        "description": "Abstract symbols and marks",
        "svg_preset": "logo",
        "prompts": [
            {
                "id": "abstract_mark",
                "name": "Abstract Mark",
                "prompt": "abstract geometric symbol, bold distinctive shape, HIGH CONTRAST, single solid color on white background, flat vector design, clean sharp edges, memorable brand mark",
                "negative_prompt": "gradients, shadows, realistic, complex, detailed, textured, 3d"
            },
            {
                "id": "monogram",
                "name": "Monogram",
                "prompt": "elegant monogram letter design, intertwined letters, HIGH CONTRAST, single bold color on white, flat vector style, clean geometric letterforms, sharp edges",
                "negative_prompt": "gradients, shadows, ornate details, 3d effects, soft edges"
            },
            {
                "id": "badge_emblem",
                "name": "Badge/Emblem",
                "prompt": "circular badge emblem design, bold geometric elements, HIGH CONTRAST, 2-3 colors maximum, white background, flat vector style, clean sharp lines, vintage badge aesthetic",
                "negative_prompt": "gradients, shadows, photorealistic, complex details, soft edges, 3d"
            }
        ]
    },
    "photorealistic": {
        "name": "Photorealistic",
        "description": "High-quality photorealistic images (not optimized for SVG)",
        "svg_preset": "detailed",
        "prompts": [
            {
                "id": "portrait",
                "name": "Portrait",
                "prompt": "professional portrait photograph, natural lighting, high detail, sharp focus, studio quality",
                "negative_prompt": "blurry, distorted, artificial, cartoon"
            },
            {
                "id": "landscape",
                "name": "Landscape",
                "prompt": "stunning landscape photograph, golden hour lighting, high dynamic range, professional photography",
                "negative_prompt": "blurry, oversaturated, artificial"
            },
            {
                "id": "product",
                "name": "Product Shot",
                "prompt": "professional product photography, clean white background, studio lighting, high detail, commercial quality",
                "negative_prompt": "blurry, distorted, messy background"
            }
        ]
    }
}


# =============================================================================
# VECTOR-OPTIMIZED TEMPLATES - Ensure high quality SVG conversion
# =============================================================================

VECTOR_TEMPLATES = {
    "logo_template": {
        "name": "Logo Template",
        "description": "Optimized for clean logo SVG output",
        "template": "{subject}, minimalist logo design, HIGH CONTRAST, bold solid colors, pure white background, flat vector style, clean sharp edges, no gradients, no shadows, professional corporate identity, geometric shapes",
        "negative": "gradients, shadows, soft edges, photorealistic, 3d, texture, noise, blurry, complex details, realistic shading",
        "svg_preset": "logo",
        "recommended_size": [512, 512]
    },
    "icon_template": {
        "name": "Icon Template",
        "description": "Optimized for simple icon SVG output",
        "template": "{subject}, simple icon design, HIGH CONTRAST, single bold color, white background, flat design, clean geometric shape, minimal, vector style, sharp edges",
        "negative": "gradients, shadows, realistic, detailed, textured, 3d, complex, photorealistic",
        "svg_preset": "logo",
        "recommended_size": [256, 256]
    },
    "illustration_template": {
        "name": "Illustration Template",
        "description": "Optimized for flat illustration SVG output",
        "template": "{subject}, flat vector illustration, HIGH CONTRAST, bold distinct colors, solid color fills, white background, clean edges, cartoon style, no gradients, graphic design style",
        "negative": "gradients, shadows, realistic, photorealistic, complex shading, soft edges, 3d, detailed textures",
        "svg_preset": "default",
        "recommended_size": [1024, 1024]
    },
    "silhouette_template": {
        "name": "Silhouette Template",
        "description": "Perfect for single-color silhouette SVG",
        "template": "{subject}, bold black silhouette, HIGH CONTRAST, solid black shape on pure white background, clean sharp edges, no details inside, flat vector style",
        "negative": "gradients, shading, gray tones, details, texture, 3d, realistic",
        "svg_preset": "bw",
        "recommended_size": [512, 512]
    },
    "badge_template": {
        "name": "Badge Template",
        "description": "Optimized for badge/emblem SVG output",
        "template": "{subject}, circular badge emblem, HIGH CONTRAST, 2-3 bold colors, white background, flat vector design, clean geometric shapes, vintage badge style, sharp edges",
        "negative": "gradients, shadows, photorealistic, complex details, soft edges, 3d effects, realistic textures",
        "svg_preset": "logo",
        "recommended_size": [512, 512]
    },
    "infographic_template": {
        "name": "Infographic Template",
        "description": "Optimized for data visualization elements",
        "template": "{subject}, infographic design element, HIGH CONTRAST, bold flat colors, white background, clean vector style, geometric shapes, data visualization, sharp clean edges",
        "negative": "gradients, shadows, photorealistic, complex details, soft edges, 3d rendering",
        "svg_preset": "simplified",
        "recommended_size": [800, 600]
    }
}


# =============================================================================
# AI ENHANCE - Improve prompts for better vector/SVG output
# =============================================================================

def enhance_prompt_for_vector(prompt: str, style: str = "logo") -> dict:
    """
    Enhance a basic prompt to be optimized for vector/SVG conversion.
    Uses rule-based enhancement (no external LLM required).
    """

    # Core vector optimization keywords
    vector_keywords = [
        "HIGH CONTRAST",
        "bold solid colors",
        "flat design",
        "clean sharp edges",
        "no gradients",
        "no shadows",
        "vector style"
    ]

    # Style-specific enhancements
    style_enhancements = {
        "logo": {
            "add": ["minimalist logo design", "pure white background", "professional corporate identity", "geometric shapes", "scalable"],
            "negative": "gradients, shadows, soft edges, photorealistic, 3d, texture, noise, blurry, complex details, realistic shading, soft lighting"
        },
        "icon": {
            "add": ["simple icon design", "single bold color", "white background", "minimal geometric shape", "clean lines"],
            "negative": "gradients, shadows, realistic, detailed, textured, 3d, complex, photorealistic, soft edges"
        },
        "illustration": {
            "add": ["flat vector illustration", "bold distinct colors", "solid color fills", "white background", "cartoon style", "graphic design"],
            "negative": "gradients, shadows, realistic, photorealistic, complex shading, soft edges, 3d, detailed textures, soft lighting"
        },
        "silhouette": {
            "add": ["bold black silhouette", "solid black shape", "pure white background", "no internal details"],
            "negative": "gradients, shading, gray tones, details inside shape, texture, 3d, realistic, colors"
        },
        "badge": {
            "add": ["circular badge emblem", "2-3 bold colors maximum", "vintage badge aesthetic", "clean geometric elements"],
            "negative": "gradients, shadows, photorealistic, complex details, soft edges, 3d effects, many colors"
        }
    }

    # Get style-specific additions
    style_config = style_enhancements.get(style, style_enhancements["logo"])

    # Check if prompt already has vector optimization
    prompt_lower = prompt.lower()
    has_contrast = "contrast" in prompt_lower
    has_flat = "flat" in prompt_lower
    has_vector = "vector" in prompt_lower

    # Build enhanced prompt
    enhanced_parts = [prompt.strip().rstrip(',').rstrip('.')]

    # Add vector keywords if missing
    if not has_contrast:
        enhanced_parts.append("HIGH CONTRAST")
    if not has_flat:
        enhanced_parts.append("flat design")
    if not has_vector:
        enhanced_parts.append("vector style")

    # Add style-specific enhancements
    for add in style_config["add"]:
        if add.lower() not in prompt_lower:
            enhanced_parts.append(add)

    # Add core vector keywords
    for kw in ["bold solid colors", "clean sharp edges", "no gradients"]:
        if kw.lower() not in prompt_lower:
            enhanced_parts.append(kw)

    enhanced_prompt = ", ".join(enhanced_parts)

    return {
        "original": prompt,
        "enhanced": enhanced_prompt,
        "negative_prompt": style_config["negative"],
        "style": style,
        "optimizations_applied": [
            "Added HIGH CONTRAST for clean edges",
            "Added flat design keywords",
            "Added vector style indicators",
            f"Applied {style} style enhancements",
            "Added gradient/shadow removal"
        ]
    }


def enhance_prompt_with_llm(prompt: str, style: str = "logo") -> dict:
    """
    Enhance prompt using ZImageCLI's built-in --enhance flag (uses local LLM).
    Falls back to rule-based enhancement if --enhance is not available.
    """
    # First apply rule-based vector optimization
    base_enhancement = enhance_prompt_for_vector(prompt, style)

    # Try to use ZImageCLI's enhance feature for additional improvement
    # Note: This would require ZImageCLI to support a prompt-only enhance mode
    # For now, we'll use our rule-based enhancement which is optimized for vectors

    return base_enhancement


# AI Enhance endpoint models
class EnhanceRequest(BaseModel):
    prompt: str
    style: str = "logo"  # logo, icon, illustration, silhouette, badge
    use_llm: bool = False  # Whether to use LLM enhancement (if available)


class EnhanceResponse(BaseModel):
    original: str
    enhanced: str
    negative_prompt: str
    style: str
    optimizations_applied: list[str]

# Configuration
DATA_DIR = Path(os.environ.get("ZIMAGE_DATA_DIR", Path.home() / ".zimage-server"))
OUTPUT_DIR = DATA_DIR / "outputs"
LORAS_DIR = DATA_DIR / "loras"
DB_PATH = DATA_DIR / "history.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LORAS_DIR.mkdir(parents=True, exist_ok=True)

# FastAPI app
app = FastAPI(
    title="ZImageCLI Server",
    description="Web interface for ZImageCLI with SVG support",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


# Database setup
def init_db():
    """Initialize SQLite database for generation history."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id TEXT PRIMARY KEY,
            prompt TEXT NOT NULL,
            negative_prompt TEXT,
            width INTEGER,
            height INTEGER,
            steps INTEGER,
            seed TEXT,
            output_path TEXT,
            svg_path TEXT,
            svg_preset TEXT,
            loras TEXT,
            duration REAL,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


# Pydantic models
class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=1024, ge=256, le=2048)
    steps: int = Field(default=16, ge=1, le=50)
    seed: Optional[int] = None
    svg: bool = False
    svg_preset: str = "default"
    loras: Optional[list[dict]] = None  # [{"path": "...", "scale": 0.8}]


class GenerateResponse(BaseModel):
    id: str
    prompt: str
    output_url: str
    svg_url: Optional[str] = None
    duration: float
    seed: str


class HistoryItem(BaseModel):
    id: str
    prompt: str
    negative_prompt: Optional[str]
    width: int
    height: int
    steps: int
    seed: str
    output_url: str
    svg_url: Optional[str]
    duration: float
    created_at: str


# Helper functions
def adjust_dimension(dim: int) -> int:
    """Adjust dimension to be divisible by 16."""
    return ((dim + 15) // 16) * 16


def run_zimage_cli(args: list[str]) -> tuple[bool, str, str]:
    """Run ZImageCLI and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["ZImageCLI"] + args,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Generation timed out"
    except FileNotFoundError:
        return False, "", "ZImageCLI not found. Please ensure it's installed."


def save_to_history(data: dict):
    """Save generation to history database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO history (id, prompt, negative_prompt, width, height, steps,
                            seed, output_path, svg_path, svg_preset, loras, duration, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["id"], data["prompt"], data.get("negative_prompt"),
        data["width"], data["height"], data["steps"], data["seed"],
        data["output_path"], data.get("svg_path"), data.get("svg_preset"),
        json.dumps(data.get("loras", [])), data["duration"],
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zimage Studio</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #eee;
                min-height: 100vh;
                padding: 20px;
            }
            .container { max-width: 1400px; margin: 0 auto; }
            h1 { text-align: center; margin-bottom: 10px; color: #00d9ff; }
            .subtitle { text-align: center; margin-bottom: 25px; color: #666; font-size: 0.9em; }
            .grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
            @media (max-width: 1200px) { .grid { grid-template-columns: 1fr 1fr; } }
            @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
            .panel {
                background: rgba(255,255,255,0.05);
                border-radius: 12px;
                padding: 20px;
                backdrop-filter: blur(10px);
            }
            .panel-tall { grid-row: span 2; }
            h2 { margin-bottom: 15px; color: #00d9ff; font-size: 1.1em; display: flex; align-items: center; gap: 8px; }
            h2 .icon { font-size: 1.2em; }
            h3 { margin: 15px 0 10px; color: #aaa; font-size: 0.9em; }
            label { display: block; margin-bottom: 5px; color: #aaa; font-size: 0.9em; }
            input, textarea, select {
                width: 100%;
                padding: 10px;
                border: 1px solid #333;
                border-radius: 6px;
                background: #1a1a2e;
                color: #eee;
                margin-bottom: 12px;
                font-size: 14px;
            }
            textarea { min-height: 80px; resize: vertical; }
            .row { display: flex; gap: 10px; }
            .row > div { flex: 1; }
            button, .btn {
                display: inline-block;
                padding: 10px 16px;
                background: linear-gradient(135deg, #00d9ff 0%, #0099ff 100%);
                color: #000;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                cursor: pointer;
                font-size: 14px;
                transition: transform 0.2s, box-shadow 0.2s;
                text-decoration: none;
                text-align: center;
            }
            button:hover, .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0,217,255,0.4); }
            button:disabled { background: #333; color: #666; cursor: not-allowed; transform: none; box-shadow: none; }
            button.full { width: 100%; }
            button.secondary { background: linear-gradient(135deg, #4a4a6a 0%, #3a3a5a 100%); color: #eee; }
            button.secondary:hover { box-shadow: 0 4px 20px rgba(100,100,150,0.4); }
            button.enhance { background: linear-gradient(135deg, #ff9500 0%, #ff6b00 100%); }
            button.enhance:hover { box-shadow: 0 4px 20px rgba(255,149,0,0.4); }
            .checkbox-row { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
            .checkbox-row input { width: auto; margin: 0; }
            .checkbox-row label { margin: 0; color: #eee; }
            #result { margin-top: 15px; text-align: center; }
            #result img { max-width: 100%; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
            .status { padding: 10px; border-radius: 6px; margin-bottom: 12px; font-size: 0.9em; }
            .status.loading { background: #1a3a5c; }
            .status.success { background: #1a5c3a; }
            .status.error { background: #5c1a1a; }
            .history-item {
                background: rgba(255,255,255,0.03);
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 8px;
                cursor: pointer;
                transition: background 0.2s;
            }
            .history-item:hover { background: rgba(255,255,255,0.08); }
            .history-item img { width: 50px; height: 50px; object-fit: cover; border-radius: 4px; float: left; margin-right: 10px; }
            .history-item .prompt { font-size: 0.85em; color: #ccc; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
            .history-item .meta { font-size: 0.7em; color: #666; margin-top: 4px; }
            .clear { clear: both; }

            /* Prompt Library Styles */
            .category-tabs { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 15px; }
            .category-tab {
                padding: 6px 12px;
                background: rgba(255,255,255,0.05);
                border: 1px solid #333;
                border-radius: 20px;
                cursor: pointer;
                font-size: 0.8em;
                transition: all 0.2s;
            }
            .category-tab:hover { background: rgba(255,255,255,0.1); }
            .category-tab.active { background: #00d9ff; color: #000; border-color: #00d9ff; }
            .prompt-list { max-height: 300px; overflow-y: auto; }
            .prompt-item {
                padding: 10px;
                background: rgba(255,255,255,0.03);
                border-radius: 6px;
                margin-bottom: 8px;
                cursor: pointer;
                transition: background 0.2s;
            }
            .prompt-item:hover { background: rgba(255,255,255,0.08); }
            .prompt-item .name { font-weight: bold; color: #00d9ff; font-size: 0.9em; }
            .prompt-item .preview { font-size: 0.75em; color: #888; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

            /* Template Styles */
            .template-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
            .template-card {
                padding: 12px;
                background: rgba(255,255,255,0.03);
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s;
                border: 1px solid transparent;
            }
            .template-card:hover { background: rgba(255,255,255,0.08); border-color: #00d9ff; }
            .template-card.selected { border-color: #00d9ff; background: rgba(0,217,255,0.1); }
            .template-card .name { font-weight: bold; font-size: 0.85em; color: #eee; }
            .template-card .desc { font-size: 0.7em; color: #888; margin-top: 4px; }

            /* Enhance Panel Styles */
            .enhance-style-select { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
            .style-chip {
                padding: 6px 12px;
                background: rgba(255,255,255,0.05);
                border: 1px solid #333;
                border-radius: 20px;
                cursor: pointer;
                font-size: 0.8em;
                transition: all 0.2s;
            }
            .style-chip:hover { background: rgba(255,255,255,0.1); }
            .style-chip.active { background: #ff9500; color: #000; border-color: #ff9500; }
            .enhanced-preview {
                background: rgba(0,0,0,0.3);
                border-radius: 6px;
                padding: 10px;
                margin-top: 10px;
                font-size: 0.85em;
                line-height: 1.4;
            }
            .enhanced-preview .label { color: #ff9500; font-weight: bold; margin-bottom: 5px; }
            .optimizations { margin-top: 10px; }
            .optimizations li { font-size: 0.75em; color: #888; margin-left: 15px; }

            /* Scrollbar */
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); border-radius: 3px; }
            ::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
            ::-webkit-scrollbar-thumb:hover { background: #555; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Zimage Studio</h1>
            <p class="subtitle">AI Image Generation with Vector/SVG Optimization</p>

            <div class="grid">
                <!-- Generate Panel -->
                <div class="panel panel-tall">
                    <h2><span class="icon">&#9881;</span> Generate</h2>
                    <form id="generateForm">
                        <label>Prompt</label>
                        <textarea id="prompt" placeholder="Describe your image..." required></textarea>

                        <div class="row" style="margin-bottom: 8px;">
                            <button type="button" class="secondary" onclick="enhanceCurrentPrompt()" style="flex: 1;">Enhance for Vector</button>
                        </div>

                        <label>Negative Prompt</label>
                        <input type="text" id="negativePrompt" placeholder="What to avoid...">

                        <div class="row">
                            <div>
                                <label>Width</label>
                                <input type="number" id="width" value="1024" min="256" max="2048" step="16">
                            </div>
                            <div>
                                <label>Height</label>
                                <input type="number" id="height" value="1024" min="256" max="2048" step="16">
                            </div>
                        </div>

                        <div class="row">
                            <div>
                                <label>Steps</label>
                                <input type="number" id="steps" value="16" min="1" max="50">
                            </div>
                            <div>
                                <label>Seed</label>
                                <input type="number" id="seed" placeholder="Random">
                            </div>
                        </div>

                        <div class="checkbox-row">
                            <input type="checkbox" id="svg" checked>
                            <label for="svg">Generate SVG</label>
                            <select id="svgPreset" style="width: auto; margin: 0;">
                                <option value="logo">Logo</option>
                                <option value="default">Default</option>
                                <option value="detailed">Detailed</option>
                                <option value="simplified">Simplified</option>
                                <option value="bw">B&W</option>
                            </select>
                        </div>

                        <button type="submit" id="generateBtn" class="full">Generate Image</button>
                    </form>

                    <div id="status"></div>
                    <div id="result"></div>
                </div>

                <!-- Prompt Library Panel -->
                <div class="panel">
                    <h2><span class="icon">&#128218;</span> Prompt Library</h2>
                    <div class="category-tabs" id="categoryTabs"></div>
                    <div class="prompt-list" id="promptList"></div>
                </div>

                <!-- Templates Panel -->
                <div class="panel">
                    <h2><span class="icon">&#128196;</span> Vector Templates</h2>
                    <p style="font-size: 0.8em; color: #888; margin-bottom: 12px;">Click a template, then enter your subject below</p>
                    <div class="template-grid" id="templateGrid"></div>
                    <div id="templateInput" style="margin-top: 15px; display: none;">
                        <label>Subject for <span id="selectedTemplateName"></span></label>
                        <input type="text" id="templateSubject" placeholder="e.g., coffee cup, mountain, rocket">
                        <button type="button" onclick="applySelectedTemplate()" class="full secondary">Apply Template</button>
                    </div>
                </div>

                <!-- AI Enhance Panel -->
                <div class="panel">
                    <h2><span class="icon">&#10024;</span> AI Enhance</h2>
                    <p style="font-size: 0.8em; color: #888; margin-bottom: 12px;">Optimize any prompt for vector/SVG output</p>

                    <label>Enhancement Style</label>
                    <div class="enhance-style-select" id="enhanceStyles">
                        <span class="style-chip active" data-style="logo">Logo</span>
                        <span class="style-chip" data-style="icon">Icon</span>
                        <span class="style-chip" data-style="illustration">Illustration</span>
                        <span class="style-chip" data-style="silhouette">Silhouette</span>
                        <span class="style-chip" data-style="badge">Badge</span>
                    </div>

                    <label>Your Prompt</label>
                    <input type="text" id="enhanceInput" placeholder="e.g., a phoenix bird">

                    <button type="button" onclick="enhancePrompt()" class="full enhance">Enhance Prompt</button>

                    <div id="enhanceResult"></div>
                </div>

                <!-- History Panel -->
                <div class="panel">
                    <h2><span class="icon">&#128345;</span> History</h2>
                    <input type="text" id="searchHistory" placeholder="Search history...">
                    <div id="historyList" style="max-height: 400px; overflow-y: auto;"></div>
                </div>
            </div>
        </div>

        <script>
            // State
            let selectedCategory = 'vector_logos';
            let selectedTemplate = null;
            let selectedEnhanceStyle = 'logo';
            let promptLibrary = {};
            let templates = {};

            // DOM Elements
            const form = document.getElementById('generateForm');
            const statusEl = document.getElementById('status');
            const resultEl = document.getElementById('result');
            const historyEl = document.getElementById('historyList');
            const searchEl = document.getElementById('searchHistory');
            const categoryTabsEl = document.getElementById('categoryTabs');
            const promptListEl = document.getElementById('promptList');
            const templateGridEl = document.getElementById('templateGrid');

            // Load Prompt Library
            async function loadPromptLibrary() {
                const res = await fetch('/prompts');
                const data = await res.json();
                promptLibrary = data.categories;
                renderCategoryTabs();
                renderPrompts();
            }

            function renderCategoryTabs() {
                categoryTabsEl.innerHTML = Object.entries(promptLibrary).map(([id, cat]) =>
                    `<span class="category-tab ${id === selectedCategory ? 'active' : ''}"
                          onclick="selectCategory('${id}')">${cat.name}</span>`
                ).join('');
            }

            function selectCategory(id) {
                selectedCategory = id;
                renderCategoryTabs();
                renderPrompts();
            }

            function renderPrompts() {
                const cat = promptLibrary[selectedCategory];
                if (!cat) return;
                promptListEl.innerHTML = cat.prompts.map(p =>
                    `<div class="prompt-item" onclick="usePrompt('${selectedCategory}', '${p.id}')">
                        <div class="name">${p.name}</div>
                        <div class="preview">${p.prompt.substring(0, 80)}...</div>
                    </div>`
                ).join('');
            }

            function usePrompt(category, promptId) {
                const cat = promptLibrary[category];
                const prompt = cat.prompts.find(p => p.id === promptId);
                if (prompt) {
                    document.getElementById('prompt').value = prompt.prompt;
                    document.getElementById('negativePrompt').value = prompt.negative_prompt || '';
                    document.getElementById('svgPreset').value = cat.svg_preset;
                    document.getElementById('svg').checked = true;
                    statusEl.className = 'status success';
                    statusEl.textContent = `Loaded: ${prompt.name}`;
                }
            }

            // Load Templates
            async function loadTemplates() {
                const res = await fetch('/templates');
                const data = await res.json();
                templates = data.templates;
                renderTemplates();
            }

            function renderTemplates() {
                templateGridEl.innerHTML = Object.entries(templates).map(([id, t]) =>
                    `<div class="template-card ${selectedTemplate === id ? 'selected' : ''}"
                          onclick="selectTemplate('${id}')">
                        <div class="name">${t.name}</div>
                        <div class="desc">${t.description}</div>
                    </div>`
                ).join('');
            }

            function selectTemplate(id) {
                selectedTemplate = id;
                renderTemplates();
                document.getElementById('templateInput').style.display = 'block';
                document.getElementById('selectedTemplateName').textContent = templates[id].name;
                document.getElementById('templateSubject').focus();
            }

            async function applySelectedTemplate() {
                if (!selectedTemplate) return;
                const subject = document.getElementById('templateSubject').value;
                if (!subject) {
                    alert('Please enter a subject');
                    return;
                }

                const res = await fetch(`/templates/${selectedTemplate}/apply?subject=${encodeURIComponent(subject)}`, {
                    method: 'POST'
                });
                const data = await res.json();

                document.getElementById('prompt').value = data.prompt;
                document.getElementById('negativePrompt').value = data.negative_prompt;
                document.getElementById('svgPreset').value = data.svg_preset;
                document.getElementById('width').value = data.recommended_size[0];
                document.getElementById('height').value = data.recommended_size[1];
                document.getElementById('svg').checked = true;

                statusEl.className = 'status success';
                statusEl.textContent = `Applied template: ${templates[selectedTemplate].name}`;
            }

            // Enhance Styles
            document.getElementById('enhanceStyles').addEventListener('click', (e) => {
                if (e.target.classList.contains('style-chip')) {
                    document.querySelectorAll('.style-chip').forEach(c => c.classList.remove('active'));
                    e.target.classList.add('active');
                    selectedEnhanceStyle = e.target.dataset.style;
                }
            });

            async function enhancePrompt() {
                const input = document.getElementById('enhanceInput').value;
                if (!input) {
                    alert('Please enter a prompt to enhance');
                    return;
                }

                const res = await fetch('/enhance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: input, style: selectedEnhanceStyle })
                });
                const data = await res.json();

                document.getElementById('enhanceResult').innerHTML = `
                    <div class="enhanced-preview">
                        <div class="label">Enhanced Prompt:</div>
                        <div>${data.enhanced}</div>
                        <div class="label" style="margin-top: 10px;">Negative Prompt:</div>
                        <div style="color: #ff6b6b;">${data.negative_prompt}</div>
                        <ul class="optimizations">
                            ${data.optimizations_applied.map(o => `<li>${o}</li>`).join('')}
                        </ul>
                        <button type="button" onclick="useEnhancedPrompt()" style="margin-top: 10px; width: 100%;">Use This Prompt</button>
                    </div>
                `;

                // Store for later use
                window.lastEnhanced = data;
            }

            function useEnhancedPrompt() {
                if (window.lastEnhanced) {
                    document.getElementById('prompt').value = window.lastEnhanced.enhanced;
                    document.getElementById('negativePrompt').value = window.lastEnhanced.negative_prompt;
                    document.getElementById('svg').checked = true;
                    statusEl.className = 'status success';
                    statusEl.textContent = 'Enhanced prompt loaded!';
                }
            }

            async function enhanceCurrentPrompt() {
                const currentPrompt = document.getElementById('prompt').value;
                if (!currentPrompt) {
                    alert('Please enter a prompt first');
                    return;
                }

                const res = await fetch('/enhance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: currentPrompt, style: selectedEnhanceStyle })
                });
                const data = await res.json();

                document.getElementById('prompt').value = data.enhanced;
                document.getElementById('negativePrompt').value = data.negative_prompt;
                document.getElementById('svg').checked = true;

                statusEl.className = 'status success';
                statusEl.textContent = 'Prompt enhanced for vector output!';
            }

            // History
            async function loadHistory(search = '') {
                const res = await fetch(`/history?search=${encodeURIComponent(search)}&limit=20`);
                const data = await res.json();
                historyEl.innerHTML = data.items.map(item => `
                    <div class="history-item" onclick="showImage('${item.output_url}', '${item.svg_url || ''}')">
                        <img src="${item.output_url}" alt="">
                        <div class="prompt">${item.prompt.substring(0, 50)}...</div>
                        <div class="meta">${item.width}x${item.height} | ${item.steps}s | ${item.duration.toFixed(1)}s</div>
                        <div class="clear"></div>
                    </div>
                `).join('') || '<p style="color:#666; font-size:0.9em;">No history yet</p>';
            }

            function showImage(url, svgUrl) {
                let html = `<img src="${url}" alt="Generated image">`;
                if (svgUrl) {
                    html += `<p style="margin-top:10px"><a href="${svgUrl}" target="_blank" style="color:#00d9ff">View SVG</a> | <a href="${svgUrl}" download style="color:#00d9ff">Download SVG</a></p>`;
                }
                resultEl.innerHTML = html;
            }

            // Generate Form
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const btn = document.getElementById('generateBtn');
                btn.disabled = true;
                statusEl.className = 'status loading';
                statusEl.textContent = 'Generating image...';
                resultEl.innerHTML = '';

                const body = {
                    prompt: document.getElementById('prompt').value,
                    negative_prompt: document.getElementById('negativePrompt').value || null,
                    width: parseInt(document.getElementById('width').value),
                    height: parseInt(document.getElementById('height').value),
                    steps: parseInt(document.getElementById('steps').value),
                    seed: document.getElementById('seed').value ? parseInt(document.getElementById('seed').value) : null,
                    svg: document.getElementById('svg').checked,
                    svg_preset: document.getElementById('svgPreset').value
                };

                try {
                    const res = await fetch('/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    const data = await res.json();

                    if (res.ok) {
                        statusEl.className = 'status success';
                        statusEl.textContent = `Generated in ${data.duration.toFixed(1)}s (seed: ${data.seed})`;
                        showImage(data.output_url, data.svg_url);
                        loadHistory();
                    } else {
                        throw new Error(data.detail || 'Generation failed');
                    }
                } catch (err) {
                    statusEl.className = 'status error';
                    statusEl.textContent = err.message;
                } finally {
                    btn.disabled = false;
                }
            });

            searchEl.addEventListener('input', (e) => loadHistory(e.target.value));

            // Initial load
            loadPromptLibrary();
            loadTemplates();
            loadHistory();
        </script>
    </body>
    </html>
    """


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate an image using ZImageCLI."""
    # Adjust dimensions
    width = adjust_dimension(request.width)
    height = adjust_dimension(request.height)

    # Generate unique ID and filename
    gen_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{gen_id}.png"
    output_path = OUTPUT_DIR / filename

    # Build ZImageCLI command
    args = [
        "-p", request.prompt,
        "-W", str(width),
        "-H", str(height),
        "-s", str(request.steps),
        "-o", str(output_path),
        "--no-progress"
    ]

    if request.negative_prompt:
        args.extend(["--negative-prompt", request.negative_prompt])

    if request.seed:
        args.extend(["--seed", str(request.seed)])

    if request.svg:
        args.append("--svg")
        args.extend(["--svg-preset", request.svg_preset])

    # Add LoRAs if specified
    if request.loras:
        for lora in request.loras:
            args.extend(["--lora", lora["path"]])
            if "scale" in lora:
                args.extend(["--lora-scale", str(lora["scale"])])

    # Run generation
    start_time = time.time()
    success, stdout, stderr = await asyncio.get_event_loop().run_in_executor(
        None, run_zimage_cli, args
    )
    duration = time.time() - start_time

    if not success:
        raise HTTPException(status_code=500, detail=f"Generation failed: {stderr}")

    # Extract seed from output
    seed = "unknown"
    for line in stderr.split("\n"):
        if "seed" in line.lower():
            parts = line.split()
            for i, p in enumerate(parts):
                if "seed" in p.lower() and i + 1 < len(parts):
                    seed = parts[i + 1].strip(":")
                    break

    # Check for SVG output
    svg_path = None
    svg_url = None
    if request.svg:
        svg_filename = filename.replace(".png", ".svg")
        potential_svg = OUTPUT_DIR / svg_filename
        if potential_svg.exists():
            svg_path = str(potential_svg)
            svg_url = f"/outputs/{svg_filename}"

    # Save to history
    save_to_history({
        "id": gen_id,
        "prompt": request.prompt,
        "negative_prompt": request.negative_prompt,
        "width": width,
        "height": height,
        "steps": request.steps,
        "seed": seed,
        "output_path": str(output_path),
        "svg_path": svg_path,
        "svg_preset": request.svg_preset if request.svg else None,
        "loras": request.loras,
        "duration": duration
    })

    return GenerateResponse(
        id=gen_id,
        prompt=request.prompt,
        output_url=f"/outputs/{filename}",
        svg_url=svg_url,
        duration=duration,
        seed=seed
    )


@app.get("/history")
async def get_history(
    search: str = Query(default=""),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0)
):
    """Get generation history with optional search."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if search:
        rows = conn.execute("""
            SELECT * FROM history
            WHERE prompt LIKE ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (f"%{search}%", limit, offset)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM history
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()

    conn.close()

    items = []
    for row in rows:
        filename = Path(row["output_path"]).name
        svg_filename = filename.replace(".png", ".svg") if row["svg_path"] else None
        items.append({
            "id": row["id"],
            "prompt": row["prompt"],
            "negative_prompt": row["negative_prompt"],
            "width": row["width"],
            "height": row["height"],
            "steps": row["steps"],
            "seed": row["seed"],
            "output_url": f"/outputs/{filename}",
            "svg_url": f"/outputs/{svg_filename}" if svg_filename else None,
            "duration": row["duration"],
            "created_at": row["created_at"]
        })

    return {"items": items, "total": len(items)}


@app.delete("/history/{item_id}")
async def delete_history(item_id: str):
    """Delete a history item and its associated files."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT output_path, svg_path FROM history WHERE id = ?", (item_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    # Delete files
    if row[0] and Path(row[0]).exists():
        Path(row[0]).unlink()
    if row[1] and Path(row[1]).exists():
        Path(row[1]).unlink()

    # Delete from database
    conn.execute("DELETE FROM history WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

    return {"status": "deleted"}


@app.get("/models")
async def list_models():
    """List available models and hardware info."""
    import platform

    # Get system info
    machine = platform.machine()
    system = platform.system()

    return {
        "default_model": "Tongyi-MAI/Z-Image-Turbo",
        "hardware": {
            "platform": system,
            "architecture": machine,
            "accelerator": "Apple Silicon (MPS)" if machine == "arm64" and system == "Darwin" else "Unknown"
        },
        "svg_presets": ["default", "logo", "detailed", "simplified", "bw"]
    }


@app.get("/loras")
async def list_loras():
    """List available LoRA files."""
    loras = []
    for f in LORAS_DIR.glob("*.safetensors"):
        loras.append({
            "id": f.stem,
            "filename": f.name,
            "path": str(f),
            "size_mb": f.stat().st_size / (1024 * 1024)
        })
    return {"loras": loras}


# =============================================================================
# PROMPT LIBRARY & TEMPLATES API
# =============================================================================

@app.get("/prompts")
async def get_prompt_library():
    """Get the full prompt library organized by category."""
    return {
        "categories": PROMPT_LIBRARY,
        "total_prompts": sum(len(cat["prompts"]) for cat in PROMPT_LIBRARY.values())
    }


@app.get("/prompts/{category}")
async def get_prompts_by_category(category: str):
    """Get prompts for a specific category."""
    if category not in PROMPT_LIBRARY:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    return PROMPT_LIBRARY[category]


@app.get("/prompts/{category}/{prompt_id}")
async def get_prompt_by_id(category: str, prompt_id: str):
    """Get a specific prompt by category and ID."""
    if category not in PROMPT_LIBRARY:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

    for prompt in PROMPT_LIBRARY[category]["prompts"]:
        if prompt["id"] == prompt_id:
            return {
                **prompt,
                "category": category,
                "svg_preset": PROMPT_LIBRARY[category]["svg_preset"]
            }

    raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found in category '{category}'")


@app.get("/templates")
async def get_templates():
    """Get all vector-optimized templates."""
    return {
        "templates": VECTOR_TEMPLATES,
        "total": len(VECTOR_TEMPLATES)
    }


@app.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get a specific template by ID."""
    if template_id not in VECTOR_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    return {
        "id": template_id,
        **VECTOR_TEMPLATES[template_id]
    }


@app.post("/templates/{template_id}/apply")
async def apply_template(template_id: str, subject: str = Query(..., description="Subject to insert into template")):
    """Apply a template with a subject to get a complete prompt."""
    if template_id not in VECTOR_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    template = VECTOR_TEMPLATES[template_id]
    prompt = template["template"].format(subject=subject)

    return {
        "template_id": template_id,
        "subject": subject,
        "prompt": prompt,
        "negative_prompt": template["negative"],
        "svg_preset": template["svg_preset"],
        "recommended_size": template["recommended_size"]
    }


# =============================================================================
# AI ENHANCE API
# =============================================================================

@app.post("/enhance", response_model=EnhanceResponse)
async def enhance_prompt(request: EnhanceRequest):
    """
    Enhance a prompt for better vector/SVG output.

    Styles available:
    - logo: Optimized for logo design
    - icon: Optimized for simple icons
    - illustration: Optimized for flat illustrations
    - silhouette: Optimized for single-color silhouettes
    - badge: Optimized for badge/emblem designs
    """
    if request.use_llm:
        result = enhance_prompt_with_llm(request.prompt, request.style)
    else:
        result = enhance_prompt_for_vector(request.prompt, request.style)

    return EnhanceResponse(**result)


@app.get("/enhance/styles")
async def get_enhance_styles():
    """Get available enhancement styles and their descriptions."""
    return {
        "styles": {
            "logo": {
                "name": "Logo",
                "description": "Optimized for minimalist logo designs with clean edges",
                "best_for": ["company logos", "brand marks", "corporate identity"],
                "svg_preset": "logo"
            },
            "icon": {
                "name": "Icon",
                "description": "Optimized for simple, single-color icons",
                "best_for": ["app icons", "UI icons", "simple symbols"],
                "svg_preset": "logo"
            },
            "illustration": {
                "name": "Illustration",
                "description": "Optimized for flat vector illustrations",
                "best_for": ["characters", "scenes", "infographics"],
                "svg_preset": "default"
            },
            "silhouette": {
                "name": "Silhouette",
                "description": "Optimized for bold black silhouettes",
                "best_for": ["silhouette art", "cutouts", "stencils"],
                "svg_preset": "bw"
            },
            "badge": {
                "name": "Badge",
                "description": "Optimized for circular badge/emblem designs",
                "best_for": ["emblems", "seals", "vintage badges"],
                "svg_preset": "logo"
            }
        }
    }


@app.post("/loras")
async def upload_lora(file: UploadFile = File(...)):
    """Upload a LoRA file."""
    if not file.filename.endswith(".safetensors"):
        raise HTTPException(status_code=400, detail="Only .safetensors files are allowed")

    dest = LORAS_DIR / file.filename
    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"status": "uploaded", "path": str(dest)}


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a generated file."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)


# MCP Server endpoints (optional)
@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """Handle MCP JSON-RPC requests."""
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "ZImageCLI-MCP", "version": "1.0.0"},
                "capabilities": {"tools": {}}
            }
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "generate",
                        "description": "Generate an image from a text prompt",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "prompt": {"type": "string"},
                                "width": {"type": "integer", "default": 1024},
                                "height": {"type": "integer", "default": 1024},
                                "steps": {"type": "integer", "default": 16},
                                "svg": {"type": "boolean", "default": False}
                            },
                            "required": ["prompt"]
                        }
                    },
                    {
                        "name": "list_history",
                        "description": "List recent generations",
                        "inputSchema": {"type": "object", "properties": {}}
                    }
                ]
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        if tool_name == "generate":
            req = GenerateRequest(**tool_args)
            result = await generate(req)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result.dict())}]}
            }

        elif tool_name == "list_history":
            history = await get_history()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(history)}]}
            }

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
