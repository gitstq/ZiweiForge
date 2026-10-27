# -*- coding: utf-8 -*-
"""
ZiweiForge
==========

**零依赖、真天文历算的紫微斗数排盘引擎。**

与主流实现的根本差异：ZiweiForge 不内置任何压缩的万年历查表数据，
农历月份、二十四节气、朔望时刻全部由自研天文内核**实时求解**——

* 太阳视黄经采用 **VSOP87D** 行星理论（636 项周期项，IMCCE 公开天文常数）；
* 月亮视黄经采用 Meeus《Astronomical Algorithms》第 47 章 Table 47.A；
* 节气与真朔由牛顿迭代反解，并计入 ΔT（TT−UT）、章动与光行差；
* 农历编排以**真朔**定月、以**冬至**锚定十一月、以**无中气**置闰，
  月序与中气归属一律按中国标准时间（UTC+8）的日历日口径判定。

因此本库可在 1900–2100 区间内独立复原农历与节气，不依赖外部数据文件。

快速开始
--------
::

    from ziweiforge import build_chart, render_text

    chart = build_chart(1992, 12, 4, 12, 30, gender="male")
    print(chart.ming_palace.main_stars[0].label)   # 紫微(庙)权
    print(render_text(chart))

命令行::

    python -m ziweiforge 1992-12-04 12:30 --gender male

.. note::
   本库为历算与传统文化研究工具，所述命理内容仅作文化研究参考，
   不构成任何决策建议。
"""

from __future__ import annotations

from . import astro, calendar, chart, render
from .calendar import DI_ZHI, TIAN_GAN, LunarDate, from_solar, to_solar
from .chart import (
    Chart,
    Gender,
    Palace,
    StarPlacement,
    build_chart,
    build_from_lunar,
    ziwei_position,
)
from .render.svg import render_svg
from .render.text import render_stars, render_text
from .version import __version__

__all__ = [
    "__version__",
    "astro", "calendar", "chart", "render",
    "DI_ZHI", "TIAN_GAN", "LunarDate", "from_solar", "to_solar",
    "Chart", "Gender", "Palace", "StarPlacement",
    "build_chart", "build_from_lunar", "ziwei_position",
    "render_text", "render_svg", "render_stars",
]
