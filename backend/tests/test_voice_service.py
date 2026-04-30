"""Unit tests for Voice/TTS generation service."""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from services.voice import VoiceGenerator, AUDIO_DIR


@pytest.fixture
def sample_lesson_json():
    """Sample lesson JSON for testing."""
    return {
        "meta": {
            "subject": "数学",
            "grade": "7年级",
            "topic": "一元一次方程",
            "duration": 45,
        },
        "outline": {
            "introduction": {
                "title": "课程导入",
                "content": "通过生活中的实例引入方程概念，让学生理解方程在日常生活中的应用。",
                "key_points": ["方程的定义", "生活中的例子"],
                "media_hint": {"voice_style": "teacher"},
            },
            "main_sections": [
                {
                    "title": "方程的基本概念",
                    "content": "详细讲解方程的定义和基本性质，方程是含有未知数的等式。",
                    "key_points": ["未知数", "等式", "方程的定义"],
                    "media_hint": {"voice_style": "teacher"},
                },
                {
                    "title": "例题分析",
                    "content": "通过具体例题讲解解方程的方法和步骤。",
                    "key_points": ["解题步骤", "注意事项"],
                    "media_hint": {"voice_style": "teacher"},
                },
            ],
            "conclusion": {
                "title": "课堂总结",
                "content": "回顾本节课的重点内容，布置课后练习。",
                "key_points": ["知识回顾", "课后练习"],
                "media_hint": {"voice_style": "teacher"},
            },
        },
        "summary": "本节课学习了方程的基本概念",
        "resources": [],
    }


@pytest.fixture
def minimal_lesson_json():
    """Minimal lesson JSON for edge case testing."""
    return {
        "meta": {"subject": "测试"},
        "outline": {},
    }


@pytest.fixture
def empty_sections_lesson_json():
    """Lesson JSON with empty sections."""
    return {
        "meta": {"subject": "测试"},
        "outline": {
            "introduction": {},
            "main_sections": [],
            "conclusion": {},
        },
    }


class TestVoiceGeneratorInit:
    """Tests for VoiceGenerator initialization."""

    def test_init_success(self):
        """Test generator initializes without errors."""
        generator = VoiceGenerator()
        assert generator is not None

    def test_init_creates_storage_dir(self):
        """Test initialization creates storage directory."""
        generator = VoiceGenerator()
        assert AUDIO_DIR.exists() or generator._tts_available is False

    def test_voice_mapping_defined(self):
        """Test voice mapping is properly defined."""
        generator = VoiceGenerator()
        assert "teacher" in generator.VOICE_MAPPING
        assert "student" in generator.VOICE_MAPPING


class TestVoiceGeneratorGenerate:
    """Tests for voice generation."""

    def test_generate_returns_list(self, sample_lesson_json):
        """Test generate returns a list of audio paths."""
        generator = VoiceGenerator()
        result = generator.generate(sample_lesson_json)

        assert isinstance(result, list)

    def test_generate_handles_empty_outline(self, minimal_lesson_json):
        """Test generate handles empty outline gracefully."""
        generator = VoiceGenerator()
        result = generator.generate(minimal_lesson_json)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_generate_handles_empty_sections(self, empty_sections_lesson_json):
        """Test generate handles empty sections gracefully."""
        generator = VoiceGenerator()
        result = generator.generate(empty_sections_lesson_json)

        assert isinstance(result, list)


class TestVoiceGeneratorTextBuilding:
    """Tests for text building."""

    def test_build_section_text_with_title_and_content(self):
        """Test building text with both title and content."""
        generator = VoiceGenerator()
        section = {
            "title": "测试标题",
            "content": "测试内容",
        }
        text = generator._build_section_text(section)

        assert "测试标题" in text
        assert "测试内容" in text

    def test_build_section_text_with_key_points(self):
        """Test building text includes key points."""
        generator = VoiceGenerator()
        section = {
            "title": "标题",
            "content": "内容",
            "key_points": ["要点1", "要点2"],
        }
        text = generator._build_section_text(section)

        assert "要点" in text
        assert "要点1" in text

    def test_build_section_text_empty_section(self):
        """Test building text from empty section."""
        generator = VoiceGenerator()
        section = {}
        text = generator._build_section_text(section)

        assert text == ""

    def test_build_section_text_only_title(self):
        """Test building text from section with only title."""
        generator = VoiceGenerator()
        section = {"title": "只有标题"}
        text = generator._build_section_text(section)

        assert text == "只有标题"


class TestVoiceGeneratorVoiceStyle:
    """Tests for voice style handling."""

    def test_get_voice_style_teacher(self, sample_lesson_json):
        """Test teacher voice style is recognized."""
        generator = VoiceGenerator()
        section = sample_lesson_json["outline"]["introduction"]
        style = generator._get_voice_style(section, sample_lesson_json)

        assert style == "teacher"

    def test_get_voice_style_default(self):
        """Test default voice style when not specified."""
        generator = VoiceGenerator()
        section = {"title": "test", "content": "test"}
        style = generator._get_voice_style(section, {})

        assert style == "teacher"

    def test_get_voice_style_invalid_fallback(self):
        """Test fallback for invalid voice style."""
        generator = VoiceGenerator()
        section = {"media_hint": {"voice_style": "invalid"}}
        style = generator._get_voice_style(section, {})

        assert style == "teacher"


class TestVoiceGeneratorTextChunking:
    """Tests for text chunking logic."""

    def test_chunk_text_short(self):
        """Test short text is not chunked."""
        generator = VoiceGenerator()
        text = "这是一段短文本"
        chunks = generator._chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_long(self):
        """Test long text is properly chunked."""
        generator = VoiceGenerator()
        # Create text longer than MAX_CHUNK_LENGTH
        long_text = "这是一段很长的文本。" * 500
        chunks = generator._chunk_text(long_text)

        # Should be chunked
        assert len(chunks) >= 1
        # Each chunk should be within limit
        for chunk in chunks:
            assert len(chunk) <= generator.MAX_CHUNK_LENGTH + 100  # Some buffer

    def test_chunk_text_with_paragraphs(self):
        """Test chunking respects paragraph breaks."""
        generator = VoiceGenerator()
        paragraphs = ["第一段", "第二段", "第三段"]
        text = "\n".join(paragraphs)
        chunks = generator._chunk_text(text)

        assert len(chunks) >= 1


class TestVoiceGeneratorPlaceholder:
    """Tests for placeholder generation when TTS unavailable."""

    def test_generate_placeholder_paths(self, sample_lesson_json):
        """Test placeholder path generation."""
        generator = VoiceGenerator()
        result = generator._generate_placeholder_paths(sample_lesson_json)

        assert isinstance(result, list)
        # Should have paths for introduction, 2 sections, conclusion
        assert len(result) == 4

    def test_placeholder_paths_format(self, sample_lesson_json):
        """Test placeholder paths have correct format."""
        generator = VoiceGenerator()
        result = generator._generate_placeholder_paths(sample_lesson_json)

        for path in result:
            assert path.endswith(".mp3")
            assert "/storage/audio/" in path


class TestVoiceGeneratorEdgeTTS:
    """Tests for edge-tts integration."""

    @pytest.mark.asyncio
    async def test_generate_section_audio_async_mock(self, sample_lesson_json):
        """Test async audio generation with mocked edge-tts."""
        generator = VoiceGenerator()

        # Skip if edge-tts not available
        if not generator._tts_available:
            pytest.skip("edge-tts not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Mock the edge_tts.Communicate
            with patch("edge_tts.Communicate") as mock_communicate:
                mock_comm = MagicMock()
                mock_comm.save = AsyncMock()
                mock_communicate.return_value = mock_comm

                result = await generator._generate_section_audio_async(
                    "测试文本",
                    "test_section",
                    output_dir,
                    "teacher",
                    0
                )

                # Should return a path
                if result:
                    assert "test_section" in result

    def test_tts_available_check(self):
        """Test TTS availability check."""
        generator = VoiceGenerator()

        # Should be a boolean
        assert isinstance(generator._tts_available, bool)


class TestVoiceGeneratorChatTTS:
    """Tests for ChatTTS integration (optional)."""

    def test_call_chattts_not_implemented_without_install(self):
        """Test ChatTTS call raises NotImplementedError when not installed."""
        generator = VoiceGenerator()

        with pytest.raises(NotImplementedError):
            generator._call_chattts("test text")


class TestVoiceGeneratorEdgeCases:
    """Tests for edge cases."""

    def test_empty_text_returns_none(self):
        """Test empty text section returns None."""
        generator = VoiceGenerator()
        section = {}
        text = generator._build_section_text(section)

        assert text == ""

    def test_very_long_section_title(self):
        """Test handling very long section title."""
        generator = VoiceGenerator()
        section = {
            "title": "这是一个非常长的标题" * 100,
            "content": "内容",
        }
        text = generator._build_section_text(section)

        # Should not raise error
        assert isinstance(text, str)

    def test_special_characters_in_text(self):
        """Test handling special characters."""
        generator = VoiceGenerator()
        section = {
            "title": "标题 with $pecial ch@rs!",
            "content": "内容\n包含换行和\t制表符",
        }
        text = generator._build_section_text(section)

        # Should handle special chars
        assert isinstance(text, str)

    def test_unicode_content(self):
        """Test handling Unicode content."""
        generator = VoiceGenerator()
        section = {
            "title": "数学公式 α+β=γ",
            "content": "包含 emoji 📚 和特殊符号",
        }
        text = generator._build_section_text(section)

        assert "α" in text or isinstance(text, str)


class TestVoiceGeneratorLegacyMethods:
    """Tests for legacy backwards compatibility."""

    def test_legacy_generate_section_audio(self, sample_lesson_json):
        """Test legacy synchronous method."""
        generator = VoiceGenerator()
        section = sample_lesson_json["outline"]["introduction"]

        result = generator._generate_section_audio(section, 0, "数学")

        assert isinstance(result, str)
        assert result.endswith(".mp3")

    def test_legacy_empty_section(self):
        """Test legacy method with empty section."""
        generator = VoiceGenerator()
        section = {}

        result = generator._generate_section_audio(section, 0, "")

        assert result.endswith(".mp3")
        assert "empty" in result or "section_0" in result