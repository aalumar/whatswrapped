"""
Data Analyzer Module
Processes parsed chat data to extract patterns, emojis, stickers, etc.
"""

import re
from collections import Counter, defaultdict
from datetime import timedelta
from typing import List, Dict, Tuple
import emoji as emoji_lib
from chat_parser import ChatMessage


class ChatAnalyzer:
    """Analyzes chat messages to extract statistics and patterns."""

    def __init__(self, messages: List[ChatMessage]):
        self.messages = messages
        self.emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f680-\U0001f6ff"  # transport & map symbols
            "\U0001f1e0-\U0001f1ff"  # flags
            "\U00002702-\U000027b0"  # dingbats
            "\U000024c2-\U0001f251"  # enclosed characters
            "\U0001f900-\U0001f9ff"  # supplemental symbols
            "\U0001fa00-\U0001fa6f"  # chess symbols
            "\U0001fa70-\U0001faff"  # symbols and pictographs extended-A
            "\U00002600-\U000026ff"  # miscellaneous symbols
            "\U00002700-\U000027bf"  # dingbats
            "]+",
            flags=re.UNICODE,
        )

    def get_message_counts_by_sender(self) -> Dict[str, int]:
        """Get message count per sender."""
        return Counter(msg.sender for msg in self.messages)

    def get_most_active_day_time(self) -> Tuple[str, str]:
        """Get most active day of week and hour."""
        day_counts = Counter(msg.timestamp.strftime("%A") for msg in self.messages)
        hour_counts = Counter(msg.timestamp.hour for msg in self.messages)

        most_active_day = day_counts.most_common(1)[0][0] if day_counts else "Unknown"
        most_active_hour = hour_counts.most_common(1)[0][0] if hour_counts else 0

        return most_active_day, f"{most_active_hour}:00"

    def get_emoji_usage(self) -> Dict[str, int]:
        """Extract and count emoji usage."""
        emoji_counter = Counter()

        for msg in self.messages:
            for item in emoji_lib.emoji_list(msg.content):
                emoji_counter[item["emoji"]] += 1

        return dict(emoji_counter.most_common(20))  # Top 20

    def _is_emoji(self, char: str) -> bool:
        """Check if character is an emoji."""
        return bool(self.emoji_pattern.match(char))

    def get_sticker_usage(self) -> Dict[str, int]:
        """Get sticker usage count (webp files)."""
        sticker_counter = Counter()

        for msg in self.messages:
            if msg.is_media and msg.media_file:
                if msg.media_file.lower().endswith(".webp"):
                    sticker_counter[msg.media_file] += 1

        return dict(sticker_counter.most_common(10))  # Top 10 for display

    def get_unique_sticker_count(self) -> int:
        """Get total number of unique stickers used (uncapped)."""
        return len(
            {
                msg.media_file
                for msg in self.messages
                if msg.is_media
                and msg.media_file
                and msg.media_file.lower().endswith(".webp")
            }
        )

    def get_media_counts(self) -> Dict[str, int]:
        """Count media files by type."""
        media_counts = defaultdict(int)

        for msg in self.messages:
            if msg.is_media:
                if msg.media_file:
                    ext = msg.media_file.split(".")[-1].lower()
                    media_counts[ext] += 1
                else:
                    media_counts["omitted"] += 1

        return dict(media_counts)

    def get_word_frequency(
        self, min_length: int = 3, top_n: int = 100
    ) -> Dict[str, int]:
        """Get word frequency for word cloud."""
        word_counter = Counter()

        # Common stop words (English and Arabic)
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "her",
            "its",
            "our",
            "their",
            "https",
            "http",
            "www",
            "com",
            "org",
            "net",
            "edu",
            "gov",
            "ال",
            "في",
            "من",
            "إلى",
            "على",
            "أن",
            "هذا",
            "هذه",
            "ذلك",
            "تلك",
        }

        # URL pattern to remove URLs from content
        url_pattern = re.compile(
            r"https?://\S+|www\.\S+|\S+\.(com|org|net|edu|gov|io|co)\S*", re.IGNORECASE
        )

        # Pattern to remove @mentions: @⁨Name⁩
        mention_pattern = re.compile(r"@⁨[^⁩]+⁩")

        for msg in self.messages:
            if msg.is_media:
                continue

            # Remove URLs and mentions from content
            content = url_pattern.sub("", msg.content)
            content = mention_pattern.sub("", content)

            # Extract words (handle both English and Arabic)
            # Pattern matches: English words OR Arabic words (Arabic Unicode range)
            # Arabic range: \u0600-\u06FF (includes Arabic, Persian, Urdu, etc.)
            # Extract English words
            english_words = re.findall(r"\b[a-zA-Z]+\b", content.lower())
            # Extract Arabic words (Arabic Unicode range)
            arabic_words = re.findall(r"[\u0600-\u06FF]+", content)

            all_words = english_words + arabic_words

            for word in all_words:
                if len(word) >= min_length and word not in stop_words:
                    word_counter[word] += 1

        return dict(word_counter.most_common(top_n))

    def get_conversation_streak(self) -> int:
        """Calculate longest consecutive days with messages."""
        if not self.messages:
            return 0

        # Get unique dates
        dates = sorted(set(msg.timestamp.date() for msg in self.messages))

        if not dates:
            return 0

        max_streak = 1
        current_streak = 1

        for i in range(1, len(dates)):
            if dates[i] - dates[i - 1] == timedelta(days=1):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        return max_streak

    def get_activity_timeline(self) -> Dict[str, int]:
        """Get message count per day."""
        timeline = defaultdict(int)

        for msg in self.messages:
            date_str = msg.timestamp.strftime("%Y-%m-%d")
            timeline[date_str] += 1

        return dict(sorted(timeline.items()))

    def get_top_senders(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Get top senders by message count."""
        sender_counts = self.get_message_counts_by_sender()
        return sender_counts.most_common(top_n)

    def get_activity_heatmap_data(self) -> Dict:
        """Get message counts broken down by weekday and hour (for heatmap)."""
        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        heatmap = {day: [0] * 24 for day in weekdays}
        for msg in self.messages:
            day_name = msg.timestamp.strftime("%A")
            hour = msg.timestamp.hour
            if day_name in heatmap:
                heatmap[day_name][hour] += 1
        return heatmap

    def get_all_statistics(self) -> Dict:
        """Get all statistics in one call."""
        return {
            "total_messages": len(self.messages),
            "message_counts_by_sender": self.get_message_counts_by_sender(),
            "most_active_day": self.get_most_active_day_time()[0],
            "most_active_hour": self.get_most_active_day_time()[1],
            "top_emojis": self.get_emoji_usage(),
            "top_stickers": self.get_sticker_usage(),
            "unique_sticker_count": self.get_unique_sticker_count(),
            "media_counts": self.get_media_counts(),
            "word_frequency": self.get_word_frequency(),
            "longest_streak": self.get_conversation_streak(),
            "activity_timeline": self.get_activity_timeline(),
            "activity_heatmap": self.get_activity_heatmap_data(),
            "top_senders": self.get_top_senders(),
        }
