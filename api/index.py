import asyncio
import os
import uuid
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask
import yt_dlp

app = FastAPI(title="YouTube A/V Downloader")

# Vercel environments have read-only filesystems, so we must use /tmp
DOWNLOAD_DIR = Path("/tmp")

# Setup templates directory relative to this file's location
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_info_sync(url: str):
    """Synchronous function to extract yt-dlp metadata."""
    ydl_opts = {
        "quiet": True,
        "nocheckcertificate": True,
        "noplaylist": True,
        "cachedir": False,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("Could not extract video information.")
        return ydl.sanitize_info(info)

def download_sync(url: str, format_id: str, is_audio: bool):
    """Synchronous function to download media using yt-dlp to /tmp."""
    unique_id = str(uuid.uuid4())
    
    # Define a temporary output template
    outtmpl = str(DOWNLOAD_DIR / f"{unique_id}.%(ext)s")
    
    ydl_opts = {
        "quiet": True,
        "nocheckcertificate": True,
        "noplaylist": True,
        "cachedir": False,
        "format": format_id,
        "outtmpl": outtmpl,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            raise ValueError("Could not extract video information.")
        
        # Get the actual filename downloaded
        downloaded_file = ydl.prepare_filename(info)
        
        if not os.path.exists(downloaded_file):
            raise FileNotFoundError("Downloaded file could not be found.")
            
        ext = info.get("ext", "mp4" if not is_audio else "m4a")
        title = info.get("title", "download").replace("/", "_").replace("\\", "_")
        final_filename = f"{title}.{ext}"
        
        return downloaded_file, final_filename, ext

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )

@app.get("/fetch")
async def fetch_info(url: str = Query(...)):
    """
    Fetch video metadata asynchronously.
    """
    try:
        info = await asyncio.to_thread(extract_info_sync, url)
        return {
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "duration_string": info.get("duration_string"),
            "thumbnail": info.get("thumbnail"),
            "formats": info.get("formats"),
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )

@app.get("/download")
async def download(
    url: str = Query(...),
    format_id: str = Query(...),
    as_audio: bool = Query(False),
):
    """
    Download video/audio safely and return FileResponse.
    Uses /tmp directory which is allowed in Vercel serverless.
    """
    try:
        downloaded_file, filename, ext = await asyncio.to_thread(
            download_sync, url, format_id, as_audio
        )

        media_type = "audio/mp4" if as_audio else "video/mp4"
        if ext == "webm" and as_audio:
            media_type = "audio/webm"
        elif ext == "webm":
            media_type = "video/webm"

        return FileResponse(
            path=downloaded_file,
            filename=filename,
            media_type=media_type,
            background=BackgroundTask(os.remove, downloaded_file),
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )
