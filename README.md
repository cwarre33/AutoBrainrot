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
- **OpenClaw / TypeScript side** — skill manifest at `openclaw/skills/video-factory/SKILL.md`. See **Testing OpenClaw** below to run the gateway and agent so the agent can invoke the video-factory skill.

---

## Testing OpenClaw

Use this to run the OpenClaw gateway and agent so it can run the video-factory skill (build/post videos from natural language).

### 1. Install OpenClaw (Node 22+ and pnpm)

From the **repo root** (AutoBrainrot):

```powershell
cd openclaw
pnpm install
```

(If you don’t have pnpm: `npm install -g pnpm`.)

### 2. Create OpenClaw config

Create or edit **`%USERPROFILE%\.openclaw\openclaw.json`** (e.g. `C:\Users\YourName\.openclaw\openclaw.json`). Use your **actual repo root path** for `workspace` and `extraDirs` (Windows: use forward slashes or escaped backslashes in JSON).

Minimal config so the agent sees the video-factory skill and runs from the repo (include `gateway.mode` so the gateway starts without "Missing config"):

```json
{
  "gateway": { "mode": "local" },
  "agents": {
    "defaults": {
      "workspace": "C:/Users/YourName/CleanDevEnvironment/Passion/OpenClaw/AutoBrainrot"
    }
  },
  "skills": {
    "load": {
      "extraDirs": ["C:/Users/YourName/CleanDevEnvironment/Passion/OpenClaw/AutoBrainrot/openclaw/skills"]
    }
  },
  "providers": {
    "anthropic": { "apiKey": "your-anthropic-key" }
  },
  "models": {
    "default": "anthropic/claude-sonnet-4-20250514"
  }
}
```

- Replace `YourName` and the path with your real user and repo path.
- `agents.defaults.workspace`: repo root so the agent runs `python openclaw/skills/video-factory/bridge.py ...` from the right directory.
- `skills.load.extraDirs`: so OpenClaw loads the `video-factory` skill from `openclaw/skills`.
- Set a real `providers` / `models` key you use (e.g. OpenAI, Anthropic). The agent needs at least one model to respond.

### 3. Start the gateway

From **`openclaw/`**:

```powershell
pnpm openclaw gateway --port 18789 --verbose
```

To use the project’s **NVIDIA NIM** model (so the log shows `agent model: nvidia/llama-3.1-nemotron-70b-instruct`), set the config before starting:

```powershell
cd openclaw
$env:OPENCLAW_CONFIG_PATH = "$PWD\openclaw.autobrainrot.json"
pnpm openclaw gateway --port 18789 --verbose --allow-unconfigured
```

Leave this terminal open. You should see the gateway listening (e.g. on 18789).

### 4. Run the agent (second terminal)

From the **repo root** (AutoBrainrot), in a **new** terminal:

```powershell
cd openclaw
pnpm openclaw agent --agent main --message "Make a short video about North Carolina and post it to Instagram. Use the video-factory skill: run the bridge with a topic and --post."
```

The agent should see the video-factory skill in its prompt and run something like:

`python openclaw/skills/video-factory/bridge.py --topic "North Carolina" --post`

(from the workspace directory). The bridge uses your existing `.venv` and `automated-content-generator/.env`; ensure **Python and the venv are on PATH** when the agent runs (or run the agent from the same environment where `python` points to `.venv`).

### 5. Optional: run agent in dev (from repo root)

If you want the agent to use the repo as workspace and your PATH (e.g. so `python` is the venv):

```powershell
cd C:\Users\YourName\CleanDevEnvironment\Passion\OpenClaw\AutoBrainrot
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"
cd openclaw
pnpm openclaw agent --agent main --message "Use the video-factory skill to build and post a short about octopuses. Run bridge with --topic and --post."
```

### Troubleshooting

- **“Skill not found”** — Check `extraDirs` in `openclaw.json` and that the path contains `openclaw/skills` (with a `video-factory` folder and `SKILL.md`).
- **“python not found”** — Start the agent from the repo root and prepend `.venv\Scripts` to PATH so `python` is the venv Python.
- **Bridge runs but upload fails** — Confirm `automated-content-generator/.env` has `INSTAGRAM_USERNAME` and `INSTAGRAM_PASSWORD` (and optional `INSTAGRAM_SECRET` for 2FA).
- **Gateway not found** — Ensure the gateway is running in the first terminal and the second terminal uses the same OpenClaw install (`cd openclaw` then `pnpm openclaw agent ...`).
- **"Missing config"** — Add `"gateway": { "mode": "local" }` to `~/.openclaw/openclaw.json`, or run gateway with `--allow-unconfigured`.
- **"Pass --to &lt;E.164&gt;, --session-id, or --agent to choose a session"** — The agent CLI needs a target. Use `--agent main` for the default agent (e.g. `pnpm openclaw agent --agent main --message "..."`).
- **"No API key found for provider anthropic"** / **Gateway log shows "agent model: anthropic/…"** — Use the project’s **NVIDIA NIM** model and key. Set the project config for **both** the gateway and the agent so they use nvidia:  
  **Gateway:** `$env:OPENCLAW_CONFIG_PATH = "$PWD\openclaw.autobrainrot.json"; pnpm openclaw gateway --port 18789 --verbose --allow-unconfigured`  
  **Agent:** `$env:OPENCLAW_CONFIG_PATH = "$PWD\openclaw.autobrainrot.json"; pnpm openclaw agent --agent main --message "..."`  
  (Run both from `openclaw/`; the NIM key is loaded from `automated-content-generator/.env`.)  
  Alternatively, add to `~/.openclaw/openclaw.json`: `"agents": { "defaults": { "model": { "primary": "nvidia/llama-3.1-nemotron-70b-instruct" } } }`.
- **"Unknown model: nvidia/llama-3.1-nemotron-70b-instruct"** when the agent runs via the gateway — The gateway may be using an old build. From `openclaw/` force a rebuild, then restart the gateway:  
  `$env:OPENCLAW_FORCE_BUILD = "1"; $env:OPENCLAW_CONFIG_PATH = "$PWD\openclaw.autobrainrot.json"; pnpm openclaw gateway --port 18789 --verbose --allow-unconfigured`
- **"404 status code (no body)"** when using the nvidia model — The NIM API returned 404. Usually the model is not enabled for your API key: open [build.nvidia.com](https://build.nvidia.com), sign in, open the [Nemotron 70B](https://build.nvidia.com/nvidia/llama-3_1-nemotron-70b-instruct) (or your chosen NIM) page, and ensure the model is added/activated for your account so your key can call it. If 404 persists, try the alternate model id in config: set `agents.defaults.model.primary` to `nvidia/llama-3_1-nemotron-70b-instruct` (underscore instead of dot in 3.1).
