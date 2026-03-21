"""
WhatsApp Chat Parser Module
Parses exported WhatsApp chat .txt files and extracts structured data.
"""

import re
from datetime import datetime
from typing import List, Optional
from pathlib import Path


class ChatMessage:
    """Represents a single WhatsApp message."""

    def __init__(
        self,
        timestamp: datetime,
        sender: str,
        content: str,
        is_media: bool = False,
        media_file: Optional[str] = None,
        is_edited: bool = False,
        mentions: List[str] = None,
    ):
        self.timestamp = timestamp
        self.sender = sender
        self.content = content
        self.is_media = is_media
        self.media_file = media_file
        self.is_edited = is_edited
        self.mentions = mentions or []

    def __repr__(self):
        return (
            f"ChatMessage({self.timestamp}, {self.sender}, {len(self.content)} chars)"
        )


class ChatParser:
    """Parses WhatsApp chat export files."""

    # Pattern: [D/M/YY, H:MM:SS AM/PM] Sender: message
    # Handles optional leading Unicode directional marks (U+200E/U+200F)
    MESSAGE_PATTERN = re.compile(
        r"[\u200e\u200f]?\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}:\d{2}\s+[AP]M)\]\s+([^:]+):\s+(.+)$"
    )

    def __init__(self, chat_file_path: str):
        self.chat_file_path = Path(chat_file_path)
        self.chat_name = self.chat_file_path.stem
        self.messages: List[ChatMessage] = []
        self.current_sender: Optional[str] = None
        self.current_timestamp: Optional[datetime] = None

    def parse(self) -> List[ChatMessage]:
        """Parse the chat file and return list of messages."""
        if not self.chat_file_path.exists():
            raise FileNotFoundError(f"Chat file not found: {self.chat_file_path}")

        with open(self.chat_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to match a new message
            match = self.MESSAGE_PATTERN.match(line)
            if match:
                date_str, time_str, sender, content = match.groups()
                timestamp = self._parse_timestamp(date_str, time_str)

                # Process content for media, edits, mentions
                is_media, media_file = self._extract_media(content)
                is_edited = "<This message was edited>" in content
                mentions = self._extract_mentions(content)

                # Clean content
                content = self._clean_content(content)

                message = ChatMessage(
                    timestamp=timestamp,
                    sender=sender.strip(),
                    content=content,
                    is_media=is_media,
                    media_file=media_file,
                    is_edited=is_edited,
                    mentions=mentions,
                )

                self.messages.append(message)
                self.current_sender = sender.strip()
                self.current_timestamp = timestamp
            else:
                # Continuation line - append to last message
                if self.messages and self.current_sender:
                    # Check for media omitted
                    if "<Media omitted>" in line:
                        self.messages[-1].is_media = True
                    else:
                        # Append as continuation
                        self.messages[-1].content += " " + line

        return self.messages

    def _parse_timestamp(self, date_str: str, time_str: str) -> datetime:
        """Parse timestamp from date and time strings."""
        try:
            # Format: D/M/YY
            date_parts = date_str.split("/")
            day, month, year = map(int, date_parts)

            # Convert 2-digit year to 4-digit (assuming 2000-2099)
            if year < 100:
                year += 2000

            # Parse time (includes seconds: H:MM:SS AM/PM)
            time_obj = datetime.strptime(time_str, "%I:%M:%S %p")

            return datetime(
                year, month, day, time_obj.hour, time_obj.minute, time_obj.second
            )
        except Exception as e:
            # Fallback: return current time if parsing fails
            print(f"Warning: Could not parse timestamp '{date_str} {time_str}': {e}")
            return datetime.now()

    def _extract_media(self, content: str) -> tuple:
        """Extract media file information from content."""
        # Strip leading Unicode directional marks from content
        content_clean = content.lstrip("\u200e\u200f")

        # Check for "X omitted" patterns (new iOS export format)
        omitted_pattern = re.compile(
            r"^(image|video|audio|sticker|document|gif)\s+omitted$", re.IGNORECASE
        )
        if omitted_pattern.match(content_clean.strip()):
            return True, None

        # Check for <attached: filename> pattern
        attached_pattern = re.compile(
            r"<attached:\s*([^>]+\.(jpg|jpeg|png|webp|mp4|opus|m4a|ogg))>",
            re.IGNORECASE,
        )
        match = attached_pattern.search(content)
        if match:
            return True, match.group(1).strip()

        # Check for filename (file attached) pattern (Android export format)
        file_pattern = re.compile(
            r"([A-Z0-9_-]+\.(jpg|jpeg|png|webp|mp4|opus|m4a|ogg))(?:\s+\(file attached\))?",
            re.IGNORECASE,
        )
        match = file_pattern.search(content)
        if match:
            return True, match.group(1)

        # Check for media omitted (old format)
        if "<Media omitted>" in content:
            return True, None

        return False, None

    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from content."""
        # Pattern: @⁨Name⁩
        mention_pattern = re.compile(r"@⁨([^⁩]+)⁩")
        return mention_pattern.findall(content)

    def _clean_content(self, content: str) -> str:
        """Clean message content."""
        # Remove edit markers
        content = content.replace("<This message was edited>", "")
        # Remove file attached markers but keep filename
        content = re.sub(r"\s*\(file attached\)", "", content)
        return content.strip()

    def filter_by_year(self, year: int = 2025) -> List[ChatMessage]:
        """Filter messages by year."""
        return [msg for msg in self.messages if msg.timestamp.year == year]


if __name__ == "__main__":
    # Test parser
    parser = ChatParser(
        "WhatsApp Chat with Khobar Gang/WhatsApp Chat with Khobar Gang.txt"
    )
    messages = parser.parse()
    print(f"Parsed {len(messages)} messages")
    print(f"First message: {messages[0]}")
    print(f"Last message: {messages[-1]}")
