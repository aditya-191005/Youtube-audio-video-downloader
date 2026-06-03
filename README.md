# ⚡ YouTube Audio & Video Downloader

A full-stack, Vercel-ready project using **FastAPI** and **yt-dlp** that lets you paste a YouTube link, preview its thumbnail, and download either **video (MP4/WebM)** or **audio (M4A/WebM)** in different qualities. 

The frontend is built with **HTML + TailwindCSS + JavaScript**, fully responsive and mobile-friendly, with dynamic loading states and beautiful gradients.

This project is optimized to run safely on **Vercel Serverless Functions** without requiring `ffmpeg` installations or permanent filesystem storage.

---

## 🚀 How to Run Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/aditya-191005/Youtube-audio-video-downloader.git
   cd Youtube-audio-video-downloader
   ```

2. **Create and activate a virtual environment**
   ```bash
   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate
   
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the FastAPI backend**
   ```bash
   uvicorn api.index:app --reload
   ```

5. **Open the App**
   The API will automatically serve the frontend. Just open your browser and navigate to:
   [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## ☁️ How to Deploy on Vercel (Online)

This project is pre-configured for Vercel using the `vercel.json` file.

1. **Push your code to GitHub** (or GitLab/Bitbucket).
2. Go to your [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New... > Project**.
3. Import the repository you just pushed.
4. Leave all default build settings as they are (Vercel automatically detects the `vercel.json` file and Python environment).
5. Click **Deploy**.

Vercel will build the project and provide you with a live URL where you can use your downloader instantly!

---

## ⚠️ Disclaimer
For educational purposes only. Do not use to download copyrighted material. Always respect YouTube's Terms of Service.
