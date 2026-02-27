# AutoBrainrot

Automated short-form video pipeline. An LLM (or you) provides a script string; the pipeline produces a narrated `.mp4` ready for Shorts/Reels.

**Stack:**
- **OpenClaw** (`openclaw/`) — TypeScript orchestration layer (WhatsApp gateway, skill runner, plugin SDK)
- **video-gen** (`automated-content-generator/`) — Python rendering pipeline (TTS → background clip → images → final video)
- **video-factory skill** (`openclaw/skills/video-factory/bridge.py`) — glue that calls video-gen with a script string, no Reddit required

---

## Current state (as of 2026-02-27)

The Python pipeline is **working end-to-end** with a smoke-tested build. Three bugs were patched to get here:

| Bug | Fix |
|-----|-----|
| Streamlabs Polly TTS API returns 403 | `src/text_to_speech.py` now falls back to **gTTS** automatically |
| `PIL.Image.ANTIALIAS` removed in Pillow 10 | Compat shim added at top of `bridge.py` |
| External tweet-image sites changed HTML | `bridge.py` generates plain Pillow placeholder images when Selenium can't produce them |

What still needs real content:

- `automated-content-generator/assets/backgrounds/default.mp4` — currently a 60-second black placeholder. **Replace with a real gameplay/background video** (≥ 30 s, ideally 1080p or wider, landscape).
- `automated-content-generator/assets/profile.png` — currently a gray square. Replace with your actual profile picture if you care about tweet image styling.
- Selenium tweet-image scraping (`images_win.py`) — Chrome is installed and Selenium runs, but both external tweet-generator sites have changed their HTML. The pipeline falls back to plain text overlays. Fix the scrapers or swap in a local image generator when you want polished tweet-card styling.

---

## Quick start

### 1. Activate the venv

```bash
# Windows (bash / Git Bash)
source .venv/Scripts/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 2. Run the bridge with a script

```bash
python openclaw/skills/video-factory/bridge.py "Your full narration script goes here."
```

Output: `automated-content-generator/result/<sanitized_title>.mp4`

Pipe a script instead:

```bash
echo "Some longer script content..." | python openclaw/skills/video-factory/bridge.py
```

### 3. Verify it worked

```
automated-content-generator/result/your_sanitized_title.mp4
```

---

## First-time setup (if starting fresh on a new machine)

```bash
# 1. Create venv
python -m venv .venv

# 2. Install all deps
.venv/Scripts/pip install -r requirements.txt   # Windows
# pip install -r requirements.txt               # macOS/Linux (after activating)

# 3. Copy env template
cp automated-content-generator/.env.template automated-content-generator/.env
# Fill in values — see .env section below

# 4. Add a background video
# Drop a real .mp4 into:
#   automated-content-generator/assets/backgrounds/default.mp4
# (min ~30 s; pipeline picks a random subclip)

# 5. Add a profile image (optional)
# automated-content-generator/assets/profile.png

# 6. Smoke test
python openclaw/skills/video-factory/bridge.py "This is a ten second test script."
```

All required directories (`assets/temp/`, `assets/backgrounds/`, `result/`) already exist in the repo.

---

## Environment variables

`automated-content-generator/.env` — copy from `.env.template`.

| Variable | Required for | Notes |
|----------|-------------|-------|
| `REDDIT_CLIENT_ID` | Reddit scrape path | From reddit.com/prefs/apps |
| `REDDIT_CLIENT_SECRET` | Reddit scrape path | |
| `REDDIT_USERNAME` | Reddit scrape path | |
| `REDDIT_PASSWORD` | Reddit scrape path | |
| `INSTAGRAM_USERNAME` | Instagram upload | |
| `INSTAGRAM_PASSWORD` | Instagram upload | |
| `INSTAGRAM_SECRET` | Instagram upload | 2FA TOTP secret |

**None of these are needed for `bridge.py`** — the video-factory skill takes a script directly and skips Reddit entirely.

---

## Repo layout

```
AutoBrainrot/
├── .venv/                          # Python 3.10 venv (gitignored)
├── requirements.txt                # Unified Python deps for the whole pipeline
├── openclaw/
│   ├── skills/
│   │   └── video-factory/
│   │       ├── bridge.py           # Entry point: script → video
│   │       └── SKILL.md            # OpenClaw skill manifest
│   └── src/                        # TypeScript orchestration (WhatsApp, plugins, etc.)
└── automated-content-generator/    # video-gen (nested git repo)
    ├── config.py                   # Pipeline config: voice, video list, handles, etc.
    ├── main.py                     # Full Reddit → video → upload pipeline
    ├── .env                        # Secrets (gitignored)
    ├── assets/
    │   ├── backgrounds/            # Drop .mp4 files here (default: default.mp4)
    │   ├── temp/                   # Scratch space; auto-cleaned after each run
    │   ├── pics/                   # Profile pic pool for generated comment images
    │   └── profile.png             # Profile image for tweet-card screenshots
    └── src/
        ├── text_to_speech.py       # TTS (gTTS fallback when Streamlabs is down)
        ├── background.py           # Clips a subclip from a background video
        ├── images_win.py           # Selenium tweet-card screenshot generators (Windows)
        ├── images_linux.py         # Same, Linux
        ├── final_video.py          # moviepy compositor
        └── reddit_scrape.py        # Reddit PRAW scraper (full pipeline only)
```

---

## Configuration

`automated-content-generator/config.py` — edit directly, no restart needed between runs.

| Setting | Default | What it does |
|---------|---------|--------------|
| `video_list` | `["default.mp4"]` | Background video filename(s) in `assets/backgrounds/`; one is picked at random per run |
| `tts_voice` | `"Matthew"` | Polly voice name — ignored when falling back to gTTS |
| `comm_length` | `30` | Target video length in seconds |
| `subred` | `"askreddit"` | Subreddit to scrape (full pipeline only) |
| `name` / `username` / `theme` | `""` / `""` / `"dim"` | Tweet-card display name, handle, and theme |

---

## Pipeline stages

```
script string
    │
    ▼
text_to_speech()        gTTS → assets/temp/title.mp3, 0.mp3, …
    │
    ▼
background()            Clips default.mp4 → assets/temp/clip.mp4
    │
    ▼
title_image()           Selenium → assets/temp/title.png  (falls back to Pillow)
comments_image()        Selenium → assets/temp/0.png, …   (falls back to Pillow)
    │
    ▼
make_final_video()      moviepy composites everything → result/<name>.mp4
    │
    ▼
remove_temp_files()     Cleans assets/temp/ (keeps clip.mp4)
```

---

## Known issues / next steps

- **Tweet-card image quality** — Selenium scrapers target two external sites that have changed their HTML. The fallback is plain white text on dark background. To get real tweet-card styling: fix the CSS selectors in `src/images_win.py`, swap in a local HTML renderer, or generate images with a different library.
- **TTS voice variety** — gTTS only has language/accent options, not named voices. If you want named voices (Matthew, Emma, etc.) without Streamlabs, consider AWS Polly directly or ElevenLabs.
- **Background video duration** — `background.py` picks a random start between second 20 and `(duration - script_length)`. Background videos shorter than ~30 s will crash. The placeholder `default.mp4` is 60 s; real content should be longer.
- **OpenClaw / TypeScript side** — not yet wired to the Python bridge. The skill manifest is at `openclaw/skills/video-factory/SKILL.md`; integration with the OpenClaw runtime is the next step.
