"""
Media Matcher Module
Matches media file references in chat to actual files in directory.
"""

from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image
import hashlib


class MediaMatcher:
    """Matches and processes media files."""

    def __init__(self, chat_directory: str):
        self.chat_directory = Path(chat_directory)
        self.media_files = self._scan_media_files()

    def _scan_media_files(self) -> Dict[str, Path]:
        """Scan directory for media files."""
        media_files = {}

        if not self.chat_directory.exists():
            return media_files

        # Supported media extensions
        media_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".mp4",
            ".opus",
            ".m4a",
            ".ogg",
        }

        for file_path in self.chat_directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in media_extensions:
                media_files[file_path.name] = file_path

        return media_files

    def find_media_file(self, filename: str) -> Optional[Path]:
        """Find media file by filename."""
        return self.media_files.get(filename)

    def get_media_by_type(self) -> Dict[str, List[Path]]:
        """Group media files by type."""
        media_by_type = {"images": [], "videos": [], "audio": [], "stickers": []}

        image_exts = {".jpg", ".jpeg", ".png"}
        video_exts = {".mp4", ".mov", ".avi"}
        audio_exts = {".opus", ".m4a", ".ogg", ".mp3"}

        for file_path in self.media_files.items():
            ext = file_path.suffix.lower()

            if ext == ".webp":
                media_by_type["stickers"].append(file_path)
            elif ext in image_exts:
                media_by_type["images"].append(file_path)
            elif ext in video_exts:
                media_by_type["videos"].append(file_path)
            elif ext in audio_exts:
                media_by_type["audio"].append(file_path)

        return media_by_type

    def create_sticker_thumbnail(
        self, sticker_path: Path, output_path: Path, size: tuple = (100, 100)
    ) -> Optional[str]:
        """Create thumbnail for sticker and save to file."""
        try:
            img = Image.open(sticker_path)
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save thumbnail
            img.save(output_path, format="PNG")
            return str(output_path)
        except Exception as e:
            print(f"Error creating thumbnail for {sticker_path}: {e}")
            return None

    def get_sticker_groups_by_hash(self, sticker_filenames: List[str]) -> List[Dict]:
        """Group sticker sends by file content hash to find most-used sticker images.

        Each unique sticker image (regardless of filename) is grouped by MD5 hash.
        Returns all groups sorted by send count descending. Each entry contains:
          - 'count': number of times this sticker image was sent
          - 'representative': filename of one send, used for thumbnail generation
        """
        hash_to_group: Dict[str, Dict] = {}

        for filename in sticker_filenames:
            file_path = self.find_media_file(filename)
            if not file_path or not file_path.exists():
                continue

            file_hash = hashlib.md5(file_path.read_bytes()).hexdigest()

            if file_hash not in hash_to_group:
                hash_to_group[file_hash] = {
                    "count": 0,
                    "representative": file_path.name,
                }
            hash_to_group[file_hash]["count"] += 1

        return sorted(hash_to_group.values(), key=lambda x: x["count"], reverse=True)

    def get_sticker_paths(
        self,
        sticker_filenames: List[str],
        thumbnail_dir: str = "static/images/stickers",
    ) -> List[Dict]:
        """Get paths and thumbnails for top stickers."""
        sticker_data = []
        thumbnail_base = Path(thumbnail_dir)
        thumbnail_base.mkdir(parents=True, exist_ok=True)

        for idx, filename in enumerate(sticker_filenames[:10]):  # Top 10
            file_path = self.find_media_file(filename)
            if file_path and file_path.exists():
                # Create thumbnail path
                thumbnail_filename = f"thumb_{idx}_{file_path.stem}.png"
                thumbnail_path = thumbnail_base / thumbnail_filename

                thumbnail_file = self.create_sticker_thumbnail(
                    file_path, thumbnail_path
                )

                sticker_data.append(
                    {
                        "filename": filename,
                        "path": str(file_path.relative_to(self.chat_directory)),
                        "thumbnail": thumbnail_file,
                    }
                )

        return sticker_data

    def count_media_by_type(self) -> Dict[str, int]:
        """Count media files by type."""
        media_by_type = self.get_media_by_type()
        return {
            "images": len(media_by_type["images"]),
            "videos": len(media_by_type["videos"]),
            "audio": len(media_by_type["audio"]),
            "stickers": len(media_by_type["stickers"]),
        }
