<div align="center">

# 🔮 ZiweiForge

**零依赖 · 真天文历算 · 紫微斗数排盘引擎**

[简体中文](./README.md) · [繁體中文](./README.zh-TW.md) · [English](./README.en.md)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)](./requirements.txt)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

</div>

---

## 📖 一、项目简介

市面上的紫微斗数排盘库，几乎清一色内置一张**压缩过的万年历查表**（节气时刻表、朔望时刻表），
再把生日丢进去查表定位紫微星。这类实现很轻，但有三个绕不开的短板：数据过期即失效、
跨越表外年份直接崩溃、无法解释「为什么」。

**ZiweiForge 走的是另一条路**：不内置任何万年历数据，农历月份、二十四节气、朔望时刻
全部由自研天文内核**实时求解**。

- 太阳视黄经：采用 **VSOP87D** 行星理论，636 项周期项（IMCCE 公开发布的天文常数）
- 月亮视黄经：采用 Meeus《Astronomical Algorithms》第 47 章 Table 47.A
- 节气与真朔：由牛顿迭代反解，计入 ΔT（TT−UT）、章动与光行差
- 农历编排：以**真朔**定月、以**冬至**锚定十一月、以**无中气**置闰；月序与中气归属
  一律按中国标准时间（UTC+8）的**日历日**口径判定

于是它能在 1900–2100 区间内独立复原农历与节气——不联网、不读文件、不装任何包。

> 本项目为历算与传统文化研究工具。所述命理内容仅作文化研究参考，不构成任何决策建议。

---

## ✨ 二、核心特性

| 特性 | 说明 |
| --- | --- |
| 🪶 **零依赖** | 仅用 Python 标准库，不引入 NumPy / pandas / 任何天文包 |
| 🌌 **真天文历算** | VSOP87D 636 项 + Meeus 月离表，实时反解节气与真朔 |
| 📅 **自研农历引擎** | 真朔定月、冬至定序、无中气置闰，含 2033 年闰十一月等特例 |
| 🧭 **完整排盘** | 十四主星 + 30 颗辅曜煞曜杂曜，共 44 颗星曜 |
| 🎨 **四化双轨** | 生年四化（先天定数）与宫干自化（后天不定数）分别标注 |
| 🖼️ **三种输出** | 终端四方格文本、SVG 矢量图、JSON 结构化数据 |
| ⏳ **大限排布** | 按五行局数起运，阳男阴女顺行、阴男阳女逆行 |
| 🧪 **强校验测试** | 150 组紫微定位表 + 2 张公开命盘 + 400 张随机盘压力测试 |
| 🌐 **三语文档** | 简体中文 / 繁體中文 / English，顶部可一键切换 |

---

## 🚀 三、快速开始

### 安装

```bash
pip install -e .            # 从源码安装（推荐开发用）
# 或
python -m build --wheel .   # 构建 wheel 后 pip install dist/*.whl
```

**运行时依赖：无。** `requirements.txt` 里没有任何必须安装的包。

### 一条命令排盘

```bash
python -m ziweiforge 1992-12-04 12:30
python -m ziweiforge 1992-12-04 午时 --gender female --svg chart.svg
python -m ziweiforge --lunar 1970-9-2 --hour 巳 --json
python -m ziweiforge 2025-02-03 22:10 --stars        # 只输出宫位→星曜表
```

安装后也可直接用控制台脚本：`ziweiforge 1992-12-04 12:30`

### 三行代码排盘

```python
from ziweiforge import build_chart, render_text

chart = build_chart(1992, 12, 4, 12, 30, gender="male")
print(chart.ming_palace.main_stars[0].label)   # 紫微(庙)权
print(render_text(chart))
```

---

## 🧩 四、使用示例

### 4.1 访问命盘对象

```python
from ziweiforge import build_chart
from ziweiforge.calendar import DI_ZHI

c = build_chart(1992, 12, 4, 12, 30)

c.lunar                  # 农历壬申年冬月十一
c.four_pillars           # ('壬申', '辛亥', '甲寅', '庚午')
c.ju_name                # '水二局'
DI_ZHI[c.ming_branch]    # '午'   命宫地支
DI_ZHI[c.body_branch]    # '午'   身宫地支
DI_ZHI[c.ziwei_branch]   # '午'   紫微星落宫
c.ming_zhu               # '破军' 命主星
c.si_hua                 # {'天梁': '化禄', '紫微': '化权', '左辅': '化科', '武曲': '化忌'}

c.palace("夫妻")         # 按宫名取宫位
c.palace("夫妻").stars   # 该宫星曜列表
c.by_branch(4)           # 按地支序号取宫位（辰=4）
```

### 4.2 导出 SVG

```python
from ziweiforge.render.svg import render_svg

with open("chart.svg", "w", encoding="utf-8") as fh:
    fh.write(render_svg(chart))
```

生成的 SVG 不依赖外部字体或库，可直接用浏览器打开、嵌入网页或打印。

### 4.3 导出 JSON

```python
from ziweiforge.cli import chart_to_json

print(chart_to_json(chart))
```

JSON 含十二宫的宫名、地支、干支、大限区间，以及每颗星的名称、是否主星、亮度与四化，
方便接入前端或其他系统。

### 4.4 用农历生日排盘

```python
from ziweiforge import build_from_lunar

# 农历 2023 年闰二月初十，午时
chart = build_from_lunar(2023, 2, 10, 6, is_leap=True)
```

### 4.5 只做历法换算

天文内核与农历模块可独立于排盘使用：

```python
from ziweiforge.calendar import from_solar, to_solar, LunarDate

from_solar(2025, 1, 29)            # 农历乙巳年正月初一
to_solar(LunarDate(2033, 11, 1, True))   # (2033, 12, 22) 闰冬月初一
```

---

## 🏗️ 五、项目结构

```
ZiweiForge/
├── ziweiforge/
│   ├── astro/              # 天文历算内核
│   │   ├── core.py         #   儒略日 / ΔT / 日月视黄经 / 节气 / 真朔
│   │   └── _vsop87.py      #   VSOP87D 太阳视黄经周期项（636 项，自动生成）
│   ├── calendar/           # 历法
│   │   ├── ganzhi.py       #   干支 / 纳音 / 五虎遁 / 五鼠遁
│   │   └── lunar.py        #   真朔定月、冬至定序、无中气置闰
│   ├── chart/              # 排盘
│   │   ├── constants.py    #   星曜名录、亮度表、四化表、安星歌诀数据
│   │   └── builder.py      #   命宫身宫 → 十二宫 → 五行局 → 安星 → 四化 → 大限
│   ├── render/             # 输出
│   │   ├── text.py         #   终端四方格版式
│   │   └── svg.py          #   SVG 矢量命盘
│   ├── cli.py              # 命令行入口
│   └── __main__.py         # python -m ziweiforge
├── tests/                  # 29 项自测（unittest，无需 pytest）
├── examples/               # 可运行示例
├── pyproject.toml
├── requirements.txt        # 运行时依赖：无
├── LICENSE                 # MIT
└── README.md / README.zh-TW.md / README.en.md
```

---

## 🔬 六、算法与精度

### 6.1 天文内核

| 环节 | 方法 | 误差 |
| --- | --- | --- |
| 太阳视黄经 | VSOP87D（636 项周期项）+ 光行差 + 章动 Δψ | — |
| 二分二至时刻 | 牛顿迭代反解黄经 | 与 pyephem 偏差 **≤ 0.44 分钟**（1900–2100，164 组） |
| 月亮视黄经 | Meeus Table 47.A（62 项）+ A1/A2 | — |
| 真朔（朔望） | 日月黄经差反解 | 与 pyephem 偏差 **≤ 1.4 分钟** |

### 6.2 农历编排

- **月界**：真朔所在的那一个**日历日**为初一（不是精确时刻）
- **月序**：冬至所在朔望月为十一月，上一年十一月往后第 2 个朔望月为正月
- **置闰**：13 个月时，第一个无中气的月份为闰月，并强制校验「冬至仍落十一月」
  （2033 年即典型反例，须顺延至闰十一月）

| 校验项 | 结果 |
| --- | --- |
| 春节日期（2015–2027） | **13 / 13 通过** |
| 闰月（2006/2009/2012/2014/2017/2020/2023/2025/2028/2033） | **10 / 10 通过** |
| 朔望月长度恒为 29 或 30 日 | 通过 |

### 6.3 排盘规则

全部遵循通行歌诀，实现前逐条核对：

- 命宫 / 身宫——「寅起正月，顺数至生月；逆数生时安命，顺数生时安身」
- 五行局——命宫干支纳音（水二 / 木三 / 金四 / 土五 / 火六局）
- 紫微星——「生日除局商为月，一自寅起紫微定；只加不减到整除，阳退阴进」
- 紫微系逆布、天府系顺布、紫府以寅申为轴对称
- 四化——「甲廉破武阳，乙机梁紫阴，丙同机昌廉……癸破巨阴贪」
- 六吉六煞、禄马羊陀、火铃空劫、鸾喜孤寡等 30 颗辅杂曜

> ⚠️ **关于星曜亮度**：`ziweiforge.chart.constants.BRIGHTNESS` 采用一套完整的
> 七级（庙旺得利平不陷）版本。各流派亮度表存在个别差异，如需切换可直接替换该字典。

---

## 🧪 七、测试与验证

```bash
make test          # 或 python -m unittest discover -s tests -v
```

29 项自测，全部通过，无需安装 pytest：

| 测试组 | 内容 | 结果 |
| --- | --- | --- |
| `test_astro` | 24 节气黄经反解自洽、节气日期、朔时刻日月黄经差 | 通过 |
| `test_astro` | 与 pyephem 交叉校验二分二至（未安装则跳过） | 偏差 ≤ 0.44 分钟 |
| `test_lunar` | 春节 13 例、闰月 10 例、公历↔农历往返、闰月往返 | 全部通过 |
| `test_chart` | **紫微定位表 150 组全表比对**（30 生日 × 5 局） | 150 / 150 |
| `test_chart` | 2 张公开命盘的十四主星逐宫比对 | 28 / 28 |
| `test_chart` | 结构不变量（主星不重不漏、紫府对称、十二宫逆布、大限连续） | 通过 |
| 压力测试 | 1901–2099 随机 400 张命盘 | 0 失败 |

**两张公开命盘的比对结果**

| 案例 | 公开命盘 | ZiweiForge |
| --- | --- | --- |
| 1970-10-01 10:10（庚戌年九月初二巳时） | 金四局，紫微在辰，天府在子 | ✅ 完全一致，14 颗主星逐宫吻合 |
| 1992-12-04 午时（壬申年十一月十一） | 水二局，命宫午、身宫午，紫微在午 | ✅ 完全一致，星曜落宫 100% 吻合 |

---

## 📄 八、许可与免责声明

- **许可证**：[MIT](./LICENSE)，可自由使用、修改与商用。
- **天文数据**：VSOP87 周期项为 IMCCE（法国天体力学与历算研究所）公开发布的天文常数
  （Bretagnon & Francou, 1988），月球理论取自 Meeus《Astronomical Algorithms》。
  二者均属公共科学常数，本项目仅以数值表形式引用，不包含任何第三方源代码。
- **免责声明**：本项目是历算与传统文化研究工具。紫微斗数属于传统文化范畴，
  其命理阐释不具备科学依据，所有输出仅供文化研究与程序验证参考，
  **请勿用于医疗、金融、法律等任何实际决策**。

---

<div align="center">

用真天文，排一张可验证的命盘。

</div>
