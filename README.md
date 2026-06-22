# rhino-finance-latest

Fetch the latest video from [Rhino Finance / 犀牛哥](https://www.youtube.com/@RhinoFinance) and extract all trading information.

## What it does

1. Auto-discovers the latest public upload from Rhino Finance's YouTube channel
2. Fetches transcript or captions (Chinese/English)
3. **Extracts all trading signals**: tickers, direction, entry logic, key price levels, stop-loss/take-profit, position sizing, time horizon
4. Captures macro views, sector rotation, capital flows, event-driven catalysts
5. Outputs structured Chinese trading notes with ticker tables, risk flags, and uncertainty markers

## Prerequisites

- Python 3.9+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): `pip install yt-dlp`
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api): `pip install youtube-transcript-api`
- ffmpeg (optional, for key frame extraction)

## Usage

### Standalone

```bash
# Fetch latest video info
python3 scripts/latest_video.py --count 1

# Fetch multiple recent videos
python3 scripts/latest_video.py --count 3

# Quick discovery without full metadata enrichment
python3 scripts/latest_video.py --count 1 --no-enrich
```

### As a Claude Code / Codex Skill

Copy or symlink this directory into your skills folder:

```bash
# Claude Code
cp -r rhino-finance-latest ~/.claude/skills/

# Codex
cp -r rhino-finance-latest ~/.codex/skills/
```

Then invoke with:
```
/rhino-finance-latest
```

Or just ask naturally: "犀牛哥最新视频讲了什么"

## Project Structure

```
rhino-finance-latest/
├── scripts/
│   └── latest_video.py       # Fetch latest videos from YouTube
├── references/
│   └── core-thesis.md        # Durable thesis record (updated over time)
├── agents/
│   └── openai.yaml           # OpenAI agent config
├── README.md
├── LICENSE
└── .gitignore
```

## Transcript Workflow

The skill tries these methods in order:

1. **youtube-transcript-api** — fastest, fewest rate-limit issues
2. **yt-dlp captions** — fallback when API is rate-limited
3. **Audio transcription** — last resort (requires whisper)

## Output Format

Summaries cover all actionable trading info:

| Section | Content |
|---|---|
| **一句话结论** | One-line verdict on the video's core call |
| **核心观点** | Market regime, direction, thesis, timing |
| **宏观/消息** | Fed, data, earnings, policy, geopolitics |
| **板块与主题** | Sector rotation, themes, capital flows |
| **个股/ETF** | Tickers, catalysts, levels, setups, invalidation |
| **交易含义** | Continuation / invalidation conditions |
| **风险提醒** | Chasing, event, liquidity, concentration risks |

## License

MIT
