#!/usr/bin/env python3
"""Analyze a YouTube trading video: fetch transcript → auto-extract key frames → call LLM → output structured summary.

Usage:
    # Analyze latest video from default channel (Rhino Finance)
    python3 scripts/analyze.py

    # Analyze a specific video
    python3 scripts/analyze.py --url "https://www.youtube.com/watch?v=VIDEO_ID"

    # Use a specific LLM provider
    python3 scripts/analyze.py --provider openai --model gpt-4o

    # Save output to file
    python3 scripts/analyze.py -o summary.md

    # Disable auto frame extraction
    python3 scripts/analyze.py --no-frames
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
REFS_DIR = os.path.join(os.path.dirname(SCRIPTS_DIR), "references")
DEFAULT_CHANNEL = "https://www.youtube.com/@RhinoFinance"

# Load trading knowledge if available
KNOWLEDGE_PATH = os.path.join(REFS_DIR, "trading_knowledge.md")
KNOWLEDGE_SECTION = ""
if os.path.exists(KNOWLEDGE_PATH):
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        KNOWLEDGE_SECTION = f"\n\n## Reference: Trading Knowledge\n\n{f.read()}"

SYSTEM_PROMPT = f"""You are a financial analyst assistant. Given a YouTube video transcript (and optionally key frame screenshots), extract ALL trading and market information into a structured Chinese summary.

When frame screenshots are provided, use them to:
- Verify price levels, charts, and data tables shown on screen
- Extract data the speaker references but doesn't read aloud
- Identify ticker symbols, support/resistance levels, and option chains visible on screen
- Note any discrepancy between what the speaker says and what's shown

Output format (use this exact structure):

**标题** | **频道** | **发布日期** | **时长** | **链接**

## 一句话结论
(One sentence: the single most important call/thesis from this video)

## 核心观点
- Market regime, direction, thesis, timing

## 宏观/消息
- Fed, data, earnings, liquidity, policy, geopolitical, commodity drivers

## 板块与主题
- Sector strength/weakness, rotation, themes (AI, semis, crypto, China, energy, etc.)

## 个股/ETF

| 标的 | 方向/观点 | 关键位/条件 | 风险 |
|---|---|---|---|
| TICKER | long/short/neutral | entry/stop/target | risk note |

## 交易含义
- What supports continuation
- What invalidates the setup
- What to watch next

## 风险提醒
- Chasing risk, event risk, concentration, liquidity, paid promotion

Rules:
- Preserve all tickers, numbers, dates, price levels, percentages exactly as stated
- Mark uncertain items with (待确认)
- For data visible in screenshots but not in transcript, cite as [屏幕数据 @Xs] with the timestamp
- Keep it concise but comprehensive — don't omit any trading signal
- Output in Chinese unless the transcript is entirely in English
{KNOWLEDGE_SECTION}
"""


def detect_key_timestamps(segments: list[dict], interval: int = 120) -> list[int]:
    """Detect timestamps worth extracting frames from.

    Strategy:
    1. Always extract at regular intervals (every `interval` seconds)
    2. Boost timestamps where speaker references visual content
    """
    if not segments:
        return []

    # Get video duration from last segment
    max_time = max(s["start"] for s in segments)
    timestamps = set()

    # Regular interval sampling (at least 15 frames, max 30)
    step = max(60, min(interval, max_time // 15))
    t = 0
    while t <= max_time:
        timestamps.add(t)
        t += step

    # Boost: segments containing visual reference keywords
    visual_keywords = [
        "看这个", "你看", "屏幕上", "这个图", "这个表", "这里显示",
        "如图所示", "大家看", "注意看", "标出来", "圈出来",
        "look at", "see this", "shown here", "as you can see",
        "chart", "graph", "on screen",
    ]
    for seg in segments:
        text = seg["text"].lower()
        if any(kw in text for kw in visual_keywords):
            timestamps.add(seg["start"])

    return sorted(timestamps)


def extract_frames(video_url: str, timestamps: list[int], output_dir: str) -> list[dict]:
    """Extract frames at given timestamps using ffmpeg.

    Returns list of {timestamp, path} for successfully extracted frames.
    """
    if not shutil.which("ffmpeg"):
        print("warning: ffmpeg not found, skipping frame extraction", file=sys.stderr)
        return []

    # Get stream URL (one request only)
    try:
        yt_bin = shutil.which("yt-dlp")
        if not yt_bin:
            print("warning: yt-dlp not found, skipping frame extraction", file=sys.stderr)
            return []
        cmd = [yt_bin, "-f", "best[height<=480]/best", "--get-url", video_url]
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
        if proc.returncode != 0:
            print(f"warning: could not get stream URL: {proc.stderr.strip()}", file=sys.stderr)
            return []
        stream_url = proc.stdout.strip().split("\n")[0]
    except Exception as exc:
        print(f"warning: stream URL lookup failed: {exc}", file=sys.stderr)
        return []

    os.makedirs(output_dir, exist_ok=True)
    frames = []
    procs = []
    for t in timestamps:
        out_path = os.path.join(output_dir, f"frame_{t}s.jpg")
        ffmpeg_cmd = [
            "ffmpeg", "-ss", str(t),
            "-i", stream_url,
            "-vframes", "1", "-update", "1",
            "-q:v", "2", out_path, "-y",
        ]
        procs.append((t, out_path, subprocess.Popen(
            ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )))

    for t, out_path, p in procs:
        p.wait()
        if p.returncode == 0 and os.path.exists(out_path):
            frames.append({"timestamp": t, "path": out_path})

    return frames


def format_timestamp(seconds: int) -> str:
    """Format seconds into HH:MM:SS."""
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def run_script(name: str, args: list[str]) -> str:
    """Run a sibling script and return stdout."""
    script_path = os.path.join(SCRIPTS_DIR, name)
    cmd = [sys.executable, script_path] + args
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"{name} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def get_latest_video_url(channel: str = DEFAULT_CHANNEL) -> str:
    """Get the latest video URL from a channel."""
    raw = run_script("latest_video.py", ["--channel", channel, "--count", "1"])
    items = json.loads(raw)
    if not items:
        raise RuntimeError("No videos found")
    return items[0]["webpage_url"]


def get_transcript(video_url: str, output_dir: str) -> tuple[str, list[dict]]:
    """Fetch transcript, return (full_text, segments)."""
    raw = run_script("transcript.py", [video_url, "--output-dir", output_dir])
    data = json.loads(raw)
    return data.get("text", ""), data.get("segments", [])


def call_llm_openai(transcript: str, frames: list[dict] | None = None,
                     model: str = "gpt-4o", api_key: str | None = None) -> str:
    """Call OpenAI API for summarization (supports vision if frames provided)."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai package not installed: pip install openai")

    import base64

    client = OpenAI(api_key=api_key)
    if len(transcript) > 120000:
        transcript = transcript[:120000] + "\n\n[transcript truncated]"

    # Build user message content
    content = [{"type": "text", "text": f"Summarize this video transcript:\n\n{transcript}"}]

    # Add frames as images if available
    if frames:
        content.append({"type": "text", "text": "\n\n--- Key Frame Screenshots ---\n"})
        for frame in frames:
            ts = format_timestamp(frame["timestamp"])
            try:
                with open(frame["path"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                content.append({"type": "text", "text": f"\n[Frame @ {ts}]"})
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"},
                })
            except Exception as exc:
                print(f"warning: could not read frame {frame['path']}: {exc}", file=sys.stderr)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content


def call_llm_anthropic(transcript: str, frames: list[dict] | None = None,
                        model: str = "claude-sonnet-4-20250514", api_key: str | None = None) -> str:
    """Call Anthropic API for summarization (supports vision if frames provided)."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed: pip install anthropic")

    import base64

    client = anthropic.Anthropic(api_key=api_key)
    if len(transcript) > 120000:
        transcript = transcript[:120000] + "\n\n[transcript truncated]"

    # Build user message content
    content = [{"type": "text", "text": f"Summarize this video transcript:\n\n{transcript}"}]

    # Add frames as images if available
    if frames:
        content.append({"type": "text", "text": "\n\n--- Key Frame Screenshots ---\n"})
        for frame in frames:
            ts = format_timestamp(frame["timestamp"])
            try:
                with open(frame["path"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                content.append({"type": "text", "text": f"\n[Frame @ {ts}]"})
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
                })
            except Exception as exc:
                print(f"warning: could not read frame {frame['path']}: {exc}", file=sys.stderr)

    resp = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": content},
        ],
    )
    return resp.content[0].text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", "-u", help="YouTube video URL (default: latest from default channel)")
    parser.add_argument("--channel", default=DEFAULT_CHANNEL, help="YouTube channel URL")
    parser.add_argument("--provider", choices=["openai", "anthropic"], default=None,
                        help="LLM provider (auto-detect from env if not set)")
    parser.add_argument("--model", default=None, help="Model name (provider-specific default)")
    parser.add_argument("--transcript-only", action="store_true", help="Only fetch transcript, skip LLM")
    parser.add_argument("--no-frames", action="store_true", help="Disable automatic frame extraction")
    parser.add_argument("--frame-interval", type=int, default=120,
                        help="Seconds between auto-extracted frames (default: 120)")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--transcript-file", help="Use existing transcript file instead of fetching")
    args = parser.parse_args()

    # Resolve video URL
    video_url = args.url
    if not video_url:
        print("Fetching latest video...", file=sys.stderr)
        video_url = get_latest_video_url(args.channel)
        print(f"Found: {video_url}", file=sys.stderr)

    # Fetch or load transcript
    segments = []
    if args.transcript_file:
        with open(args.transcript_file, "r", encoding="utf-8") as f:
            transcript_text = f.read()
        print(f"Loaded transcript from {args.transcript_file}", file=sys.stderr)
    else:
        tmpdir = tempfile.mkdtemp(prefix="yt_analyze_")
        print("Fetching transcript...", file=sys.stderr)
        transcript_text, segments = get_transcript(video_url, tmpdir)
        if not transcript_text:
            print("error: could not fetch transcript", file=sys.stderr)
            return 1
        print(f"Got {len(segments)} segments", file=sys.stderr)

    # Save transcript for reference
    transcript_path = os.path.join(tempfile.gettempdir(), "last_transcript.txt")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcript_text)
    print(f"Transcript saved to {transcript_path}", file=sys.stderr)

    if args.transcript_only:
        print(transcript_text)
        return 0

    # Auto-extract key frames
    frames = []
    if not args.no_frames and segments:
        print("Detecting key timestamps...", file=sys.stderr)
        timestamps = detect_key_timestamps(segments, interval=args.frame_interval)
        print(f"Extracting {len(timestamps)} key frames...", file=sys.stderr)
        frames_dir = os.path.join(tempfile.gettempdir(), "yt_frames")
        frames = extract_frames(video_url, timestamps, frames_dir)
        print(f"Extracted {len(frames)} frames", file=sys.stderr)

    # Resolve LLM provider
    provider = args.provider
    if not provider:
        if os.environ.get("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
        else:
            print("error: no LLM provider. Set ANTHROPIC_API_KEY or OPENAI_API_KEY, or use --transcript-only", file=sys.stderr)
            return 1

    # Call LLM
    print(f"Summarizing with {provider} (with {len(frames)} frames)...", file=sys.stderr)
    try:
        if provider == "openai":
            summary = call_llm_openai(transcript_text, frames=frames, model=args.model or "gpt-4o")
        else:
            summary = call_llm_anthropic(transcript_text, frames=frames, model=args.model or "claude-sonnet-4-20250514")
    except Exception as exc:
        print(f"error: LLM call failed: {exc}", file=sys.stderr)
        return 1

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"Summary saved to {args.output}", file=sys.stderr)
    else:
        print(summary)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
