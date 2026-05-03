"""PPT template styles for educational content."""
from enum import Enum
from typing import Dict, Any
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR


class TemplateStyle(str, Enum):
    """Educational PPT template styles."""

    classic = "classic"       # 经典学术风格 - 蓝色系，正式
    creative = "creative"     # 创意活泼风格 - 绿色系，生动
    minimal = "minimal"       # 简约现代风格 - 黑白灰，简洁


class TemplateConfig:
    """Configuration for each template style."""

    STYLES: Dict[TemplateStyle, Dict[str, Any]] = {
        TemplateStyle.classic: {
            "name": "经典学术风格",
            "primary_color": RGBColor(0, 51, 102),      # 深蓝
            "secondary_color": RGBColor(0, 102, 204),   # 中蓝
            "accent_color": RGBColor(255, 153, 0),      # 金色强调
            "background": RGBColor(255, 255, 255),      # 白色背景
            "text_color": RGBColor(51, 51, 51),         # 深灰文字
            "title_font": "Microsoft YaHei",
            "body_font": "Microsoft YaHei",
            "title_size": Pt(36),
            "subtitle_size": Pt(24),
            "body_size": Pt(18),
        },
        TemplateStyle.creative: {
            "name": "创意活泼风格",
            "primary_color": RGBColor(0, 153, 76),      # 翠绿
            "secondary_color": RGBColor(102, 178, 102), # 浅绿
            "accent_color": RGBColor(255, 102, 102),    # 红色强调
            "background": RGBColor(245, 255, 245),      # 浅绿背景
            "text_color": RGBColor(51, 51, 51),
            "title_font": "Microsoft YaHei",
            "body_font": "Microsoft YaHei",
            "title_size": Pt(40),
            "subtitle_size": Pt(28),
            "body_size": Pt(20),
        },
        TemplateStyle.minimal: {
            "name": "简约现代风格",
            "primary_color": RGBColor(51, 51, 51),      # 深灰
            "secondary_color": RGBColor(128, 128, 128), # 中灰
            "accent_color": RGBColor(0, 0, 0),          # 黑色强调
            "background": RGBColor(255, 255, 255),      # 白色背景
            "text_color": RGBColor(51, 51, 51),
            "title_font": "Microsoft YaHei Light",
            "body_font": "Microsoft YaHei Light",
            "title_size": Pt(44),
            "subtitle_size": Pt(26),
            "body_size": Pt(18),
        },
    }

    @classmethod
    def get_style(cls, style: TemplateStyle) -> Dict[str, Any]:
        """Get configuration for a specific style."""
        return cls.STYLES.get(style, cls.STYLES[TemplateStyle.classic])

    @classmethod
    def get_default_style(cls) -> TemplateStyle:
        """Get default template style."""
        return TemplateStyle.classic


# Subject-to-style mapping recommendations
SUBJECT_STYLE_MAP: Dict[str, TemplateStyle] = {
    "physics": TemplateStyle.classic,
    "chemistry": TemplateStyle.classic,
    "mathematics": TemplateStyle.minimal,
    "chinese": TemplateStyle.creative,
    "history": TemplateStyle.classic,
    "geography": TemplateStyle.creative,
    "biology": TemplateStyle.creative,
    "english": TemplateStyle.minimal,
}


def get_recommended_style(subject: str) -> TemplateStyle:
    """Get recommended template style for a subject."""
    return SUBJECT_STYLE_MAP.get(subject.lower(), TemplateStyle.classic)