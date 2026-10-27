# -*- coding: utf-8 -*-
"""ZiweiForge 渲染子包：把命盘输出为纯文本、SVG 与 JSON。"""

from .svg import render_svg
from .text import render_text

__all__ = ["render_text", "render_svg"]
