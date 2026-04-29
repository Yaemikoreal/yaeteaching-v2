"""Tests for PPT generation service."""
import pytest
from unittest.mock import MagicMock, patch
from services.ppt import PPTGenerator


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
                "content": "通过生活中的实例引入方程概念",
                "key_points": ["建立学习兴趣"],
                "media_hint": {"slide_type": "title"},
            },
            "main_sections": [
                {
                    "title": "方程的基本概念",
                    "content": "详细讲解方程的定义",
                    "key_points": ["未知数", "等式"],
                    "media_hint": {"slide_type": "knowledge"},
                },
                {
                    "title": "例题分析",
                    "content": "通过具体例题加深理解",
                    "key_points": ["解题方法"],
                    "media_hint": {"slide_type": "example"},
                },
            ],
            "conclusion": {
                "title": "课堂总结",
                "content": "回顾本节课重点",
                "key_points": ["知识回顾"],
                "media_hint": {"slide_type": "summary"},
            },
        },
        "summary": "本节课学习了方程的基本概念",
        "resources": [],
    }


def test_ppt_generator_init():
    """Test PPTGenerator initializes correctly."""
    generator = PPTGenerator()
    assert generator is not None


@patch("services.ppt.Presentation")
def test_ppt_generator_generate(mock_presentation, sample_lesson_json):
    """Test PPT generation from lesson JSON."""
    mock_prs = MagicMock()
    mock_presentation.return_value = mock_prs

    # Mock slide layouts
    mock_prs.slide_layouts = [MagicMock(), MagicMock()]

    generator = PPTGenerator()
    result = generator.generate(sample_lesson_json)

    # Should save presentation
    mock_prs.save.assert_called_once()
    assert result.endswith(".pptx")


@patch("services.ppt.Presentation")
def test_ppt_generator_add_title_slide(mock_presentation):
    """Test adding title slide."""
    mock_prs = MagicMock()
    mock_presentation.return_value = mock_prs

    # Mock slide layouts
    mock_slide_layout = MagicMock()
    mock_prs.slide_layouts = [mock_slide_layout, mock_slide_layout]

    # Mock slide
    mock_slide = MagicMock()
    mock_prs.slides.add_slide.return_value = mock_slide
    mock_slide.shapes.title = MagicMock()
    mock_slide.placeholders = {1: MagicMock()}

    generator = PPTGenerator()
    generator._add_title_slide(mock_prs, {"topic": "测试主题", "subject": "数学", "grade": "7年级"})

    # Should add slide
    mock_prs.slides.add_slide.assert_called()


@patch("services.ppt.Presentation")
def test_ppt_generator_add_content_slide(mock_presentation):
    """Test adding content slide."""
    mock_prs = MagicMock()
    mock_presentation.return_value = mock_prs

    # Mock slide layouts
    mock_slide_layout = MagicMock()
    mock_prs.slide_layouts = [mock_slide_layout, mock_slide_layout]

    # Mock slide
    mock_slide = MagicMock()
    mock_prs.slides.add_slide.return_value = mock_slide
    mock_slide.shapes.title = MagicMock()

    # Mock placeholder with text_frame
    mock_placeholder = MagicMock()
    mock_placeholder.text_frame = MagicMock()
    mock_slide.placeholders = {1: mock_placeholder}

    generator = PPTGenerator()
    section = {
        "title": "测试章节",
        "content": "测试内容",
        "key_points": ["要点1", "要点2"],
    }

    from models.lesson import SlideType
    generator._add_content_slide(mock_prs, section, SlideType.knowledge)

    # Should add slide
    mock_prs.slides.add_slide.assert_called()


@patch("services.ppt.Presentation")
def test_ppt_generator_empty_outline(mock_presentation):
    """Test PPT generation with empty outline."""
    mock_prs = MagicMock()
    mock_presentation.return_value = mock_prs
    mock_prs.slide_layouts = [MagicMock(), MagicMock()]

    generator = PPTGenerator()
    empty_lesson = {
        "meta": {"topic": "空课程"},
        "outline": {},
        "summary": "",
        "resources": [],
    }
    result = generator.generate(empty_lesson)

    # Should still save
    mock_prs.save.assert_called_once()


def test_ppt_generator_with_sample_lesson_json(sample_lesson_json):
    """Test PPTGenerator with fixture data."""
    generator = PPTGenerator()
    with patch("services.ppt.Presentation") as mock_prs:
        mock_instance = MagicMock()
        mock_prs.return_value = mock_instance
        mock_instance.slide_layouts = [MagicMock(), MagicMock()]
        result = generator.generate(sample_lesson_json)
        assert result is not None