---
name: rhino-finance-latest
description: Fetch and summarize trading info from YouTube videos. Defaults to Rhino Finance / 犀牛哥. Use when the user asks for 犀牛哥, RhinoFinance, or wants to extract trading signals, market views, tickers, or actionable takeaways from any YouTube finance video.
---

# Rhino Finance Latest

Fetch YouTube trading videos, extract transcripts, and output structured trading summaries.

Default channel: `https://www.youtube.com/@RhinoFinance`
Supports any YouTube channel via `--channel` flag.

## Quick Start

```bash
# Get latest video info
python3 scripts/latest_video.py --count 1

# Fetch transcript only
python3 scripts/transcript.py "VIDEO_URL"

# Full analysis (transcript + LLM summary)
python3 scripts/analyze.py --url "VIDEO_URL"
```

## Transcript Workflow

Try these methods in order:

1. **youtube-transcript-api** (fastest):
   ```bash
   python3 scripts/transcript.py "VIDEO_URL"
   ```

2. **yt-dlp captions** (fallback):
   ```bash
   python3 scripts/transcript.py "VIDEO_URL" --method captions
   ```

3. **Audio transcription** (last resort):
   ```bash
   python3 scripts/transcript.py "VIDEO_URL" --method audio
   ```
   Then use local Whisper or faster-whisper to transcribe the audio file.

## Key Frame Extraction

When the transcript references charts, tables, or on-screen data not read aloud:

```bash
python3 scripts/latest_video.py --video-url "VIDEO_URL" --timestamps 3100,3130,3175
```

Read extracted frames visually to capture price levels, options tables, etc.

## Summary Format

Output in Chinese unless the user asks otherwise:

- **一句话结论**: single most important call
- **核心观点**: market regime, direction, thesis, timing
- **宏观/消息**: Fed, data, earnings, policy, geopolitics
- **板块与主题**: sector rotation, themes, capital flows
- **个股/ETF**: tickers with table (标的 / 方向/观点 / 关键位/条件 / 风险)
- **交易含义**: continuation / invalidation conditions
- **风险提醒**: chasing, event, liquidity, concentration risks

## When Used as Claude Code Skill

When invoked via `/rhino-finance-latest` or naturally ("犀牛哥最新视频讲了什么"):

1. Run `python3 scripts/latest_video.py --count 1` to find the video
2. Run `python3 scripts/transcript.py "VIDEO_URL"` to get the transcript
3. Summarize the transcript yourself using the format above
4. If the transcript references on-screen data, extract key frames with `--video-url` + `--timestamps`
5. Update `references/core-thesis.md` if a recurring framework is revealed

## Dependencies

- Python 3.9+
- `pip install yt-dlp youtube-transcript-api`
- ffmpeg (optional, for frame extraction)
- For standalone LLM mode: `pip install openai` or `pip install anthropic`
