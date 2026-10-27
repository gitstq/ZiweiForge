# -*- coding: utf-8 -*-
"""
排盘引擎自测。

包含三组强校验：

1. **紫微星定位全表**——30 个农历生日 × 5 种五行局，共 150 组，逐一比对
   通行版本《紫微星位置表》；
2. **公开命盘案例**——以命理网站公布的两张完整命盘逐宫比对；
3. **结构不变量**——十四主星不重不漏、紫府对称、十二宫逆布等。
"""

from __future__ import annotations

import unittest

from ziweiforge.calendar import DI_ZHI
from ziweiforge.chart import build_chart, build_from_lunar
from ziweiforge.chart.builder import ziwei_position

# 通行版本《紫微星位置表》：生日 → (水二局, 木三局, 金四局, 土五局, 火六局)
ZIWEI_TABLE = (
    "丑辰亥午酉", "寅丑辰亥午", "寅寅丑辰亥", "卯巳寅丑辰", "卯寅子寅丑",
    "辰卯巳未寅", "辰午寅子戌", "巳卯卯巳未", "巳辰丑寅子", "午未午卯巳",
    "午辰卯申寅", "未巳辰丑卯", "未申寅午亥", "申巳未卯申", "申午辰辰丑",
    "酉酉巳酉午", "酉午卯寅卯", "戌未申未辰", "戌戌巳辰子", "亥未午巳酉",
    "亥申辰戌寅", "子亥酉卯未", "子申午申辰", "丑酉未巳巳", "丑子巳午丑",
    "寅酉戌亥戌", "寅戌未辰卯", "卯丑申酉申", "卯戌午午巳", "辰亥亥未午",
)

_JU_ORDER = (2, 3, 4, 5, 6)


class TestZiweiTable(unittest.TestCase):
    def test_full_table(self):
        """150 组全表比对。"""
        for day_idx, row in enumerate(ZIWEI_TABLE, start=1):
            for ju_idx, expect in enumerate(row):
                got = DI_ZHI[ziwei_position(day_idx, _JU_ORDER[ju_idx])]
                self.assertEqual(
                    got, expect,
                    "生日 %d、%s：紫微应在 %s，实得 %s"
                    % (day_idx, _JU_ORDER[ju_idx], expect, got),
                )

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            ziwei_position(0, 4)
        with self.assertRaises(ValueError):
            ziwei_position(31, 4)
        with self.assertRaises(ValueError):
            ziwei_position(15, 7)


class TestPublishedChartA(unittest.TestCase):
    """案例 A：阳历 1970-10-01 10:10 → 农历庚戌年九月初二巳时。

    公开命盘给出的十四主星落宫：
    紫微辰、天机卯、太阳丑、武曲子、天同亥、廉贞申；
    天府子、太阴丑、贪狼寅、巨门卯、天相辰、天梁巳、七杀午、破军戌。
    """

    EXPECT = {
        "紫微": "辰", "天机": "卯", "太阳": "丑", "武曲": "子",
        "天同": "亥", "廉贞": "申", "天府": "子", "太阴": "丑",
        "贪狼": "寅", "巨门": "卯", "天相": "辰", "天梁": "巳",
        "七杀": "午", "破军": "戌",
    }

    @classmethod
    def setUpClass(cls):
        cls.chart = build_chart(1970, 10, 1, 10, 10)

    def test_lunar_and_hour(self):
        self.assertEqual(self.chart.lunar.year, 1970)
        self.assertEqual((self.chart.lunar.month, self.chart.lunar.day), (9, 2))
        self.assertEqual(DI_ZHI[self.chart.hour_branch], "巳")

    def test_ju(self):
        self.assertEqual(self.chart.ju, 4)
        self.assertEqual(self.chart.ju_name, "金四局")

    def test_main_star_positions(self):
        actual = {}
        for p in self.chart.palaces:
            for s in p.stars:
                if s.is_main:
                    actual[s.name] = DI_ZHI[s.branch]
        self.assertEqual(actual, self.EXPECT)


class TestPublishedChartB(unittest.TestCase):
    """案例 B：1992-12-04 午时 → 农历壬申年十一月十一午时。

    公开命盘：命宫午、身宫午、水二局、紫微在午；四化为
    天梁化禄 / 紫微化权 / 左辅化科 / 武曲化忌。
    """

    @classmethod
    def setUpClass(cls):
        cls.chart = build_chart(1992, 12, 4, 12, 30)

    def test_ming_and_body(self):
        self.assertEqual(DI_ZHI[self.chart.ming_branch], "午")
        self.assertEqual(DI_ZHI[self.chart.body_branch], "午")

    def test_ju_and_ziwei(self):
        self.assertEqual(self.chart.ju, 2)
        self.assertEqual(DI_ZHI[self.chart.ziwei_branch], "午")
        self.assertEqual(DI_ZHI[self.chart.tianfu_branch], "戌")

    def test_si_hua(self):
        self.assertEqual(
            self.chart.si_hua,
            {"天梁": "化禄", "紫微": "化权", "左辅": "化科", "武曲": "化忌"},
        )

    def test_auxiliary_stars(self):
        """六吉星与羊陀的落宫。"""
        pos = {}
        for p in self.chart.palaces:
            for s in p.stars:
                pos.setdefault(s.name, DI_ZHI[s.branch])
        self.assertEqual(pos["文昌"], "辰")
        self.assertEqual(pos["文曲"], "戌")
        self.assertEqual(pos["左辅"], "寅")
        self.assertEqual(pos["右弼"], "子")
        self.assertEqual(pos["天魁"], "卯")
        self.assertEqual(pos["天钺"], "巳")
        self.assertEqual(pos["禄存"], "亥")
        self.assertEqual(pos["擎羊"], "子")
        self.assertEqual(pos["陀罗"], "戌")


class TestStructure(unittest.TestCase):
    def _all_charts(self):
        for args in [
            (1949, 10, 1, 15, 0), (1960, 1, 1, 0, 30), (1978, 8, 26, 13, 0),
            (1990, 5, 5, 22, 0), (2000, 2, 29, 8, 0), (2025, 6, 15, 17, 45),
            (2033, 12, 1, 3, 0),
        ]:
            yield build_chart(*args)

    def test_fourteen_main_stars_unique(self):
        """每个命盘的十四主星必须恰好各出现一次。"""
        from ziweiforge.chart import MAIN_STARS

        for chart in self._all_charts():
            seen = {}
            for p in chart.palaces:
                for s in p.stars:
                    if s.is_main:
                        self.assertNotIn(s.name, seen, "主星重复：%s" % s.name)
                        seen[s.name] = s.branch
            self.assertEqual(sorted(seen), sorted(MAIN_STARS))

    def test_ziwei_tianfu_symmetry(self):
        """紫微与天府以寅申为轴对称。"""
        for chart in self._all_charts():
            self.assertEqual(
                chart.tianfu_branch, (4 - chart.ziwei_branch) % 12,
                "紫府不对称：紫微%s 天府%s"
                % (DI_ZHI[chart.ziwei_branch], DI_ZHI[chart.tianfu_branch]),
            )

    def test_twelve_palaces_counterclockwise(self):
        """十二宫自命宫起逆时针排布，且地支各出现一次。"""
        for chart in self._all_charts():
            branches = [p.branch for p in chart.palaces]
            self.assertEqual(sorted(branches), list(range(12)))
            for i, p in enumerate(chart.palaces):
                self.assertEqual(p.branch, (chart.ming_branch - i) % 12)

    def test_daxian_covers_ten_years(self):
        """大限自五行局数起运，每宫十年，共十二宫。"""
        for chart in self._all_charts():
            ranges = sorted((p.daxian_start, p.daxian_end) for p in chart.palaces)
            self.assertEqual(ranges[0][0], chart.ju)
            for a, b in zip(ranges, ranges[1:]):
                self.assertEqual(b[0], a[1] + 1)
                self.assertEqual(a[1] - a[0], 9)

    def test_brightness_present(self):
        for chart in self._all_charts():
            for p in chart.palaces:
                for s in p.stars:
                    if s.is_main:
                        self.assertTrue(s.brightness, "主星缺少亮度：%s" % s.name)


class TestLeapMonthBirth(unittest.TestCase):
    def test_leap_month_chart(self):
        """闰月生人可正常排盘。"""
        chart = build_from_lunar(2023, 2, 10, 6, is_leap=True)
        self.assertEqual(chart.lunar.is_leap, True)
        self.assertEqual(chart.lunar.month, 2)
        self.assertEqual(len(chart.palaces), 12)

    def test_reject_bad_gender(self):
        with self.assertRaises(ValueError):
            build_chart(2000, 1, 1, 12, 0, gender="other")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
