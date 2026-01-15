#!/usr/bin/env python3
"""
ZImageCLI Web Server
A FastAPI-based web interface for ZImageCLI with generation history and MCP support.
Inspired by z-image-studio (https://github.com/iconben/z-image-studio)
"""

import asyncio
import json
import os
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
        <title>ZImageCLI Server</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #eee;
                min-height: 100vh;
                padding: 20px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { text-align: center; margin-bottom: 30px; color: #00d9ff; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
            .panel {
                background: rgba(255,255,255,0.05);
                border-radius: 12px;
                padding: 20px;
                backdrop-filter: blur(10px);
            }
            h2 { margin-bottom: 15px; color: #00d9ff; font-size: 1.2em; }
            label { display: block; margin-bottom: 5px; color: #aaa; font-size: 0.9em; }
            input, textarea, select {
                width: 100%;
                padding: 10px;
                border: 1px solid #333;
                border-radius: 6px;
                background: #1a1a2e;
                color: #eee;
                margin-bottom: 15px;
                font-size: 14px;
            }
            textarea { min-height: 100px; resize: vertical; }
            .row { display: flex; gap: 10px; }
            .row > div { flex: 1; }
            button {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #00d9ff 0%, #0099ff 100%);
                color: #000;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                cursor: pointer;
                font-size: 16px;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            button:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0,217,255,0.4); }
            button:disabled { background: #333; color: #666; cursor: not-allowed; transform: none; }
            .checkbox-row { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }
            .checkbox-row input { width: auto; margin: 0; }
            .checkbox-row label { margin: 0; color: #eee; }
            #result { margin-top: 20px; text-align: center; }
            #result img { max-width: 100%; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
            .status { padding: 10px; border-radius: 6px; margin-bottom: 15px; }
            .status.loading { background: #1a3a5c; }
            .status.success { background: #1a5c3a; }
            .status.error { background: #5c1a1a; }
            .history-item {
                background: rgba(255,255,255,0.03);
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 10px;
                cursor: pointer;
                transition: background 0.2s;
            }
            .history-item:hover { background: rgba(255,255,255,0.08); }
            .history-item img { width: 60px; height: 60px; object-fit: cover; border-radius: 4px; float: left; margin-right: 10px; }
            .history-item .prompt { font-size: 0.9em; color: #ccc; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
            .history-item .meta { font-size: 0.75em; color: #666; margin-top: 5px; }
            .clear { clear: both; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ZImageCLI Server</h1>
            <div class="grid">
                <div class="panel">
                    <h2>Generate Image</h2>
                    <form id="generateForm">
                        <label>Prompt</label>
                        <textarea id="prompt" placeholder="Describe your image..." required></textarea>

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
                                <label>Seed (optional)</label>
                                <input type="number" id="seed" placeholder="Random">
                            </div>
                        </div>

                        <div class="checkbox-row">
                            <input type="checkbox" id="svg">
                            <label for="svg">Generate SVG</label>
                            <select id="svgPreset" style="width: auto; margin: 0;">
                                <option value="default">Default</option>
                                <option value="logo">Logo</option>
                                <option value="detailed">Detailed</option>
                                <option value="simplified">Simplified</option>
                                <option value="bw">B&W</option>
                            </select>
                        </div>

                        <button type="submit" id="generateBtn">Generate</button>
                    </form>

                    <div id="status"></div>
                    <div id="result"></div>
                </div>

                <div class="panel">
                    <h2>History</h2>
                    <input type="text" id="searchHistory" placeholder="Search history...">
                    <div id="historyList"></div>
                </div>
            </div>
        </div>

        <script>
            const form = document.getElementById('generateForm');
            const statusEl = document.getElementById('status');
            const resultEl = document.getElementById('result');
            const historyEl = document.getElementById('historyList');
            const searchEl = document.getElementById('searchHistory');

            async function loadHistory(search = '') {
                const res = await fetch(`/history?search=${encodeURIComponent(search)}&limit=20`);
                const data = await res.json();
                historyEl.innerHTML = data.items.map(item => `
                    <div class="history-item" onclick="showImage('${item.output_url}', '${item.svg_url || ''}')">
                        <img src="${item.output_url}" alt="">
                        <div class="prompt">${item.prompt}</div>
                        <div class="meta">${item.width}x${item.height} | ${item.steps} steps | ${item.duration.toFixed(1)}s</div>
                        <div class="clear"></div>
                    </div>
                `).join('');
            }

            function showImage(url, svgUrl) {
                let html = `<img src="${url}" alt="Generated image">`;
                if (svgUrl) {
                    html += `<p style="margin-top:10px"><a href="${svgUrl}" target="_blank" style="color:#00d9ff">View SVG</a></p>`;
                }
                resultEl.innerHTML = html;
            }

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const btn = document.getElementById('generateBtn');
                btn.disabled = true;
                statusEl.className = 'status loading';
                statusEl.textContent = 'Generating...';
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
