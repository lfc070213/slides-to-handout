#!/usr/bin/env python3
"""noteskit — 课件转详细讲义的 HTML/PDF 构建工具包。

设计要点（都是实战踩坑后的结论，改动前先读 SKILL.md 的「排版与公式」一节）：
  * 公式一律用 matplotlib mathtext 渲染成 PNG，再以 base64 内嵌进 HTML，最后由
    weasyprint 排版成 PDF。mathtext 不是完整 LaTeX，见 _precheck()。
  * matplotlib 按 RENDER_DPI(=200) 出图，而 CSS px 与 pt 是 96dpi 口径，
    所以图片像素要乘 96/DPI 才是正确的 CSS 宽度；否则行内公式会大约 2 倍。
  * 分页控制只加在小块（.slide-block：标题+原页图）上，大块加 avoid 会出现大片空白。

用法：
    import noteskit as nk
    nk.init(slide_dir="/abs/path/pages", course_line="公司金融 · 第三课")
    parts = [nk.cover(...), nk.toc(...)]
    parts += [nk.slide(7, "…"), nk.p("…"), nk.formula(r"$P_0=\\frac{Div_1}{r-g}$")]
    nk.build(parts, "讲义.html", "讲义.pdf", title="公司金融 第三课 详细讲义")
"""

import base64
import io
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RENDER_DPI = 200
_CSS_SCALE = 96.0 / RENDER_DPI  # 图片像素 → CSS 像素（96dpi 口径）

_SLIDE_IMG_DIR = None
_SLIDE_CACHE = {}
_PAGE_TITLE = "详细讲义"
_PAGE_RUNNING_HEAD = ""

# 当前目录（供内容脚本 sys.path.insert 后 import 用）
HERE = os.path.dirname(os.path.abspath(__file__))


def init(slide_dir=None, page_title=None, course_line=None):
    """设置原幻灯片目录（含 slide_NNN.jpg）与页眉文字。"""
    global _SLIDE_IMG_DIR, _PAGE_TITLE, _PAGE_RUNNING_HEAD
    if slide_dir is not None:
        _SLIDE_IMG_DIR = slide_dir
    if page_title is not None:
        _PAGE_TITLE = page_title
    if course_line is not None:
        _PAGE_RUNNING_HEAD = course_line


# ─────────────────────────── LaTeX 渲染 ───────────────────────────

_UNSUPPORTED = {
    r"\boxed": "mathtext 不支持 \\boxed；改用 formula_boxed()（CSS 边框实现）",
    r"\xrightarrow": "mathtext 不支持 \\xrightarrow；改用 \\to（如 (N \\to \\infty)）",
    r"\text{中文}": "mathtext 不能渲染 CJK；把中文拆到 HTML 里（formula() 会自动处理结尾的 \\text{中文}）",
}


def _precheck(latex_str):
    for macro, hint in _UNSUPPORTED.items():
        if macro in latex_str and macro != r"\text{中文}":
            raise ValueError(f"{hint}\n  公式：{latex_str}")
    if re.search(r"[\u4e00-\u9fff]", latex_str):
        raise ValueError(
            "公式含中文字符，matplotlib mathtext 无法渲染（会报 Font 'rm' does not have a glyph）。\n"
            "  处理办法：结尾的 \\text{中文} 交给 formula() 自动转换；"
            "公式中间的中文请手工拆成 HTML + imath() 组合。\n"
            f"  公式：{latex_str}"
        )


def _normalize(latex_str):
    """裸数学串自动补 $...$（matplotlib 只对 $...$ 内的内容按数学排版）。"""
    s = latex_str.strip()
    if "$" not in s:
        s = f"${s}$"
    return s


def render_latex(latex_str, fontsize=17, bg_color="#f0f4ff", border_color="#c8d4f0"):
    """渲染公式，返回 (data_uri, css_width, css_height)。注：只能传纯数学，不含中文。"""
    latex_str = _normalize(latex_str)
    _precheck(latex_str)
    fig, ax = plt.subplots(figsize=(0.01, 0.01))
    ax.text(
        0.5, 0.5, latex_str, fontsize=fontsize, ha="center", va="center",
        transform=ax.transAxes, color="#1a2a6c",
        bbox=dict(boxstyle="round,pad=0.45", facecolor=bg_color,
                  edgecolor=border_color, linewidth=1.2, alpha=0.95),
    )
    ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=RENDER_DPI, bbox_inches="tight",
                pad_inches=0.12, facecolor="white", edgecolor="none")
    plt.close(fig)
    raw = buf.getvalue()
    from PIL import Image as _PILImage
    with _PILImage.open(io.BytesIO(raw)) as _im:
        w_px, h_px = _im.size
    b64 = base64.b64encode(raw).decode()
    return f"data:image/png;base64,{b64}", w_px * _CSS_SCALE, h_px * _CSS_SCALE


def _sized_img(latex_str, fontsize=12, bg_color="#f0f4ff", border_color="#c8d4f0",
               cls="formula-img", extra_style=""):
    """渲染公式并输出带正确 CSS 宽度的 <img>（不要手写 <img> 绕过这里）。"""
    uri, w, _h = render_latex(latex_str, fontsize=fontsize,
                              bg_color=bg_color, border_color=border_color)
    style = f"width:{w:.1f}px;{extra_style}"
    return f'<img src="{uri}" class="{cls}" style="{style}">'


def formula(latex_str, **kwargs):
    """居中显示的公式块。结尾的 \\text{中文} 自动搬到 HTML <span> 里。

    兼容三种写法（是否带外层 $ 都行）：
        r"$P_0=\\frac{Div_1}{r_E-g}\\quad \\text{戈登公式}$"
        r"P_0=\\frac{Div_1}{r_E-g}"          # 裸数学，自动补 $
    """
    s = latex_str.strip()
    m = re.search(r"\\text\{([^}]*[\u4e00-\u9fff][^}]*)\}\$?\s*$", s)
    suffix = ""
    core = s
    if m:
        suffix = m.group(1)
        core = s[: m.start()].rstrip()
        if core.endswith("$"):          # "$…\text{中文}$" → 去掉收尾 $
            core = core[:-1].rstrip()
        if "$" in core and not core.endswith("$"):   # "$…\quad" → 补回 $
            core = core + "$"
    html = '<div class="formula">' + _sized_img(core, **kwargs)
    if suffix:
        html += f'<span class="formula-suffix"> {suffix}</span>'
    return html + "</div>"


def formula_boxed(latex_str, annotation=None, **kwargs):
    """加粗突出（黄色描边）的核心结论公式；annotation 为公式下的斜体小注。"""
    inner = re.sub(r"^\$?\\boxed\{(.*)\}\$?$", r"\1", latex_str).strip()
    if not inner.startswith("$"):
        inner = "$" + inner + "$"
    kwargs.pop("bg_color", None)
    kwargs.pop("border_color", None)
    inner_html = _sized_img(inner, bg_color="#fff8e1", border_color="#f0c040", **kwargs)
    html = f'<div class="formula formula-box">{inner_html}</div>'
    if annotation:
        html += f'<div class="formula-annotation">{annotation}</div>'
    return html


def formula_multi(lines, fontsize=15, **kwargs):
    """多行公式合并成一张图（各行为纯数学）。"""
    combined = r"\begin{array}{l} " + r" \\ ".join(lines) + r" \end{array}"
    return formula(combined, fontsize=fontsize, **kwargs)


def imath(latex_str, fontsize=11):
    """行内数学（嵌在正文/推导步骤里）。"""
    return _sized_img(latex_str, fontsize=fontsize, bg_color="none", border_color="none",
                      extra_style="display:inline-block;vertical-align:-0.35em;margin:0 1.5pt;")


def dline(latex_str, fontsize=13):
    """推导块内部的居中公式行。"""
    return ('<div class="formula" style="margin:5pt 0;">'
            + _sized_img(latex_str, fontsize=fontsize,
                         bg_color="#ffffff", border_color="#dde4f0") + "</div>")


# ─────────────────────────── 原页对照 ───────────────────────────

def slide_img(num):
    """第 num 页原幻灯片图片（base64 内嵌，优先 .jpg）。"""
    if num in _SLIDE_CACHE:
        return _SLIDE_CACHE[num]
    if not _SLIDE_IMG_DIR:
        raise RuntimeError("未设置幻灯片目录：先调用 noteskit.init(slide_dir=...)")
    path = None
    for ext in ("jpg", "png"):
        p = os.path.join(_SLIDE_IMG_DIR, f"slide_{num:03d}.{ext}")
        if os.path.exists(p):
            path = p
            break
    if path is None:
        return f'<div class="slide-ref"><div class="cap">（缺少第 {num} 页原图）</div></div>'
    mime = "jpeg" if path.endswith(".jpg") else "png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    html = (f'<div class="slide-ref"><img src="data:image/{mime};base64,{b64}">'
            f'<div class="cap">▲ 原幻灯片 第 {num} 页</div></div>')
    _SLIDE_CACHE[num] = html
    return html


def slide(num, title, show_original=True):
    """页标题 + 原页对照图，包在 .slide-block 里保证不被分页拆开。"""
    hd = f'<div class="slide-hd">第 {num} 页 &nbsp; {title}</div>'
    if show_original:
        return f'<div class="slide-block">{hd}{slide_img(num)}</div>'
    return hd


# ─────────────────────────── 版式积木 ───────────────────────────

def cover(main_title, subtitle, author, note=""):
    n = f'<div class="note">{note}</div>' if note else ""
    return f"""
    <div class="cover">
      <h1>{main_title}</h1>
      <div class="line"></div>
      <div class="subtitle">{subtitle}</div>
      <div class="author">{author}</div>
      {n}
    </div>
    """


def toc(groups):
    """groups: [(小标题, [条目, ...]), ...]，首页目录页。"""
    out = ['<div class="toc"><h2>目 录</h2>']
    for head, items in groups:
        out.append(f'<div class="toc-part">{head}</div><ul>')
        out += [f"<li>{it}</li>" for it in items]
        out.append("</ul>")
    out.append("</div>")
    return "".join(out)


def part_title(num_cn, name, desc=""):
    d = f'<div class="desc">{desc}</div>' if desc else ""
    return (f'<div class="part-title"><div class="num">{num_cn}</div>'
            f'<div class="name">{name}</div>{d}</div>')


def section(title):
    return f'<h2 class="section">{title}</h2>'


def deriv(title, steps):
    """推导块。steps 元素为 str 或 (标签, 内容) 元组。"""
    out = [f'<div class="deriv"><div class="deriv-title">{title}</div>']
    for s in steps:
        if isinstance(s, tuple):
            out.append(f'<div class="deriv-step"><span class="lbl">{s[0]}</span>{s[1]}</div>')
        else:
            out.append(f'<div class="deriv-step">{s}</div>')
    out.append("</div>")
    return "".join(out)


def p(text):
    return f"<p>{text}</p>"


def note(text):
    return f'<div class="note">{text}</div>'


def chart(desc):
    """图表占位（原课件有图但未导出时用，讲清该图画的是什么）。"""
    return f'<div class="chart-ph">{desc}</div>'


def img(desc):
    return f'<div class="img-ph">{desc}</div>'


def bullets(items):
    lines = []
    for it in items:
        if isinstance(it, tuple):
            lines.append(f'<li class="sub">{it[0]}</li>')
        else:
            lines.append(f"<li>{it}</li>")
    return '<ul class="bullets">' + "".join(lines) + "</ul>"


def table(headers, rows, cls=""):
    h = "".join(f"<th>{x}</th>" for x in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table>'


def divider():
    return '<div class="divider"></div>'


# ─────────────────────────── 页面骨架 ───────────────────────────

HTML_HEAD = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>__TITLE__</title>
<style>
  @page {
    size: A4;
    margin: 2.2cm 2cm 2.2cm 2.5cm;
    @bottom-center { content: counter(page); font: 9pt 'PingFang SC','Helvetica Neue',sans-serif; color: #999; }
    @top-right     { content: "__RUNNING_HEAD__"; font: 8pt 'PingFang SC',sans-serif; color: #bbb; }
  }
  @page :first { @bottom-center { content: none; } @top-right { content: none; } }

  html { font-size: 11pt; }
  body {
    font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
    color: #1a1a2e; line-height: 1.75; margin: 0; padding: 0;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }

  /* 封面 */
  .cover { page-break-after: always; text-align: center; padding-top: 18vh; }
  .cover h1 { font-size: 28pt; font-weight: 700; color: #1a1a2e; letter-spacing: 2pt; margin-bottom: 8pt; }
  .cover .subtitle { font-size: 18pt; color: #4a4a8a; margin-bottom: 24pt; }
  .cover .author  { font-size: 13pt; color: #666; margin-bottom: 6pt; }
  .cover .note    { font-size: 11pt; color: #999; margin-top: 48pt; }
  .cover .line    { width: 120pt; height: 2pt; background: linear-gradient(90deg,#4a4a8a,#8a8aca); margin: 24pt auto; border-radius: 1pt; }

  /* 目录 */
  .toc { page-break-after: always; }
  .toc h2 { font-size: 18pt; color: #1a1a2e; border-bottom: 2pt solid #4a4a8a; padding-bottom: 6pt; margin-bottom: 16pt; }
  .toc-part { font-size: 12pt; font-weight: 700; color: #333; margin: 14pt 0 6pt; }
  .toc ul { list-style: none; padding-left: 12pt; margin: 0 0 12pt; }
  .toc li { font-size: 10.5pt; color: #555; padding: 3pt 0; border-bottom: 1px dotted #ddd; }

  /* 部分扉页 */
  .part-title {
    page-break-before: always; page-break-after: always;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    min-height: 60vh; text-align: center;
  }
  .part-title .num  { font-size: 48pt; font-weight: 200; color: #4a4a8a; opacity: 0.4; }
  .part-title .name { font-size: 22pt; font-weight: 700; color: #1a1a2e; margin-top: -12pt; }
  .part-title .desc { font-size: 11pt; color: #888; margin-top: 12pt; max-width: 70%; }

  h2.section {
    font-size: 16pt; font-weight: 700; color: #1a1a2e;
    border-left: 4pt solid #4a4a8a; padding-left: 12pt; margin: 28pt 0 14pt;
    page-break-after: avoid;
  }

  /* 页标题条 + 原页对照图：整块不被拆页（小块才加 avoid！） */
  .slide-hd {
    font-size: 12pt; font-weight: 700; color: #fff;
    background: linear-gradient(135deg, #4a4a8a 0%, #6a6aba 100%);
    padding: 6pt 14pt; border-radius: 4pt; margin: 18pt 0 10pt;
    page-break-after: avoid; display: inline-block;
  }
  .slide-block { page-break-inside: avoid; margin-bottom: 10pt; }
  .slide-ref { margin: 0 0 4pt; text-align: center; }
  .slide-ref img {
    width: 82%; max-width: 82%; height: auto;
    border: 1pt solid #c8c8d8; border-radius: 4pt;
    box-shadow: 0 2pt 6pt rgba(74,74,138,0.12);
  }
  .slide-ref .cap { font-size: 9pt; color: #999; margin-top: 3pt; font-style: italic; }

  /* 推导块 */
  .deriv {
    background: #f7f9fc; border: 1pt solid #d8e0f0; border-radius: 5pt;
    padding: 10pt 16pt; margin: 10pt 0;
  }
  .deriv-title {
    font-size: 11pt; font-weight: 700; color: #2a3a7a; margin-bottom: 6pt;
    border-bottom: 1pt dashed #b8c4e0; padding-bottom: 4pt;
  }
  .deriv-step { font-size: 10.5pt; color: #333; margin: 5pt 0; line-height: 1.6; }
  .deriv-step .lbl { display: inline-block; min-width: 46pt; font-weight: 600; color: #4a4a8a; }
  .deriv .formula { margin: 6pt 0; }

  p { margin: 6pt 0; text-align: justify; }

  /* 公式（内容是 <img>） */
  .formula { margin: 10pt 0; text-align: center; page-break-inside: avoid; }
  .formula-img { max-width: 100%; height: auto; }
  .formula-suffix { font-size: 12pt; color: #1a2a6c; font-weight: 500; vertical-align: middle; margin-left: 4pt; }
  .formula-box { display: inline-block; border: 2.5px solid #f0c040; border-radius: 8px; padding: 8px 16px; background: #fffdf5; }
  .formula-annotation { text-align: center; font-size: 10.5pt; color: #666; margin-top: 4pt; font-style: italic; }

  /* 注意：装饰标记只用 GB2312 内的符号（※【】▲），不用 emoji——
     emoji 依赖 emoji 字体，Windows/Linux/手机渲染结果不可控，会显示成方块。 */
  .note {
    background: #fff8e1; border-left: 3pt solid #f0c040; border-radius: 0 4pt 4pt 0;
    padding: 8pt 14pt; margin: 10pt 0; font-size: 10pt; color: #8B6914;
    page-break-inside: avoid;
  }
  .note::before { content: "※ "; font-weight: 700; }

  .chart-ph {
    background: #e8f5e9; border: 1pt dashed #81c784; border-radius: 4pt;
    padding: 10pt 14pt; margin: 10pt 0; text-align: center;
    font-size: 10pt; color: #2E7D32; page-break-inside: avoid;
  }
  .chart-ph::before { content: "【图表】"; font-weight: 700; }
  .img-ph {
    background: #f3e5f5; border: 1pt dashed #ba68c8; border-radius: 4pt;
    padding: 10pt 14pt; margin: 10pt 0; text-align: center;
    font-size: 10pt; color: #7B1FA2; page-break-inside: avoid;
  }
  .img-ph::before { content: "【图片】"; font-weight: 700; }

  ul.bullets { padding-left: 20pt; margin: 6pt 0; }
  ul.bullets li { margin: 3pt 0; font-size: 10.5pt; }
  ul.bullets li.sub { list-style: none; margin-left: 16pt; }
  ul.bullets li.sub::before { content: "– "; color: #999; }

  table {
    border-collapse: collapse; width: 100%; margin: 10pt 0;
    font-size: 10pt; page-break-inside: avoid;
  }
  th { background: #4a4a8a; color: #fff; font-weight: 600; padding: 6pt 10pt; text-align: center; border: 1pt solid #3a3a7a; }
  td { padding: 5pt 10pt; border: 1pt solid #ddd; text-align: center; }
  tr:nth-child(even) td { background: #f8f8fc; }

  .divider { width: 60%; margin: 16pt auto; border-top: 1pt dotted #ccc; }
  .summary-table th { background: #1a1a2e; }
  .end-mark { text-align: center; color: #999; font-size: 12pt; margin-top: 36pt; }
</style>
</head>
<body>
"""

HTML_TAIL = "</body>\n</html>\n"


def build(parts, output_html, output_pdf, title=None, running_head=None):
    """拼 HTML → 写文件 → weasyprint 出 PDF → 打印页数/体积。

    编码策略（跨平台通用）：
      * 代码/脚本/SKILL.md 一律 UTF-8 无 BOM——带 BOM 会顶掉 shell 的 shebang、
        破坏 skill frontmatter 的 `---` 解析。
      * 交付给"任何地方"双击打开的 HTML 写 UTF-8 **带 BOM**（utf-8-sig）：
        文件头再加 <meta charset>，Windows 记事本/WPS 一类按 GBK 猜编码的工具
        也能自动识别为 UTF-8，不会乱码。
      * 正文与装饰不用 emoji（依赖 emoji 字体，换机器可能显示方块），
        只用 GB2312 范围内的符号（※【】▲）。
    """
    if title is not None:
        init(page_title=title)
    if running_head is not None:
        init(course_line=running_head)
    head = (HTML_HEAD
            .replace("__TITLE__", _PAGE_TITLE)
            .replace("__RUNNING_HEAD__", _PAGE_RUNNING_HEAD))
    html_content = head + "".join(parts) + HTML_TAIL
    with open(output_html, "w", encoding="utf-8-sig") as f:
        f.write(html_content)
    print(f"HTML: {output_html} ({len(html_content) // 1024} KB)")

    from weasyprint import HTML as WP_HTML
    WP_HTML(filename=output_html).write_pdf(output_pdf)
    size_mb = os.path.getsize(output_pdf) / 1024 / 1024
    pages = ""
    try:
        import pymupdf
        pages = f"，{pymupdf.open(output_pdf).page_count} 页"
    except Exception:
        pass
    print(f"PDF: {output_pdf} ({size_mb:.1f} MB{pages})")
    return output_pdf
