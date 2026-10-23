#!/usr/bin/env python3
"""Replace (or insert) the pdp-detail image stack with VG6 01..06."""
from __future__ import annotations
import argparse, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build_block(slug: str, name: str, alts: list[str], sku: str | None, blurb: str) -> str:
    figs = []
    for i, alt in enumerate(alts, 1):
        figs.append(
            f'      <figure class="pdp-detail-fig">\n'
            f'        <img src="../assets/products/{slug}/detail/vg6-{i:02d}.jpg" '
            f'alt="{alt}" width="720" height="1280" loading="lazy">\n'
            f'      </figure>'
        )
    sku_bit = f'SKU：{sku}。' if sku else ''
    return (
        f'  <!-- VG6 直向詳圖：英雄・持貨・成分・科學・見證・對比 -->\n'
        f'  <div class="lf-section pdp-detail" id="product-detail-images">\n'
        f'    <h2>產品<span class="accent">詳圖</span></h2>\n'
        f'    <p class="ml-soft" style="margin-top:0;margin-bottom:0.85rem">'
        f'{blurb}{sku_bit}</p>\n'
        f'    <div class="pdp-detail-stack">\n'
        + '\n'.join(figs) +
        f'\n    </div>\n'
        f'  </div>'
    )

def update(slug: str, alts: list[str], blurb: str | None = None) -> None:
    path = ROOT / 'products' / f'{slug}.html'
    html = path.read_text(encoding='utf-8')
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
    name = re.sub(r'<[^>]+>', '', h1.group(1)).strip() if h1 else slug
    sku_m = re.search(r'SKU[：:]\s*([A-Za-z0-9_]+)', html)
    sku = sku_m.group(1) if sku_m else None
    if blurb is None:
        blurb = '六段直向詳圖（英雄價位・持貨・配方・科學・用家分享・對比），可直向滑動瀏覽。'
    block = build_block(slug, name, alts, sku, blurb)

    # Prefer replacing existing detail section (with optional preceding comment)
    pat = re.compile(
        r'(?:<!--[^>]*詳圖[^>]*-->\s*)?<div class="lf-section pdp-detail"[^>]*id="product-detail-images"[^>]*>.*?</div>\s*</div>',
        re.S,
    )
    if pat.search(html):
        html2 = pat.sub(block, html, count=1)
    else:
        # insert before pdp-efficacy or before closing wrap
        ins = re.search(r'<!-- pdp-efficacy:start -->|<div class="lf-section"[^>]*id="pdp-efficacy"', html)
        if ins:
            html2 = html[:ins.start()] + block + '\n</div>\n\n' + html[ins.start():]
            # fix if we duplicated wrap close — simpler: insert before efficacy inside wrap
        else:
            # before </div> that closes .wrap — fragile; append before footer
            html2 = html.replace('</div>\n\n<!-- pdp-efficacy', block + '\n</div>\n\n<!-- pdp-efficacy', 1)
            if html2 == html:
                raise SystemExit(f'Could not find insertion point for {slug}')

    if html2 == html:
        raise SystemExit(f'No change for {slug}')
    path.write_text(html2, encoding='utf-8')
    print(f'updated {path}')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--alts', nargs=6, required=True)
    ap.add_argument('--blurb', default=None)
    args = ap.parse_args()
    update(args.slug, args.alts, args.blurb)
