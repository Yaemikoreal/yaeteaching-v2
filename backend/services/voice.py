"""Voice/TTS generation service using edge-tts (Microsoft Edge TTS)."""
import asyncio
import os
import uuid
from pathlib import Path
from typing import Optional

from config.settings import settings

# Storage directory for audio files
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "/tmp/yaeteaching/storage"))
AUDIO_DIR = STORAGE_DIR / "audio"


class VoiceGenerator:
    """Generate audio from lesson content using edge-tts."""

    # Voice mapping for different content types
    VOICE_MAPPING = {
        "teacher": "zh-CN-XiaoxiaoNeural",  # Female teacher voice
        "teacher_male": "zh-CN-YunxiNeural",  # Male teacher voice
        "student": "zh-CN-shaoyangNeural",  # Younger voice
        "narrator": "zh-CN-XiaoyiNeural",  # Narrator voice
    }

    # Maximum chunk length in characters (edge-tts handles ~5000 chars per request)
    MAX_CHUNK_LENGTH = 2000

    def __init__(self):
        self._ensure_storage_dir()
        self._tts_available = self._check_tts_available()

    def _ensure_storage_dir(self):
        """Ensure storage directory exists."""
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    def _check_tts_available(self) -> bool:
        """Check if edge-tts is available."""
        try:
            import edge_tts
            return True
        except ImportError:
            return False

    def generate(self, lesson_json: dict) -> list[str]:
        """Generate audio files for each section.

        Args:
            lesson_json: Lesson JSON dict

        Returns:
            List of audio file paths
        """
        if not self._tts_available:
            # Fallback to placeholder if edge-tts not installed
            return self._generate_placeholder_paths(lesson_json)

        audio_files = []
        job_id = str(uuid.uuid4())[:8]

        # Create job-specific directory
        job_audio_dir = AUDIO_DIR / job_id
        job_audio_dir.mkdir(parents=True, exist_ok=True)

        # Extract sections to convert
        outline = lesson_json.get("outline", {})
        sections = []

        # Introduction
        intro = outline.get("introduction", {})
        if intro:
            sections.append(("introduction", intro))

        # Main sections
        for i, section in enumerate(outline.get("main_sections", [])):
            if section:
                sections.append((f"section_{i}", section))

        # Conclusion
        conclusion = outline.get("conclusion", {})
        if conclusion:
            sections.append(("conclusion", conclusion))

        # Generate audio for each section
        for index, (section_name, section) in enumerate(sections):
            text = self._build_section_text(section)
            voice_style = self._get_voice_style(section, lesson_json)

            audio_path = asyncio.run(
                self._generate_section_audio_async(
                    text, section_name, job_audio_dir, voice_style, index
                )
            )
            if audio_path:
                audio_files.append(audio_path)

        return audio_files

    def _build_section_text(self, section: dict) -> str:
        """Build text to convert from section content."""
        title = section.get("title", "")
        content = section.get("content", "")

        # Combine title and content
        if title and content:
            text = f"{title}。\n{content}"
        elif title:
            text = title
        elif content:
            text = content
        else:
            return ""

        # Add key points if available
        key_points = section.get("key_points", [])
        if key_points:
            points_text = "要点：" + "、".join(key_points)
            text = f"{text}\n{points_text}"

        return text.strip()

    def _get_voice_style(self, section: dict, lesson_json: dict) -> str:
        """Get voice style for section."""
        media_hint = section.get("media_hint", {})
        voice_style = media_hint.get("voice_style", "teacher")

        # Validate voice style
        if voice_style not in self.VOICE_MAPPING:
            voice_style = "teacher"

        return voice_style

    async def _generate_section_audio_async(
        self,
        text: str,
        section_name: str,
        output_dir: Path,
        voice_style: str,
        index: int
    ) -> Optional[str]:
        """Generate audio for a single section using edge-tts.

        Args:
            text: Text to convert
            section_name: Section identifier
            output_dir: Output directory
            voice_style: Voice style to use
            index: Section index

        Returns:
            Path to generated audio file or None if generation failed
        """
        if not text:
            return None

        import edge_tts

        # Get voice for style
        voice = self.VOICE_MAPPING.get(voice_style, self.VOICE_MAPPING["teacher"])

        # Chunk text if too long
        chunks = self._chunk_text(text)

        output_path = output_dir / f"{section_name}.mp3"

        try:
            # Generate audio
            communicate = edge_tts.Communicate(text, voice)

            # Stream to file
            await communicate.save(str(output_path))

            return str(output_path)

        except Exception as e:
            print(f"Error generating audio for {section_name}: {e}")
            return None

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into chunks if too long."""
        if len(text) <= self.MAX_CHUNK_LENGTH:
            return [text]

        chunks = []
        # Split by natural breaks (paragraphs, sentences)
        paragraphs = text.split("\n")

        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) + 1 > self.MAX_CHUNK_LENGTH:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n" + para
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _generate_placeholder_paths(self, lesson_json: dict) -> list[str]:
        """Generate placeholder paths when TTS is not available."""
        audio_files = []
        outline = lesson_json.get("outline", {})

        # Introduction
        if outline.get("introduction"):
            audio_files.append("/storage/audio/placeholder_intro.mp3")

        # Main sections
        for i, section in enumerate(outline.get("main_sections", [])):
            if section:
                audio_files.append(f"/storage/audio/placeholder_section_{i}.mp3")

        # Conclusion
        if outline.get("conclusion"):
            audio_files.append("/storage/audio/placeholder_conclusion.mp3")

        return audio_files

    # Legacy method for backwards compatibility
    def _generate_section_audio(
        self, section: dict, index: int, subject: str
    ) -> str:
        """Legacy synchronous method - now generates placeholder."""
        text = self._build_section_text(section)
        if text:
            return f"/storage/audio/section_{index}.mp3"
        return f"/storage/audio/section_{index}_empty.mp3"

    # ChatTTS integration (optional, requires GPU)
    def _call_chattts(self, text: str, voice_style: str = "teacher") -> bytes:
        """Call ChatTTS for text-to-speech (requires ChatTTS installation).

        Note: ChatTTS requires:
        - PyTorch installation
        - GPU support recommended
        - ChatTTS model download (~1GB)

        To enable ChatTTS:
        pip install ChatTTS torch
        """
        try:
            import ChatTTS
            import torch

            chat = ChatTTS.Chat()
            chat.load_models()

            # Generate audio
            wavs = chat.infer([text])

            # Return first wav as bytes
            if wavs and len(wavs) > 0:
                return wavs[0]

            raise RuntimeError("ChatTTS generated no audio")

        except ImportError:
            raise NotImplementedError(
                "ChatTTS requires PyTorch installation. "
                "Use edge-tts for lightweight TTS, or install: pip install ChatTTS torch"
            )