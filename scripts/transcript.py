#!/usr/bin/env python3
"""Fetch transcript or captions from a YouTube video.

Tries youtube-transcript-api first, falls back to yt-dlp captions,
and as a last resort extracts audio for transcription.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


def yt_dlp_bin() -> str:
    found = shutil.which("yt-dlp")
    if found:
        return found
    raise RuntimeError("yt-dlp not found; install with: pip install yt-dlp")


def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from a YouTube URL or return as-is if already an ID."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for p in patterns:
        m = re.search(p, url_or_id)
        if m:
            return m.group(1)
    return url_or_id


def fetch_via_api(video_id: str, languages: list[str] | None = None) -> list[dict] | None:
    """Try youtube-transcript-api. Returns list of {start, text} or None."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("youtube-transcript-api not installed, skipping API method", file=sys.stderr)
        return None

    langs = languages or ["zh-Hans", "zh-Hant", "yue", "en"]
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=langs)
        return [{"start": int(s.start), "text": s.text} for s in transcript]
    except Exception as exc:
        print(f"youtube-transcript-api failed: {exc}", file=sys.stderr)
        return None


def fetch_via_ytdlp_captions(video_url: str, output_dir: str) -> list[dict] | None:
    """Try yt-dlp auto-generated/manual captions. Returns list of {start, text} or None."""
    cmd = [
        yt_dlp_bin(), "--skip-download", "--write-auto-subs",
        "--sub-langs", "zh.*,zh-Hans,zh-Hant,en.*",
        "--sub-format", "vtt",
        "-o", os.path.join(output_dir, "subs_%(id)s.%(ext)s"),
        video_url,
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        print(f"yt-dlp captions failed: {proc.stderr.strip()}", file=sys.stderr)
        return None

    # Find the downloaded subtitle file
    for f in os.listdir(output_dir):
        if f.startswith("subs_") and f.endswith(".vtt"):
            return parse_vtt(os.path.join(output_dir, f))
    return None


def parse_vtt(filepath: str) -> list[dict]:
    """Parse a VTT subtitle file into [{start, text}, ...]."""
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Match VTT cue blocks: HH:MM:SS.mmm --> HH:MM:SS.mmm\ntext
    pattern = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})[\.,](\d{3})\s*-->\s*\d{2}:\d{2}:\d{2}[\.,]\d{3}\s*\n(.+?)(?:\n\n|\Z)",
        re.DOTALL,
    )
    for m in pattern.finditer(content):
        h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        start = h * 3600 + mi * 60 + s
        text = m.group(5).strip().replace("\n", " ")
        # Strip VTT tags
        text = re.sub(r"<[^>]+>", "", text)
        if text:
            entries.append({"start": start, "text": text})
    return entries


def fetch_via_audio(video_url: str, output_dir: str) -> str | None:
    """Extract audio as mp3 for external transcription. Returns path or None."""
    out_path = os.path.join(output_dir, "audio.mp3")
    cmd = [
        yt_dlp_bin(), "-f", "ba", "--extract-audio", "--audio-format", "mp3",
        "--audio-quality", "5",
        "-o", out_path,
        video_url,
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        print(f"yt-dlp audio extraction failed: {proc.stderr.strip()}", file=sys.stderr)
        return None
    # yt-dlp may append extension
    for f in os.listdir(output_dir):
        if f.startswith("audio"):
            return os.path.join(output_dir, f)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_url", help="YouTube video URL or ID")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--output-dir", default=None, help="Temp directory for intermediate files")
    parser.add_argument("--method", choices=["api", "captions", "audio"], default="api",
                        help="Preferred method: api (default), captions, audio")
    parser.add_argument("--languages", default="zh-Hans,zh-Hant,yue,en",
                        help="Comma-separated language codes for API method")
    args = parser.parse_args()

    video_id = extract_video_id(args.video_url)
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    output_dir = args.output_dir or tempfile.mkdtemp(prefix="yt_transcript_")
    os.makedirs(output_dir, exist_ok=True)
    languages = [l.strip() for l in args.languages.split(",")]

    segments = None
    method_used = None

    # Try methods in order based on preference
    if args.method == "api":
        segments = fetch_via_api(video_id, languages)
        method_used = "api"
        if not segments:
            segments = fetch_via_ytdlp_captions(video_url, output_dir)
            method_used = "captions"
    elif args.method == "captions":
        segments = fetch_via_ytdlp_captions(video_url, output_dir)
        method_used = "captions"
    else:
        # audio method
        audio_path = fetch_via_audio(video_url, output_dir)
        if audio_path:
            print(json.dumps({"method": "audio", "path": audio_path}, ensure_ascii=False))
            return 0
        return 1

    if not segments:
        print("error: all transcript methods failed", file=sys.stderr)
        return 1

    # Format output
    lines = [f"{s['start']}s: {s['text']}" for s in segments]
    text = "\n".join(lines)

    result = {
        "video_id": video_id,
        "method": method_used,
        "segments": segments,
        "text": text,
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        result["saved_to"] = args.output
        print(json.dumps({"method": method_used, "saved_to": args.output, "segments": len(segments)}))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
