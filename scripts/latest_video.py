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

    candidates = [
        "/usr/local/bin/yt-dlp",
        "/opt/homebrew/bin/yt-dlp",
        os.path.expanduser("~/Library/Python/3.9/bin/yt-dlp"),
        os.path.expanduser("~/Library/Python/3.10/bin/yt-dlp"),
        os.path.expanduser("~/Library/Python/3.11/bin/yt-dlp"),
        os.path.expanduser("~/Library/Python/3.12/bin/yt-dlp"),
        os.path.expanduser("~/.local/bin/yt-dlp"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    raise RuntimeError("yt-dlp not found; install with: python3 -m pip install --user yt-dlp")


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", default=DEFAULT_CHANNEL, help="YouTube channel URL")
    parser.add_argument("--count", type=int, default=1, help="Number of latest uploads to return")
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip per-video metadata lookup after flat playlist discovery",
    )
    args = parser.parse_args()

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
