"""Tests for PPT generation service."""
import pytest
import os
from services.ppt import PPTGenerator
from templates import TemplateStyle, TemplateConfig, get_recommended_style


# Sample lesson JSON for testing
SAMPLE_LESSON = {
    "meta": {
        "subject": "physics",
        "grade": "七年级",
        "topic": "力学基础",
        "duration": 45,
        "style": "启发式教学"
    },
    "outline": {
        "introduction": {
            "title": "课程导入",
            "content": "通过生活中的实例引入力学概念...\n力是物体对物体的作用。",
            "key_points": ["建立学习兴趣", "理解力的定义"],
            "media_hint": {"slide_type": "title"}
        },
        "main_sections": [
            {
                "title": "力的概念",
                "content": "力是物体之间的相互作用。\n力的作用效果：改变运动状态、改变形状。",
                "key_points": ["力的定义", "力的作用效果"],
                "media_hint": {"slide_type": "knowledge"}
            },
            {
                "title": "例题：力的分析",
                "content": "分析以下场景中的力：\n1. 推箱子\n2. 拉弹簧",
                "key_points": ["受力分析", "力的方向"],
                "media_hint": {"slide_type": "example"}
            }
        ],
        "conclusion": {
            "title": "课堂总结",
            "content": "本节课学习了力的基本概念和应用。",
            "key_points": ["知识回顾", "课后练习"],
            "media_hint": {"slide_type": "summary"}
        }
    },
    "summary": "本节课介绍了力的基本概念和作用效果。",
    "resources": []
}


def test_ppt_generator_basic():
    """Test basic PPT generation."""
    generator = PPTGenerator()
    output_path = generator.generate(SAMPLE_LESSON)

    assert output_path is not None
    assert output_path.endswith(".pptx")
    assert os.path.exists(output_path)

    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)


def test_ppt_generator_with_style():
    """Test PPT generation with specific style."""
    generator = PPTGenerator(style=TemplateStyle.creative)
    output_path = generator.generate(SAMPLE_LESSON)

    assert output_path is not None
    assert "creative" in output_path
    assert os.path.exists(output_path)

    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)


def test_all_template_styles():
    """Test generating PPT with all available styles."""
    generator = PPTGenerator()
    results = generator.generate_all_styles(SAMPLE_LESSON)

    assert len(results) == 3  # classic, creative, minimal
    for style, path in results.items():
        if not path.startswith("Error"):
            assert os.path.exists(path)
            if os.path.exists(path):
                os.remove(path)


def test_template_config():
    """Test template configuration retrieval."""
    classic_config = TemplateConfig.get_style(TemplateStyle.classic)
    assert classic_config["name"] == "经典学术风格"
    assert classic_config["primary_color"] is not None

    creative_config = TemplateConfig.get_style(TemplateStyle.creative)
    assert creative_config["name"] == "创意活泼风格"


def test_subject_style_mapping():
    """Test subject to style mapping."""
    assert get_recommended_style("physics") == TemplateStyle.classic
    assert get_recommended_style("chinese") == TemplateStyle.creative
    assert get_recommended_style("mathematics") == TemplateStyle.minimal
    assert get_recommended_style("unknown") == TemplateStyle.classic  # default


def test_slide_type_handling():
    """Test that different slide types are handled correctly."""
    generator = PPTGenerator()
    output_path = generator.generate(SAMPLE_LESSON)

    # Verify file was created
    assert os.path.exists(output_path)

    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)


def test_output_path_custom():
    """Test custom output path."""
    generator = PPTGenerator()
    custom_path = "/tmp/test_custom.pptx"
    output_path = generator.generate(SAMPLE_LESSON, output_path=custom_path)

    assert output_path == custom_path
    assert os.path.exists(output_path)

    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])