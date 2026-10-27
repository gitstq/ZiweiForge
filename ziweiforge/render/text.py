# -*- coding: utf-8 -*-
"""
ZiweiForge / ziweiforge.render.text
===================================

把命盘渲染为终端可读的「四方格」纯文本版式。

版式遵循传统斗数命盘的排布：地支自 **巳宫** 起顺时针环绕外圈，中央区域书写
命盘基本信息。输出宽度自适应，中文按双宽字符对齐。
"""

from __future__ import annotations

import unicodedata
from typing import List, Sequence

from ..calendar import DI_ZHI
from ..chart import Chart, Palace

__all__ = ["render_text", "render_stars", "day_cn"]

# 外圈 12 宫在 4×4 网格中的位置：(行, 列) → 地支序号
_GRID: Sequence[Sequence[int]] = (
    (5, 6, 7, 8),
    (4, None, None, 9),
    (3, None, None, 10),
    (2, 1, 0, 11),
)

#: 默认单格宽度（显示列数）
_BOX_W = 22

_ANSI = {
    "reset": "\033[0m",
    "ming": "\033[1;33m",     # 命宫：亮黄
    "body": "\033[1;35m",     # 身宫：亮紫
    "main": "\033[1;31m",     # 主星：亮红
    "minor": "\033[0;36m",    # 辅曜：青
    "hua": "\033[1;32m",      # 四化：亮绿
    "head": "\033[1m",
}
_NOCOLOR = dict.fromkeys(_ANSI, "")


def _width(s: str) -> int:
    """字符串的显示宽度（东亚宽/全角字符计 2）。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def _fit(s: str, width: int, mode: str = "left") -> str:
    """把字符串按显示宽度填充到 ``width`` 列。"""
    gap = max(0, width - _width(s))
    if mode == "center":
        left = gap // 2
        return " " * left + s + " " * (gap - left)
    return s + " " * gap


def _wrap_tokens(tokens: Sequence[str], width: int, indent: str = " ") -> List[str]:
    """按词条折行，保证不把一个词拆断。"""
    lines: List[str] = []
    cur = ""
    for t in tokens:
        cand = (cur + " " + t) if cur else t
        if _width(indent + cand) > width and cur:
            lines.append(indent + cur)
            cur = t
        else:
            cur = cand
    if cur:
        lines.append(indent + cur)
    return lines


def _cell_lines(palace: Palace, width: int, c: dict) -> List[str]:
    """生成单个宫位的内部文字行（不含左右边框）。"""
    inner = width - 2
    head = palace.name + ("·身" if palace.is_body else "")
    if palace.index == 0:
        head = c["ming"] + head + c["reset"]
    elif palace.is_body:
        head = c["body"] + head + c["reset"]

    lines = [
        _fit(head, inner, "center"),
        _fit("%s宫 %s" % (DI_ZHI[palace.branch], palace.ganzhi), inner, "center"),
        "─" * inner,
    ]
    body: List[str] = []
    for s in palace.main_stars:
        label = s.name + ("(%s)" % s.brightness if s.brightness else "")
        line = c["main"] + label + c["reset"]
        if s.si_hua:
            line += c["hua"] + s.si_hua[1:] + c["reset"]
        if s.self_hua:
            line += "〔%s〕" % s.self_hua
        body.append(line)
    if not palace.main_stars:
        body.append("（无主星）")
    if palace.minor_stars:
        toks = [s.name + (s.si_hua[1:] if s.si_hua else "") for s in palace.minor_stars]
        body += [c["minor"] + seg + c["reset"] for seg in _wrap_tokens(toks, inner)]
    lines += body
    if palace.daxian_start is not None:
        lines.append("─" * inner)
        lines.append(_fit("%d–%d岁" % (palace.daxian_start, palace.daxian_end), inner, "center"))
    return lines


def _info_lines(chart: Chart, width: int, c: dict) -> List[str]:
    sihua = " ".join(
        "%s%s" % (k, v[1:]) for k, v in chart.si_hua.items()
    )
    rows = [
        "%s　%s" % ("男命" if chart.gender == "male" else "女命", chart.ju_name),
        "公历 %04d-%02d-%02d %s" % (*chart.solar, chart.hour_name),
        "农历 %s年 %s%s %s"
        % (chart.lunar.ganzhi, chart.lunar.month_label, day_cn(chart.lunar.day), chart.hour_name),
        "四柱 " + " ".join(chart.four_pillars),
        "命宫 %s宫　身宫 %s宫" % (DI_ZHI[chart.ming_branch], DI_ZHI[chart.body_branch]),
        "命主 %s　紫微 %s宫　天府 %s宫"
        % (chart.ming_zhu, DI_ZHI[chart.ziwei_branch], DI_ZHI[chart.tianfu_branch]),
        "四化 " + sihua,
    ]
    lines: List[str] = []
    for r in rows:
        lines.append(_fit(c["head"] + r + c["reset"], width - 4))
    return lines


def day_cn(day: int) -> str:
    """农历日 → 中文（初一、十五、廿三……）。"""
    if day in (10, 20, 30):
        return {10: "初十", 20: "二十", 30: "三十"}[day]
    head = ("初", "十", "廿", "三")[day // 10]
    return head + "十" if day % 10 == 0 else head + "一二三四五六七八九"[day % 10 - 1]


def render_text(chart: Chart, width: int = _BOX_W, color: bool = False) -> str:
    """把命盘渲染为四方格纯文本。

    :param chart: :class:`~ziweiforge.chart.Chart`
    :param width: 单格宽度（显示列数），默认 22
    :param color: 是否输出 ANSI 颜色转义序列
    """
    width = max(width, 20)
    c = _ANSI if color else _NOCOLOR
    inner = width - 2
    mid = width * 2 - 2          # 中央信息区内部宽度
    total = width * 4 - 2

    cells = {}
    for r in range(4):
        for col in range(4):
            b = _GRID[r][col]
            if b is not None:
                cells[(r, col)] = _cell_lines(chart.by_branch(b), width, c)

    info = _info_lines(chart, mid + 2, c)
    half = (len(info) + 1) // 2
    depth_outer = max(max(len(cells[(r, col)]) for col in range(4)) for r in (0, 3))
    depth_mid = max(
        max(len(cells[(r, col)]) for r in (1, 2) for col in (0, 3)),
        half,
    )

    def at(cell: List[str], i: int) -> str:
        return _fit(cell[i], inner) if i < len(cell) else " " * inner

    def row_outer(r: int) -> List[str]:
        return ["│" + "│".join(at(cells[(r, col)], i) for col in range(4)) + "│"
                for i in range(depth_outer)]

    def row_mid(r: int, part: List[str]) -> List[str]:
        out = []
        for i in range(depth_mid):
            info_i = _fit(part[i], mid) if i < len(part) else " " * mid
            out.append("│" + at(cells[(r, 0)], i) + "│" + info_i + "│" + at(cells[(r, 3)], i) + "│")
        return out

    out = ["┌" + "─" * total + "┐"]
    out += row_outer(0)
    out.append("├" + "─" * inner + "┬" + "─" * mid + "┬" + "─" * inner + "┤")
    out += row_mid(1, info[:half])
    out.append("├" + "─" * inner + "│" + " " * mid + "│" + "─" * inner + "┤")
    out += row_mid(2, info[half:])
    out.append("├" + "─" * inner + "┴" + "─" * mid + "┴" + "─" * inner + "┤")
    out += row_outer(3)
    out.append("└" + "─" * total + "┘")
    return "\n".join(out)


def render_stars(chart: Chart) -> str:
    """输出「宫位 → 星曜」一览表，便于肉眼核对与程序化校验。"""
    return "\n".join(
        "%-4s %s宫 %s  %s"
        % (p.name, DI_ZHI[p.branch], p.ganzhi, " ".join(s.label for s in p.stars))
        for p in chart.palaces
    )
