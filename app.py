from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import yt_dlp
import os
import uuid
from pathlib import Path

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to ["http://localhost:5500"] if serving frontend locally
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return templates.TemplateResponse("index.html", {"request": {}})

@app.get("/fetch")
async def fetch_info(url: str = Query(...)):
    """Fetch video metadata without downloading."""
    try:
        ydl_opts = {"quiet": True}
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
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.get("/download")
async def download(url: str, format_id: str, as_mp3: bool = False):
    """Download video/audio and return as file response."""
    try:
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        ext = "mp3" if as_mp3 else "mp4"
        outtmpl = str(DOWNLOAD_DIR / f"{unique_id}.%(ext)s")

        ydl_opts = {
            "quiet": True,
            "format": format_id,
            "outtmpl": outtmpl,
        }

        # If audio requested as MP3
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
                downloaded_file = downloaded_file.rsplit(".", 1)[0] + ".mp3"

        # Stream file to client
        filename = f"{info.get('title', 'download')}.{ext}"
        return FileResponse(
            path=downloaded_file,
            media_type="audio/mpeg" if as_mp3 else "video/mp4",
            filename=filename,
            background=lambda: os.remove(downloaded_file),  # auto cleanup
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
