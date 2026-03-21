"""
Script to create a background collage from all 2025 media files across all chats.
"""

from pathlib import Path
from PIL import Image
import random
import math
from chat_parser import ChatParser
from media_matcher import MediaMatcher
from main import find_chat_directories


def collect_2025_media_files():
    """Collect all media files from 2025 messages across all chats."""
    print("Collecting 2025 media files from all chats...")

    chat_dirs = find_chat_directories()
    all_media_files = []

    for chat_dir in chat_dirs:
        print(f"  Processing: {chat_dir['name']}")

        # Parse chat
        parser = ChatParser(str(chat_dir["txt_file"]))
        parser.parse()

        # Filter by 2025
        messages_2025 = parser.filter_by_year(2025)
        print(f"    Found {len(messages_2025)} messages from 2025")

        if not messages_2025:
            continue

        # Match media
        media_matcher = MediaMatcher(str(chat_dir["directory"]))

        # Collect media files from 2025 messages
        for msg in messages_2025:
            if msg.is_media and msg.media_file:
                # Only include images and stickers (webp)
                ext = msg.media_file.split(".")[-1].lower()
                if ext in ["jpg", "jpeg", "png", "webp"]:
                    media_path = media_matcher.find_media_file(msg.media_file)
                    if media_path and media_path.exists():
                        all_media_files.append(media_path)

    print(f"\nTotal media files found: {len(all_media_files)}")
    return all_media_files


def create_collage_background(
    media_files, output_path, target_size=(1920, 1080), tile_size=150, max_images=200
):
    """Create a collage background from media files."""
    print(f"\nCreating collage background ({target_size[0]}x{target_size[1]})...")

    # Limit number of images to avoid memory issues
    if len(media_files) > max_images:
        print(f"  Limiting to {max_images} random images from {len(media_files)} total")
        media_files = random.sample(media_files, max_images)

    # Create base image with black background
    collage = Image.new("RGB", target_size, color="black")

    # Calculate grid dimensions
    cols = math.ceil(target_size[0] / tile_size)
    rows = math.ceil(target_size[1] / tile_size)
    total_tiles = cols * rows

    print(f"  Grid: {cols}x{rows} = {total_tiles} tiles")
    print(f"  Processing {len(media_files)} images...")

    # Process images and place them in grid
    processed = 0
    for idx, media_path in enumerate(media_files):
        if processed >= total_tiles:
            break

        try:
            # Open and resize image
            img = Image.open(media_path)

            # Convert RGBA to RGB if needed
            if img.mode == "RGBA":
                # Create white background
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Create thumbnail maintaining aspect ratio
            img.thumbnail((tile_size, tile_size), Image.Resampling.LANCZOS)

            # Create square tile with padding
            tile = Image.new("RGB", (tile_size, tile_size), color="black")

            # Center the image in the tile
            x_offset = (tile_size - img.width) // 2
            y_offset = (tile_size - img.height) // 2
            tile.paste(img, (x_offset, y_offset))

            # Calculate position in grid
            row = processed // cols
            col = processed % cols

            x = col * tile_size
            y = row * tile_size

            # Paste tile onto collage
            collage.paste(tile, (x, y))

            processed += 1

            if (idx + 1) % 50 == 0:
                print(f"    Processed {idx + 1}/{len(media_files)} images...")

        except Exception as e:
            print(f"    Error processing {media_path.name}: {e}")
            continue

    # Add dark overlay for better text readability
    overlay = Image.new("RGBA", target_size, (0, 0, 0, 180))  # 70% opacity black
    collage = Image.alpha_composite(collage.convert("RGBA"), overlay).convert("RGB")

    # Save collage
    output_path.parent.mkdir(parents=True, exist_ok=True)
    collage.save(output_path, "JPEG", quality=85)
    print(f"\n✓ Collage saved to {output_path}")

    return output_path


def main():
    """Main function."""
    print("=" * 60)
    print("Creating 2025 Background Collage")
    print("=" * 60)

    # Collect media files
    media_files = collect_2025_media_files()

    if not media_files:
        print("\nNo media files found from 2025!")
        return

    # Create collage
    output_path = Path("static/background_2025.jpg")
    create_collage_background(media_files, output_path)

    print("\n" + "=" * 60)
    print("Background creation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
