---
name: lecture-notes
description: 把课件（PPT/PPTX/PDF）转换成图文并茂的详细讲义（HTML + PDF）：逐页嵌入原幻灯片对照图、公式一律用 LaTeX 渲染、补详细推导与例题。当用户说"课件转讲义""做详细笔记/精读""每页加原图对照""补公式推导"时使用。
---

# 课件 → 详细讲义

## 何时用

- 用户给一份课件（.pptx / .ppt / .pdf），要"详细讲义 / 精读 / 笔记 / 预习材料"。
- 明确要求"每一页加原界面（原幻灯片）对照""公式推导要详细"时走完整流程。
- 产出：`<课件名>_详细讲义.html`（中间产物，浏览器可直接看）+ `.pdf`（交付物，全图文、公式为 LaTeX 渲染）。

## 依赖

- python3：`matplotlib`、`weasyprint`、`pymupdf`、`Pillow`（`python3 -c "import matplotlib, weasyprint, pymupdf, PIL"`）
- LibreOffice：`soffice`（macOS 在 `/Applications/LibreOffice.app/Contents/MacOS/soffice`，也常见于 `/opt/homebrew/bin`）
- 缺包时先装：`pip3 install matplotlib weasyprint pymupdf pillow`（Ubuntu 24.04 的 python3 需加 `--user --break-system-packages`）
- 也能在无桌面 Linux 服务器上整套跑（pip 包 + `libreoffice-impress` + `fonts-noto-cjk` 即可，四步全部本地完成）；实测 103 页课件转图 34 s、讲义构建 23 s、轮廓化 0 残留字体。`failed to launch javaldx` 和 libpng iCCP 警告无害；中文经 fontconfig 回退到 Noto Sans CJK，公式由 matplotlib 自带字体渲染，与 macOS 端一致。

## 四步流水线（按序执行，不要跳步）

### 第 0 步：核对源页内容 —— 绝不凭记忆写（最重要）

先落盘每页的"真实内容"，再动笔写讲解。踩过的坑：凭印象举例，把课件里的公司名/数字写错（把 A 公司的例题写成 B 公司、把 12% 写成 10%），全篇都要返工。

- 页码少：`pages/slide_NNN.png` 用 Read 工具直接看图，逐页记录关键数字、人名、公司名、公式记号。
- 页码多（>30）：派子代理按区间逐页转写（如"第 5-41 页，每页列出标题、全部数字、公式、专有名词"），自己再抽查几页核对。
- 课件本身的笔误**不要默默改**：在讲义对应处标注"原课件此处疑似笔误（按上下文应为 …）"。
- 讲义里出现的每个数字都要能在源页里指出来。

### 第 1 步：课件 → 每页图片

```bash
scripts/slides_to_pages.sh <课件.pptx|pdf> <输出目录> [dpi=150]
# 产出 <输出目录>/pages/slide_NNN.png（看图用）与 slide_NNN.jpg（讲义内嵌用，体积小）
```

### 第 2 步：写内容脚本

新建 `gen_<课件名>_pdf.py`，开头引入 noteskit（路径指向本 skill 的 scripts 目录）：

```python
import sys
sys.path.insert(0, "<本 skill>/scripts")
import noteskit as nk

nk.init(slide_dir="<输出目录>/pages", course_line="公司金融 · 第三课")
parts = [nk.cover("公司金融 Corporate Finance", "第三课：股票估值", "北京大学光华管理学院 · 徐信忠 教授", "（详细讲义 · 共 103 页幻灯片逐页精解）")]
parts.append(nk.toc([("第一部分 …（第 1-41 页）", ["…", "…"])]))

parts.append(nk.part_title("一", "估值理论与方法"))
parts.append(nk.slide(7, "股利贴现模型"))
parts.append(nk.p("…讲解…"))
parts.append(nk.deriv("推导：Gordon 增长模型", [
    ("第 1 步", "由股利贴现公式 " + nk.imath(r"$P_0=\sum \frac{Div_t}{(1+r_E)^t}$") + " 出发"),
    nk.dline(r"$P_0=\frac{Div_1}{r_E-g}$"),
]))
parts.append(nk.formula_boxed(r"$P_0=\frac{Div_1}{r_E-g}$", "核心结论"))
nk.build(parts, "讲义.html", "讲义.pdf", title="公司金融 第三课 详细讲义", running_head="公司金融 · 第三课")
```

每页的固定写法：`nk.slide(页码, 标题)` 给"标题条 + 原页对照图"（自动成对、不被分页拆开），随后接讲解、`nk.deriv()` 推导块、`nk.formula()/formula_boxed()` 结论公式、`nk.note()` 提示、`nk.table()/bullets()`。一页讲不完就多写几段，不要为省篇幅牺牲推导。

### 第 3 步：构建

```bash
python3 gen_<课件名>_pdf.py     # 打印 HTML 体积、PDF 体积与页数
```

### 第 4 步：验证（必须真的看图，不能只看页数）

```bash
python3 scripts/preview_pdf.py <讲义.pdf> 1 5 20 40   # 渲染成 PNG
# 然后用 Read 工具打开这些 PNG 逐一看：公式大小与正文协调、没有超宽截断、
# 页脚页码在、标题条没被留在页底、没有半页空白
```

- 交付前跑一遍完整检查清单（见文末）。
- 页数参考：103 页课件 → 122 页讲义（原页对照 + 详细推导）；若页数异常少，通常是分页规则把内容挤没了。

### 第 5 步：出"到处都能打开"的可分享版（别跳过）

WeasyPrint 出的 PDF 文字是**子集化字体 + Identity-H 编码**：正文流里存的是**原字体的 glyph ID**，靠内嵌字体表查回字形。主流阅读器（MuPDF、Chromium/PDFium、Adobe、macOS 预览）都按规范渲染，但**部分手机阅读器 / 微信内置预览 / 网盘预览会跳过内嵌字体表，把 glyph ID 直接当 Unicode 码位**画出来——字母整体右移（"Corporate Finance" → "Eqt r qtcv g Hkpcpeg"）、中文空白或乱码。这不是文件坏了，是查看器的锅；但交付物在别人手里，只能自己兜住。

根治办法是把文字**转成矢量轮廓**（页面里不再有任何字体，也就无从误解码）：

```bash
python3 scripts/flatten_pdf.py <讲义.pdf> <讲义_手机版.pdf>
# 打印 "N/N 页, X MB, 剩余字体数 0（应为 0）"——字体数必须为 0，不为 0 就是没转干净
python3 scripts/preview_pdf.py <讲义_手机版.pdf> 1 20 <末页号>   # 再肉眼核一遍（封面/公式页/末页）
```

- 代价：轮廓版**文字不能选中/搜索/复制**（只剩线条，没有字符信息）。
- 所以**两个都交付**：`<课件名>_详细讲义.pdf`（可搜索，电脑上用）+ `<课件名>_详细讲义_手机版.pdf`（到处能开，手机/转发用），并在交付说明里讲清区别。
- 不要试图用整字体内嵌绕过（`weasyprint` 的 `full_fonts=True`）：PingFang 这类中文字体整套内嵌后 4 页就 246 MB，不可用。

## noteskit API 速查

| 调用 | 作用 |
|---|---|
| `init(slide_dir=, course_line=)` | 指定原页图片目录与页眉文字（必须先调一次） |
| `slide(页号, 标题)` | 页标题条 + 原页对照图（`.slide-block` 整块不拆页） |
| `slide_img(页号)` | 只要原页对照图 |
| `formula(公式)` | 居中公式块；结尾 `\text{中文}` 自动搬到 HTML 里 |
| `formula_boxed(公式, 注)` | 黄框突出核心结论 |
| `formula_multi([...])` | 多行公式合成一张图 |
| `imath(公式)` | 行内数学（嵌在正文/推导步骤中间） |
| `dline(公式)` | 推导块内的居中公式行 |
| `deriv(标题, [步骤…])` | 蓝底推导块；步骤可写字符串或 `(标签, 内容)` |
| `p / note / bullets / table / divider / chart / img` | 正文段落、提示框、列表、表格、分隔线、图表占位、图片占位 |
| `cover / toc / part_title / section` | 封面、目录、部分扉页、小节标题 |
| `build(parts, html, pdf, title=, running_head=)` | 拼 HTML → weasyprint 出 PDF → 打印页数体积 |

## 排版与公式硬规矩（每条都是踩坑换来的）

1. **matplotlib mathtext ≠ 完整 LaTeX**：
   - 不支持 `\boxed{}` → 用 `nk.formula_boxed()`（CSS 边框实现）
   - 不支持 `\xrightarrow{}` → 用 `\to`（如 `(N \to \infty)`）
   - **不能渲染中文**（报 `Font 'rm' does not have a glyph`）→ 结尾的 `\text{中文}` 由 `formula()` 自动处理；公式开头/中间有中文要手工拆成 HTML + `nk.imath()` 组合
   - 公式字符串里不要出现中文以外的生僻宏；报 `Unknown symbol` 就查 mathtext 支持列表
2. **图片像素 ≠ CSS 像素**（最容易犯的错）：matplotlib 以 200 DPI 出图，若按"1 图 px = 1 CSS px"放进 HTML，行内公式会**大约 2 倍**。noteskit 已按 `_CSS_SCALE = 96/DPI` 换算并输出 `width:xx px`——**不要绕过 `imath/dline/formula` 自己写 `<img>`**。
3. **分页控制只加在小块上**：`page-break-inside: avoid` 只用于 `.slide-block`（标题+原页图）、表格、公式行。加在 `.deriv` 这样的大块上会产生大片空白（曾把 131 页挤成 120 页的假象）。
4. 原页对照图宽 `82%`（CSS 里已定）：再宽会把每页撑散，再窄看不清源页细节。
5. **交付物里的公式必须 LaTeX 渲染**（硬性要求），不接受纯文本/Unicode 公式；下标、希腊字母、分式一律走公式图。
6. `.formula` 内的图片自带 `max-width:100%`，长公式不会被裁掉，但超过一行的公式建议拆成 `formula_multi` 多行。

## 编码与跨平台可读性

- **代码、脚本、SKILL.md 一律 UTF-8 无 BOM**：带 BOM 会顶掉 shell 的 shebang（`#!/usr/bin/env bash` 失效），也可能让 skill frontmatter 的 `---` 解析失败。
- **交付给"任何地方"打开的 HTML 写 UTF-8 带 BOM**（`noteskit.build()` 已用 `utf-8-sig`），文件头另有 `<meta charset="UTF-8">`。Windows 老记事本/WPS 一类按 GBK 猜编码的工具靠 BOM 才能正确识别，否则中文全乱。
- **正文与装饰不用 emoji**（💡📊 这类依赖 emoji 字体，换机器/换平台会显示成方块）；只用 GB2312 范围内的符号：`※ 【】 ▲ ·` 等。
- PDF/docx 是自包含容器，不依赖外部文件，但**内嵌字体可能被个别手机查看器误读**——若 PDF 在别人手机上乱码（字母整体错位、中文空白），不要怀疑内容，直接走"第 5 步"出轮廓版；自己在 MuPDF/Chromium 里看到的正常不代表对方正常。
- 给 Windows 用户的纯文本/表格导出（.txt/.csv）也应带 BOM：`open(path, "w", encoding="utf-8-sig")`。

## 交付前检查清单

- [ ] `preview_pdf.py` 渲染首页、若干正文页、末页，**肉眼看过**：公式大小协调、无截断、无孤行标题、无半页空白
- [ ] 抽查 3-5 页与源页对照：数字、人名、公司名、记号一致（第 0 步的纪律）
- [ ] 源课件的笔误已显式标注
- [ ] 目录页页码区间与正文一致
- [ ] 打印出的页数/体积合理（对照源课件页数，一般 1.1-1.6 倍）
- [ ] 已跑 `flatten_pdf.py` 出手机版（打印"剩余字体数 0"），且抽查过渲染；两个 PDF 一起交付、说明用途区别
- [ ] 文件命名：`<课件名>_详细讲义.pdf`（可搜索）+ `<课件名>_详细讲义_手机版.pdf`（轮廓版），放课件同目录或用户指定位置

## 完整示例

`examples/` 里有一个从零跑通的完整示例：`示例课件.pptx`（5 页）→ `gen_示例_讲义.py` → `示例_详细讲义.pdf` + `示例_详细讲义_手机版.pdf`，包含封面、目录、逐页原图对照、公式渲染、推导块与例题的全部写法，可作为新讲义的起手模板。
