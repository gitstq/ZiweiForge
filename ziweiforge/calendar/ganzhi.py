# -*- coding: utf-8 -*-
"""
ZiweiForge / ziweiforge.calendar.ganzhi
=======================================

天干、地支、六十甲子、纳音五行与「五虎遁 / 五鼠遁」推算。

紫微斗数只用得到其中的一部分：

* 生年干支 → 定禄存、擎羊、陀罗、天魁、天钺、四化；
* 命宫干支 → 定纳音五行局（水二 / 木三 / 金四 / 土五 / 火六局）；
* 五虎遁 → 定十二宫天干（寅宫为遁首，顺时针排布）。
"""

from __future__ import annotations

from typing import Tuple

__all__ = [
    "TIAN_GAN", "DI_ZHI", "NA_YIN", "WU_XING_JU",
    "ganzhi_name", "ganzhi_index", "year_ganzhi", "day_ganzhi",
    "hour_branch_index", "hour_ganzhi", "wu_hu_dun_yin", "wu_shu_dun_zi",
    "na_yin", "wu_xing_ju",
]

#: 十天干
TIAN_GAN: Tuple[str, ...] = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")

#: 十二地支（下标即斗数中使用的地支序号：子=0 … 亥=11）
DI_ZHI: Tuple[str, ...] = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")

#: 六十甲子纳音（每两个干支共用一个纳音，按六十甲子顺序排列 30 组）
NA_YIN: Tuple[str, ...] = (
    "海中金", "炉中火", "大林木", "路旁土", "剑锋金",
    "山头火", "涧下水", "城头土", "白蜡金", "杨柳木",
    "泉中水", "屋上土", "霹雳火", "松柏木", "长流水",
    "沙中金", "山下火", "平地木", "壁上土", "金箔金",
    "覆灯火", "天河水", "大驿土", "钗钏金", "桑柘木",
    "大溪水", "沙中土", "天上火", "石榴木", "大海水",
)

#: 纳音五行 → 五行局数（水二局、木三局、金四局、土五局、火六局）
WU_XING_JU = {"水": 2, "木": 3, "金": 4, "土": 5, "火": 6}

# 五行局的中文名
_JU_NAMES = {2: "水二局", 3: "木三局", 4: "金四局", 5: "土五局", 6: "火六局"}


def ganzhi_index(gan: int, zhi: int) -> int:
    """由天干、地支序号（均自 0 起）求六十甲子序号；组合非法时返回 -1。"""
    if (gan - zhi) % 2 != 0:
        return -1
    for i in range(6):
        idx = gan + 10 * i
        if idx % 12 == zhi:
            return idx % 60
    return -1


def ganzhi_name(index: int) -> str:
    """六十甲子序号 → 「甲子」形式的名称。"""
    index %= 60
    return TIAN_GAN[index % 10] + DI_ZHI[index % 12]


def year_ganzhi(lunar_year: int) -> Tuple[int, int]:
    """农历年 → ``(天干序号, 地支序号)``。以农历正月初一为换年节点。"""
    return (lunar_year - 4) % 10, (lunar_year - 4) % 12


def day_ganzhi(julian_day_number: int) -> Tuple[int, int]:
    """儒略日数 → 日干支 ``(天干序号, 地支序号)``。

    以 1900-01-01（JDN 2415021）为甲戌日作为锚点。
    """
    idx = (int(julian_day_number) + 49) % 60
    return idx % 10, idx % 12


def hour_branch_index(hour: int, minute: int = 0) -> int:
    """本地时间 → 时辰序号（子=0 … 亥=11）。

    子时覆盖 23:00–00:59，即 23 点整起算。
    """
    return ((hour + 1) // 2) % 12


def wu_hu_dun_yin(year_gan: int) -> int:
    """五虎遁：由年干求**寅**宫天干序号（甲己年起丙寅）。"""
    return ((year_gan % 5) * 2 + 2) % 10


def wu_shu_dun_zi(day_gan: int) -> int:
    """五鼠遁：由日干求**子**时天干序号（甲己日起甲子）。"""
    return ((day_gan % 5) * 2) % 10


def hour_ganzhi(day_gan: int, branch_index: int) -> int:
    """由日干与时辰序号求该时辰的天干序号。"""
    return (wu_shu_dun_zi(day_gan) + branch_index) % 10


def na_yin(gan: int, zhi: int) -> str:
    """干支 → 纳音五行名（如「城头土」）。"""
    idx = ganzhi_index(gan, zhi)
    if idx < 0:
        raise ValueError("非法的干支组合：%s%s" % (TIAN_GAN[gan], DI_ZHI[zhi]))
    return NA_YIN[(idx % 60) // 2]


def wu_xing_ju(gan: int, zhi: int) -> int:
    """干支 → 五行局数（2/3/4/5/6），取纳音五行的尾字。"""
    return WU_XING_JU[na_yin(gan, zhi)[-1]]


def ju_name(ju: int) -> str:
    """五行局数 → 中文名，如 ``6 → 火六局``。"""
    return _JU_NAMES.get(ju, "未知局")
