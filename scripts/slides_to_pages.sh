#!/usr/bin/env bash
# 课件 → 每页图片。用法: slides_to_pages.sh <课件.pptx|ppt|pdf> <输出目录> [dpi]
#
# 产出 <输出目录>/pages/slide_NNN.png 与同名 .jpg（quality 82）。
# 讲义里嵌 .jpg 控制体积，.png 留给需要看细节/OCR 的场合。
# 依赖: LibreOffice(soffice) 转 PDF、python3 的 pymupdf + Pillow 出图。
set -euo pipefail

IN=${1:?用法: slides_to_pages.sh <课件.pptx|ppt|pdf> <输出目录> [dpi]}
OUT=${2:?缺少输出目录}
DPI=${3:-150}

mkdir -p "$OUT/pages"

case "$IN" in
  *.pdf|*.PDF)
    PDF="$IN"
    ;;
  *)
    SOFFICE=$(command -v soffice || true)
    [ -n "$SOFFICE" ] || SOFFICE=/Applications/LibreOffice.app/Contents/MacOS/soffice
    [ -x "$SOFFICE" ] || { echo "找不到 soffice（装 LibreOffice）" >&2; exit 1; }
    "$SOFFICE" --headless --convert-to pdf --outdir "$OUT" "$IN" >/dev/null
    PDF="$OUT/$(basename "${IN%.*}").pdf"
    ;;
esac

[ -f "$PDF" ] || { echo "找不到转换后的 PDF: $PDF" >&2; exit 1; }

python3 - "$PDF" "$OUT/pages" "$DPI" <<'PY'
import os, sys
import pymupdf
from PIL import Image

pdf, pages_dir, dpi = sys.argv[1], sys.argv[2], int(sys.argv[3])
doc = pymupdf.open(pdf)
for i, page in enumerate(doc, 1):
    png = os.path.join(pages_dir, f"slide_{i:03d}.png")
    jpg = os.path.join(pages_dir, f"slide_{i:03d}.jpg")
    page.get_pixmap(dpi=dpi).save(png)
    Image.open(png).convert("RGB").save(jpg, quality=82, optimize=True)
w, h = None, None
if doc.page_count:
    p = doc[0]
    w, h = int(p.rect.width), int(p.rect.height)
print(f"{doc.page_count} 页 → {pages_dir}/  ({dpi} dpi, 页面 {w}x{h} pt)")
PY
