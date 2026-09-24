#!/usr/bin/env python3
"""示例：把 示例课件.pptx 转成详细讲义（逐页原图对照 + LaTeX 公式 + 推导 + 例题）。

前置：python3 make_demo_deck.py && ../scripts/slides_to_pages.sh 示例课件.pptx .
运行：python3 gen_示例课件_pdf.py
产出：示例_详细讲义.html / 示例_详细讲义.pdf
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))   # 指向本 skill 的 scripts 目录
import noteskit as nk  # noqa: E402

nk.init(slide_dir=os.path.join(HERE, "pages"), course_line="股票估值 · 示例讲义")

parts = []

parts.append(nk.cover(
    "股票估值入门",
    "从股利贴现模型到戈登增长模型",
    "示例课件 · 详细讲义",
    "（示例：5 页课件逐页精解）",
))

parts.append(nk.toc([
    ("第一部分 估值理论", [
        "第 2 页　股利贴现模型（DDM）",
        "第 3 页　戈登增长模型",
    ]),
    ("第二部分 应用与局限", [
        "第 4 页　例题：用戈登模型估值",
        "第 5 页　模型局限",
    ]),
]))

# ─────────────────────── 第一部分 ───────────────────────
parts.append(nk.part_title("一", "估值理论", "从“未来股利的现值”这一条主线出发，推出可用的估值公式"))

parts.append(nk.slide(2, "股利贴现模型（DDM）"))
parts.append(nk.p(
    "股利贴现模型（Dividend Discount Model, DDM）把股票看作一张永续的现金流凭证："
    "股东从公司拿到的只有股利，因此股票的价值就等于未来全部股利的现值之和。"
    "这里的折现率是股权资本成本 " + nk.imath(r"$r_E$") + "——它反映这笔现金流对股东的风险。"
))
parts.append(nk.note(
    "常见疑问：那未来把股票卖掉的钱不算吗？算，但买入者付出的价格最终仍由他未来能拿到的股利决定。"
    "所以“股利是唯一现金流”不是假设，而是把“卖出价”不断往后递推得到的结论。"
))
parts.append(nk.deriv("推导：从现值定义到 DDM", [
    ("第 1 步", "第 " + nk.imath(r"$t$") + " 期股利 " + nk.imath(r"$Div_t$") + " 按 " + nk.imath(r"$r_E$") + " 折现，得到它的现值"),
    nk.dline(r"$PV(Div_t)=\frac{Div_t}{(1+r_E)^t}$"),
    ("第 2 步", "股票价值 = 全部未来股利的现值之和"),
    nk.dline(r"$P_0=\sum_{t=1}^{\infty}\frac{Div_t}{(1+r_E)^t}$"),
]))
parts.append(nk.formula_boxed(r"$P_0=\sum_{t=1}^{\infty}\frac{Div_t}{(1+r_E)^t}$", "股利贴现模型（DDM）"))
parts.append(nk.note(
    "这个式子本身没有错，但不能直接用：无限多项股利无法逐项预测。"
    "要让公式变得可用，必须给股利加上一条可描述的规律——这正是下一页戈登模型做的事。"
))

parts.append(nk.slide(3, "戈登增长模型（Gordon Growth Model）"))
parts.append(nk.p(
    "戈登增长模型给股利加一条最简单的规律：股利以固定增长率 " + nk.imath(r"$g$") +
    " 永续增长。即第 1 期股利为 " + nk.imath(r"$Div_1$") + "，此后每期在上期基础上乘以 " +
    nk.imath(r"$(1+g)$") + "。"
))
parts.append(nk.deriv("推导：等比级数求和", [
    ("第 1 步", "按固定增长率写出第 " + nk.imath(r"$t$") + " 期股利"),
    nk.dline(r"$Div_t=Div_1(1+g)^{\,t-1}$"),
    ("第 2 步", "代入 DDM"),
    nk.dline(r"$P_0=\sum_{t=1}^{\infty}\frac{Div_1(1+g)^{\,t-1}}{(1+r_E)^t}"
             r"=\frac{Div_1}{1+r_E}\sum_{k=0}^{\infty}\left(\frac{1+g}{1+r_E}\right)^{k}$"),
    ("第 3 步", "公比 " + nk.imath(r"$q=\frac{1+g}{1+r_E}$") +
     "；当 " + nk.imath(r"$r_E>g$") + " 时 " + nk.imath(r"$|q|<1$") +
     "，几何级数收敛于 " + nk.imath(r"$\frac{1}{1-q}$")),
    nk.dline(r"$P_0=\frac{Div_1}{1+r_E}\cdot\frac{1}{1-\frac{1+g}{1+r_E}}=\frac{Div_1}{r_E-g}$"),
]))
parts.append(nk.formula_boxed(r"$P_0=\frac{Div_1}{r_E-g}$", "戈登增长模型"))
parts.append(nk.note(
    "适用条件 " + nk.imath(r"$r_E>g$") + " 不是技术细节，而是经济含义："
    "股利增速长期不可能高于股权资本成本，否则股价发散（趋于无穷）。"
))
parts.append(nk.p("公式的三个方向都常用——给出任意三个量就能解出第四个："))
parts.append(nk.table(
    ["已知", "求解", "公式"],
    [
        ["Div_1、r_E、g", "内在价值 P_0", "P_0 = Div_1 / (r_E − g)"],
        ["P_0、Div_1、g", "隐含资本成本 r_E", "r_E = Div_1 / P_0 + g"],
        ["P_0、Div_1、r_E", "隐含增长率 g", "g = r_E − Div_1 / P_0"],
    ],
))

# ─────────────────────── 第二部分 ───────────────────────
parts.append(nk.part_title("二", "应用与局限", "代入一组真实感的数据算一遍，再看模型在什么情况下会失灵"))

parts.append(nk.slide(4, "例题：用戈登模型估值"))
parts.append(nk.p(
    "某公司明年每股股利 " + nk.imath(r"$Div_1=2.00$") + " 元，股权资本成本 " +
    nk.imath(r"$r_E=10\%$") + "，股利永续增长率 " + nk.imath(r"$g=4\%$") + "，求内在价值。"
))
parts.append(nk.deriv("代入公式", [
    ("条件", "Div_1 = 2.00 元，r_E = 10%，g = 4%，满足 r_E > g"),
    nk.dline(r"$P_0=\frac{2.00}{0.10-0.04}=\frac{2.00}{0.06}=33.33$"),
]))
parts.append(nk.formula_boxed(r"$P_0=33.33$", "例题结论：内在价值 33.33 元"))
parts.append(nk.p("若当前股价为 30 元，模型价 33.33 元比市价高约 11.1%，按模型判断为低估。但这个结论有多稳？把增长率换个假设看看："))
parts.append(nk.table(
    ["g", "0.02", "0.03", "0.04", "0.05", "0.06"],
    [["P_0（元）", "25.00", "28.57", "33.33", "40.00", "50.00"]],
))
parts.append(nk.note(
    "g 从 4% 下调 1 个百分点到 3%，模型价就从 33.33 元掉到 28.57 元，"
    "结论由“低估”直接翻成“高估”。估值对 g 的敏感性，是戈登模型最大的软肋。"
))

parts.append(nk.slide(5, "模型局限"))
parts.append(nk.p("把上一页的敏感性放回模型假设里看，戈登模型的边界就清楚了："))
parts.append(nk.bullets([
    "g → r_E 时价格趋于无穷：估值对 g 的微小变化极其敏感（上一页表格已量化）。",
    "只适合分红稳定、增长平稳的公司；不分红或股利波动大的公司没有稳定的 Div_1 和 g。",
    ("高增长公司要用两阶段或多阶段模型：前期逐年预测，后期再套戈登公式算终值。",),
    "长期看 g 不可能持续高于名义 GDP 增速——否则公司规模会超过整个经济体。",
]))
parts.append(nk.note(
    "实务中的用法：把戈登公式当作“终值”计算器（多阶段模型的最后一段），"
    "而不是给任何公司都直接套用的万能公式。"
))
parts.append(nk.divider())
parts.append('<div class="end-mark">— 示例讲义 完 —</div>')

nk.build(
    parts,
    os.path.join(HERE, "示例_详细讲义.html"),
    os.path.join(HERE, "示例_详细讲义.pdf"),
    title="股票估值入门 详细讲义",
    running_head="股票估值 · 示例讲义",
)
