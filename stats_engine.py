"""
Statistics Engine
Calculates all statistics and generates fun facts.
"""

from typing import Dict, List
from collections import Counter
from analyzer import ChatAnalyzer
from chat_parser import ChatMessage


class StatsEngine:
    """Generates comprehensive statistics and fun facts."""

    def __init__(self, analyzer: ChatAnalyzer, messages: List[ChatMessage]):
        self.analyzer = analyzer
        self.messages = messages

    def calculate_all_stats(self) -> Dict:
        """Calculate all statistics."""
        stats = self.analyzer.get_all_statistics()

        # Add additional calculated stats
        stats["longest_message"] = self._get_longest_message()
        stats["average_message_length"] = self._get_average_message_length()
        stats["media_percentage"] = self._get_media_percentage()
        stats["most_active_weekday"] = self._get_most_active_weekday()
        stats["most_active_hour_numeric"] = self._get_most_active_hour_numeric()
        stats["weekend_vs_weekday"] = self._get_weekend_vs_weekday()
        stats["fun_facts"] = self._generate_fun_facts(stats)

        return stats

    def _get_longest_message(self) -> Dict:
        """Get the longest message."""
        if not self.messages:
            return {"sender": "", "content": "", "length": 0}

        longest = max(self.messages, key=lambda m: len(m.content))
        return {
            "sender": longest.sender,
            "content": longest.content,
            "length": len(longest.content),
        }

    def _get_average_message_length(self) -> float:
        """Calculate average message length."""
        if not self.messages:
            return 0.0

        text_messages = [m for m in self.messages if not m.is_media]
        if not text_messages:
            return 0.0

        total_length = sum(len(m.content) for m in text_messages)
        return round(total_length / len(text_messages), 1)

    def _get_media_percentage(self) -> float:
        """Calculate percentage of messages that are media."""
        if not self.messages:
            return 0.0

        media_count = sum(1 for m in self.messages if m.is_media)
        return round((media_count / len(self.messages)) * 100, 1)

    def _get_most_active_weekday(self) -> str:
        """Get most active weekday."""
        weekday_counts = Counter(msg.timestamp.strftime("%A") for msg in self.messages)
        return weekday_counts.most_common(1)[0][0] if weekday_counts else "Unknown"

    def _get_most_active_hour_numeric(self) -> int:
        """Get most active hour as integer."""
        hour_counts = Counter(msg.timestamp.hour for msg in self.messages)
        return hour_counts.most_common(1)[0][0] if hour_counts else 0

    def _get_weekend_vs_weekday(self) -> Dict[str, int | float]:
        """Compare weekend vs weekday activity."""
        weekend_days = {"Friday", "Saturday"}
        weekend_count = 0
        weekday_count = 0

        for msg in self.messages:
            weekday = msg.timestamp.strftime("%A")
            if weekday in weekend_days:
                weekend_count += 1
            else:
                weekday_count += 1

        return {
            "weekend": weekend_count,
            "weekday": weekday_count,
            "weekend_percentage": round((weekend_count / len(self.messages)) * 100, 1)
            if self.messages
            else 0,
        }

    def _generate_fun_facts(self, stats: Dict) -> List[str]:
        """Generate interesting fun facts."""
        facts = []

        total_messages = stats["total_messages"]
        top_sender = stats["top_senders"][0] if stats["top_senders"] else None

        if top_sender:
            sender_percentage = (
                round((top_sender[1] / total_messages) * 100, 1)
                if total_messages > 0
                else 0
            )
            facts.append(f"{top_sender[0]} sent {sender_percentage}% of all messages")

        longest_streak = stats["longest_streak"]
        facts.append(f"Our longest conversation streak was {longest_streak} days")

        most_active_day = stats["most_active_day"]
        facts.append(f"Most messages were sent on {most_active_day}s")

        most_active_hour = stats["most_active_hour"]
        facts.append(f"Peak messaging time: {most_active_hour}")

        media_pct = stats["media_percentage"]
        facts.append(f"{media_pct}% of our messages were media files")

        top_emoji = list(stats["top_emojis"].keys())[0] if stats["top_emojis"] else None
        if top_emoji:
            emoji_count = stats["top_emojis"][top_emoji]
            facts.append(
                f"Our most used emoji was {top_emoji} (used {emoji_count} times)"
            )

        avg_length = stats["average_message_length"]
        facts.append(f"Average message length: {avg_length} characters")

        longest_msg = stats["longest_message"]
        if longest_msg["length"] > 0:
            facts.append(
                f"Longest message was {longest_msg['length']} characters by {longest_msg['sender']}"
            )

        weekend_pct = stats["weekend_vs_weekday"]["weekend_percentage"]
        facts.append(f"{weekend_pct}% of messages were sent on weekends")

        sticker_count = stats.get("unique_sticker_count", 0)
        if sticker_count > 0:
            facts.append(f"We used {sticker_count} different stickers")

        return facts
