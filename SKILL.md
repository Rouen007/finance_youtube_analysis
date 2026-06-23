---
name: rhino-finance-latest
description: Fetch and summarize Rhino Finance / 犀牛哥 YouTube content. Use when the user asks for 犀牛哥, RhinoFinance, Rhino Finance, the latest video from https://www.youtube.com/@RhinoFinance, or wants a Chinese translation, finance/trading summary, ticker extraction, market view, timestamps, or actionable takeaways from Rhino Finance videos.
---

# Rhino Finance Latest

## Goal

Fetch Rhino Finance's latest public YouTube upload, obtain transcript or captions, translate into Chinese, and summarize market/trading takeaways without inventing content.

Default channel: `https://www.youtube.com/@RhinoFinance`

Maintain `references/core-thesis.md` as the local durable record. Update it only when transcript-grounded summaries reveal a repeated market model, recurring watchlist logic, or durable risk rule.

## Quick Start

1. Find the latest upload:
   ```bash
   python3 scripts/latest_video.py --count 1
   ```
2. Use the returned `webpage_url` as the video URL.
3. Get metadata:
   ```bash
   yt-dlp --skip-download --print "TITLE:%(title)s" --print "DATE:%(upload_date)s" \
     --print "CHANNEL:%(channel)s" --print "DURATION:%(duration_string)s" "VIDEO_URL"
   ```
4. Fetch transcript/captions, save under `/tmp`, then summarize.

## Transcript Workflow

1. **youtube-transcript-api** (fastest):
   ```bash
   python3 -c "
   from youtube_transcript_api import YouTubeTranscriptApi
   t = YouTubeTranscriptApi().fetch('VIDEO_ID', languages=['zh-Hans','zh-Hant','yue','en'])
   for x in t: print(f'{int(x.start)}s: {x.text}')
   " > /tmp/rhino_VIDEO_ID.txt
   ```
   Install if missing: `pip3 install youtube-transcript-api`

2. **yt-dlp captions** (fallback):
   ```bash
   yt-dlp --skip-download --write-auto-subs --sub-langs "zh.*,en.*" \
     --sub-format vtt -o "/tmp/rhino_%(id)s.%(ext)s" "VIDEO_URL"
   ```

3. **Audio transcription** (last resort):
   ```bash
   yt-dlp -f ba --extract-audio --audio-format mp3 --audio-quality 5 \
     -o "/tmp/rhino_%(id)s.%(ext)s" "VIDEO_URL"
   ```
   Use local faster-whisper if available.

## Summary Format

Start with: `标题 | Rhino Finance / 犀牛哥 | 发布日期 | 时长 | 链接`

Then structure:

- **一句话结论**: Core call in one sentence.
- **核心观点**: Market regime, direction, thesis, timing.
- **宏观/消息**: Fed, data, earnings, policy, geopolitics.
- **板块与主题**: Sector rotation, themes.
- **个股/ETF**: Tickers with table (标的 / 方向 / 关键位 / 风险).
- **交易含义**: Continuation / invalidation conditions.
- **风险提醒**: Chasing, event, liquidity, concentration risks.

## Key Frames

Extract frames when transcript references on-screen data (charts, tables):

```bash
VIDEO_URL=$(yt-dlp -f "best[height<=480]/best" --get-url "URL" | head -1)
ffmpeg -ss TIMESTAMP -i "$VIDEO_URL" -vframes 1 -q:v 2 /tmp/rhino_frame.jpg -y
```

## Failure Handling

- `youtube_transcript_api` 429 → wait 60s retry, then yt-dlp captions.
- yt-dlp no captions → audio fallback.
- Network blocks → request escalation, do not invent content.
