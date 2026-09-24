#!/usr/bin/env python3
"""把 PDF 指定页渲染成 PNG，供肉眼检查排版（公式大小/超宽/孤行/分页空白）。

用法:
    preview_pdf.py <pdf> 1 5 20          # 渲染第 1、5、20 页
    preview_pdf.py <pdf> --all           # 全部页
    preview_pdf.py <pdf> 1-6 40 --dpi 110 --outdir /tmp/check
渲染后用 Read 工具打开 PNG 真的看一眼——这一步不能省，页数对不代表排版对。
"""
import argparse
import os
import sys
import time

import pymupdf


def parse_pages(specs, total):
    nums = set()
    for s in specs:
        if "-" in s:
            a, b = s.split("-", 1)
            nums.update(range(int(a), int(b) + 1))
        else:
            nums.add(int(s))
    return sorted(n for n in nums if 1 <= n <= total)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("pages", nargs="*", help="页码/区间，如 1 5 20 或 3-8；--all 表示全部")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    outdir = args.outdir or f"/tmp/pdfpreview-{time.strftime('%H%M%S')}"
    os.makedirs(outdir, exist_ok=True)

    doc = pymupdf.open(args.pdf)
    pages = list(range(1, doc.page_count + 1)) if args.all else parse_pages(args.pages, doc.page_count)
    if not pages:
        print(f"PDF 共 {doc.page_count} 页；请给页码，如: preview_pdf.py {args.pdf} 1 5", file=sys.stderr)
        return 1
    for n in pages:
        path = os.path.join(outdir, f"page_{n:03d}.png")
        doc[n - 1].get_pixmap(dpi=args.dpi).save(path)
        print(path)
    print(f"(共 {doc.page_count} 页，本次渲染 {len(pages)} 页)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
