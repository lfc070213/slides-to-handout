#!/usr/bin/env python3
"""把 PDF 中的文字转成矢量轮廓，生成"任何阅读器都渲染正确"的版本。

用途：部分手机/微信/WPS 类阅读器不理会 PDF 内嵌字体、直接把字形序号当码位渲染
（表现为拉丁字母整段偏移、中文变成空白或怪字）。转成轮廓后 PDF 里不再有字体，
这类阅读器也无从出错；代价是文字不可选中/搜索（需要搜索时保留原版）。

用法: flatten_pdf.py <输入.pdf> <输出.pdf> [起始页] [结束页]
"""
import sys
import os

import pymupdf


def flatten(src_path, dst_path, first=None, last=None):
    src = pymupdf.open(src_path)
    out = pymupdf.open()
    pages = range(src.page_count)
    if first:
        pages = range(first - 1, (last or src.page_count))
    for i in pages:
        page = src[i]
        svg = page.get_svg_image(text_as_path=1)
        tmp = pymupdf.open("svg", svg.encode("utf-8"))
        one = pymupdf.open("pdf", tmp.convert_to_pdf())
        new = out.new_page(width=page.rect.width, height=page.rect.height)
        new.show_pdf_page(new.rect, one, 0)
    out.save(dst_path, garbage=4, deflate=True)
    return src.page_count, len(pages)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    src, dst = sys.argv[1], sys.argv[2]
    first = int(sys.argv[3]) if len(sys.argv) > 3 else None
    last = int(sys.argv[4]) if len(sys.argv) > 4 else None
    total, done = flatten(src, dst, first, last)
    d = pymupdf.open(dst)
    fonts = sum(
        1 for x in range(1, d.xref_length())
        if d.xref_get_key(x, "Type")[1] == "/Font")
    print(f"{dst}: {done}/{total} 页, {os.path.getsize(dst)/1024/1024:.1f} MB, "
          f"剩余字体数 {fonts}（应为 0）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
