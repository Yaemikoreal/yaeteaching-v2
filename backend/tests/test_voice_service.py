"""Tests for Voice/TTS generation service."""
import pytest
from unittest.mock import MagicMock, patch
from services.voice import VoiceGenerator


@pytest.fixture
def sample_lesson_json():
    """Sample lesson JSON for testing."""
    return {
        "meta": {
            "subject": "数学",
            "grade": "7年级",
        },
        "outline": {
            "introduction": {
                "title": "课程导入",
                "content": "通过生活中的实例引入方程概念",
            },
            "main_sections": [
                {
                    "title": "方程的基本概念",
                    "content": "详细讲解方程的定义",
                },
            ],
            "conclusion": {
                "title": "课堂总结",
                "content": "回顾本节课重点",
            },
        },
        "summary": "本节课学习了方程的基本概念",
        "resources": [],
    }


def test_voice_generator_init():
    """Test VoiceGenerator initializes correctly."""
    generator = VoiceGenerator()
    assert generator is not None


def test_voice_generator_generate(sample_lesson_json):
    """Test voice generation returns audio file paths."""
    generator = VoiceGenerator()
    result = generator.generate(sample_lesson_json)

    # Should return list of audio paths
    assert isinstance(result, list)
    assert len(result) > 0
    for path in result:
        assert path.endswith(".mp3")


def test_voice_generator_generate_section_audio(sample_lesson_json):
    """Test generating audio for a single section."""
    generator = VoiceGenerator()
    section = {
        "title": "测试章节",
        "content": "测试内容",
    }

    result = generator._generate_section_audio(section, 0, "数学")

    # Should return mock path (actual implementation pending)
    assert result == "/storage/audio/section_0.mp3"


def test_voice_generator_empty_outline():
    """Test voice generation with empty outline."""
    generator = VoiceGenerator()
    empty_lesson = {
        "meta": {"subject": "数学"},
        "outline": {},
        "summary": "",
        "resources": [],
    }
    result = generator.generate(empty_lesson)

    # Should return empty list or handle gracefully
    assert isinstance(result, list)


def test_voice_generator_call_chattts_raises():
    """Test ChatTTS integration raises NotImplementedError."""
    generator = VoiceGenerator()

    with pytest.raises(NotImplementedError):
        generator._call_chattts("test text", "teacher")


def test_voice_generator_missing_sections():
    """Test voice generation handles missing sections."""
    generator = VoiceGenerator()
    lesson_json = {
        "meta": {"subject": "物理"},
        "outline": {
            "introduction": None,
            "main_sections": [],
            "conclusion": {"title": "总结", "content": "内容"},
        },
        "summary": "",
        "resources": [],
    }
    result = generator.generate(lesson_json)

    # Should still return paths for available sections
    assert isinstance(result, list)


def test_voice_generator_with_full_lesson(sample_lesson_json):
    """Test VoiceGenerator with complete lesson structure."""
    generator = VoiceGenerator()
    with patch.object(generator, "_generate_section_audio", return_value="/mock/audio.mp3"):
        result = generator.generate(sample_lesson_json)
        # Should generate audio for intro, main sections, and conclusion
        assert len(result) >= 1