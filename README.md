# rhino-finance-latest

Fetch the latest video from any YouTube channel and extract all trading information. Defaults to [Rhino Finance / 犀牛哥](https://www.youtube.com/@RhinoFinance).

## What it does

1. Auto-discovers the latest public upload from a YouTube channel
2. Fetches transcript or captions (Chinese/English)
3. **Extracts all trading signals**: tickers, direction, entry logic, key price levels, stop-loss/take-profit, position sizing, time horizon
4. Captures macro views, sector rotation, capital flows, event-driven catalysts
5. Outputs structured Chinese trading notes with ticker tables, risk flags, and uncertainty markers
6. Supports key frame extraction for on-screen charts and data

## Prerequisites

- Python 3.9+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): `pip install yt-dlp`
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api): `pip install youtube-transcript-api`
- ffmpeg (optional, for key frame extraction)

### For standalone LLM mode

- `pip install openai` (for OpenAI) or `pip install anthropic` (for Anthropic)
- Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` environment variable

## Usage

### 1. Video Discovery

```bash
# Get latest video from Rhino Finance (default)
python3 scripts/latest_video.py --count 1

# Get from any YouTube channel
python3 scripts/latest_video.py --channel "https://www.youtube.com/@SomeChannel" --count 1

# Get multiple recent videos
python3 scripts/latest_video.py --count 3
```

### 2. Transcript Extraction

```bash
# Fetch transcript (auto: API → captions → audio fallback)
python3 scripts/transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Force a specific method
python3 scripts/transcript.py "VIDEO_URL" --method captions

# Save to file
python3 scripts/transcript.py "VIDEO_URL" -o transcript.txt
```

### 3. Full Analysis (transcript + LLM summary)

```bash
# Analyze latest video (auto-detects LLM provider from env)
python3 scripts/analyze.py

# Analyze a specific video
python3 scripts/analyze.py --url "https://www.youtube.com/watch?v=VIDEO_ID"

# Use specific provider/model
python3 scripts/analyze.py --provider openai --model gpt-4o
python3 scripts/analyze.py --provider anthropic --model claude-sonnet-4-20250514

# Save to file
python3 scripts/analyze.py -o summary.md

# Transcript only (skip LLM)
python3 scripts/analyze.py --transcript-only
```

### 4. Key Frame Extraction

```bash
# Extract frames at specific timestamps (for on-screen charts/tables)
python3 scripts/latest_video.py --video-url "VIDEO_URL" --timestamps 3100,3130,3175

# Save to custom directory
python3 scripts/latest_video.py --video-url "VIDEO_URL" --timestamps 120,240 --output-dir ./frames
```

### As a Claude Code / Codex Skill

Copy or symlink into your skills folder:

```bash
# Claude Code
cp -r rhino-finance-latest ~/.claude/skills/

# Codex
cp -r rhino-finance-latest ~/.codex/skills/
```

Then invoke:
```
/rhino-finance-latest
```

Or ask naturally:
- "犀牛哥最新视频讲了什么"
- "帮我总结这个 YouTube 视频的交易信息 https://www.youtube.com/watch?v=xxx"

## Project Structure

```
rhino-finance-latest/
├── SKILL.md                    # Claude Code / Codex skill definition
├── scripts/
│   ├── latest_video.py         # Video discovery (channel → latest uploads)
│   ├── transcript.py           # Transcript extraction (API → captions → audio)
│   └── analyze.py              # Full pipeline: discover → transcript → LLM summary
├── references/
│   └── core-thesis.md          # Durable thesis record (updated over time)
├── agents/
│   └── openai.yaml             # OpenAI agent config
├── README.md
├── LICENSE
└── .gitignore
```

## How It Works

```
YouTube Channel
     │
     ▼
latest_video.py ──→ Video URL + Metadata
     │
     ▼
transcript.py  ──→ Transcript (API / captions / audio fallback)
     │
     ▼
analyze.py     ──→ LLM summarization (OpenAI / Anthropic)
     │
     ▼
Structured trading summary (Chinese)
```

## License

MIT
