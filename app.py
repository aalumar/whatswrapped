"""
Web Application
Flask server for WhatsWrapped recap.
"""

from flask import (
    Flask,
    render_template,
    jsonify,
    redirect,
    url_for,
)
import json
import os
import re
from pathlib import Path
from urllib.parse import quote, unquote

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
CACHE_DIR = Path("cache")
NAME_MAPPING = {}


@app.route("/")
def start():
    return redirect(url_for("index"))


@app.route("/chats")
def index():
    """Chat selection page."""
    chat_dirs = []
    base_path = Path("chats")

    if not base_path.exists():
        base_path = Path(".")

    for item in sorted(base_path.iterdir()):
        if item.is_dir():
            txt_files = list(item.glob("*.txt"))
            if txt_files:
                chat_dirs.append(
                    {
                        "name": item.name,
                        "path": quote(item.name, safe=""),
                    }
                )

    return render_template("index.html", chats=chat_dirs)


@app.route("/recap/<path:chat_name>")
def recap(chat_name):
    """Individual recap page."""
    chat_name = unquote(chat_name)

    safe_name = re.sub(r"[^\w\-_\.]", "_", chat_name)
    cache_file = CACHE_DIR / f"{safe_name}_stats.json"

    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            stats = json.load(f)

        viz_files = {}
        static_dir = Path("static/images")
        safe_name_clean = safe_name.replace(" ", "_").replace("/", "_")

        viz_types = ["emojis", "senders", "timeline", "media", "wordcloud", "heatmap"]
        for viz_type in viz_types:
            if viz_type == "wordcloud":
                file_path = static_dir / f"wordcloud_{safe_name_clean}.png"
            else:
                file_path = static_dir / f"{viz_type}_{safe_name_clean}.html"

            if file_path.exists():
                viz_files[viz_type] = f"images/{file_path.name}"

        if stats.get("top_senders"):
            stats["top_senders"] = [
                [NAME_MAPPING.get(name, name), count]
                for name, count in stats["top_senders"]
            ]
            stats["senders_total"] = sum(c for _, c in stats["top_senders"])

        if stats.get("longest_message") and stats["longest_message"].get("sender"):
            sender = stats["longest_message"]["sender"]
            stats["longest_message"]["sender"] = NAME_MAPPING.get(sender, sender)

        if stats.get("fun_facts"):
            mapped_facts = []
            for fact in stats["fun_facts"]:
                for raw_name, mapped_name in NAME_MAPPING.items():
                    fact = fact.replace(raw_name, mapped_name)
                mapped_facts.append(fact)
            stats["fun_facts"] = mapped_facts

        return render_template(
            "recap.html", chat_name=chat_name, stats=stats, viz_files=viz_files
        )
    else:
        return f"Stats not found for {chat_name}. Please run main.py first.", 404


@app.route("/api/stats/<path:chat_name>")
def api_stats(chat_name):
    """API endpoint for stats."""
    chat_name = unquote(chat_name)
    safe_name = re.sub(r"[^\w\-_\.]", "_", chat_name)
    cache_file = CACHE_DIR / f"{safe_name}_stats.json"

    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            stats = json.load(f)
        return jsonify(stats)
    else:
        return jsonify({"error": "Stats not found"}), 404


if __name__ == "__main__":
    os.makedirs(CACHE_DIR, exist_ok=True)
    app.run(debug=False, port=5000)
