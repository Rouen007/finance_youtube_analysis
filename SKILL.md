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
4. Fetch transcript via the pipeline script:
   ```bash
   python3 scripts/transcript.py "VIDEO_URL" -o /tmp/rhino_VIDEO_ID.txt
   ```
   This tries API → captions → whisper audio automatically.
5. Summarize from the saved transcript file.

## Transcript Workflow

The `transcript.py` script handles the full pipeline automatically:

1. **youtube-transcript-api** (fastest, works when subtitles exist):
   ```bash
   python3 scripts/transcript.py "VIDEO_URL" --method api
   ```

2. **yt-dlp captions** (fallback, auto-generated subs):
   ```bash
   python3 scripts/transcript.py "VIDEO_URL" --method captions
   ```

3. **Audio + Whisper transcription** (auto fallback when no captions, **default behavior**):
   ```bash
   python3 scripts/transcript.py "VIDEO_URL" --method whisper
   ```
   Requires: `pip install faster-whisper` and `yt-dlp`.
   Uses `small` model by default for Chinese; `base` for quick English rough cuts.
   **Note**: In `auto` mode, whisper is automatically triggered when API and captions fail — do NOT ask user.

4. **Auto mode** (tries all in order, default):
   ```bash
   python3 scripts/transcript.py "VIDEO_URL"
   ```

### Manual Whisper (when transcript.py whisper fails)

```bash
# Download audio
yt-dlp -f ba --extract-audio --audio-format mp3 --audio-quality 5 \
  -o "/tmp/rhino_%(id)s.%(ext)s" "VIDEO_URL"

# Transcribe
python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
segments, info = model.transcribe('/tmp/rhino_VIDEO_ID.mp3', language='zh', beam_size=5)
for seg in segments:
    print(f'{int(seg.start)}s: {seg.text}')
" > /tmp/rhino_VIDEO_ID.txt
```

## Summary Format

Start with: `标题 | 频道 | 发布日期 | 时长 | 链接`

Then structure:

- **一句话结论**: Core call in one sentence.
- **核心观点**: Market regime, direction, thesis, timing.
- **宏观/消息**: Fed, data, earnings, policy, geopolitics.
- **板块与主题**: Sector rotation, themes.
- **个股/ETF**: Tickers with table (标的 / 方向/观点 / 关键位/条件 / 风险).
- **交易含义**: What supports continuation, what invalidates it, what to watch next.
- **风险提醒**: Chasing, event, liquidity, concentration risks, promo disclosures.

Use tables when there are multiple tickers or price levels.

## Key Frames

Extract frames when transcript references on-screen data (charts, tables):

```bash
VIDEO_URL=$(yt-dlp -f "best[height<=480]/best" --get-url "URL" | head -1)
ffmpeg -ss TIMESTAMP -i "$VIDEO_URL" -vframes 1 -q:v 2 /tmp/rhino_frame.jpg -y
```

## Dependencies

- Python 3.9+
- `pip install yt-dlp youtube-transcript-api`
- `pip install faster-whisper` (for audio transcription)
- ffmpeg (for audio extraction and key frame extraction)

## Failure Handling

- `youtube_transcript_api` 429 → wait 60s retry, then yt-dlp captions.
- yt-dlp no captions → **automatically** proceed to audio + whisper (no user prompt).
- Whisper too slow → use `base` model or `--compute-type float32` on GPU.
- Network blocks → request escalation, do not invent content.
- Always save transcript to file before summarizing (never dump full transcript to stdout).
