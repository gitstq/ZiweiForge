# -*- coding: utf-8 -*-
"""
ZiweiForge / ziweiforge.cli
===========================

命令行入口：::

    python -m ziweiforge 1992-12-04 12:30 --gender male
    python -m ziweiforge 1992-12-04 12:30 --svg chart.svg
    python -m ziweiforge --lunar-date 1992-11-11 --hour 午 --gender male
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence

from .calendar import DI_ZHI
from .chart import Chart, Gender, build_chart, build_from_lunar
from .render.svg import render_svg
from .render.text import render_stars, render_text

__all__ = ["main", "chart_to_dict", "chart_to_json"]

#: 地支序号 → 中文时辰
_HOUR_ALIAS = {z: i for i, z in enumerate(DI_ZHI)}
_HOUR_ALIAS.update({"子": 0, "丑": 1, "寅": 2, "卯": 3, "辰": 4, "巳": 5,
                    "午": 6, "未": 7, "申": 8, "酉": 9, "戌": 10, "亥": 11})


def chart_to_dict(chart: Chart) -> dict:
    """把命盘序列化为可 JSON 化的字典。"""
    return {
        "solar": list(chart.solar),
        "hour_branch": DI_ZHI[chart.hour_branch],
        "gender": chart.gender,
        "lunar": {
            "year": chart.lunar.year,
            "month": chart.lunar.month,
            "day": chart.lunar.day,
            "is_leap": chart.lunar.is_leap,
            "ganzhi": chart.lunar.ganzhi,
            "label": chart.lunar.month_label,
        },
        "year_ganzhi": chart.year_ganzhi,
        "four_pillars": list(chart.four_pillars),
        "ju": chart.ju,
        "ju_name": chart.ju_name,
        "ming_branch": DI_ZHI[chart.ming_branch],
        "body_branch": DI_ZHI[chart.body_branch],
        "ming_zhu": chart.ming_zhu,
        "ziwei_branch": DI_ZHI[chart.ziwei_branch],
        "tianfu_branch": DI_ZHI[chart.tianfu_branch],
        "si_hua": {v: k for k, v in chart.si_hua.items()},
        "palaces": [
            {
                "index": p.index,
                "name": p.name,
                "branch": DI_ZHI[p.branch],
                "ganzhi": p.ganzhi,
                "is_body": p.is_body,
                "daxian": [p.daxian_start, p.daxian_end],
                "stars": [
                    {
                        "name": s.name,
                        "is_main": s.is_main,
                        "brightness": s.brightness,
                        "si_hua": s.si_hua,
                    }
                    for s in p.stars
                ],
            }
            for p in chart.palaces
        ],
    }


def chart_to_json(chart: Chart, indent: int = 2) -> str:
    """把命盘序列化为 JSON 字符串（``ensure_ascii=False``）。"""
    return json.dumps(chart_to_dict(chart), ensure_ascii=False, indent=indent)


def _parse_hour(value: str) -> int:
    v = value.strip()
    if v.isdigit():
        h = int(v)
        if not 0 <= h <= 23:
            raise argparse.ArgumentTypeError("小时须在 0–23 之间")
        return h
    if v.endswith("时"):
        v = v[:-1]
    if v not in _HOUR_ALIAS:
        raise argparse.ArgumentTypeError("无法识别的时辰：%s" % value)
    return _HOUR_ALIAS[v] * 2


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ziweiforge",
        description="ZiweiForge —— 零依赖、真天文历算的紫微斗数排盘引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python -m ziweiforge 1992-12-04 12:30\n"
            "  python -m ziweiforge 1992-12-04 午时 --gender female --svg chart.svg\n"
            "  python -m ziweiforge --lunar 1992-11-11 --hour 午 --json\n"
        ),
    )
    p.add_argument("date", nargs="?", help="公历生日，格式 YYYY-MM-DD")
    p.add_argument("time", nargs="?", default="12:00",
                   help="出生时刻 HH:MM 或时辰（如 午 / 午时），默认 12:00")
    p.add_argument("--lunar", dest="lunar", metavar="YYYY-M-D",
                   help="改用农历生日排盘（需同时给 --hour）")
    p.add_argument("--leap", action="store_true", help="--lunar 给出的月份为闰月")
    p.add_argument("--hour", dest="hour_opt", help="时辰（配合 --lunar 使用）")
    p.add_argument("--gender", choices=["male", "female", "m", "f"], default="male",
                   help="性别，仅影响大限顺逆，默认 male")
    p.add_argument("--tz", type=float, default=8.0,
                   help="输入时间的时区偏移小时数，默认 8（中国标准时间）")
    p.add_argument("--width", type=int, default=20, help="文本版式单格宽度，默认 20")
    p.add_argument("--color", action="store_true", help="文本输出启用 ANSI 颜色")
    p.add_argument("--svg", metavar="PATH", help="额外导出 SVG 到指定路径")
    p.add_argument("--json", action="store_true", dest="as_json", help="以 JSON 输出")
    p.add_argument("--stars", action="store_true", help="输出宫位→星曜一览表")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行入口，返回进程退出码。"""
    args = _build_parser().parse_args(argv)
    gender = Gender.MALE if args.gender in ("male", "m") else Gender.FEMALE

    try:
        if args.lunar:
            if not args.hour_opt:
                print("错误：使用 --lunar 时必须提供 --hour", file=sys.stderr)
                return 2
            y, m, d = (int(x) for x in args.lunar.split("-"))
            hb = _parse_hour(args.hour_opt) // 2 % 12
            chart = build_from_lunar(y, m, d, hb, args.leap, gender)
        else:
            if not args.date:
                print("错误：缺少公历生日，或用 --lunar 指定农历生日", file=sys.stderr)
                return 2
            y, m, d = (int(x) for x in args.date.split("-"))
            if ":" in args.time:
                hh, mm = (int(x) for x in args.time.split(":"))
            else:
                hh, mm = _parse_hour(args.time), 30
            chart = build_chart(y, m, d, hh, mm, gender, tz=args.tz)
    except (ValueError, KeyError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2

    if args.as_json:
        print(chart_to_json(chart))
    elif args.stars:
        print(render_stars(chart))
    else:
        print(render_text(chart, width=args.width, color=args.color))

    if args.svg:
        with open(args.svg, "w", encoding="utf-8") as fh:
            fh.write(render_svg(chart))
        print("\nSVG 已导出：%s" % args.svg, file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
