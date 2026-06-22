#!/usr/bin/env python3
"""Analyze a YouTube trading video: fetch transcript → call LLM → output structured summary.

Usage:
    # Analyze latest video from default channel (Rhino Finance)
    python3 scripts/analyze.py

    # Analyze a specific video
    python3 scripts/analyze.py --url "https://www.youtube.com/watch?v=VIDEO_ID"

    # Use a specific LLM provider
    python3 scripts/analyze.py --provider openai --model gpt-4o

    # Save output to file
    python3 scripts/analyze.py -o summary.md
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CHANNEL = "https://www.youtube.com/@RhinoFinance"

SYSTEM_PROMPT = """You are a financial analyst assistant. Given a YouTube video transcript, extract ALL trading and market information into a structured Chinese summary.

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
- If the transcript mentions charts/tables not read aloud, note them as [屏幕数据]
- Keep it concise but comprehensive — don't omit any trading signal
- Output in Chinese unless the transcript is entirely in English
"""


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


def call_llm_openai(transcript: str, model: str = "gpt-4o", api_key: str | None = None) -> str:
    """Call OpenAI API for summarization."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai package not installed: pip install openai")

    client = OpenAI(api_key=api_key)
    # Truncate if too long (~120k chars ≈ 30k tokens)
    if len(transcript) > 120000:
        transcript = transcript[:120000] + "\n\n[transcript truncated]"
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Summarize this video transcript:\n\n{transcript}"},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content


def call_llm_anthropic(transcript: str, model: str = "claude-sonnet-4-20250514", api_key: str | None = None) -> str:
    """Call Anthropic API for summarization."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key)
    if len(transcript) > 120000:
        transcript = transcript[:120000] + "\n\n[transcript truncated]"
    resp = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Summarize this video transcript:\n\n{transcript}"},
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
    print(f"Summarizing with {provider}...", file=sys.stderr)
    try:
        if provider == "openai":
            summary = call_llm_openai(transcript_text, model=args.model or "gpt-4o")
        else:
            summary = call_llm_anthropic(transcript_text, model=args.model or "claude-sonnet-4-20250514")
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
