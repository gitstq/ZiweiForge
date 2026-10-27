# -*- coding: utf-8 -*-
"""
ZiweiForge / ziweiforge.render.svg
==================================

把命盘渲染为一张可直接嵌入网页 / 打印的 SVG 图。

依赖为零：仅用标准库拼装 SVG 文本，不引入任何绘图库。
"""

from __future__ import annotations

from typing import List, Sequence
from xml.sax.saxutils import escape

from ..calendar import DI_ZHI
from ..chart import Chart

__all__ = ["render_svg"]

_GRID: Sequence[Sequence[int]] = (
    (5, 6, 7, 8),
    (4, None, None, 9),
    (3, None, None, 10),
    (2, 1, 0, 11),
)

_FONT = "'Noto Sans CJK SC','Source Han Sans SC','Microsoft YaHei','PingFang SC'," \
        "'Hiragino Sans GB','WenQuanYi Micro Hei',sans-serif"


def _esc(text: str) -> str:
    return escape(text)


def render_svg(chart: Chart, cell: int = 170, pad: int = 16) -> str:
    """把命盘渲染为 SVG 字符串。

    :param chart: :class:`~ziweiforge.chart.Chart`
    :param cell: 单格边长（像素）
    :param pad: 画布外边距
    """
    size = cell * 4
    w = h = size + pad * 2
    out: List[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" font-family="%s">' % (w, h, w, h, _FONT),
        '<rect width="%d" height="%d" fill="#fdfaf3"/>' % (w, h),
        '<g transform="translate(%d,%d)">' % (pad, pad),
    ]

    def rect(x: int, y: int, cw: int, ch: int, fill: str = "#ffffff") -> str:
        return (
            '<rect x="%d" y="%d" width="%d" height="%d" fill="%s" '
            'stroke="#8a7a5c" stroke-width="1.2"/>' % (x, y, cw, ch, fill)
        )

    def text(x: int, y: int, s: str, size_: int = 13, fill: str = "#222",
             anchor: str = "start", weight: str = "normal") -> str:
        return (
            '<text x="%d" y="%d" font-size="%d" fill="%s" text-anchor="%s" '
            'font-weight="%s">%s</text>' % (x, y, size_, fill, anchor, weight, _esc(s))
        )

    for r in range(4):
        for col in range(4):
            b = _GRID[r][col]
            if b is None:
                continue
            x, y = col * cell, r * cell
            p = chart.by_branch(b)
            fill = "#fff8e6" if p.index == 0 else ("#f6f0ff" if p.is_body else "#ffffff")
            out.append(rect(x, y, cell, cell, fill))
            # 宫名（左上）
            name = p.name + ("·身" if p.is_body else "")
            nfill = "#b8860b" if p.index == 0 else ("#7b3fa0" if p.is_body else "#333")
            out.append(text(x + 9, y + 20, name, 14, nfill, "start", "bold"))
            # 地支 + 干支（右上）
            out.append(
                text(x + cell - 9, y + 20, "%s宫 %s" % (DI_ZHI[p.branch], p.ganzhi),
                     12, "#8a7a5c", "end")
            )
            # 大限（右下角）
            if p.daxian_start is not None:
                out.append(
                    text(x + cell - 9, y + cell - 8,
                         "%d–%d岁" % (p.daxian_start, p.daxian_end), 11, "#9a8f7a", "end")
                )
            # 星曜
            ty = y + 40
            for s in p.main_stars:
                label = s.name + ("(%s)" % s.brightness if s.brightness else "")
                out.append(text(x + 9, ty, label, 13, "#c0392b", "start", "bold"))
                if s.si_hua:
                    out.append(text(x + cell - 9, ty, s.si_hua, 12, "#1e7a4c", "end", "bold"))
                ty += 19
            if not p.main_stars:
                out.append(text(x + 9, ty, "（无主星）", 12, "#aaaaaa"))
                ty += 19
            line = " ".join(s.name + (s.si_hua or "") for s in p.minor_stars)
            for seg in _chunk(line, 15):
                if ty > y + cell - 14:
                    break
                out.append(text(x + 9, ty, seg, 11.5, "#3a5a7a"))
                ty += 16

    # 中央信息区
    cx, cy = cell, cell
    out.append(rect(cx, cy, cell * 2, cell * 2, "#fffdf7"))
    info = [
        ("%s　%s" % ("男命" if chart.gender == "male" else "女命", chart.ju_name), 15, "#b8860b"),
        ("公历 %04d-%02d-%02d %s" % (*chart.solar, chart.hour_name), 13, "#333"),
        ("农历 %s年 %s%s"
         % (chart.lunar.ganzhi, chart.lunar.month_label, _day_cn(chart.lunar.day)), 13, "#333"),
        ("四柱 " + "  ".join(chart.four_pillars), 13, "#333"),
        ("命宫 %s宫　身宫 %s宫" % (DI_ZHI[chart.ming_branch], DI_ZHI[chart.body_branch]), 13, "#333"),
        ("命主 %s　紫微 %s宫　天府 %s宫"
         % (chart.ming_zhu, DI_ZHI[chart.ziwei_branch], DI_ZHI[chart.tianfu_branch]), 13, "#333"),
        ("四化 " + " ".join("%s%s" % (v, k) for k, v in chart.si_hua.items()), 12.5, "#1e7a4c"),
    ]
    ty = cy + 34
    for s, fs, color in info:
        out.append(text(cx + 18, ty, s, fs, color))
        ty += 24

    out.append("</g></svg>")
    return "\n".join(out)


def _chunk(s: str, n: int) -> List[str]:
    """按字符数切分（中文等宽，足够用于换行）。"""
    return [s[i:i + n] for i in range(0, len(s), n)] or [""]


def _day_cn(day: int) -> str:
    if day in (10, 20, 30):
        return {10: "初十", 20: "二十", 30: "三十"}[day]
    head = ("初", "十", "廿", "三")[day // 10]
    return head + "十" if day % 10 == 0 else head + "一二三四五六七八九"[day % 10 - 1]
