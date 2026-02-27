# Prompt: Get AutoBrainrot pipeline up and running

Copy everything below the line into Claude Code (or your coding agent).

---

**Goal:** Get the AutoBrainrot automated content pipeline running in this repo. The stack is: **OpenClaw** (orchestration), **video-gen** (the `automated-content-generator` folder does the actual rendering), and the **video-factory** OpenClaw skill that turns an LLM script string into a video without Reddit.

**Do the following:**

1. **Environment**
   - Ensure `.env` exists in the repo root (or in `automated-content-generator/` if the video pipeline reads it from there). If there’s an `.env.template` or `.env.example`, copy it to `.env` and tell me which placeholders to fill (e.g. Reddit credentials, Streamlabs/API keys). The video-factory bridge can run with just a script and doesn’t need Reddit; full Reddit scrape path needs Reddit env vars.

2. **Dependencies**
   - From the **repo root**, run: `pip install -r requirements.txt` (or create a venv first and then install). Fix any install errors (e.g. missing system libs, Python version). The unified `requirements.txt` includes moviepy, praw, gTTS, selenium, and the rest for both OpenClaw and the video pipeline.

3. **Background video**
   - The pipeline expects at least one background video in `automated-content-generator/assets/backgrounds/`. Config defaults to `default.mp4`. Either:
     - Add a placeholder or note that I need to drop a `default.mp4` (or another .mp4) into `automated-content-generator/assets/backgrounds/`, or
     - If there’s a way to download a short stock clip or use a test asset, set that up so the pipeline has something to use.

4. **Directories**
   - Ensure these exist (create if missing):
     - `automated-content-generator/assets/temp`
     - `automated-content-generator/assets/backgrounds`
     - `automated-content-generator/result`

5. **Smoke test the video-factory bridge**
   - From the repo root, run the bridge with a short script so we know TTS + video path work (skip or mock Selenium if that’s not set up):
     - `python openclaw/skills/video-factory/bridge.py "This is a ten second test script for the video pipeline."`
   - If the bridge fails, fix the reported error (e.g. missing module, wrong path, missing background file). If Selenium is required for title/comment images and Chrome isn’t available, document that and what runs successfully without it.

6. **Summary**
   - List what’s done, what I need to do manually (e.g. add `default.mp4`, fill `.env` secrets), and the exact command to run the video-factory bridge with a script.

Use the repo layout as-is: OpenClaw skills live under `openclaw/skills/`, and the rendering pipeline lives under `automated-content-generator/` (that’s the “video-gen” component).
