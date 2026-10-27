# -*- coding: utf-8 -*-
"""
天文内核自测。

节气时刻由 VSOP87D 太阳视黄经真实反解得到，此处以「节气时刻的太阳视黄经
应精确等于该节气的黄经」作为自洽性校验，并以权威历书公布的节气日期作为
外部基准。
"""

from __future__ import annotations

import unittest

from ziweiforge.astro import (
    gregorian_from_julian,
    julian_day,
    moon_longitude,
    solar_longitude,
    solar_term,
    tt_to_ut,
)
from ziweiforge.calendar.lunar import LUNAR_TZ

#: 权威历书公布的节气日期（中国标准时间）
KNOWN_SOLAR_TERM_DATES = [
    (2024, 0, (2, 4)),     # 立春
    (2024, 4, (4, 4)),     # 清明
    (2024, 10, (7, 6)),    # 小暑
    (2024, 21, (12, 21)),  # 冬至
    (2025, 0, (2, 3)),     # 立春
    (2025, 12, (8, 7)),    # 立秋
    (2026, 0, (2, 4)),     # 立春
    (2026, 21, (12, 22)),  # 冬至
    (2027, 0, (2, 4)),     # 立春
]

#: 节气序号 → 该节气的太阳视黄经（立春 315°，每节气递增 15°）
SOLAR_TERM_LONGITUDE = [(315 + 15 * i) % 360 for i in range(24)]

#: 二分二至的节气序号
EQUINOX_SOLSTICE = {3: 0.0, 9: 90.0, 15: 180.0, 21: 270.0}


def _local_date(jd_tt: float):
    """地球时儒略日 → 中国标准时间的 (年, 月, 日)。"""
    y, m, d = gregorian_from_julian(tt_to_ut(jd_tt) + LUNAR_TZ / 24.0)
    return y, m, int(d)


class TestSolarLongitude(unittest.TestCase):
    def test_equinox_solstice_longitudes(self):
        """二分二至时刻的太阳视黄经应精确等于 0/90/180/270 度。"""
        for index, expected in EQUINOX_SOLSTICE.items():
            for year in (1900, 1950, 2000, 2024, 2050, 2099):
                jd = solar_term(year, index)
                lon = solar_longitude(jd) % 360.0
                diff = min(abs(lon - expected), 360 - abs(lon - expected))
                self.assertLess(
                    diff, 1e-6,
                    "节气 %d 于 %d 年的太阳视黄经偏差过大：%.9f" % (index, year, diff),
                )

    def test_all_term_longitudes(self):
        """24 个节气时刻的太阳视黄经应逐一等于该节气的黄经。"""
        for year in (1975, 2000, 2025, 2075):
            for index in range(24):
                jd = solar_term(year, index)
                lon = solar_longitude(jd) % 360.0
                expect = SOLAR_TERM_LONGITUDE[index]
                diff = min(abs(lon - expect), 360 - abs(lon - expect))
                self.assertLess(diff, 1e-6, "%d 年节气 %d 反解失败" % (year, index))

    def test_longitude_monotonic_within_year(self):
        """一年内 24 个节气时刻应严格递增。"""
        for year in (1950, 2024, 2099):
            prev = None
            for i in range(24):
                jd = solar_term(year, i)
                if prev is not None:
                    self.assertGreater(jd, prev)
                prev = jd

    def test_known_solar_term_dates(self):
        """与权威历书公布的节气日期逐一比对（精确到日）。"""
        for year, index, expect in KNOWN_SOLAR_TERM_DATES:
            got = _local_date(solar_term(year, index))
            self.assertEqual(
                got, (year, *expect),
                "%d 年节气 %d 的日期不符：期望 %s，实得 %s" % (year, index, expect, got),
            )


class TestMoonLongitude(unittest.TestCase):
    def test_longitude_range(self):
        """月亮视黄经应始终归一到 [0, 360)。"""
        for day in range(0, 400, 37):
            jd = julian_day(2024, 1, 1.0 + day) + 0.0
            lon = moon_longitude(jd)
            self.assertTrue(0.0 <= lon < 360.0, "月亮视黄经越界：%r" % lon)

    def test_new_moon_elongation_zero(self):
        """朔时刻的日月黄经差应为 0（模 360）。"""
        from ziweiforge.astro import true_new_moon
        from ziweiforge.calendar.lunar import _k_of

        for jd0 in (julian_day(2020, 1, 1.0), julian_day(2033, 6, 1.0)):
            k = _k_of(jd0)
            jd = true_new_moon(float(k))
            diff = (moon_longitude(jd) - solar_longitude(jd)) % 360.0
            delta = min(diff, 360 - diff)
            self.assertLess(delta, 1e-4, "朔时刻日月黄经差过大：%.6f" % delta)


class TestCrossCheckPyEphem(unittest.TestCase):
    """与 pyephem 交叉验证二分二至时刻（可选，未安装则跳过）。

    pyephem **不是**本项目的依赖，仅作为离线校验的第三方基准使用。
    """

    @classmethod
    def setUpClass(cls):
        try:
            import ephem  # noqa: F401
        except ImportError:  # pragma: no cover
            raise unittest.SkipTest("pyephem 未安装，跳过交叉校验")

    def test_equinox_solstice_times(self):
        import ephem

        ref = {
            3: ephem.next_vernal_equinox,
            9: ephem.next_summer_solstice,
            15: ephem.next_autumnal_equinox,
            21: ephem.next_winter_solstice,
        }
        for year in range(1900, 2101, 10):
            for index, fn in ref.items():
                jd = solar_term(year, index)
                mine = float(ephem.Date(tt_to_ut(jd) - 2415020.0))
                theirs = float(fn("%d/01" % year))
                self.assertLess(
                    abs(mine - theirs) * 1440.0, 2.0,
                    "%d 年节气 %d 与 pyephem 相差 %.3f 分钟"
                    % (year, index, (mine - theirs) * 1440.0),
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
