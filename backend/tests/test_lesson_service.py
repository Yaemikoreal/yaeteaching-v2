"""Tests for lesson generation service."""
import pytest
from services.lesson import LessonGenerator
from models.lesson import LessonMeta, LessonJSON


def test_lesson_generator_init():
    """Test LessonGenerator initializes correctly."""
    generator = LessonGenerator()
    assert generator.client is not None


def test_lesson_generator_template():
    """Test template generation fallback."""
    generator = LessonGenerator()
    request_data = {
        "subject": "数学",
        "grade": "7年级",
        "topic": "一元一次方程",
        "duration": 45,
        "style": "启发式教学",
    }
    result = generator.generate(request_data)

    # Check structure
    assert "meta" in result
    assert "outline" in result
    assert "summary" in result
    assert "resources" in result

    # Check meta (internal dict uses topic/duration)
    assert result["meta"]["subject"] == "数学"
    assert result["meta"]["grade"] == "7年级"
    assert result["meta"]["topic"] == "一元一次方程"

    # Check outline structure
    assert "introduction" in result["outline"]
    assert "main_sections" in result["outline"]
    assert "conclusion" in result["outline"]


def test_lesson_meta_alias_serialization():
    """Test LessonMeta serializes with correct aliases for frontend."""
    # Create LessonMeta from internal dict (uses topic/duration)
    meta_dict = {
        "subject": "数学",
        "grade": "7年级",
        "topic": "一元一次方程",
        "duration": 45,
        "style": "启发式教学",
    }
    meta = LessonMeta(**meta_dict)

    # Serialize with aliases (frontend expects title/duration_minutes)
    serialized = meta.model_dump(by_alias=True)
    assert serialized["subject"] == "数学"
    assert serialized["grade"] == "7年级"
    assert serialized["title"] == "一元一次方程"
    assert serialized["duration_minutes"] == 45

    # Verify original field names are NOT in serialized output
    assert "topic" not in serialized
    assert "duration" not in serialized


def test_lesson_meta_accepts_both_names():
    """Test LessonMeta accepts both internal and alias field names."""
    # Accept alias names (from frontend)
    meta1 = LessonMeta(
        subject="数学",
        grade="7年级",
        title="方程",  # alias
        duration_minutes=30,  # alias
    )
    assert meta1.topic == "方程"  # internal field
    assert meta1.duration == 30  # internal field

    # Accept internal names (from LLM/template)
    meta2 = LessonMeta(
        subject="数学",
        grade="7年级",
        topic="方程",  # internal
        duration=30,  # internal
    )
    assert meta2.topic == "方程"
    assert meta2.duration == 30


def test_lesson_generator_build_prompt():
    """Test prompt building."""
    generator = LessonGenerator()
    request_data = {
        "subject": "物理",
        "grade": "高一",
        "topic": "牛顿第一定律",
        "duration": 30,
        "style": None,
    }
    prompt = generator._build_prompt(request_data)

    assert "物理" in prompt
    assert "高一" in prompt
    assert "牛顿第一定律" in prompt
    assert "30" in prompt


def test_lesson_generator_parse_response():
    """Test parsing LLM JSON response."""
    generator = LessonGenerator()

    # Valid JSON response (LLM returns topic/duration)
    valid_response = """```json
{
  "meta": {
    "subject": "数学",
    "grade": "7年级",
    "topic": "方程",
    "duration": 45
  },
  "outline": {
    "introduction": {"title": "导入", "content": "test"},
    "main_sections": [],
    "conclusion": {"title": "总结", "content": "test"}
  },
  "summary": "test"
}
```"""

    result = generator._parse_llm_response(valid_response)
    assert result["meta"]["subject"] == "数学"
    assert "outline" in result

    # Verify dict can be validated by LessonJSON and serialized with aliases
    lesson = LessonJSON(**result)
    serialized_meta = lesson.meta.model_dump(by_alias=True)
    assert serialized_meta["title"] == "方程"
    assert serialized_meta["duration_minutes"] == 45


def test_lesson_generator_parse_invalid_response():
    """Test parsing invalid response raises error."""
    generator = LessonGenerator()

    # Invalid response
    invalid_response = "This is not valid JSON"

    with pytest.raises(ValueError):
        generator._parse_llm_response(invalid_response)