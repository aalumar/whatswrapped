"""
Main Entry Point
Scans for chat directories, processes each chat, and serves web interface.
"""

import json
from pathlib import Path
from chat_parser import ChatParser
from analyzer import ChatAnalyzer
from media_matcher import MediaMatcher
from stats_engine import StatsEngine
from visualizer import Visualizer

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# year defaulting to 2025
YEAR = 2025


def find_chat_directories(base_path: str = "chats") -> list:
    """Find all WhatsApp chat directories."""
    chat_dirs = []
    base = Path(base_path)

    if not base.exists():
        # Fallback to project root for backwards compatibility
        base = Path(".")

    for item in base.iterdir():
        if item.is_dir():
            # Check if it has a .txt file
            txt_files = list(item.glob("*.txt"))
            if txt_files:
                chat_dirs.append(
                    {"directory": item, "txt_file": txt_files[0], "name": item.name}
                )

    return chat_dirs


def process_chat(chat_dir: dict, year: int = YEAR):
    """Process a single chat directory."""
    print(f"\nProcessing: {chat_dir['name']}")

    # Parse chat
    print("  Parsing chat file...")
    parser = ChatParser(str(chat_dir["txt_file"]))
    parser.parse()

    # Filter by year
    messages_2025 = parser.filter_by_year(year)
    print(f"  Found {len(messages_2025)} messages from {year}")

    if not messages_2025:
        print(f"  No messages found for {year}, skipping...")
        return None

    # Analyze
    print("  Analyzing messages...")
    analyzer = ChatAnalyzer(messages_2025)

    # Match media
    print("  Matching media files...")
    media_matcher = MediaMatcher(str(chat_dir["directory"]))

    # Generate statistics
    print("  Generating statistics...")
    stats_engine = StatsEngine(analyzer, messages_2025)
    stats = stats_engine.calculate_all_stats()

    # Group stickers by image hash to find truly most-used sticker images.
    # WhatsApp gives every sticker send a unique filename, so filename-based
    # counting always gives count=1 per sticker. Hashing the actual .webp bytes
    # correctly groups repeated sends of the same image.
    all_sticker_filenames = [
        msg.media_file
        for msg in messages_2025
        if msg.is_media and msg.media_file and msg.media_file.lower().endswith(".webp")
    ]
    sticker_groups = media_matcher.get_sticker_groups_by_hash(all_sticker_filenames)

    # Override the broken filename-based counts with hash-based ones
    stats["top_stickers"] = {
        g["representative"]: g["count"] for g in sticker_groups[:10]
    }
    stats["unique_sticker_count"] = len(sticker_groups)

    top_representatives = [g["representative"] for g in sticker_groups[:10]]
    sticker_data = media_matcher.get_sticker_paths(top_representatives)
    # Attach send counts and convert thumbnail paths for web serving
    for i, sticker in enumerate(sticker_data):
        sticker["count"] = sticker_groups[i]["count"] if i < len(sticker_groups) else 0
        if sticker["thumbnail"]:
            sticker["thumbnail"] = sticker["thumbnail"].replace("static/", "")
    stats["top_sticker_files"] = sticker_data

    # Generate visualizations
    print("  Creating visualizations...")
    visualizer = Visualizer()
    # Create safe filename by replacing problematic characters
    import re

    safe_name = re.sub(r"[^\w\-_\.]", "_", chat_dir["name"])
    viz_files = visualizer.generate_all_visualizations(stats, messages_2025, safe_name)
    stats["visualization_files"] = viz_files

    # Cache results
    print("  Caching results...")
    cache_file = CACHE_DIR / f"{safe_name}_stats.json"

    # Convert datetime objects to strings for JSON serialization
    def json_serial(obj):
        if isinstance(obj, dict):
            return {k: json_serial(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [json_serial(item) for item in obj]
        elif hasattr(obj, "isoformat"):  # datetime
            return obj.isoformat()
        else:
            return obj

    stats_serialized = json_serial(stats)

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(stats_serialized, f, ensure_ascii=False, indent=2)

    print(f"  ✓ Completed! Stats saved to {cache_file}")

    return stats


def main():
    """Main function."""
    print(f"WhatsWrapped {YEAR} Recap Generator")
    print("=" * 50)

    # Find all chat directories
    print("\nScanning for chat directories...")
    chat_dirs = find_chat_directories()

    if not chat_dirs:
        print("No WhatsApp chat directories found!")
        return

    print(f"Found {len(chat_dirs)} chat(s):")
    for chat in chat_dirs:
        print(f"  - {chat['name']}")

    # Process each chat
    results = {}
    for chat_dir in chat_dirs:
        try:
            stats = process_chat(chat_dir)
            if stats:
                results[chat_dir["name"]] = stats
        except Exception as e:
            print(f"  ✗ Error processing {chat_dir['name']}: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 50)
    print(f"Processing complete! Processed {len(results)} chat(s).")
    print("\nTo view the recaps, run:")
    print("  python app.py")
    print("\nThen open http://localhost:5000 in your browser")


if __name__ == "__main__":
    main()
