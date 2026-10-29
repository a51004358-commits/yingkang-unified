#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Healthblog 「推薦產品」block — inject into posts + helpers for future daily posts.

Browse-first only (no purchase CTA / price). Soft Traditional Chinese reasons.
Supports 1–2 related products per post.

Usage:
  python3 scripts/healthblog_rec_product.py              # inject all mapped posts
  python3 scripts/healthblog_rec_product.py --print SLUG # print HTML for one product slug
  python3 scripts/healthblog_rec_product.py --list       # list post→product map
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "healthblog" / "posts"
CSS_VER = "20261029a"

# slug → display name, image path relative to repo root, soft 1-line reason
PRODUCTS: dict[str, dict[str, str]] = {
    "biyan-60caps-mk368": {
        "name": "鼻炎素 60粒",
        "img": "assets/products/biyan-60caps-mk368/primary.jpg",
        "reason": "換季鼻部日常護理時，可先瀏覽這款口服系列的規格與成分說明。",
    },
    "fengse-gucidan-60caps-k0002": {
        "name": "風澀骨剌丹 60粒",
        "img": "assets/products/fengse-gucidan-60caps-k0002/primary.png",
        "reason": "天氣轉涼想了解關節相關口服系列，可先看規格與食用方法。",
    },
    "futeiling-120ml-yk404": {
        "name": "膚特靈 120ml 噴霧",
        "img": "assets/products/futeiling-120ml-yk404/primary.png",
        "reason": "外用噴霧護理節奏，可先瀏覽規格與使用說明（請依標籤使用）。",
    },
    "futeiling-tokyo-tower-120ml-x3-k0037": {
        "name": "東京塔牌膚特靈 120ml×3",
        "img": "assets/products/futeiling-tokyo-tower-120ml-x3-k0037/primary.png",
        "reason": "皮膚乾癢／乾燥龜裂外用時，可先瀏覽這款家庭裝噴霧規格與使用說明。",
    },
    "difugen-15ml-yk395": {
        "name": "滴膚堅 Difugen 15ml",
        "img": "assets/products/difugen-15ml-yk395/primary.webp",
        "reason": "外用保濕節奏，可一併瀏覽這款規格與使用說明。",
    },
    "xiangshui-50caps-k0035": {
        "name": "想睡就睡 50粒",
        "img": "assets/products/xiangshui-50caps-k0035/primary.png",
        "reason": "想調整睡前節奏時，可先看看這款口服的標籤說明。",
    },
    "huatatang-50caps-x4-yk470": {
        "name": "花塔糖 50粒×4支",
        "img": "assets/products/huatatang-50caps-x4-yk470/primary.png",
        "reason": "關注飲食與開胃節奏，可先瀏覽花塔糖系列規格。",
    },
    "yahuanxian-60caps-k0038": {
        "name": "蕥歡仙 60粒",
        "img": "assets/products/yahuanxian-60caps-k0038/primary.png",
        "reason": "午後想補充日常營養時，可先瀏覽規格與份量說明。",
    },
    "baqi-she-jianjing-cigu-oil-50ml-mk383": {
        "name": "八岐蛇肩頸刺骨靈油 50ml",
        "img": "assets/products/baqi-she-jianjing-cigu-oil-50ml-mk383/primary.jpg",
        "reason": "肩頸外用護理，可先對照這款活絡油的適用部位說明。",
    },
    "jinmen-yitiaogen-zuogu-gaobu-10pcs-yk401": {
        "name": "金門一條根坐骨神經膏布 10片",
        "img": "assets/products/jinmen-yitiaogen-zuogu-gaobu-10pcs-yk401/primary.png",
        "reason": "選膏布時可對照這款的尺寸、片數與透氣說明。",
    },
    "taiwan-yitiaogen-zuogu-gaobu-20pcs-k0025": {
        "name": "台灣一條根坐骨神經膏布 20片",
        "img": "assets/products/taiwan-yitiaogen-zuogu-gaobu-20pcs-k0025/primary.png",
        "reason": "需要較大覆蓋與較多片數時，可先瀏覽這款膏布規格。",
    },
    "zuogu-gaobu-10pcs-x11-yk400": {
        "name": "坐骨神經膏布 7×11cm（10片）",
        "img": "assets/products/zuogu-gaobu-10pcs-x11-yk400/primary.png",
        "reason": "久坐腰背護理，可先了解膏布尺寸與透氣規格。",
    },
    "yanbiqing-60caps-y5": {
        "name": "強力炎必清 60粒",
        "img": "assets/products/yanbiqing-60caps-y5/primary.png",
        "reason": "口服輕養生節奏，可先瀏覽一款規格與食用方法。",
    },
    "liuwei-dihuang-350caps-yk396": {
        "name": "六味地黃丸 350粒",
        "img": "assets/products/liuwei-dihuang-350caps-yk396/primary.png",
        "reason": "日常口服輕養生，可先瀏覽規格與食用方法。",
    },
    "liuwei-dihuang-350caps-x2-k0012": {
        "name": "六味地黃丸 350粒×2",
        "img": "assets/products/liuwei-dihuang-350caps-x2-k0012/primary.png",
        "reason": "想對照家庭裝／雙盒規格時，可先瀏覽片數與標籤說明。",
    },

    "jianbu-huqian-320caps-mk370": {
        "name": "健步虎潛丸 320粒",
        "img": "assets/products/jianbu-huqian-320caps-mk370/primary.jpg",
        "reason": "關注腿腳日常節奏時，可先看看口服的用法與成分標示。",
    },
    "zuogu-wan-60caps-hky7389": {
        "name": "坐骨神經丸 60粒",
        "img": "assets/products/zuogu-wan-60caps-hky7389/primary.png",
        "reason": "久坐臀腿相關口服系列，可先瀏覽規格與說明。",
    },
}

# post filename stem → one slug or list of 1–2 slugs
POST_PRODUCT: dict[str, str | list[str]] = {
    "2026-05-30-nasal-season-change": ["biyan-60caps-mk368", "yanbiqing-60caps-y5"],
    "2026-06-20-cold-weather-joints": ["fengse-gucidan-60caps-k0002", "jinmen-yitiaogen-zuogu-gaobu-10pcs-yk401"],
    "2026-07-10-hydration-summer": ["difugen-15ml-yk395", "futeiling-120ml-yk404"],
    "2026-07-28-sleep-routine": ["xiangshui-50caps-k0035", "liuwei-dihuang-350caps-yk396"],
    "2026-08-18-digestion-kids-adults": ["huatatang-50caps-x4-yk470", "yanbiqing-60caps-y5"],
    "2026-09-05-workplace-fatigue": ["yahuanxian-60caps-k0038", "liuwei-dihuang-350caps-yk396"],
    "2026-09-22-neck-shoulder-desk": ["baqi-she-jianjing-cigu-oil-50ml-mk383", "jinmen-yitiaogen-zuogu-gaobu-10pcs-yk401"],
    "2026-10-08-office-back-care": ["zuogu-gaobu-10pcs-x11-yk400", "taiwan-yitiaogen-zuogu-gaobu-20pcs-k0025"],
    "2026-10-17-office-dry-eyes": ["futeiling-120ml-yk404", "difugen-15ml-yk395"],
    "2026-10-18-plaster-selection-tips": ["jinmen-yitiaogen-zuogu-gaobu-10pcs-yk401", "taiwan-yitiaogen-zuogu-gaobu-20pcs-k0025"],
    "2026-10-19-oral-wellness-rhythm": ["yanbiqing-60caps-y5", "liuwei-dihuang-350caps-yk396"],
    "2026-10-20-autumn-nasal-comfort": ["biyan-60caps-mk368", "yanbiqing-60caps-y5"],
    "2026-10-21-autumn-skin-hydration": ["difugen-15ml-yk395", "futeiling-120ml-yk404"],
    "2026-10-22-autumn-sleep-wind-down": ["xiangshui-50caps-k0035", "liuwei-dihuang-350caps-yk396"],
    "2026-10-23-lunch-digestion-rhythm": ["huatatang-50caps-x4-yk470", "yanbiqing-60caps-y5"],
    "2026-10-24-autumn-joint-warmth": ["jinmen-yitiaogen-zuogu-gaobu-10pcs-yk401", "fengse-gucidan-60caps-k0002"],
    "2026-10-28-afternoon-neck-microbreaks": ["baqi-she-jianjing-cigu-oil-50ml-mk383", "jinmen-yitiaogen-zuogu-gaobu-10pcs-yk401"],
    "2026-10-29-evening-leg-buffer": ["jianbu-huqian-320caps-mk370", "zuogu-wan-60caps-hky7389"],
    "2026-10-29-yitiaogen-patch-how-to-use": ["taiwan-yitiaogen-zuogu-gaobu-20pcs-k0025", "jinmen-yitiaogen-zuogu-gaobu-10pcs-yk401"],
    "2026-10-29-sciatica-patch-how-to-choose": ["taiwan-yitiaogen-zuogu-gaobu-20pcs-k0025", "zuogu-gaobu-10pcs-x11-yk400"],
    "2026-10-29-liuwei-dihuang-who-its-for": ["liuwei-dihuang-350caps-yk396", "liuwei-dihuang-350caps-x2-k0012"],
    "2026-10-29-athlete-foot-spray-how-to-choose": "futeiling-tokyo-tower-120ml-x3-k0037",
    "2026-10-29-heatiness-acne-qingre-how-to-read": "yanbiqing-60caps-y5",
    "2026-10-29-jinmen-vs-taiwan-yitiaogen": ["jinmen-yitiaogen-zuogu-gaobu-10pcs-yk401", "taiwan-yitiaogen-zuogu-gaobu-20pcs-k0025"],
}

# Keyword hints for future daily posts (first match wins)
THEME_KEYWORDS: list[tuple[list[str], str]] = [
    (["鼻", "噴霧", "換季", "鼻腔", "呼吸道"], "biyan-60caps-mk368"),
    (["膏布", "貼", "透氣", "貼敷"], "jinmen-yitiaogen-zuogu-gaobu-10pcs-yk401"),
    (["口服", "養生", "膠囊", "丸"], "yanbiqing-60caps-y5"),
    (["睡", "失眠", "關機", "睡眠"], "xiangshui-50caps-k0035"),
    (["消化", "脾胃", "開胃", "花塔", "油膩"], "huatatang-50caps-x4-yk470"),
    (["肩", "頸", "低頭"], "baqi-she-jianjing-cigu-oil-50ml-mk383"),
    (["腰", "背", "久坐", "坐骨"], "zuogu-gaobu-10pcs-x11-yk400"),
    (["關節", "轉涼", "僵"], "fengse-gucidan-60caps-k0002"),
    (["皮膚", "乾燥", "保濕", "腳"], "difugen-15ml-yk395"),
    (["疲勞", "午後", "職場", "補水"], "yahuanxian-60caps-k0038"),
    (["眼", "螢幕", "乾澀", "冷氣房"], "futeiling-120ml-yk404"),
    (["腿", "通勤", "緩衝"], "jianbu-huqian-320caps-mk370"),
]


def _as_list(val: str | list[str]) -> list[str]:
    if isinstance(val, list):
        return val
    return [val]


def pick_product_for_theme(title: str, body: str = "") -> str:
    """Pick a product slug from title/body keywords; default oral flagship."""
    text = f"{title}\n{body}"
    for keys, slug in THEME_KEYWORDS:
        if any(k in text for k in keys):
            return slug
    return "yanbiqing-60caps-y5"


def render_card(product_slug: str, *, rel_prefix: str = "../../") -> str:
    p = PRODUCTS[product_slug]
    href = f"{rel_prefix}products/{product_slug}.html"
    img = f"{rel_prefix}{p['img']}"
    return (
        f'  <a class="hb-rec-card" href="{href}">\n'
        f'    <div class="hb-rec-img">\n'
        f'      <img src="{img}" alt="{p["name"]}" loading="lazy" width="88" height="88">\n'
        f'    </div>\n'
        f'    <div class="hb-rec-body">\n'
        f'      <div class="hb-rec-name">{p["name"]}</div>\n'
        f'      <p class="hb-rec-why">{p["reason"]}</p>\n'
        f'      <span class="hb-rec-link">瀏覽產品詳情 →</span>\n'
        f'    </div>\n'
        f'  </a>\n'
    )


def render_block(product_slugs: str | list[str], *, rel_prefix: str = "../../") -> str:
    slugs = _as_list(product_slugs)
    cards = "".join(render_card(s, rel_prefix=rel_prefix) for s in slugs)
    return (
        f'<section class="hb-rec" aria-label="推薦產品">\n'
        f'  <h2 class="hb-rec-title">推薦產品</h2>\n'
        f'{cards}'
        f'</section>\n'
    )


MARKER_START = "<!-- hb-rec:start -->"
MARKER_END = "<!-- hb-rec:end -->"


def wrap_block(html: str) -> str:
    return f"{MARKER_START}\n{html}{MARKER_END}\n"


def inject_into_html(html: str, block: str) -> str:
    """Insert (or replace) recommended block before article footer CTAs."""
    wrapped = wrap_block(block)
    html = re.sub(
        rf"\s*{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}\s*",
        "\n",
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r'\s*<section class="hb-rec"[^>]*>.*?</section>\s*',
        "\n",
        html,
        flags=re.DOTALL,
    )
    m = re.search(
        r'(\s*)(<p class="hb-back">|<p class="hb-cta"|<div class="hb-cta"|'
        r'<a class="hb-back"|</article>)',
        html,
    )
    if not m:
        raise ValueError("no insertion anchor found (hb-back/hb-cta/article end)")
    insertion = "\n  " + wrapped.replace("\n", "\n  ").rstrip() + "\n"
    html = html[: m.start(2)] + insertion + html[m.start(2) :]
    html = re.sub(
        r'(href="[^"]*assets/site\.css)\?v=[^"]*"',
        rf'\1?v={CSS_VER}"',
        html,
    )
    return html


def process_all() -> list[tuple[str, list[str]]]:
    updated: list[tuple[str, list[str]]] = []
    for stem, val in sorted(POST_PRODUCT.items()):
        slugs = _as_list(val)
        path = POSTS / f"{stem}.html"
        if not path.exists():
            print(f"SKIP missing {path.name}", file=sys.stderr)
            continue
        for slug in slugs:
            if slug not in PRODUCTS:
                print(f"SKIP unknown product {slug} for {stem}", file=sys.stderr)
                break
            img_path = ROOT / PRODUCTS[slug]["img"]
            if not img_path.exists():
                print(f"WARN missing image {img_path}", file=sys.stderr)
        else:
            raw = path.read_text(encoding="utf-8")
            new = inject_into_html(raw, render_block(slugs))
            path.write_text(new, encoding="utf-8")
            updated.append((stem, slugs))
            names = ", ".join(PRODUCTS[s]["name"] for s in slugs)
            print(f"OK {stem} → {names}")
    # Also catch any unmapped posts that already exist
    mapped = set(POST_PRODUCT)
    for path in sorted(POSTS.glob("*.html")):
        stem = path.stem
        if stem in mapped:
            continue
        raw = path.read_text(encoding="utf-8")
        title_m = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.S)
        title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else stem
        slug = pick_product_for_theme(title, raw)
        new = inject_into_html(raw, render_block(slug))
        path.write_text(new, encoding="utf-8")
        updated.append((stem, [slug]))
        print(f"OK(auto) {stem} → {PRODUCTS[slug]['name']}")
    return updated


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--print", metavar="PRODUCT_SLUG", dest="print_slug")
    ap.add_argument("--pick", metavar="TITLE", help="Suggest product slug from title keywords")
    args = ap.parse_args()
    if args.list:
        for stem, val in sorted(POST_PRODUCT.items()):
            slugs = _as_list(val)
            names = ", ".join(PRODUCTS[s]["name"] for s in slugs)
            print(f"{stem}\t{','.join(slugs)}\t{names}")
        return 0
    if args.print_slug:
        if args.print_slug not in PRODUCTS:
            print(f"Unknown product: {args.print_slug}", file=sys.stderr)
            return 1
        print(wrap_block(render_block(args.print_slug)), end="")
        return 0
    if args.pick:
        slug = pick_product_for_theme(args.pick)
        print(f"{slug}\t{PRODUCTS[slug]['name']}")
        print(wrap_block(render_block(slug)), end="")
        return 0
    process_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
