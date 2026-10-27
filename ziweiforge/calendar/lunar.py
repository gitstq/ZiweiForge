# -*- coding: utf-8 -*-
"""
ZiweiForge / ziweiforge.calendar.lunar
======================================

农历（夏历）编排与公历 ↔ 农历互转。

编排规则
--------
1. 以**真朔**所在的那一个日历日为每月初一（朔望月长 29 或 30 天）；
2. 以**冬至**锚定月序：冬至所在的朔望月为十一月（冬月）；
3. 上一年冬至所在月往后第 2 个朔望月为当年正月；
4. 若当年出现 13 个朔望月，则其中第一个「无中气」的月份置为闰月。

实现要点
--------
农历的月序与中气归属一律以**日历日**（中国标准时间 UTC+8 的日界）比较，
而不是比较精确时刻——这是农历的传统定义方式，也是各权威历书采用的口径。
例如 2020 年夏至（6-21 05:44）与五月初一的朔（6-21 14:41）同处一日，
按日历日口径夏至归属五月，故闰四月无中气；若按精确时刻比较则会得出错误结果。

由于朔与节气均由自研天文内核真实求解，本模块在 1900–2100 区间内可独立
复原农历，无需内置任何压缩数据表。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Tuple

from ..astro.core import (
    gregorian_from_julian,
    julian_day,
    solar_term,
    tt_to_ut,
    true_new_moon,
    ut_to_tt,
)
from .ganzhi import DI_ZHI, TIAN_GAN, year_ganzhi

__all__ = [
    "LunarDate", "LunarMonth", "lunar_year_months", "from_solar",
    "to_solar", "lunar_new_year", "hour_branch_index", "solar_term_of_day",
]

#: 农历编排所依据的时区（中国标准时间 UTC+8）
LUNAR_TZ = 8.0

#: 中气在二十四节气中的序号（雨水、春分、……、大寒）
_MAJOR_TERMS = (1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23)

#: 冬至在二十四节气中的序号
_WINTER_SOLSTICE = 21

_MONTH_NAMES = ("正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊")


@lru_cache(maxsize=8192)
def _cached_solar_term(year: int, index: int) -> float:
    return solar_term(year, index)


@lru_cache(maxsize=8192)
def _cached_new_moon(k: int) -> float:
    return true_new_moon(float(k))


def _day_index(jd_tt: float) -> int:
    """地球时儒略日 → 中国标准时间的「日历日序号」。

    儒略日的日界在 UT 12:00，故 ``floor(jd_ut + 8/24 + 0.5)`` 即北京时间的日期序号。
    """
    return int(math.floor(tt_to_ut(jd_tt) + LUNAR_TZ / 24.0 + 0.5))


def _k_of(jd_tt: float) -> int:
    """估算 ``jd_tt`` 所属朔望月的序号。"""
    return int(round((jd_tt - 2451550.09766) / 29.530588853))


def _k_of_new_moon_before(jd_tt: float) -> int:
    """按日历日口径，返回 ``jd_tt`` 所在朔望月的序号。"""
    day = _day_index(jd_tt)
    k = _k_of(jd_tt)
    while _day_index(_cached_new_moon(k)) > day:
        k -= 1
    while _day_index(_cached_new_moon(k + 1)) <= day:
        k += 1
    return k


@dataclass(frozen=True)
class LunarMonth:
    """农历年中的一个月。

    :param number: 月序号 1–12；闰月时表示「闰几月」
    :param is_leap: 是否为闰月
    :param new_moon_jd: 该月初一（朔）时刻，地球时儒略日
    :param index: 在当年月份表中的位置（0 起）
    """

    number: int
    is_leap: bool
    new_moon_jd: float
    index: int

    @property
    def label(self) -> str:
        return ("闰" if self.is_leap else "") + _MONTH_NAMES[self.number - 1]


def _has_major_term(start: float, end: float, year_hint: int) -> bool:
    """按日历日口径判断 ``[start, end)`` 这一农历月内是否含有中气。"""
    d0 = _day_index(start)
    d1 = _day_index(end)
    for y in range(year_hint - 1, year_hint + 2):
        for idx in _MAJOR_TERMS:
            t = _cached_solar_term(y, idx)
            if d0 <= _day_index(t) < d1:
                return True
    return False


def _november_holds_winter_solstice(
    moons: list, leap_index: int, count: int, winter_solstice_jd: float
) -> bool:
    """校验置闰于 ``leap_index`` 后，冬至是否仍落在十一月（冬月）内。

    置闰位置为 ``i`` 时，index 0..i-1 依次为正月……第 i 月，index i 为闰月，
    因此「十一月」落在 index 10（i ≥ 11，即闰十一月）或 index 11（i < 11）。
    """
    nov_idx = 10 if leap_index >= 11 else 11
    if nov_idx < 0 or nov_idx + 1 > count:
        return False
    d = _day_index(winter_solstice_jd)
    return _day_index(moons[nov_idx]) <= d < _day_index(moons[nov_idx + 1])


@lru_cache(maxsize=1024)
def lunar_year_months(lunar_year: int) -> Tuple[LunarMonth, ...]:
    """构建农历 ``lunar_year`` 年的月份表（含闰月）。

    返回的元组按时间顺序排列，长度为 12（平年）或 13（闰年）。
    """
    prev_ws = _cached_solar_term(lunar_year - 1, _WINTER_SOLSTICE)
    this_ws = _cached_solar_term(lunar_year, _WINTER_SOLSTICE)
    next_ws = _cached_solar_term(lunar_year + 1, _WINTER_SOLSTICE)

    k_prev_nov = _k_of_new_moon_before(prev_ws)   # 前一年十一月
    k_this_nov = _k_of_new_moon_before(this_ws)   # 当年十一月
    k_next_nov = _k_of_new_moon_before(next_ws)   # 次年十一月

    def _no_major_term(k: int) -> bool:
        return not _has_major_term(
            _cached_new_moon(k), _cached_new_moon(k + 1), lunar_year
        )

    # 当年正月 = 前一年十一月往后第 2 个朔望月；若前一年存在「闰十一月」则再后移一位
    k_first = k_prev_nov + 2
    if (k_this_nov - k_prev_nov) == 13 and _no_major_term(k_prev_nov + 1):
        k_first += 1
    # 来年正月同理
    k_next_first = k_this_nov + 2
    if (k_next_nov - k_this_nov) == 13 and _no_major_term(k_this_nov + 1):
        k_next_first += 1

    count = k_next_first - k_first
    if count not in (12, 13):  # pragma: no cover - 防御性兜底
        count = 13 if (k_this_nov - k_prev_nov) == 13 else 12

    moons = [_cached_new_moon(k_first + i) for i in range(count + 1)]

    leap_index = -1
    if count == 13:
        for i in range(count):
            if _has_major_term(moons[i], moons[i + 1], lunar_year):
                continue
            # 置闰后仍需保证「冬至落在十一月」——农历编算的硬性前置条件。
            # 2033 年即典型反例：第一个无中气月若置闰会使冬至移出十一月，
            # 依 GB/T 33661-2017 须顺延到下一个无中气月（闰十一月）。
            leap_index = i
            if _november_holds_winter_solstice(moons, i, count, this_ws):
                break
            leap_index = -1

    months = []
    number = 1
    for i in range(count):
        if i == leap_index:
            months.append(LunarMonth(max(number - 1, 1), True, moons[i], i))
            continue
        months.append(LunarMonth(number, False, moons[i], i))
        number += 1
    return tuple(months)


def lunar_new_year(lunar_year: int) -> float:
    """农历 ``lunar_year`` 年正月初一的朔时刻（TT 儒略日）。"""
    return lunar_year_months(lunar_year)[0].new_moon_jd


@dataclass(frozen=True)
class LunarDate:
    """一个农历日期。"""

    year: int
    month: int
    day: int
    is_leap: bool = False
    #: 该日期所在月的朔时刻（TT 儒略日）
    month_start_jd: float = 0.0

    @property
    def month_label(self) -> str:
        return ("闰" if self.is_leap else "") + _MONTH_NAMES[self.month - 1] + "月"

    @property
    def ganzhi(self) -> str:
        gan, zhi = year_ganzhi(self.year)
        return TIAN_GAN[gan] + DI_ZHI[zhi]

    def __str__(self) -> str:  # pragma: no cover
        return "农历%s年%s%s" % (self.ganzhi, self.month_label, _day_name(self.day))


def _day_name(day: int) -> str:
    if day == 10:
        return "初十"
    if day == 20:
        return "二十"
    if day == 30:
        return "三十"
    head = ("初", "十", "廿", "三")[day // 10]
    if day % 10 == 0:
        return head + "十"
    return head + ("", "一", "二", "三", "四", "五", "六", "七", "八", "九")[day % 10]


def from_solar(
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    tz: float = LUNAR_TZ,
) -> LunarDate:
    """公历（本地时间）→ 农历日期。

    :param tz: 输入时间所处的时区偏移小时数，默认 ``8``（中国标准时间）。
        农历的月界固定按中国标准时间判定，``tz`` 仅用于把输入时间换算到统一时标。
    """
    jd_ut = julian_day(year, month, day + (hour + minute / 60.0) / 24.0) - tz / 24.0
    return _from_jd(ut_to_tt(jd_ut))


def _from_jd(jd_tt: float) -> LunarDate:
    """由地球时儒略日定位农历日期。"""
    gy = gregorian_from_julian(tt_to_ut(jd_tt) + LUNAR_TZ / 24.0)[0]
    ly = gy
    target_day = _day_index(jd_tt)
    for _ in range(4):
        months = lunar_year_months(ly)
        first = months[0].new_moon_jd
        next_first = lunar_new_year(ly + 1)
        # 年界的判定同样以日历日为口径：朔发生日即正月初一
        if target_day < _day_index(first):
            ly -= 1
            continue
        if target_day >= _day_index(next_first):
            ly += 1
            continue
        for i, m in enumerate(months):
            end = (
                months[i + 1].new_moon_jd
                if i + 1 < len(months)
                else lunar_new_year(ly + 1)
            )
            if _day_index(m.new_moon_jd) <= target_day < _day_index(end):
                return LunarDate(
                    ly, m.number, target_day - _day_index(m.new_moon_jd) + 1,
                    m.is_leap, m.new_moon_jd,
                )
        break  # pragma: no cover
    raise ValueError("无法由儒略日定位农历日期")


def to_solar(date: LunarDate, tz: float = LUNAR_TZ) -> Tuple[int, int, int]:
    """农历日期 → 公历 ``(年, 月, 日)``（本地时间）。"""
    target = None
    for m in lunar_year_months(date.year):
        if m.number == date.month and m.is_leap == date.is_leap:
            target = m
            break
    if target is None:
        raise ValueError("该农历年不存在此月份：%s" % date.month_label)
    jd_ut = tt_to_ut(target.new_moon_jd) + (date.day - 1)
    y, m, d = gregorian_from_julian(jd_ut + tz / 24.0)
    return y, m, int(math.floor(d))


def solar_term_of_day(year: int, month: int, day: int) -> int:
    """返回公历某日（中国标准时间）所处的节气序号，0=立春 … 23=大寒。

    若当日恰为两个节气的交界，返回该日零点之后到来的那个节气。
    """
    jd_tt = ut_to_tt(julian_day(year, month, day + 0.5) - LUNAR_TZ / 24.0)
    day0 = _day_index(jd_tt)
    best = None
    for y in (year - 1, year, year + 1):
        for idx in range(24):
            t = _cached_solar_term(y, idx)
            if _day_index(t) <= day0 and (best is None or t > best[0]):
                best = (t, idx)
    if best is None:  # pragma: no cover
        raise ValueError("无法定位节气")
    return best[1]


def hour_branch_index(hour: int, minute: int = 0) -> int:
    """本地时间 → 时辰序号（子=0 … 亥=11），子时自 23:00 起算。"""
    return ((hour + 1) // 2) % 12
