<div align="center">

# 🔮 ZiweiForge

**零依賴 · 真天文曆算 · 紫微斗數排盤引擎**

[简体中文](./README.md) · [繁體中文](./README.zh-TW.md) · [English](./README.en.md)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)](./requirements.txt)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

</div>

---

## 📖 一、專案簡介

市面上的紫微斗數排盤函式庫，幾乎清一色內建一張**壓縮過的萬年曆查表**（節氣時刻表、
朔望時刻表），再把生日丟進去查表定位紫微星。這類實作很輕，但有三個繞不開的短板：
資料過期即失效、跨越表外年份直接崩潰、無法解釋「為什麼」。

**ZiweiForge 走的是另一條路**：不內建任何萬年曆資料，農曆月份、二十四節氣、朔望時刻
全部由自研天文核心**即時求解**。

- 太陽視黃經：採用 **VSOP87D** 行星理論，636 項週期項（IMCCE 公開發布的天文常數）
- 月亮視黃經：採用 Meeus《Astronomical Algorithms》第 47 章 Table 47.A
- 節氣與真朔：由牛頓迭代反解，計入 ΔT（TT−UT）、章動與光行差
- 農曆編排：以**真朔**定月、以**冬至**錨定十一月、以**無中氣**置閏；月序與中氣歸屬
  一律按中國標準時間（UTC+8）的**日曆日**口徑判定

於是它能在 1900–2100 區間內獨立復原農曆與節氣——不連網、不讀檔案、不裝任何套件。

> 本專案為曆算與傳統文化研究工具。所述命理內容僅作文化研究參考，不構成任何決策建議。

---

## ✨ 二、核心特色

| 特色 | 說明 |
| --- | --- |
| 🪶 **零依賴** | 僅用 Python 標準函式庫，不引入 NumPy / pandas / 任何天文套件 |
| 🌌 **真天文曆算** | VSOP87D 636 項 + Meeus 月離表，即時反解節氣與真朔 |
| 📅 **自研農曆引擎** | 真朔定月、冬至定序、無中氣置閏，含 2033 年閏十一月等特例 |
| 🧭 **完整排盤** | 十四主星 + 30 顆輔曜煞曜雜曜，共 44 顆星曜 |
| 🎨 **四化雙軌** | 生年四化（先天定數）與宮干自化（後天不定數）分別標註 |
| 🖼️ **三種輸出** | 終端四方格文字、SVG 向量圖、JSON 結構化資料 |
| ⏳ **大限排布** | 按五行局數起運，陽男陰女順行、陰男陽女逆行 |
| 🧪 **強校驗測試** | 150 組紫微定位表 + 2 張公開命盤 + 400 張隨機盤壓力測試 |
| 🌐 **三語文件** | 简体中文 / 繁體中文 / English，頂部可一鍵切換 |

---

## 🚀 三、快速開始

### 安裝

```bash
pip install -e .            # 從原始碼安裝（建議開發用）
# 或
python -m build --wheel .   # 建置 wheel 後 pip install dist/*.whl
```

**執行時依賴：無。** `requirements.txt` 裡沒有任何必須安裝的套件。

### 一條指令排盤

```bash
python -m ziweiforge 1992-12-04 12:30
python -m ziweiforge 1992-12-04 午時 --gender female --svg chart.svg
python -m ziweiforge --lunar 1970-9-2 --hour 巳 --json
python -m ziweiforge 2025-02-03 22:10 --stars        # 只輸出宮位→星曜表
```

安裝後也可直接用主控台指令：`ziweiforge 1992-12-04 12:30`

### 三行程式碼排盤

```python
from ziweiforge import build_chart, render_text

chart = build_chart(1992, 12, 4, 12, 30, gender="male")
print(chart.ming_palace.main_stars[0].label)   # 紫微(廟)權
print(render_text(chart))
```

---

## 🧩 四、使用範例

### 4.1 存取命盤物件

```python
from ziweiforge import build_chart
from ziweiforge.calendar import DI_ZHI

c = build_chart(1992, 12, 4, 12, 30)

c.lunar                  # 農曆壬申年冬月十一
c.four_pillars           # ('壬申', '辛亥', '甲寅', '庚午')
c.ju_name                # '水二局'
DI_ZHI[c.ming_branch]    # '午'   命宮地支
DI_ZHI[c.body_branch]    # '午'   身宮地支
DI_ZHI[c.ziwei_branch]   # '午'   紫微星落宮
c.ming_zhu               # '破軍' 命主星
c.si_hua                 # {'天梁': '化祿', '紫微': '化權', '左輔': '化科', '武曲': '化忌'}

c.palace("夫妻")         # 依宮名取宮位
c.palace("夫妻").stars   # 該宮星曜清單
c.by_branch(4)           # 依地支序號取宮位（辰=4）
```

### 4.2 匯出 SVG

```python
from ziweiforge.render.svg import render_svg

with open("chart.svg", "w", encoding="utf-8") as fh:
    fh.write(render_svg(chart))
```

產生的 SVG 不依賴外部字型或函式庫，可直接用瀏覽器開啟、嵌入網頁或列印。

### 4.3 匯出 JSON

```python
from ziweiforge.cli import chart_to_json

print(chart_to_json(chart))
```

JSON 含十二宮的宮名、地支、干支、大限區間，以及每顆星的名稱、是否主星、亮度與四化，
方便串接前端或其他系統。

### 4.4 以農曆生日排盤

```python
from ziweiforge import build_from_lunar

# 農曆 2023 年閏二月初十，午時
chart = build_from_lunar(2023, 2, 10, 6, is_leap=True)
```

### 4.5 只做曆法換算

天文核心與農曆模組可獨立於排盤使用：

```python
from ziweiforge.calendar import from_solar, to_solar, LunarDate

from_solar(2025, 1, 29)                     # 農曆乙巳年正月初一
to_solar(LunarDate(2033, 11, 1, True))      # (2033, 12, 22) 閏冬月初一
```

---

## 🏗️ 五、專案結構

```
ZiweiForge/
├── ziweiforge/
│   ├── astro/              # 天文曆算核心
│   │   ├── core.py         #   儒略日 / ΔT / 日月視黃經 / 節氣 / 真朔
│   │   └── _vsop87.py      #   VSOP87D 太陽視黃經週期項（636 項，自動生成）
│   ├── calendar/           # 曆法
│   │   ├── ganzhi.py       #   干支 / 納音 / 五虎遁 / 五鼠遁
│   │   └── lunar.py        #   真朔定月、冬至定序、無中氣置閏
│   ├── chart/              # 排盤
│   │   ├── constants.py    #   星曜名錄、亮度表、四化表、安星歌訣資料
│   │   └── builder.py      #   命宮身宮 → 十二宮 → 五行局 → 安星 → 四化 → 大限
│   ├── render/             # 輸出
│   │   ├── text.py         #   終端四方格版式
│   │   └── svg.py          #   SVG 向量命盤
│   ├── cli.py              # 命令列入口
│   └── __main__.py         # python -m ziweiforge
├── tests/                  # 29 項自測（unittest，無需 pytest）
├── examples/               # 可執行範例
├── pyproject.toml
├── requirements.txt        # 執行時依賴：無
├── LICENSE                 # MIT
└── README.md / README.zh-TW.md / README.en.md
```

---

## 🔬 六、演算法與精度

### 6.1 天文核心

| 環節 | 方法 | 誤差 |
| --- | --- | --- |
| 太陽視黃經 | VSOP87D（636 項週期項）+ 光行差 + 章動 Δψ | — |
| 二分二至時刻 | 牛頓迭代反解黃經 | 與 pyephem 偏差 **≤ 0.44 分鐘**（1900–2100，164 組） |
| 月亮視黃經 | Meeus Table 47.A（62 項）+ A1/A2 | — |
| 真朔（朔望） | 日月黃經差反解 | 與 pyephem 偏差 **≤ 1.4 分鐘** |

### 6.2 農曆編排

- **月界**：真朔所在的那一**日曆日**為初一（不是精確時刻）
- **月序**：冬至所在朔望月為十一月，上一年十一月往後第 2 個朔望月為正月
- **置閏**：13 個月時，第一個無中氣的月份為閏月，並強制校驗「冬至仍落十一月」
  （2033 年即典型反例，須順延至閏十一月）

| 校驗項 | 結果 |
| --- | --- |
| 春節日期（2015–2027） | **13 / 13 通過** |
| 閏月（2006/2009/2012/2014/2017/2020/2023/2025/2028/2033） | **10 / 10 通過** |
| 朔望月長度恆為 29 或 30 日 | 通過 |

### 6.3 排盤規則

全部遵循通行歌訣，實作前逐條核對：

- 命宮 / 身宮——「寅起正月，順數至生月；逆數生時安命，順數生時安身」
- 五行局——命宮干支納音（水二 / 木三 / 金四 / 土五 / 火六局）
- 紫微星——「生日除局商為月，一自寅起紫微定；只加不減到整除，陽退陰進」
- 紫微系逆布、天府系順布、紫府以寅申為軸對稱
- 四化——「甲廉破武陽，乙機梁紫陰，丙同機昌廉……癸破巨陰貪」
- 六吉六煞、祿馬羊陀、火鈴空劫、鸞喜孤寡等 30 顆輔雜曜

> ⚠️ **關於星曜亮度**：`ziweiforge.chart.constants.BRIGHTNESS` 採用一套完整的
> 七級（廟旺得利平不陷）版本。各流派亮度表存在個別差異，如需切換可直接替換該字典。

---

## 🧪 七、測試與驗證

```bash
make test          # 或 python -m unittest discover -s tests -v
```

29 項自測，全部通過，無需安裝 pytest：

| 測試組 | 內容 | 結果 |
| --- | --- | --- |
| `test_astro` | 24 節氣黃經反解自洽、節氣日期、朔時刻日月黃經差 | 通過 |
| `test_astro` | 與 pyephem 交叉校驗二分二至（未安裝則跳過） | 偏差 ≤ 0.44 分鐘 |
| `test_lunar` | 春節 13 例、閏月 10 例、公曆↔農曆往返、閏月往返 | 全部通過 |
| `test_chart` | **紫微定位表 150 組全表比對**（30 生日 × 5 局） | 150 / 150 |
| `test_chart` | 2 張公開命盤的十四主星逐宮比對 | 28 / 28 |
| `test_chart` | 結構不變量（主星不重不漏、紫府對稱、十二宮逆布、大限連續） | 通過 |
| 壓力測試 | 1901–2099 隨機 400 張命盤 | 0 失敗 |

**兩張公開命盤的比對結果**

| 案例 | 公開命盤 | ZiweiForge |
| --- | --- | --- |
| 1970-10-01 10:10（庚戌年九月初二巳時） | 金四局，紫微在辰，天府在子 | ✅ 完全一致，14 顆主星逐宮吻合 |
| 1992-12-04 午時（壬申年十一月十一） | 水二局，命宮午、身宮午，紫微在午 | ✅ 完全一致，星曜落宮 100% 吻合 |

---

## 📄 八、授權與免責聲明

- **授權條款**：[MIT](./LICENSE)，可自由使用、修改與商用。
- **天文資料**：VSOP87 週期項為 IMCCE（法國天體力學與曆算研究所）公開發布的天文常數
  （Bretagnon & Francou, 1988），月球理論取自 Meeus《Astronomical Algorithms》。
  二者均屬公共科學常數，本專案僅以數值表形式引用，不包含任何第三方原始碼。
- **免責聲明**：本專案是曆算與傳統文化研究工具。紫微斗數屬傳統文化範疇，
  其命理闡釋不具備科學依據，所有輸出僅供文化研究與程式驗證參考，
  **請勿用於醫療、金融、法律等任何實際決策**。

---

<div align="center">

用真天文，排一張可驗證的命盤。

</div>
