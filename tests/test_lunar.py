# -*- coding: utf-8 -*-
"""
农历编排自测。

春节日期与闰月月份均以《中国天文年历》/ GB/T 33661-2017 公布的数据为基准，
由本库真天文内核独立反解，不依赖任何内置历表。
"""

from __future__ import annotations

import unittest

from ziweiforge.calendar import LunarDate, from_solar, lunar_year_months, to_solar

#: 权威公布的春节（农历正月初一）公历日期
SPRING_FESTIVALS = {
    2015: (2, 19), 2016: (2, 8), 2017: (1, 28), 2018: (2, 16),
    2019: (2, 5), 2020: (1, 25), 2021: (2, 12), 2022: (2, 1),
    2023: (1, 22), 2024: (2, 10), 2025: (1, 29), 2026: (2, 17),
    2027: (2, 6),
}

#: 权威公布的闰月（农历年 → 闰几月）
LEAP_MONTHS = {
    2006: 7, 2009: 5, 2012: 4, 2014: 9, 2017: 6,
    2020: 4, 2023: 2, 2025: 6, 2028: 5, 2033: 11,
}

#: 无闰月的年份
PLAIN_YEARS = (2015, 2016, 2018, 2019, 2021, 2022, 2024, 2026, 2027)


class TestSpringFestival(unittest.TestCase):
    def test_spring_festival_dates(self):
        for year, (m, d) in SPRING_FESTIVALS.items():
            got = to_solar(LunarDate(year, 1, 1))
            self.assertEqual(
                got, (year, m, d),
                "%d 年春节不符：期望 %d-%d，实得 %s" % (year, m, d, got),
            )

    def test_from_solar_roundtrip(self):
        """公历 → 农历 → 公历 的往返一致性。"""
        for (y, m, d) in [
            (2020, 1, 25), (2020, 6, 21), (2023, 3, 22),
            (2025, 7, 25), (2033, 12, 31), (1996, 2, 19),
        ]:
            lunar = from_solar(y, m, d)
            back = to_solar(lunar)
            self.assertEqual(
                back, (y, m, d),
                "往返不一致：%s → %s → %s" % ((y, m, d), lunar, back),
            )


class TestLeapMonth(unittest.TestCase):
    def test_leap_months(self):
        for year, month in LEAP_MONTHS.items():
            months = lunar_year_months(year)
            leaps = [m.number for m in months if m.is_leap]
            self.assertEqual(
                leaps, [month],
                "%d 年闰月不符：期望 [闰%d]，实得 %s" % (year, month, leaps),
            )
            self.assertEqual(len(months), 13)

    def test_plain_years(self):
        for year in PLAIN_YEARS:
            months = lunar_year_months(year)
            self.assertEqual(
                [m.number for m in months], list(range(1, 13)),
                "%d 年应为平年且月份序号连续" % year,
            )

    def test_month_boundaries_increasing(self):
        """任一农历年的朔时刻必须严格递增、且每月 29 或 30 天。"""
        for year in (2006, 2020, 2025, 2033):
            months = lunar_year_months(year)
            for i, m in enumerate(months):
                start = int(round(m.new_moon_jd))
                end = int(round(
                    months[i + 1].new_moon_jd
                    if i + 1 < len(months)
                    else lunar_year_months(year + 1)[0].new_moon_jd
                ))
                self.assertTrue(
                    29 <= end - start <= 30,
                    "%d 年第 %d 月长度为 %d 天（应为 29 或 30）" % (year, i + 1, end - start),
                )


class TestLunarRoundtrip(unittest.TestCase):
    def test_leap_month_roundtrip(self):
        """闰月日期的公历↔农历往返。"""
        for year, month in LEAP_MONTHS.items():
            solar = to_solar(LunarDate(year, month, 1, True))
            back = from_solar(*solar)
            self.assertEqual(
                (back.year, back.month, back.is_leap, back.day),
                (year, month, True, 1),
                "%d 年闰%d月往返失败：%s → %s" % (year, month, solar, back),
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
