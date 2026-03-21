# WhatsWrapped

A self-hosted WhatsApp year-in-review generator. Export your chats, run the pipeline, and get a beautiful recap with charts, emoji stats, word clouds, and more.

## Setup

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Export your WhatsApp chats

On your phone: **Settings → Chats → Export Chat → Without Media** (or With Media for sticker support).

Unzip each export into its own folder under `chats/`:

```
chats/
  My Friends/
    _chat.txt
  Family/
    _chat.txt
```

### 3. Process your chats

```bash
python main.py
```

This parses each chat, generates visualizations, and caches results in `cache/`.

### 4. Start the web server

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Project structure

```
app.py              # Flask web server
main.py             # Data pipeline entry point
chat_parser.py      # Parses WhatsApp .txt exports
analyzer.py         # Emoji, word, sender frequency
stats_engine.py     # Streaks, fun facts, media %
media_matcher.py    # Sticker thumbnails
visualizer.py       # Plotly charts + word cloud
chats/              # Your chat exports (gitignored)
cache/              # Processed stats JSON (gitignored)
static/images/      # Generated charts (gitignored)
```

## Expected chat format

WhatsApp exports follow this format (the parser handles both 12h and 24h clocks, and Arabic/English):

```
[1/1/25, 9:00:00 AM] Alice: Hello!
[1/1/25, 9:01:00 AM] Bob: Hey there
```

## License

MIT
