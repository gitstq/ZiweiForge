# -*- coding: utf-8 -*-
"""
ZiweiForge / ziweiforge.chart.builder
=====================================

紫微斗数本命盘排盘引擎。

排盘流程
--------
1. **定命宫 / 身宫**——寅宫起正月，顺数至生月；再自生月起子时，**逆**数生时安命，
   **顺**数生时安身（《安身命例》：大抵人命俱从寅上起正月，顺数至本生月止，又自
   人生月起子时逆至本生时安命，顺至本生时安身）。
2. **逆布十二宫**——命宫起，依次逆时针安兄弟、夫妻……父母。
3. **定十二宫天干**——五虎遁，寅宫为遁首（甲己年丙寅、乙庚年戊寅……）。
4. **定五行局**——取命宫干支纳音五行（水二、木三、金四、土五、火六局）。
5. **安紫微星**——``(生日 + 合数) ÷ 局数 = 商``，商自寅宫顺数，合数偶数顺行、
   奇数逆行。
6. **安十四主星**——紫微系逆布、天府系顺布；天府与紫微以寅申为轴对称。
7. **安辅曜煞曜**——左右曲昌魁钺、禄马羊陀、火铃空劫、鸾喜孤寡等。
8. **安四化**——生年干四化，及各宫宫干自化。
9. **排大限**——按五行局数起运，阳男阴女顺行、阴男阳女逆行，每宫十年。

关于闰月
--------
古籍《安身命例》云「凡闰月生者，要在次月内起安身命」，即闰四月生人当作五月起
正月数。现代排盘软件则多以闰月本身的月序计算。本模块以 ``leap_month_next``
参数开放两种口径，默认为现代口径（闰月用其自身月序）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from ..calendar import (
    DI_ZHI,
    TIAN_GAN,
    LunarDate,
    day_ganzhi,
    from_solar,
    hour_branch_index,
    solar_term_of_day,
    wu_hu_dun_yin,
    wu_xing_ju,
    year_ganzhi,
)
from ..calendar.lunar import LUNAR_TZ
from .constants import (
    BRIGHTNESS,
    GU_GUA,
    GU_GUA_GROUP,
    HUO_LING,
    KUI_YUE,
    LONG_FENG,
    LU_CUN,
    MINOR_STARS,
    MING_ZHU,
    PALACE_NAMES,
    SAN_HE_GROUP,
    SI_HUA,
    SI_HUA_NAMES,
    TIAN_MA,
    TIANFU_OFFSET,
    TIANFU_SERIES,
    ZIWEI_OFFSET,
    ZIWEI_SERIES,
)

__all__ = [
    "Gender", "StarPlacement", "Palace", "Chart", "build_chart",
    "ziwei_position",
]

#: 地支序号常量，便于阅读
YIN = 2      # 寅
CHEN = 4     # 辰
XU = 10      # 戌
YOU = 9      # 酉
CHOU = 1     # 丑
WU = 6       # 午
HAI = 11     # 亥


class Gender:
    """性别常量。仅用于大限顺逆。"""

    MALE = "male"
    FEMALE = "female"


@dataclass(frozen=True)
class StarPlacement:
    """一颗落在命盘上的星曜。

    :param name: 星名
    :param branch: 所在宫位的地支序号
    :param brightness: 亮度（庙/旺/得/利/平/不/陷），辅曜为 ``None``
    :param si_hua: 生年四化（化禄/化权/化科/化忌），未化者为 ``None``
    :param self_hua: 宫干自化（后天自化），未化者为 ``None``
    :param is_main: 是否为十四主星
    """

    name: str
    branch: int
    brightness: Optional[str] = None
    si_hua: Optional[str] = None
    self_hua: Optional[str] = None
    is_main: bool = False

    @property
    def label(self) -> str:
        """带亮度与四化的显示名，如 ``紫微(庙)权``。"""
        out = self.name
        if self.brightness:
            out += "(%s)" % self.brightness
        if self.si_hua:
            out += self.si_hua[1:]
        if self.self_hua:
            out += "〔%s〕" % self.self_hua
        return out


@dataclass
class Palace:
    """命盘中的一个宫位。"""

    #: 宫位序号，0=命宫 … 11=父母
    index: int
    name: str
    #: 宫位所在地支序号
    branch: int
    #: 宫位天干序号
    gan: int
    stars: List[StarPlacement] = field(default_factory=list)
    #: 是否为身宫所在
    is_body: bool = False
    #: 大限起止年龄（含）
    daxian_start: Optional[int] = None
    daxian_end: Optional[int] = None

    @property
    def ganzhi(self) -> str:
        return TIAN_GAN[self.gan] + DI_ZHI[self.branch]

    @property
    def main_stars(self) -> List[StarPlacement]:
        return [s for s in self.stars if s.is_main]

    @property
    def minor_stars(self) -> List[StarPlacement]:
        return [s for s in self.stars if not s.is_main]

    @property
    def is_empty(self) -> bool:
        """无十四主星坐守（空宫）。"""
        return not self.main_stars

    @property
    def daxian(self) -> str:
        if self.daxian_start is None:
            return ""
        return "%d-%d岁" % (self.daxian_start, self.daxian_end)


@dataclass
class Chart:
    """一张完整的紫微斗数本命盘。"""

    #: 公历生日 ``(年, 月, 日)``
    solar: Tuple[int, int, int]
    #: 出生时刻的时辰序号（子=0 … 亥=11）
    hour_branch: int
    #: 性别
    gender: str
    #: 农历生日
    lunar: LunarDate
    #: 生年天干序号
    year_gan: int
    #: 生年地支序号
    year_zhi: int
    #: 命宫地支序号
    ming_branch: int
    #: 身宫地支序号
    body_branch: int
    #: 五行局数（2/3/4/5/6）
    ju: int
    #: 紫微星所在地支序号
    ziwei_branch: int
    #: 天府星所在地支序号
    tianfu_branch: int
    #: 命主星
    ming_zhu: str
    #: 十二宫，按宫位序号排列（0=命宫）
    palaces: Tuple[Palace, ...]
    #: 生年四化：``星名 -> 化禄/化权/化科/化忌``
    si_hua: Dict[str, str]
    #: 生辰四柱（年、月、日、时干支字符串）
    four_pillars: Tuple[str, str, str, str]

    # -- 便捷访问 ---------------------------------------------------------

    def palace(self, name: str) -> Palace:
        """按宫名取宫位，如 ``chart.palace("命宫")``。"""
        for p in self.palaces:
            if p.name == name:
                return p
        raise KeyError("无此宫位：%s" % name)

    def by_branch(self, branch: int) -> Palace:
        """按地支序号取宫位。"""
        for p in self.palaces:
            if p.branch == branch:
                return p
        raise KeyError("无此地支宫位：%d" % branch)  # pragma: no cover

    @property
    def ming_palace(self) -> Palace:
        return self.palaces[0]

    @property
    def body_palace(self) -> Palace:
        return self.by_branch(self.body_branch)

    @property
    def ju_name(self) -> str:
        return {2: "水二局", 3: "木三局", 4: "金四局", 5: "土五局", 6: "火六局"}[self.ju]

    @property
    def year_ganzhi(self) -> str:
        return TIAN_GAN[self.year_gan] + DI_ZHI[self.year_zhi]

    @property
    def hour_name(self) -> str:
        return DI_ZHI[self.hour_branch] + "时"


# ---------------------------------------------------------------------------
# 紫微星定位
# ---------------------------------------------------------------------------


def ziwei_position(day: int, ju: int) -> int:
    """由农历生日与五行局数求紫微星的地支序号。

    歌诀：生日除局商为月，一自寅起紫微定；只加不减到整除，阳退阴进记心中。

    等价于：取最小非负合数 ``r`` 使 ``(day + r)`` 能被 ``ju`` 整除，商为 ``m``；
    自寅宫顺时针数 ``m`` 宫为基准位，``r`` 为偶数再顺行 ``r`` 宫、为奇数则逆行
    ``r`` 宫。

    >>> ziwei_position(2, 4)   # 金四局初二 → 辰宫
    4
    """
    if not 1 <= day <= 30:
        raise ValueError("农历生日须在 1–30 之间：%r" % day)
    if ju not in (2, 3, 4, 5, 6):
        raise ValueError("五行局数须为 2/3/4/5/6：%r" % ju)
    r = (-day) % ju
    m = (day + r) // ju
    base = (YIN + m - 1) % 12
    return (base - r) % 12 if r % 2 else (base + r) % 12


def _tianfu_position(ziwei: int) -> int:
    """紫府对称：天府与紫微以寅申为轴对称，仅寅、申二宫紫府同宫。"""
    return (2 * YIN - ziwei) % 12


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------


def build_chart(
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    gender: str = Gender.MALE,
    tz: float = LUNAR_TZ,
    leap_month_next: bool = False,
) -> Chart:
    """由公历出生时间排紫微斗数本命盘。

    :param year/month/day: 公历生日（本地时间）
    :param hour/minute: 出生时刻（本地时间，24 小时制）
    :param gender: :class:`Gender.MALE` 或 :class:`Gender.FEMALE`，仅影响大限顺逆
    :param tz: 输入时间的时区偏移小时数，默认 ``8``（中国标准时间）
    :param leap_month_next: 闰月生人是否按「次月」起命宫（古籍口径）
    :return: :class:`Chart`
    """
    if gender not in (Gender.MALE, Gender.FEMALE):
        raise ValueError("gender 须为 'male' 或 'female'")

    lunar = from_solar(year, month, day, hour, minute, tz=tz)
    hb = hour_branch_index(hour, minute)
    return _build(lunar, hb, gender, year, month, day, hour, leap_month_next)


def build_from_lunar(
    lunar_year: int,
    lunar_month: int,
    lunar_day: int,
    hour_branch: int,
    is_leap: bool = False,
    gender: str = Gender.MALE,
    leap_month_next: bool = False,
) -> Chart:
    """由农历生日与时辰排盘（不校核公历日期，用于已知农历生日的场合）。"""
    from ..calendar import to_solar

    y, m, d = to_solar(LunarDate(lunar_year, lunar_month, lunar_day, is_leap))
    lunar = LunarDate(lunar_year, lunar_month, lunar_day, is_leap)
    return _build(lunar, hour_branch % 12, gender, y, m, d, 12, leap_month_next)


def _build(
    lunar: LunarDate,
    hb: int,
    gender: str,
    solar_year: int,
    solar_month: int,
    solar_day: int,
    solar_hour: int = 12,
    leap_month_next: bool = False,
) -> Chart:
    y_gan, y_zhi = year_ganzhi(lunar.year)

    # 1. 命宫 / 身宫 ------------------------------------------------------
    m = lunar.month + 1 if (leap_month_next and lunar.is_leap) else lunar.month
    ming = (YIN + (m - 1) - hb) % 12
    body = (YIN + (m - 1) + hb) % 12

    # 2. 十二宫逆布 + 3. 五虎遁定宫干 ---------------------------------------
    yin_gan = wu_hu_dun_yin(y_gan)
    palaces: List[Palace] = []
    for i, name in enumerate(PALACE_NAMES):
        branch = (ming - i) % 12
        gan = (yin_gan + (branch - YIN)) % 10
        palaces.append(Palace(i, name, branch, gan))

    # 4. 五行局 ------------------------------------------------------------
    ming_gan = palaces[0].gan
    ju = wu_xing_ju(ming_gan, ming)

    # 5. 紫微 / 天府 -------------------------------------------------------
    ziwei = ziwei_position(lunar.day, ju)
    tianfu = _tianfu_position(ziwei)

    # 6. 十四主星 ----------------------------------------------------------
    positions: Dict[str, int] = {}
    for name, off in zip(ZIWEI_SERIES, ZIWEI_OFFSET):
        positions[name] = (ziwei - off) % 12
    for name, off in zip(TIANFU_SERIES, TIANFU_OFFSET):
        positions[name] = (tianfu + off) % 12

    # 7. 生年四化 ----------------------------------------------------------
    si_hua: Dict[str, str] = {}
    for star, hua in zip(SI_HUA[y_gan], SI_HUA_NAMES):
        si_hua[star] = hua

    # 8. 辅曜、煞曜、杂曜 ---------------------------------------------------
    group = SAN_HE_GROUP[y_zhi]
    lu = LU_CUN[y_gan]
    kui, yue = KUI_YUE[y_gan]
    huo_base, ling_base = HUO_LING[group]
    gu_gua = GU_GUA[GU_GUA_GROUP[y_zhi]]
    long_chi, feng_ge = LONG_FENG

    minor: List[Tuple[str, int]] = [
        # 依生月
        ("左辅", (CHEN + m - 1) % 12),
        ("右弼", (XU - (m - 1)) % 12),
        ("天刑", (YOU + m - 1) % 12),
        ("天姚", (CHOU + m - 1) % 12),
        # 依生时
        ("文昌", (XU - hb) % 12),
        ("文曲", (CHEN + hb) % 12),
        ("火星", (huo_base + hb) % 12),
        ("铃星", (ling_base + hb) % 12),
        ("地空", (HAI - hb) % 12),
        ("地劫", (HAI + hb) % 12),
        # 依生年干
        ("禄存", lu),
        ("擎羊", (lu + 1) % 12),
        ("陀罗", (lu - 1) % 12),
        ("天魁", kui),
        ("天钺", yue),
        # 依生年支
        ("天马", TIAN_MA[group]),
        ("红鸾", (3 - y_zhi) % 12),
        ("天喜", (3 - y_zhi + 6) % 12),
        ("孤辰", gu_gua[0]),
        ("寡宿", gu_gua[1]),
        ("天哭", (WU - y_zhi) % 12),
        ("天虚", (WU + y_zhi) % 12),
        ("天才", (ming + y_zhi) % 12),
        ("天寿", (body + y_zhi) % 12),
        ("龙池", (long_chi + y_zhi) % 12),
        ("凤阁", (feng_ge - y_zhi) % 12),
    ]
    # 依生日：三台由左辅起初一顺数，八座由右弼起初一逆数；
    # 恩光由文昌起初一顺数再退一位，天贵由文曲起初一顺数再退一位。
    zuo_fu = (CHEN + m - 1) % 12
    you_bi = (XU - (m - 1)) % 12
    wen_chang = (XU - hb) % 12
    wen_qu = (CHEN + hb) % 12
    minor += [
        ("三台", (zuo_fu + lunar.day - 1) % 12),
        ("八座", (you_bi - (lunar.day - 1)) % 12),
        ("恩光", (wen_chang + lunar.day - 1 - 1) % 12),
        ("天贵", (wen_qu + lunar.day - 1 - 1) % 12),
    ]

    for name, branch in minor:
        positions.setdefault(name, branch)

    # 9. 四化：生年四化（先天定数）与宫干自化（后天不定数）分别标注 ----------
    self_hua_of: Dict[str, str] = {}
    for p in palaces:
        for star, hua in zip(SI_HUA[p.gan], SI_HUA_NAMES):
            if positions.get(star) == p.branch:
                self_hua_of[star] = hua

    # 装入各宫：先主星（紫微系→天府系）、后辅曜（按 MINOR_STARS 顺序）
    for name in list(ZIWEI_SERIES) + list(TIANFU_SERIES):
        branch = positions[name]
        palaces[(ming - branch) % 12].stars.append(
            StarPlacement(name, branch, BRIGHTNESS[name][branch],
                          si_hua.get(name), self_hua_of.get(name), True)
        )
    for name in MINOR_STARS:
        branch = positions.get(name)
        if branch is None:  # pragma: no cover
            continue
        palaces[(ming - branch) % 12].stars.append(
            StarPlacement(name, branch, None,
                          si_hua.get(name), self_hua_of.get(name), False)
        )

    # 10. 大限 -------------------------------------------------------------
    forward = (y_gan % 2 == 0) == (gender == Gender.MALE)
    start = ju
    for i in range(12):
        branch = (ming + i) % 12 if forward else (ming - i) % 12
        p = palaces[(ming - branch) % 12]
        p.daxian_start = start + 10 * i
        p.daxian_end = start + 10 * i + 9

    for p in palaces:
        if p.branch == body:
            p.is_body = True

    # 11. 四柱（年柱依农历年、月柱依真节气、日柱依公历日、时柱五鼠遁）------
    # 晚子时（23:00 之后）日柱用次日，为通行的「子时换日」口径。
    y, mo, d = _add_days(solar_year, solar_month, solar_day, 1 if solar_hour >= 23 else 0)
    d_gan, d_zhi = day_ganzhi(_jdn(y, mo, d))
    four = (
        TIAN_GAN[y_gan] + DI_ZHI[y_zhi],
        _yue_zhu(y_gan, solar_year, solar_month, solar_day),
        TIAN_GAN[d_gan] + DI_ZHI[d_zhi],
        TIAN_GAN[(d_gan % 5 * 2 + hb) % 10] + DI_ZHI[hb],
    )

    return Chart(
        solar=(solar_year, solar_month, solar_day),
        hour_branch=hb,
        gender=gender,
        lunar=lunar,
        year_gan=y_gan,
        year_zhi=y_zhi,
        ming_branch=ming,
        body_branch=body,
        ju=ju,
        ziwei_branch=ziwei,
        tianfu_branch=tianfu,
        ming_zhu=MING_ZHU[ming],
        palaces=tuple(palaces),
        si_hua=si_hua,
        four_pillars=four,
    )


def _jdn(year: int, month: int, day: int) -> int:
    """公历日期 → 儒略日数（JDN）。"""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return (
        day
        + (153 * m + 2) // 5
        + 365 * y
        + y // 4
        - y // 100
        + y // 400
        - 32045
    )


def _add_days(year: int, month: int, day: int, delta: int) -> Tuple[int, int, int]:
    """公历日期加减天数（用于晚子时换日）。"""
    d = date(year, month, day) + timedelta(days=delta)
    return d.year, d.month, d.day


def _yue_zhu(year_gan: int, year: int, month: int, day: int) -> str:
    """依**真节气**排月柱：立春起寅月，惊蛰起卯月……五虎遁定月干。

    月柱的分界是「节」（立春、惊蛰、清明……）而非农历月初，故此处调用自研
    天文内核求出的节气时刻，而非查表。
    """
    term = solar_term_of_day(year, month, day)
    zhi = (YIN + term // 2) % 12
    gan = (wu_hu_dun_yin(year_gan) + (zhi - YIN)) % 10
    return TIAN_GAN[gan] + DI_ZHI[zhi]
