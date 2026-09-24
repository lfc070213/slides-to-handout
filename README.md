# slides-to-handout · 课件 → 详细讲义

> 把 PPT / PPTX / PDF 课件，变成一份**每一页都带原幻灯片对照、公式用 LaTeX 渲染、推导和例题补齐**的详细讲义 —— 一个 AI agent skill（Claude Code / Codex / Qoder 等通用）。

[效果](#效果) · [安装](#安装) · [用法](#用法) · [五步流水线](#五步流水线) · [noteskit API](#noteskit-api-速查) · [硬规矩](#排版与公式硬规矩) · [许可](#许可)

## 效果

输入一份 5 页课件，输出一份 9 页讲义：每页先放原幻灯片截图，再逐段讲解——推导过程分步写、结论公式加框突出、例题带敏感性分析。

![讲义正文页：原幻灯片对照 + 讲解 + 公式推导](examples/preview/page_004.png)

![讲义例题页：原幻灯片对照 + 分步代入 + 结论公式](examples/preview/page_008.png)

完整产出在 [`examples/`](examples/)：`示例_详细讲义.pdf`（可搜索）+ `示例_详细讲义_手机版.pdf`（到处能开）。

## 为什么需要它

用 AI 读课件，得到的通常是一份"摘要"：要点、结论、公式抄一遍，公式还常常是纯文本（`P0 = Div1/(r-g)`）。但读课件的人真正需要的是**推导过程**——这一步怎么来的、那个假设为什么必须成立、代入数字时发生了什么。

这个 skill 把"做讲义"这件事固化成流水线，并写死了几条踩坑换来的规矩：

- **绝不凭记忆写**：先逐页转写课件的真实内容（数字、人名、公式记号），再动笔，每个数字都能在源页里指出来；
- **公式一律 LaTeX 渲染**成图片，不接受纯文本/Unicode 公式；
- **每一页都贴原幻灯片**（82% 宽，宽窄都试过），读者不用来回切换文件；
- **交付两个 PDF**：可搜索的电脑版 + 文字转矢量轮廓的手机版（微信/手机阅读器不会乱码）。

## 安装

仓库本身就是 skill 目录，克隆到 agent 的 skills 目录即可（目录名建议用 `lecture-notes`，与 `SKILL.md` 里的 `name` 一致）：

```bash
git clone https://github.com/lfc070213/slides-to-handout.git ~/.claude/skills/lecture-notes   # Claude Code
git clone https://github.com/lfc070213/slides-to-handout.git ~/.codex/skills/lecture-notes    # Codex
git clone https://github.com/lfc070213/slides-to-handout.git ~/.qoder-cn/skills/lecture-notes # Qoder
```

任何会读 `SKILL.md` 的 agent 都能用：把仓库放进它的 skills 目录（或直接把仓库路径指给 agent）。

### 依赖

| 依赖 | 用途 | 安装 |
|---|---|---|
| python3 + `matplotlib` `weasyprint` `pymupdf` `Pillow` | 公式渲染、HTML→PDF、PDF 处理 | `pip3 install matplotlib weasyprint pymupdf pillow` |
| LibreOffice（`soffice`） | PPT/PPTX → PDF | macOS 装 [LibreOffice](https://www.libreoffice.org/)；Ubuntu `sudo apt install libreoffice-impress fonts-noto-cjk` |

Ubuntu 24.04 的 python3 需要 `--user --break-system-packages`；无桌面服务器上整套流程都能跑。

## 用法

对 agent 说一句就行：

> 把这份课件转成详细讲义，每页加原图对照，公式推导写详细。

agent 会按 `SKILL.md` 的五步流水线执行。也可以自己跑：

```bash
# 1. 课件 → 每页图片（pages/slide_NNN.png 看图用 / .jpg 内嵌用）
bash scripts/slides_to_pages.sh 课件.pptx 输出目录

# 2. 写内容脚本 gen_课件名_pdf.py（见 examples/gen_示例课件_pdf.py 模板）

# 3. 构建 HTML + PDF
python3 gen_课件名_pdf.py

# 4. 渲染指定页成 PNG，肉眼看排版（这一步不能省）
python3 scripts/preview_pdf.py 讲义.pdf 1 5 20 40

# 5. 出"到处都能打开"的轮廓版
python3 scripts/flatten_pdf.py 讲义.pdf 讲义_手机版.pdf
```

## 五步流水线

| 步骤 | 做什么 | 关键点 |
|---|---|---|
| 0. 核对源页 | 逐页转写课件的真实内容 | 绝不凭记忆写；页码多时派子代理分区转写再抽查；课件笔误显式标注，不默默改 |
| 1. 课件转图 | `slides_to_pages.sh` | LibreOffice 转 PDF，PyMuPDF 按 150 dpi 出 PNG + 压缩 JPG |
| 2. 写内容脚本 | `gen_*.py` 调 `noteskit` | 每页固定写法：`slide(页码, 标题)` + 讲解 + `deriv()` + `formula_boxed()` |
| 3. 构建 | `nk.build(...)` | 公式渲染成 PNG 内嵌 HTML，WeasyPrint 排版出 PDF |
| 4. 验证 | `preview_pdf.py` + 看图 | 必须真的看图：公式大小、超宽截断、孤行标题、半页空白 |
| 5. 轮廓版 | `flatten_pdf.py` | 文字转矢量轮廓，字体数必须为 0；代价是不可搜索，所以两个版本一起交付 |

## noteskit API 速查

| 调用 | 作用 |
|---|---|
| `init(slide_dir=, course_line=)` | 指定原页图片目录与页眉文字（必须先调一次） |
| `slide(页号, 标题)` / `slide_img(页号)` | 页标题条 + 原页对照图（整块不被分页拆开） |
| `formula(公式)` | 居中公式块；结尾 `\text{中文}` 自动搬到 HTML 里 |
| `formula_boxed(公式, 注)` | 黄框突出核心结论 |
| `formula_multi([...])` | 多行公式合成一张图 |
| `imath(公式)` | 行内数学（嵌在正文/推导步骤中间） |
| `dline(公式)` | 推导块内的居中公式行 |
| `deriv(标题, [步骤…])` | 蓝底推导块；步骤可写字符串或 `(标签, 内容)` |
| `p / note / bullets / table / divider / chart / img` | 正文段落、提示框、列表、表格、分隔线、图表占位、图片占位 |
| `cover / toc / part_title / section` | 封面、目录、部分扉页、小节标题 |
| `build(parts, html, pdf, title=, running_head=)` | 拼 HTML → WeasyPrint 出 PDF → 打印页数体积 |

> `chart / img` 是占位组件：原课件里的图表若不导出，就在讲义里写清"这张图画的是什么、说明什么"，不留空白。

## 排版与公式硬规矩

每条都是踩坑换来的，完整版在 [`SKILL.md`](SKILL.md)：

1. **matplotlib mathtext ≠ 完整 LaTeX**：`\boxed`、`\xrightarrow`、中文都不能直接渲染——`formula_boxed()` 用 CSS 边框模拟，中文拆到 HTML 层。
2. **图片像素 ≠ CSS 像素**：matplotlib 按 200 dpi 出图，放进 HTML 要乘 `96/200` 换算，否则行内公式大约 2 倍大。noteskit 已内置换算——不要绕过 `imath/formula` 自己写 `<img>`。
3. **分页控制只加在小块上**：`page-break-inside: avoid` 只用于 `.slide-block`（标题 + 原页图）、表格、公式行；加在推导块这种大块上会产生大片空白。
4. **原页对照图宽 82%**：再宽会把每页撑散，再窄看不清源页细节。
5. **交付物里的公式必须 LaTeX 渲染**，下标、希腊字母、分式一律走公式图。

## 跨平台可读性

- 代码/脚本/SKILL.md 用 **UTF-8 无 BOM**（带 BOM 会顶掉 shebang）；给"任何地方"打开的 HTML 用 **UTF-8 带 BOM**（`noteskit.build()` 已处理）。
- 正文与装饰**不用 emoji**（依赖 emoji 字体，换平台会变方块），只用 GB2312 内的符号 `※ 【】 ▲ ·`。
- WeasyPrint 的 PDF 用子集化字体 + Identity-H 编码，**部分手机/微信/网盘阅读器会误读成乱码**——这不是文件坏了，是查看器的锅。用第 5 步的轮廓版兜住，两个版本一起交付。

## 仓库结构

```
slides-to-handout/
├── SKILL.md                    # skill 定义（agent 读这个；含完整规则与检查清单）
├── README.md                   # 本文档
├── agents/openai.yaml          # Codex 界面元数据（可选）
├── scripts/
│   ├── noteskit.py             # 讲义构建工具包（公式渲染 / 版式积木 / 页面骨架）
│   ├── slides_to_pages.sh      # 课件 → 每页 PNG/JPG
│   ├── preview_pdf.py          # PDF 指定页 → PNG（肉眼检查排版）
│   └── flatten_pdf.py          # 文字转矢量轮廓，出手机版
└── examples/                   # 完整可复现示例（5 页课件 → 9 页讲义）
    ├── make_demo_deck.py       # 生成示例课件.pptx
    ├── gen_示例课件_pdf.py      # 讲义内容脚本（noteskit 全部用法的起手模板）
    ├── 示例课件.pptx
    ├── 示例_详细讲义.pdf / _手机版.pdf
    └── preview/                # README 用的页面截图
```

## 复现示例

```bash
cd examples
python3 make_demo_deck.py                              # 生成 示例课件.pptx
../scripts/slides_to_pages.sh 示例课件.pptx .           # 每页图片 → pages/
python3 gen_示例课件_pdf.py                             # 出 HTML + PDF
../scripts/preview_pdf.py 示例_详细讲义.pdf --all        # 看排版
../scripts/flatten_pdf.py 示例_详细讲义.pdf 示例_详细讲义_手机版.pdf
```

## 许可

[MIT](LICENSE)。示例课件与讲义内容（股利贴现模型、戈登增长模型的基础推导）为自编教学材料，可自由使用。
