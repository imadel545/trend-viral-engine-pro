"""
Generator Service - Generate content (scripts, videos, captions).
Uses Groq LLM for scripts and MoviePy for videos.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

# MoviePy import - optionnel pour le moment
try:
    from moviepy.editor import (
        ColorClip,
        CompositeVideoClip,
        TextClip,
        concatenate_videoclips,
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    logger.warning("MoviePy not available - video generation disabled")
    MOVIEPY_AVAILABLE = False
    # Types placeholder - ne jamais instantier
    ColorClip = None  # type: ignore
    CompositeVideoClip = None  # type: ignore
    TextClip = None  # type: ignore
    concatenate_videoclips = None  # type: ignore

from src.core.config import settings


class ScriptGenerator:
    """Generate video scripts using LLM."""

    def __init__(self):
        self.logger = logger.bind(generator="script")
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def generate(self, topic: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Generate script for a topic."""
        context = context or {}
        duration = context.get("duration", 25)

        prompt = self._build_prompt(topic, duration)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Tu es un expert en création de contenu viral pour TikTok et Instagram. Tu crées des scripts courts, percutants et engageants.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": settings.groq_max_tokens,
                        "temperature": settings.groq_temperature,
                    },
                )
                response.raise_for_status()

                data = response.json()
                script_text = data["choices"][0]["message"]["content"]

                # Parse script
                script = self._parse_script(script_text, topic)
                self.logger.info(f"Generated script for topic: {topic}")

                return script

        except Exception as e:
            self.logger.error(f"Error generating script: {e}")
            # Fallback to simple script
            return self._fallback_script(topic)

    def _build_prompt(self, topic: str, duration: int) -> str:
        """Build prompt for LLM."""
        return f"""Crée un script de vidéo virale pour TikTok/Instagram sur le sujet: "{topic}"

Durée: {duration} secondes

Le script DOIT contenir:
1. HOOK (3 secondes): Une accroche percutante qui capte l'attention immédiatement
2. PAYOFF (15-20 secondes): Le contenu principal, informatif et engageant
3. CTA (2-3 secondes): Un appel à l'action clair (like, follow, comment)

Format de réponse (JSON):
{{
    "hook": "texte du hook",
    "payoff": "texte du payoff",
    "cta": "texte du CTA",
    "caption": "caption pour le post (avec hashtags)"
}}

Sois créatif, viral et percutant !"""

    def _parse_script(self, script_text: str, topic: str = "") -> Dict[str, str]:
        """Parse LLM response into structured script."""
        try:
            # Try to parse as JSON
            script = json.loads(script_text)
            return script
        except:
            # Fallback: parse manually
            lines = script_text.strip().split("\n")
            topic_hashtag = topic.replace(' ', '').replace(',', '').replace('.', '') if topic else "viral"
            return {
                "hook": lines[0] if len(lines) > 0 else "Découvre ça !",
                "payoff": "\n".join(lines[1:-1]) if len(lines) > 2 else "Contenu incroyable",
                "cta": lines[-1] if len(lines) > 1 else "Like et abonne-toi !",
                "caption": f"#{topic_hashtag} #viral #tendance",
            }

    def _fallback_script(self, topic: str) -> Dict[str, str]:
        """Fallback script when API fails."""
        return {
            "hook": f"🔥 Regarde ça sur {topic} !",
            "payoff": f"Tout ce que tu dois savoir sur {topic}. C'est fou ce que personne ne te dit !",
            "cta": "💡 Like si tu as appris quelque chose !",
            "caption": f"#{topic.replace(' ', '')} #viral #tendance #pourtoi",
        }


class VideoGenerator:
    """Generate videos using MoviePy."""

    def __init__(self):
        self.logger = logger.bind(generator="video")

    def generate(
        self, script: Dict[str, str], output_path: Optional[Path] = None
    ) -> Path:
        """Generate video from script."""
        # Check if MoviePy is available
        if not MOVIEPY_AVAILABLE:
            self.logger.warning("MoviePy not available, skipping video generation")
            # Create empty placeholder file
            output_path = output_path or self._get_output_path()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(script, indent=2))
            return output_path
        
        output_path = output_path or self._get_output_path()

        try:
            # Create clips
            clips = []

            # Hook clip (3 seconds)
            hook_clip = self._create_text_clip(
                script["hook"], duration=3, fontsize=80, color="yellow"
            )
            clips.append(hook_clip)

            # Payoff clip (remaining time)
            payoff_clip = self._create_text_clip(
                script["payoff"], duration=20, fontsize=60, color="white"
            )
            clips.append(payoff_clip)

            # CTA clip (2 seconds)
            cta_clip = self._create_text_clip(
                script["cta"], duration=2, fontsize=70, color="green"
            )
            clips.append(cta_clip)

            # Concatenate
            final_clip = concatenate_videoclips(clips, method="compose")

            # Write video
            final_clip.write_videofile(
                str(output_path),
                fps=settings.video_fps,
                codec="libx264",
                audio=False,
                preset="medium",
                threads=4,
            )

            self.logger.info(f"Video generated: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error generating video: {e}")
            raise

    def _create_text_clip(
        self, text: str, duration: int, fontsize: int = 60, color: str = "white"
    ):
        """Create a text clip with background."""
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("MoviePy is required for video generation")
        
        # Background
        bg = ColorClip(
            size=(settings.video_width, settings.video_height),
            color=(0, 0, 0),
            duration=duration,
        )

        # Text
        txt = (
            TextClip(
                text,
                fontsize=fontsize,
                color=color,
                font="Arial-Bold",
                size=(settings.video_width - 100, None),
                method="caption",
            )
            .set_duration(duration)
            .set_position("center")
        )

        return CompositeVideoClip([bg, txt])

    def _get_output_path(self) -> Path:
        """Generate output path for video."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return settings.output_path / f"video_{timestamp}.mp4"


class CaptionGenerator:
    """Generate captions for posts."""

    def __init__(self):
        self.logger = logger.bind(generator="caption")

    def generate(self, script: Dict[str, str], topic: str) -> str:
        """Generate caption from script and topic."""
        caption = script.get("caption", "")

        if not caption:
            # Generate from topic
            caption = f"🔥 {topic} #viral #tendance #pourtoi"

        self.logger.info("Caption generated")
        return caption


class GeneratorService:
    """Main generator service."""

    def __init__(self):
        self.logger = logger.bind(service="generator")
        self.script_gen = ScriptGenerator()
        self.video_gen = VideoGenerator()
        self.caption_gen = CaptionGenerator()

    async def generate_content(
        self, topic: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate complete content package."""
        self.logger.info(f"Generating content for: {topic}")

        # Generate script
        script = await self.script_gen.generate(topic, context)

        # Generate video
        video_path = self.video_gen.generate(script)

        # Generate caption
        caption = self.caption_gen.generate(script, topic)

        # Save caption
        caption_path = video_path.with_suffix(".txt")
        caption_path.write_text(caption, encoding="utf-8")

        # Save metadata
        metadata = {
            "topic": topic,
            "script": script,
            "caption": caption,
            "video_path": str(video_path),
            "caption_path": str(caption_path),
            "generated_at": datetime.now().isoformat(),
        }

        metadata_path = video_path.with_suffix(".json")
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

        self.logger.info(f"Content generated: {video_path}")

        return metadata


# Singleton
_generator_service: Optional[GeneratorService] = None


def get_generator_service() -> GeneratorService:
    """Get or create generator service instance."""
    global _generator_service
    if _generator_service is None:
        _generator_service = GeneratorService()
    return _generator_service
