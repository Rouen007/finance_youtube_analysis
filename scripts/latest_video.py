#!/usr/bin/env python3
"""Fetch latest public uploads from a YouTube channel.

Defaults to Rhino Finance / 犀牛哥 if no channel is specified.
Supports any YouTube channel via the --channel flag.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Any


DEFAULT_CHANNEL = "https://www.youtube.com/@RhinoFinance"


def yt_dlp_bin() -> str:
    found = shutil.which("yt-dlp")
    if found:
        return found
    raise RuntimeError("yt-dlp not found; install with: pip install yt-dlp")


def run_yt_dlp(channel_url: str, count: int) -> list[dict[str, Any]]:
    videos_url = channel_url.rstrip("/") + "/videos"
    cmd = [
        yt_dlp_bin(),
        "--flat-playlist",
        "--playlist-end",
        str(count),
        "--dump-json",
        videos_url,
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "yt-dlp failed")

    items: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        video_id = raw.get("id")
        if not video_id:
            continue
        items.append(
            {
                "id": video_id,
                "title": raw.get("title"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "webpage_url": raw.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}",
                "channel": raw.get("channel") or raw.get("uploader"),
                "duration": raw.get("duration"),
                "view_count": raw.get("view_count"),
                "live_status": raw.get("live_status"),
            }
        )
    return items


def enrich_metadata(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for item in items:
        cmd = [
            yt_dlp_bin(),
            "--skip-download",
            "--dump-json",
            item["webpage_url"],
        ]
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
        if proc.returncode != 0:
            enriched.append(item)
            continue
        try:
            raw = json.loads(proc.stdout)
        except json.JSONDecodeError:
            enriched.append(item)
            continue
        item.update(
            {
                "title": raw.get("title") or item.get("title"),
                "upload_date": raw.get("upload_date"),
                "timestamp": raw.get("timestamp"),
                "channel": raw.get("channel") or item.get("channel"),
                "duration_string": raw.get("duration_string"),
                "description": raw.get("description"),
                "webpage_url": raw.get("webpage_url") or item.get("webpage_url"),
            }
        )
        enriched.append(item)
    return enriched


def extract_frames(video_url: str, timestamps: list[int], output_dir: str = "/tmp") -> list[str]:
    """Extract key frames from a video at given timestamps (seconds).

    Uses ffmpeg seek to pull only the needed HLS chunks — no full download.
    Returns a list of saved frame paths.
    """
    # Get stream URL (one request only)
    cmd = [yt_dlp_bin(), "-f", "best[height<=480]/best", "--get-url", video_url]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to get stream URL: {proc.stderr.strip()}")
    stream_url = proc.stdout.strip().split("\n")[0]

    paths = []
    procs = []
    for t in timestamps:
        out_path = os.path.join(output_dir, f"frame_{t}.jpg")
        ffmpeg_cmd = [
            "ffmpeg", "-ss", str(t),
            "-i", stream_url,
            "-vframes", "1", "-update", "1",
            "-q:v", "2", out_path, "-y",
        ]
        procs.append((out_path, subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)))

    for out_path, p in procs:
        p.wait()
        if p.returncode == 0 and os.path.exists(out_path):
            paths.append(out_path)

    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", default=DEFAULT_CHANNEL, help="YouTube channel URL")
    parser.add_argument("--count", type=int, default=1, help="Number of latest uploads to return")
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip per-video metadata lookup after flat playlist discovery",
    )
    parser.add_argument(
        "--video-url",
        help="Extract frames from this video URL (use with --timestamps)",
    )
    parser.add_argument(
        "--timestamps",
        help="Comma-separated timestamps in seconds for frame extraction (e.g. 3100,3130,3175)",
    )
    parser.add_argument(
        "--output-dir",
        default="/tmp",
        help="Directory to save extracted frames (default: /tmp)",
    )
    args = parser.parse_args()

    # Frame extraction mode
    if args.video_url and args.timestamps:
        if not shutil.which("ffmpeg"):
            print("error: ffmpeg not found; install with: brew install ffmpeg / apt install ffmpeg", file=sys.stderr)
            return 1
        timestamps = [int(t.strip()) for t in args.timestamps.split(",")]
        try:
            paths = extract_frames(args.video_url, timestamps, args.output_dir)
            print(json.dumps({"frames": paths}, ensure_ascii=False, indent=2))
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        return 0

    # Channel listing mode
    try:
        items = run_yt_dlp(args.channel, args.count)
        if not args.no_enrich:
            items = enrich_metadata(items)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(items, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
