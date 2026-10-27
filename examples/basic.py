# -*- coding: utf-8 -*-
"""
最简示例：排一张命盘并打印。

运行::

    python examples/basic.py
"""

from ziweiforge import build_chart, render_stars, render_text
from ziweiforge.calendar import DI_ZHI


def main() -> None:
    # 阳历 1992-12-04 12:30 出生（男命），时区默认中国标准时间 UTC+8
    chart = build_chart(1992, 12, 4, 12, 30, gender="male")

    print("农历生日：", chart.lunar)
    print("生年干支：", chart.year_ganzhi)
    print("四柱：", "  ".join(chart.four_pillars))
    print("五行局：", chart.ju_name)
    print("命宫：%s宫　身宫：%s宫" % (DI_ZHI[chart.ming_branch], DI_ZHI[chart.body_branch]))
    print("紫微在%s宫，天府在%s宫" % (DI_ZHI[chart.ziwei_branch], DI_ZHI[chart.tianfu_branch]))
    print("命主：", chart.ming_zhu)
    print("生年四化：", chart.si_hua)
    print()
    print(render_text(chart))
    print()
    print(render_stars(chart))


if __name__ == "__main__":
    main()
