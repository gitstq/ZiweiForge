# -*- coding: utf-8 -*-
"""
批量导出 SVG 命盘。

运行::

    python examples/export_svg.py

生成的 SVG 不依赖任何外部字体或库，可直接用浏览器打开、嵌入网页或打印。
"""

import os

import os
import sys

# 允许直接以 `python examples/xxx.py` 运行：把项目根目录加入模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ziweiforge import build_chart
from ziweiforge.render.svg import render_svg

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

SAMPLES = [
    (1949, 10, 1, 15, 0, "male"),
    (1970, 10, 1, 10, 10, "female"),
    (1992, 12, 4, 12, 30, "male"),
    (2025, 2, 3, 22, 10, "female"),
]


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    for year, month, day, hour, minute, gender in SAMPLES:
        chart = build_chart(year, month, day, hour, minute, gender)
        name = "chart-%04d%02d%02d-%02d%02d-%s.svg" % (
            year, month, day, hour, minute, gender,
        )
        path = os.path.join(OUT_DIR, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render_svg(chart))
        print("已导出：", path)


if __name__ == "__main__":
    main()
