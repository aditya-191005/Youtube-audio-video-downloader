from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask

import yt_dlp
import os
import uuid
import tempfile
from pathlib import Path

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel-safe writable temp directory
DOWNLOAD_DIR = Path(tempfile.gettempdir()) / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


@app.get("/fetch")
async def fetch_info(url: str = Query(...)):
    """
    Fetch video metadata without downloading.
    """
    try:
        ydl_opts = {
            "quiet": True,
            "nocheckcertificate": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            info = ydl.sanitize_info(info)

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
    url: str,
    format_id: str,
    as_mp3: bool = False,
):
    """
    Download video/audio and return file response.
    """

    try:
        unique_id = str(uuid.uuid4())

        ext = "mp3" if as_mp3 else "mp4"

        outtmpl = str(
            DOWNLOAD_DIR / f"{unique_id}.%(ext)s"
        )

        ydl_opts = {
            "quiet": True,
            "nocheckcertificate": True,
            "format": format_id,
            "outtmpl": outtmpl,
        }

        # MP3 conversion
        if as_mp3:
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            downloaded_file = ydl.prepare_filename(info)

            if as_mp3:
                downloaded_file = (
                    downloaded_file.rsplit(".", 1)[0]
                    + ".mp3"
                )

        # Safety check
        if not os.path.exists(downloaded_file):
            return JSONResponse(
                status_code=404,
                content={"detail": "Downloaded file not found"},
            )

        filename = f"{info.get('title', 'download')}.{ext}"

        return FileResponse(
            path=downloaded_file,
            filename=filename,
            media_type=(
                "audio/mpeg"
                if as_mp3
                else "video/mp4"
            ),
            background=BackgroundTask(
                os.remove,
                downloaded_file,
            ),
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )