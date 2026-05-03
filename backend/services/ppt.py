"""Enhanced PPT generation service using template system."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from typing import Dict, Any, Optional
import os
from datetime import datetime

from config.settings import settings
from models.lesson import LessonJSON, SlideType
from templates import TemplateStyle, TemplateConfig, get_recommended_style


class PPTGenerator:
    """Generate PowerPoint from lesson content using template system."""

    def __init__(self, style: Optional[TemplateStyle] = None):
        """Initialize PPT generator with optional style.

        Args:
            style: Template style to use. If None, will auto-select based on subject.
        """
        self.style = style
        self.storage_path = getattr(settings, 'storage_path', '/tmp/ppt')

    def generate(self, lesson_json: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Generate PPT file from lesson JSON.

        Args:
            lesson_json: Lesson JSON dict
            output_path: Optional custom output path

        Returns:
            Path to generated PPT file
        """
        # Extract lesson data
        meta = lesson_json.get("meta", {})
        outline = lesson_json.get("outline", {})

        # Select template style
        if self.style:
            style = self.style
        else:
            subject = meta.get("subject", "").lower()
            style = get_recommended_style(subject)

        config = TemplateConfig.get_style(style)

        # Create presentation
        prs = Presentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)

        # Generate slides
        self._add_title_slide(prs, meta, config)

        # Introduction section
        intro = outline.get("introduction", {})
        if intro:
            self._add_content_slide(prs, intro, SlideType.title, config)

        # Main sections
        for section in outline.get("main_sections", []):
            slide_type_str = section.get("media_hint", {}).get("slide_type", "knowledge")
            try:
                slide_type = SlideType(slide_type_str)
            except ValueError:
                slide_type = SlideType.knowledge
            self._add_content_slide(prs, section, slide_type, config)

        # Conclusion section
        conclusion = outline.get("conclusion", {})
        if conclusion:
            self._add_content_slide(prs, conclusion, SlideType.summary, config)

        # Save to storage
        if not output_path:
            topic = meta.get("topic", "lesson")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{topic}_{style.value}_{timestamp}.pptx"
            output_path = os.path.join(self.storage_path, filename)

        # Ensure storage directory exists
        os.makedirs(self.storage_path, exist_ok=True)

        prs.save(output_path)
        return output_path

    def _add_title_slide(self, prs: Presentation, meta: Dict[str, Any], config: Dict[str, Any]):
        """Add title slide with lesson metadata and styled background."""
        # Use blank layout for custom styling
        slide_layout = prs.slide_layouts[6]  # Blank layout
        slide = prs.slides.add_slide(slide_layout)

        # Add colored header bar
        from pptx.enum.shapes import MSO_SHAPE
        header = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0), Inches(0),
            Inches(10), Inches(2.5)
        )
        header.fill.solid()
        header.fill.fore_color.rgb = config["primary_color"]
        header.line.fill.background()

        # Add title text box
        title_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(0.8),
            Inches(9), Inches(1.2)
        )
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = meta.get("topic", "课程")
        p.font.size = config["title_size"]
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.font.name = config["title_font"]
        p.alignment = PP_ALIGN.CENTER

        # Add subtitle (subject + grade)
        subtitle_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(3),
            Inches(9), Inches(0.8)
        )
        tf = subtitle_box.text_frame
        p = tf.paragraphs[0]
        subject = meta.get("subject", "")
        grade = meta.get("grade", "")
        duration = meta.get("duration", "")
        p.text = f"{subject} | {grade} | {duration}分钟"
        p.font.size = config["subtitle_size"]
        p.font.color.rgb = config["text_color"]
        p.font.name = config["body_font"]
        p.alignment = PP_ALIGN.CENTER

        # Add style indicator at bottom
        style_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(6.5),
            Inches(9), Inches(0.5)
        )
        tf = style_box.text_frame
        p = tf.paragraphs[0]
        p.text = f"模板风格: {config['name']}"
        p.font.size = Pt(12)
        p.font.color.rgb = config["secondary_color"]
        p.font.name = config["body_font"]
        p.alignment = PP_ALIGN.RIGHT

    def _add_content_slide(self, prs: Presentation, section: Dict[str, Any],
                           slide_type: SlideType, config: Dict[str, Any]):
        """Add content slide based on section and type with styling."""
        slide_layout = prs.slide_layouts[6]  # Blank layout
        slide = prs.slides.add_slide(slide_layout)

        # Add header bar with slide type indicator
        from pptx.enum.shapes import MSO_SHAPE
        header = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0), Inches(0),
            Inches(10), Inches(1)
        )
        header.fill.solid()
        # Use accent color for different slide types
        if slide_type == SlideType.example:
            header.fill.fore_color.rgb = config["accent_color"]
        elif slide_type == SlideType.summary:
            header.fill.fore_color.rgb = config["secondary_color"]
        else:
            header.fill.fore_color.rgb = config["primary_color"]
        header.line.fill.background()

        # Add slide type label
        type_label = slide.shapes.add_textbox(
            Inches(0.3), Inches(0.2),
            Inches(2), Inches(0.5)
        )
        tf = type_label.text_frame
        p = tf.paragraphs[0]
        type_names = {
            SlideType.title: "导入",
            SlideType.knowledge: "知识点",
            SlideType.example: "例题",
            SlideType.summary: "总结",
            SlideType.exercise: "练习",
        }
        p.text = type_names.get(slide_type, "内容")
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.font.name = config["body_font"]

        # Add title
        title_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(1.3),
            Inches(9), Inches(0.8)
        )
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = section.get("title", "")
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = config["primary_color"]
        p.font.name = config["title_font"]

        # Add content body
        content_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(2.3),
            Inches(9), Inches(3.5)
        )
        tf = content_box.text_frame
        tf.word_wrap = True

        # Main content
        p = tf.paragraphs[0]
        content = section.get("content", "")
        # Split content into paragraphs
        for i, para in enumerate(content.split("\n")):
            if i == 0:
                p.text = para
            else:
                p = tf.add_paragraph()
                p.text = para
            p.font.size = config["body_size"]
            p.font.color.rgb = config["text_color"]
            p.font.name = config["body_font"]
            p.space_after = Pt(12)

        # Add key points as bullet list
        key_points = section.get("key_points", [])
        if key_points:
            points_box = slide.shapes.add_textbox(
                Inches(0.5), Inches(5.8),
                Inches(9), Inches(1.2)
            )
            tf = points_box.text_frame
            tf.word_wrap = True

            p = tf.paragraphs[0]
            p.text = "关键要点："
            p.font.size = Pt(16)
            p.font.bold = True
            p.font.color.rgb = config["accent_color"]
            p.font.name = config["body_font"]

            for point in key_points:
                p = tf.add_paragraph()
                p.text = f"• {point}"
                p.font.size = Pt(16)
                p.font.color.rgb = config["text_color"]
                p.font.name = config["body_font"]
                p.level = 1

    def generate_with_style(self, lesson_json: Dict[str, Any],
                           style: TemplateStyle) -> str:
        """Generate PPT with specific template style.

        Args:
            lesson_json: Lesson JSON dict
            style: Template style to use

        Returns:
            Path to generated PPT file
        """
        generator = PPTGenerator(style=style)
        return generator.generate(lesson_json)

    def generate_all_styles(self, lesson_json: Dict[str, Any]) -> Dict[TemplateStyle, str]:
        """Generate PPT in all available styles for comparison.

        Args:
            lesson_json: Lesson JSON dict

        Returns:
            Dict mapping each style to its generated file path
        """
        results = {}
        for style in TemplateStyle:
            try:
                path = self.generate_with_style(lesson_json, style)
                results[style] = path
            except Exception as e:
                results[style] = f"Error: {str(e)}"
        return results