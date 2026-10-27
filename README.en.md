<div align="center">

# 🔮 ZiweiForge

**Zero-dependency · Real-astronomy · Ziwei Doushu (Purple Star Astrology) chart engine**

[简体中文](./README.md) · [繁體中文](./README.zh-TW.md) · [English](./README.en.md)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)](./requirements.txt)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

</div>

---

## 📖 1. Overview

Almost every existing Ziwei Doushu library ships a **compressed perpetual-calendar
lookup table** (solar-term instants, new-moon instants) and finds the Ziwei star by
table lookup. That approach is lightweight, but it has three unavoidable drawbacks:
the data expires, years outside the table simply crash, and it can never explain *why*.

**ZiweiForge takes the other road.** It ships **no calendar data at all** — lunar months,
the 24 solar terms and true new moons are all **solved from scratch at runtime**:

- **Solar apparent longitude** — **VSOP87D** planetary theory, 636 periodic terms
  (public astronomical constants released by IMCCE)
- **Lunar apparent longitude** — Meeus, *Astronomical Algorithms*, Ch. 47, Table 47.A
- **Solar terms & true new moons** — Newton iteration, with ΔT (TT−UT), nutation
  and aberration applied
- **Lunar calendar construction** — month starts on the day of the **true new moon**;
  the winter solstice anchors the 11th month; a month with **no major solar term**
  becomes the leap month; month/term attribution is judged on **calendar days**
  in China Standard Time (UTC+8)

The result: the lunar calendar and solar terms are reconstructed independently for
1900–2100 — no network, no data files, no packages.

> This project is a tool for calendrical computation and traditional-culture research.
> Astrological interpretations are provided for cultural study only and are not advice.

---

## ✨ 2. Key Features

| Feature | Description |
| --- | --- |
| 🪶 **Zero dependencies** | Python standard library only — no NumPy, pandas or astronomy packages |
| 🌌 **Real astronomy** | VSOP87D 636 terms + Meeus lunar series, solved at runtime |
| 📅 **Custom lunar engine** | True-new-moon months, solstice anchoring, no-major-term leap months (incl. the 2033 leap-11th-month special case) |
| 🧭 **Complete chart** | 14 major stars + 30 auxiliary/malefic/minor stars = **44 stars** |
| 🎨 **Dual Si Hua** | Natal four-transformations and palace-stem self-transformations tracked separately |
| 🖼️ **Three outputs** | Terminal 4×4 grid, SVG vector chart, structured JSON |
| ⏳ **Decade luck periods** | Starting age from the Five-Element phase; forward/reverse by year-stem polarity × gender |
| 🧪 **Strongly validated** | 150-cell Ziwei table + 2 published charts + 400 random charts |
| 🌐 **Trilingual docs** | 简体中文 / 繁體中文 / English, switchable at the top |

---

## 🚀 3. Quick Start

### Install

```bash
pip install -e .            # from source (recommended for development)
# or
python -m build --wheel .   # build a wheel, then pip install dist/*.whl
```

**Runtime dependencies: none.** `requirements.txt` contains nothing mandatory.

### One command

```bash
python -m ziweiforge 1992-12-04 12:30
python -m ziweiforge 1992-12-04 12:30 --gender female --svg chart.svg
python -m ziweiforge --lunar 1970-9-2 --hour 巳 --json
python -m ziweiforge 2025-02-03 22:10 --stars        # palace → star listing only
```

After install a console script is available: `ziweiforge 1992-12-04 12:30`

### Three lines of Python

```python
from ziweiforge import build_chart, render_text

chart = build_chart(1992, 12, 4, 12, 30, gender="male")
print(chart.ming_palace.main_stars[0].label)   # 紫微(庙)权
print(render_text(chart))
```

---

## 🧩 4. Usage

### 4.1 Inspecting the chart object

```python
from ziweiforge import build_chart
from ziweiforge.calendar import DI_ZHI

c = build_chart(1992, 12, 4, 12, 30)

c.lunar                  # lunar date object (壬申 year, 11th month, day 11)
c.four_pillars           # ('壬申', '辛亥', '甲寅', '庚午')  four pillars
c.ju_name                # '水二局'  Five-Element phase (Water-2)
DI_ZHI[c.ming_branch]    # '午'  branch of the Life palace
DI_ZHI[c.body_branch]    # '午'  branch of the Body palace
DI_ZHI[c.ziwei_branch]   # '午'  branch holding the Ziwei star
c.ming_zhu               # '破军'  Life-lord star
c.si_hua                 # {'天梁': '化禄', '紫微': '化权', '左辅': '化科', '武曲': '化忌'}

c.palace("夫妻")         # get a palace by name
c.palace("夫妻").stars   # stars in that palace
c.by_branch(4)           # get a palace by Earthly-Branch index (辰 = 4)
```

### 4.2 Exporting SVG

```python
from ziweiforge.render.svg import render_svg

with open("chart.svg", "w", encoding="utf-8") as fh:
    fh.write(render_svg(chart))
```

The SVG needs no external fonts or libraries — open it in a browser, embed it, or print it.

### 4.3 Exporting JSON

```python
from ziweiforge.cli import chart_to_json

print(chart_to_json(chart))
```

The JSON carries, for each of the 12 palaces, its name, Earthly Branch, stem-branch,
decade-luck range, and for every star its name, major/minor flag, brightness and
transformations — ready for a front end or another system.

### 4.4 Building from a lunar birthday

```python
from ziweiforge import build_from_lunar

# Lunar 2023, leap 2nd month, day 10, noon hour
chart = build_from_lunar(2023, 2, 10, 6, is_leap=True)
```

### 4.5 Calendar conversion only

The astronomy kernel and the lunar module work standalone:

```python
from ziweiforge.calendar import from_solar, to_solar, LunarDate

from_solar(2025, 1, 29)                     # Lunar New Year 2025
to_solar(LunarDate(2033, 11, 1, True))      # (2033, 12, 22) leap 11th month, day 1
```

---

## 🏗️ 5. Project Layout

```
ZiweiForge/
├── ziweiforge/
│   ├── astro/              # astronomy kernel
│   │   ├── core.py         #   Julian Day / ΔT / solar & lunar longitude / terms / true new moon
│   │   └── _vsop87.py      #   VSOP87D solar-longitude terms (636 terms, generated)
│   ├── calendar/           # calendars
│   │   ├── ganzhi.py       #   stem-branch / Na Yin / Wu Hu Dun / Wu Shu Dun
│   │   └── lunar.py        #   new-moon months, solstice anchoring, leap months
│   ├── chart/              # chart building
│   │   ├── constants.py    #   star names, brightness table, Si Hua, placement mnemonic data
│   │   └── builder.py      #   Life/Body palace → 12 palaces → phase → stars → Si Hua → luck
│   ├── render/             # output
│   │   ├── text.py         #   terminal 4×4 grid
│   │   └── svg.py          #   SVG vector chart
│   ├── cli.py              # command-line entry point
│   └── __main__.py         # python -m ziweiforge
├── tests/                  # 29 self-tests (unittest; pytest not required)
├── examples/               # runnable examples
├── pyproject.toml
├── requirements.txt        # runtime dependencies: none
├── LICENSE                 # MIT
└── README.md / README.zh-TW.md / README.en.md
```

---

## 🔬 6. Algorithms & Accuracy

### 6.1 Astronomy kernel

| Stage | Method | Error |
| --- | --- | --- |
| Solar apparent longitude | VSOP87D (636 terms) + aberration + nutation Δψ | — |
| Equinox / solstice instants | Newton inversion of longitude | **≤ 0.44 min** vs pyephem (1900–2100, 164 cases) |
| Lunar apparent longitude | Meeus Table 47.A (62 terms) + A1/A2 | — |
| True new moon | Inversion of solar–lunar elongation | **≤ 1.4 min** vs pyephem |

### 6.2 Lunar calendar

- **Month boundary** — the **calendar day** containing the true new moon is day 1
  (not the precise instant)
- **Month numbering** — the month containing the winter solstice is the 11th month;
  the 2nd new moon after the previous year's 11th month is the 1st month
- **Leap month** — with 13 months, the first month lacking a major solar term becomes
  the leap month, with a hard constraint that the winter solstice must still fall in
  the 11th month (2033 is the classic counter-example: leap 11th month)

| Check | Result |
| --- | --- |
| Lunar New Year dates (2015–2027) | **13 / 13 pass** |
| Leap months (2006/2009/2012/2014/2017/2020/2023/2025/2028/2033) | **10 / 10 pass** |
| Synodic month length always 29 or 30 days | pass |

### 6.3 Chart rules

All rules follow the traditional mnemonics and were cross-checked before implementation:

- Life / Body palace — "start at 寅 for month 1, count forward to the birth month;
  count **backward** to the birth hour for Life, **forward** for Body"
- Five-Element phase — Na Yin of the Life palace stem-branch
  (Water-2 / Wood-3 / Metal-4 / Earth-5 / Fire-6)
- Ziwei star — "divide the birth day by the phase number; start at 寅; add (never
  subtract) to reach an exact quotient; odd retrogresses, even advances"
- Ziwei series runs counter-clockwise, Tianfu series clockwise, the two symmetric
  about the 寅–申 axis
- Si Hua — the ten-stem four-transformation mnemonic table
- 30 auxiliary, malefic and minor stars (Liu Ji, Liu Sha, Lu Ma, Yang Tuo, Huo Ling,
  Kong Jie, Luan Xi, Gu Gua, …)

> ⚠️ **On star brightness**: `ziweiforge.chart.constants.BRIGHTNESS` uses one complete
> seven-level scheme. Schools differ on individual entries — replace the dict to switch.

---

## 🧪 7. Testing & Validation

```bash
make test          # or: python -m unittest discover -s tests -v
```

29 self-tests, all passing, pytest not required:

| Suite | Content | Result |
| --- | --- | --- |
| `test_astro` | Solar-term longitude self-consistency, term dates, elongation at new moon | pass |
| `test_astro` | Cross-check equinoxes/solstices against pyephem (skipped if absent) | ≤ 0.44 min |
| `test_lunar` | 13 Lunar New Year cases, 10 leap months, round-trips | all pass |
| `test_chart` | **Full 150-cell Ziwei placement table** (30 days × 5 phases) | 150 / 150 |
| `test_chart` | Palace-by-palace comparison against 2 published charts | 28 / 28 |
| `test_chart` | Structural invariants (unique major stars, Ziwei/Tianfu symmetry, palace order, luck ranges) | pass |
| Stress | 400 random charts over 1901–2099 | 0 failures |

**Comparison against two published charts**

| Case | Published chart | ZiweiForge |
| --- | --- | --- |
| 1970-10-01 10:10 (lunar 庚戌, 9th month, day 2, 巳 hour) | Metal-4 phase, Ziwei in 辰, Tianfu in 子 | ✅ identical — all 14 major stars match |
| 1992-12-04 noon (lunar 壬申, 11th month, day 11) | Water-2 phase, Life and Body in 午, Ziwei in 午 | ✅ identical — star placement 100% match |

---

## 📄 8. License & Disclaimer

- **License**: [MIT](./LICENSE) — free to use, modify and commercialise.
- **Astronomical data**: the VSOP87 terms are public astronomical constants released by
  IMCCE (Bretagnon & Francou, 1988); the lunar theory comes from Meeus,
  *Astronomical Algorithms*. Both are public scientific constants; this project
  references them only as numeric tables and contains no third-party source code.
- **Disclaimer**: this is a calendrical-computation and traditional-culture research
  tool. Ziwei Doushu is a traditional practice with no scientific basis; all output is
  provided for cultural study and program verification only. **Do not use it for
  medical, financial or legal decisions.**

---

<div align="center">

Real astronomy. A chart you can actually verify.

</div>
