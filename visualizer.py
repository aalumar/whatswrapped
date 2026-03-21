"""
Visualization Generator
Creates charts and visualizations for the recap.
"""

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from wordcloud import WordCloud
from typing import Dict, List
from pathlib import Path
import pandas as pd
from typing import Optional

NAME_MAPPING = {}


class Visualizer:
    """Generates visualizations for chat statistics."""

    def __init__(self, output_dir: str = "static/images"):
        import os

        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_emoji_bar_chart(
        self, emoji_data: Dict[str, int], chat_name: str
    ) -> Optional[str]:
        """Create bar chart for top emojis."""
        if not emoji_data:
            return None

        # Get top 10
        top_emojis = list(emoji_data.items())[:10]
        emojis = [e[0] for e in top_emojis]
        counts = [e[1] for e in top_emojis]

        fig = go.Figure(data=[go.Bar(x=emojis, y=counts, marker_color="#1DB954")])

        fig.update_layout(
            title=dict(text="Top Emojis", font=dict(size=14)),
            xaxis_title="Emoji",
            yaxis_title="Count",
            template="plotly_dark",
            font=dict(size=11),
            autosize=True,
            margin=dict(l=35, r=20, t=50, b=35),
            height=350,
        )

        config = {"responsive": True, "displayModeBar": False, "staticPlot": False}

        filename = Path(self.output_dir) / f"emojis_{chat_name}.html"
        fig.write_html(str(filename), config=config)
        return f"images/{filename.name}"

    def create_sender_bar_chart(
        self, sender_data: List[tuple], chat_name: str
    ) -> Optional[str]:
        """Create bar chart for top senders."""
        if not sender_data:
            return None

        # Map original names to display names
        senders = [NAME_MAPPING.get(s[0], s[0]) for s in sender_data]
        counts = [s[1] for s in sender_data]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=senders,
                    y=counts,
                    marker_color="#1DB954",
                    text=counts,
                    textposition="outside",
                )
            ]
        )

        fig.update_layout(
            title=dict(text="Top Senders", font=dict(size=14)),
            xaxis_title="Sender",
            yaxis_title="Message Count",
            template="plotly_dark",
            font=dict(size=11),
            autosize=True,
            margin=dict(l=45, r=20, t=50, b=70),
            height=350,
            xaxis=dict(tickangle=-45, tickfont=dict(size=10)),
        )

        config = {"responsive": True, "displayModeBar": False, "staticPlot": False}

        filename = Path(self.output_dir) / f"senders_{chat_name}.html"
        fig.write_html(str(filename), config=config)
        return f"images/{filename.name}"

    def create_timeline_chart(
        self, timeline_data: Dict[str, int], chat_name: str
    ) -> Optional[str]:
        """Create timeline chart for activity."""
        if not timeline_data:
            return None

        dates = list(timeline_data.keys())
        counts = list(timeline_data.values())

        df = pd.DataFrame({"date": dates, "count": counts})
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=df["date"],
                    y=df["count"],
                    mode="lines+markers",
                    line=dict(color="#1DB954", width=2),
                    marker=dict(size=4),
                )
            ]
        )

        # Place tick marks at mid-month so labels appear centered within each month
        months = pd.period_range(df["date"].min(), df["date"].max(), freq="M")
        tickvals = [pd.Timestamp(p.year, p.month, 15) for p in months]
        ticktext = [pd.Timestamp(p.year, p.month, 1).strftime("%b") for p in months]

        # Pad axis so edge labels (Jan, Dec) aren't clipped
        x_start = pd.Timestamp(months[0].year, months[0].month, 1) - pd.Timedelta(
            days=5
        )
        x_end = (
            pd.Timestamp(months[-1].year, months[-1].month, 1)
            + pd.offsets.MonthEnd(1)
            + pd.Timedelta(days=5)
        )  # type: ignore[operator]

        fig.update_layout(
            title=dict(text="Message Activity Timeline", font=dict(size=14)),
            xaxis_title="Date",
            yaxis_title="Messages per Day",
            template="plotly_dark",
            font=dict(size=11),
            autosize=True,
            margin=dict(l=45, r=20, t=50, b=55),
            height=350,
            xaxis=dict(
                tickfont=dict(size=10),
                tickvals=tickvals,
                ticktext=ticktext,
                range=[x_start, x_end],
            ),
        )

        config = {"responsive": True, "displayModeBar": False, "staticPlot": False}

        filename = Path(self.output_dir) / f"timeline_{chat_name}.html"
        fig.write_html(str(filename), config=config)
        return f"images/{filename.name}"

    def create_media_pie_chart(
        self, media_data: Dict[str, int], chat_name: str
    ) -> Optional[str]:
        """Create pie chart for media distribution."""
        if not media_data:
            return None

        labels = list(media_data.keys())
        values = list(media_data.values())

        fig = go.Figure(
            data=[
                go.Pie(labels=labels, values=values, hole=0.3, textinfo="label+percent")
            ]
        )

        fig.update_layout(
            title=dict(text="Media Distribution", font=dict(size=14)),
            template="plotly_dark",
            font=dict(size=11),
            autosize=True,
            margin=dict(l=30, r=20, t=50, b=35),
            height=350,
        )

        config = {"responsive": True, "displayModeBar": False, "staticPlot": False}

        filename = Path(self.output_dir) / f"media_{chat_name}.html"
        fig.write_html(str(filename), config=config)
        return f"images/{filename.name}"

    def create_word_cloud(
        self, word_freq: Dict[str, int], chat_name: str
    ) -> Optional[str]:
        """Create word cloud image."""
        if not word_freq:
            return None

        # Reshape Arabic text for proper rendering
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display

            # Reshape Arabic words in the frequency dictionary
            reshaped_freq = {}
            for word, count in word_freq.items():
                # Check if word contains Arabic characters
                if any("\u0600" <= char <= "\u06ff" for char in word):
                    # Reshape Arabic text and apply bidirectional algorithm
                    reshaped = arabic_reshaper.reshape(word)
                    reshaped = get_display(reshaped)
                    reshaped_freq[reshaped] = count
                else:
                    reshaped_freq[word] = count

            word_freq = reshaped_freq
        except ImportError:
            # If arabic-reshaper is not available, continue without reshaping
            pass

        # Find a font that supports Arabic
        import matplotlib.font_manager as fm
        import platform
        import os

        font_path = None

        # Try to find Arial Unicode MS first (best for Arabic support)
        arial_unicode_path = "/Library/Fonts/Arial Unicode.ttf"
        if os.path.exists(arial_unicode_path):
            font_path = arial_unicode_path
        else:
            # Fallback: search for Arabic-supporting fonts
            if platform.system() == "Darwin":  # macOS
                # Look for Arial Unicode MS
                arial_unicode = [
                    f
                    for f in fm.fontManager.ttflist
                    if "Arial" in f.name and "Unicode" in f.name
                ]
                if arial_unicode:
                    font_path = arial_unicode[0].fname
                else:
                    # Try regular Arial
                    arial = [f for f in fm.fontManager.ttflist if f.name == "Arial"]
                    if arial:
                        font_path = arial[0].fname
                    else:
                        # Try system Arabic font
                        arabic_fonts = [
                            f for f in fm.fontManager.ttflist if "Arabic" in f.name
                        ]
                        if arabic_fonts:
                            font_path = arabic_fonts[0].fname

        # If no font found, WordCloud will use default (may not support Arabic)
        # Use dimensions optimized for mobile-first responsive design
        wordcloud = WordCloud(
            width=1000,
            height=500,
            background_color="black",
            colormap="viridis",
            max_words=100,
            font_path=font_path,
            prefer_horizontal=0.7,
            relative_scaling="auto",
        ).generate_from_frequencies(word_freq)

        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout(pad=0)

        filename = Path(self.output_dir) / f"wordcloud_{chat_name}.png"
        plt.savefig(str(filename), bbox_inches="tight", dpi=150, facecolor="black")
        plt.close()

        return f"images/{filename.name}"

    def create_activity_heatmap(self, messages, chat_name: str) -> str:
        """Create heatmap for activity by day of week and hour."""
        from collections import defaultdict

        activity = defaultdict(int)

        for msg in messages:
            weekday = msg.timestamp.strftime("%A")
            hour = msg.timestamp.hour
            activity[(weekday, hour)] += 1

        # Prepare data
        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        hours = list(range(24))

        z_data = []
        for day in weekdays:
            row = []
            for hour in hours:
                row.append(activity.get((day, hour), 0))
            z_data.append(row)

        fig = go.Figure(
            data=go.Heatmap(
                z=z_data,
                x=hours,
                y=weekdays,
                colorscale="Viridis",
                hovertemplate="Day: %{y}<br>Hour: %{x}<br>Messages: %{z}<extra></extra>",
            )
        )

        fig.update_layout(
            title=dict(text="Activity Heatmap (Day vs Hour)", font=dict(size=14)),
            xaxis_title="Hour",
            yaxis_title="Day of Week",
            template="plotly_dark",
            font=dict(size=11),
            autosize=True,
            margin=dict(l=70, r=20, t=50, b=45),
            height=350,
        )

        config = {"responsive": True, "displayModeBar": False, "staticPlot": False}

        filename = Path(self.output_dir) / f"heatmap_{chat_name}.html"
        fig.write_html(str(filename), config=config)
        return f"images/{filename.name}"

    def generate_all_visualizations(
        self, stats: Dict, messages, chat_name: str
    ) -> Dict[str, str]:
        """Generate all visualizations."""
        viz_files = {}

        # Clean chat name for filename
        safe_name = chat_name.replace(" ", "_").replace("/", "_")

        if stats.get("top_emojis"):
            viz_files["emojis"] = self.create_emoji_bar_chart(
                stats["top_emojis"], safe_name
            )

        if stats.get("top_senders"):
            viz_files["senders"] = self.create_sender_bar_chart(
                stats["top_senders"], safe_name
            )

        if stats.get("activity_timeline"):
            viz_files["timeline"] = self.create_timeline_chart(
                stats["activity_timeline"], safe_name
            )

        if stats.get("media_counts"):
            viz_files["media"] = self.create_media_pie_chart(
                stats["media_counts"], safe_name
            )

        if stats.get("word_frequency"):
            viz_files["wordcloud"] = self.create_word_cloud(
                stats["word_frequency"], safe_name
            )

        if messages:
            viz_files["heatmap"] = self.create_activity_heatmap(messages, safe_name)

        return viz_files
