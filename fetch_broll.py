#!/usr/bin/env python3
"""
fetch_broll.py — Download background b-roll for AutoBrainrot.

Usage:
  # YouTube (yt-dlp) — URL or search query:
  python fetch_broll.py yt "https://youtube.com/watch?v=..."
  python fetch_broll.py yt "minecraft parkour"

  # Pexels stock footage (requires PEXELS_API_KEY in env or --key flag):
  python fetch_broll.py pexels "minecraft parkour" --key YOUR_KEY
  python fetch_broll.py pexels "satisfying cooking"    # uses PEXELS_API_KEY env var

Downloaded files land in: automated-content-generator/assets/backgrounds/
Add their filenames to video_list in automated-content-generator/config.py.
"""

import argparse
import os
import re
import sys

BACKGROUNDS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "automated-content-generator", "assets", "backgrounds",
)


def _safe_name(text: str, ext: str = "mp4") -> str:
    s = re.sub(r"[^\w\s-]", "", text)
    s = re.sub(r"[-\s]+", "_", s).strip("_")
    return f"{s[:60].lower()}.{ext}"


# ── yt-dlp ────────────────────────────────────────────────────────────────────

def fetch_youtube(query_or_url: str, max_results: int = 1) -> list[str]:
    """Download from YouTube. Accepts a URL or a plain search query."""
    try:
        import yt_dlp
    except ImportError:
        print("[fetch_broll] yt-dlp not installed. Run: pip install yt-dlp")
        sys.exit(1)

    os.makedirs(BACKGROUNDS_DIR, exist_ok=True)

    # If it's not a URL, treat as a search query
    is_url = query_or_url.startswith("http://") or query_or_url.startswith("https://")
    source = query_or_url if is_url else f"ytsearch{max_results}:{query_or_url}"

    output_template = os.path.join(BACKGROUNDS_DIR, "%(title).60s.%(ext)s")

    ydl_opts = {
        "format": "bestvideo[ext=mp4][height>=1080]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4",
        }],
    }

    downloaded = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(source, download=True)
        entries = info.get("entries", [info]) if info else []
        for entry in entries:
            if entry:
                fn = ydl.prepare_filename(entry)
                # yt-dlp may change extension after merge
                for ext in ["mp4", "mkv", "webm"]:
                    candidate = os.path.splitext(fn)[0] + f".{ext}"
                    if os.path.isfile(candidate):
                        downloaded.append(candidate)
                        break

    return downloaded


# ── Pexels ────────────────────────────────────────────────────────────────────

PEXELS_VIDEO_SEARCH = "https://api.pexels.com/videos/search"


def fetch_pexels(query: str, api_key: str, count: int = 3, min_duration: int = 30) -> list[str]:
    """Download stock videos from Pexels. Returns list of saved paths."""
    try:
        import requests
    except ImportError:
        print("[fetch_broll] requests not installed.")
        sys.exit(1)

    os.makedirs(BACKGROUNDS_DIR, exist_ok=True)

    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "per_page": min(count * 3, 15),  # fetch extra to filter by duration
        "orientation": "landscape",
        "size": "large",
    }

    resp = requests.get(PEXELS_VIDEO_SEARCH, headers=headers, params=params, timeout=15)
    if resp.status_code == 401:
        print("[fetch_broll] Pexels API key is invalid or missing.")
        sys.exit(1)
    resp.raise_for_status()

    data = resp.json()
    videos = data.get("videos", [])
    if not videos:
        print(f"[fetch_broll] No Pexels results for '{query}'.")
        return []

    saved = []
    for video in videos:
        if len(saved) >= count:
            break
        duration = video.get("duration", 0)
        if duration < min_duration:
            continue  # skip clips that are too short for the pipeline

        # Pick highest-quality HD file (width >= 1920 preferred)
        files = sorted(
            video.get("video_files", []),
            key=lambda f: f.get("width", 0),
            reverse=True,
        )
        hd_file = next(
            (f for f in files if f.get("width", 0) >= 1280 and f.get("file_type") == "video/mp4"),
            None,
        )
        if not hd_file:
            continue

        url = hd_file["link"]
        slug = _safe_name(f"pexels_{video.get('id', 'video')}_{query}")
        dest = os.path.join(BACKGROUNDS_DIR, slug)

        print(f"[fetch_broll] Downloading Pexels #{video['id']} ({duration}s) → {slug}")
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in r.iter_content(chunk_size=1 << 16):
                fh.write(chunk)
        saved.append(dest)
        print(f"[fetch_broll] Saved: {dest}")

    return saved


# ── CLI ───────────────────────────────────────────────────────────────────────

def _print_next_steps(paths: list[str]) -> None:
    if not paths:
        print("\n[fetch_broll] No files downloaded.")
        return
    names = [os.path.basename(p) for p in paths]
    print("\n✓ Downloaded:")
    for n in names:
        print(f"  {n}")
    print("\nAdd to automated-content-generator/config.py:")
    print(f"  video_list = {names!r}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch background b-roll for AutoBrainrot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    yt_p = sub.add_parser("yt", help="Download from YouTube via yt-dlp")
    yt_p.add_argument("query", help="YouTube URL or search query")
    yt_p.add_argument("-n", "--count", type=int, default=1, help="Number of results (search only)")

    px_p = sub.add_parser("pexels", help="Download stock footage from Pexels")
    px_p.add_argument("query", help="Search term (e.g. 'minecraft parkour')")
    px_p.add_argument("-n", "--count", type=int, default=3, help="Number of videos to download")
    px_p.add_argument("-d", "--min-duration", type=int, default=30, help="Min clip length in seconds")
    px_p.add_argument("--key", default=None, help="Pexels API key (overrides PEXELS_API_KEY env var)")

    args = parser.parse_args()

    if args.mode == "yt":
        paths = fetch_youtube(args.query, max_results=args.count)
    else:  # pexels
        key = args.key or os.environ.get("PEXELS_API_KEY", "")
        if not key:
            print("[fetch_broll] Pexels API key required. Pass --key or set PEXELS_API_KEY env var.")
            print("  Get a free key at: https://www.pexels.com/api/")
            sys.exit(1)
        paths = fetch_pexels(args.query, key, count=args.count, min_duration=args.min_duration)

    _print_next_steps(paths)


if __name__ == "__main__":
    main()
