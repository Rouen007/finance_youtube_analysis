# rhino-finance-latest

Fetch the latest video from any YouTube channel and extract all trading information. Defaults to [Rhino Finance / 犀牛哥](https://www.youtube.com/@RhinoFinance).

## What it does

1. Auto-discovers the latest public upload from a YouTube channel
2. Fetches transcript or captions (Chinese/English)
3. **Auto-extracts key frame screenshots** at regular intervals + visual-referenced moments
4. **Extracts all trading signals**: tickers, direction, entry logic, key price levels, stop-loss/take-profit, position sizing, time horizon
5. Captures macro views, sector rotation, capital flows, event-driven catalysts
6. Outputs structured Chinese trading notes with ticker tables, risk flags, and uncertainty markers

## Prerequisites

- Python 3.9+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): `pip install yt-dlp`
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api): `pip install youtube-transcript-api`
- ffmpeg (required for frame extraction): `brew install ffmpeg`

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
```

### 2. Transcript Extraction

```bash
# Fetch transcript (auto: API → captions → audio fallback)
python3 scripts/transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Save to file
python3 scripts/transcript.py "VIDEO_URL" -o transcript.txt
```

### 3. Full Analysis (transcript + auto frames + LLM summary)

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

# Disable auto frame extraction
python3 scripts/analyze.py --no-frames

# Adjust frame sampling interval (default: every 120 seconds)
python3 scripts/analyze.py --frame-interval 60
```

## Project Structure

```
rhino-finance-latest/
├── scripts/
│   ├── latest_video.py         # Video discovery (channel → latest uploads)
│   ├── transcript.py           # Transcript extraction (API → captions → audio)
│   └── analyze.py              # Full pipeline: discover → transcript → frames → LLM
├── references/
│   ├── core-thesis.md          # Durable thesis record (updated over time)
│   └── trading_knowledge.md    # Ticker slang, options terms, market structure
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
analyze.py     ──→ Detect key timestamps → Extract frames with ffmpeg
     │                    │
     │                    ▼
     │            Key frame screenshots
     │                    │
     ▼                    ▼
LLM summarization (transcript + frames + trading knowledge)
     │
     ▼
Structured trading summary (Chinese)
```

## Auto Frame Extraction

The `analyze.py` script automatically:

1. Samples frames at regular intervals (default: every 2 minutes)
2. Boosts timestamps where the speaker references visual content ("看这个图", "屏幕上显示", etc.)
3. Extracts frames using ffmpeg seek (only downloads needed HLS chunks, not the full video)
4. Sends frames to the LLM as vision input alongside the transcript
5. LLM extracts price levels, charts, and data tables visible on screen

## License

MIT
