#!/usr/bin/env python3
"""Extract product-page facts for careful VG6 prompt writing."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def strip(t: str) -> str:
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def lis(block: str) -> list[str]:
    out = []
    for li in re.findall(r"<li[^>]*>(.*?)</li>", block, re.S):
        t = strip(li)
        if t and "相關搜尋" not in t:
            out.append(t)
    return out

def extract(slug: str) -> dict:
    html = (ROOT / "products" / f"{slug}.html").read_text(encoding="utf-8")
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    name = strip(h1.group(1)) if h1 else slug
    sku_m = re.search(r"SKU[：:]\s*([A-Za-z0-9_]+)", html)
    now = re.search(r"price-now[^>]*>\s*(HK\$[\d,]+)", html)
    was = re.search(r"price-was[^>]*>\s*(HK\$[\d,]+)", html)
    label = re.search(r'class="pdp-eff-label"[^>]*>(.*?)</p>', html, re.S)
    lead = re.search(r'class="pdp-eff-lead"[^>]*>(.*?)</p>', html, re.S)
    if not lead:
        lead = re.search(r'class="pdp-buy-blurb"[^>]*>(.*?)</p>', html, re.S)
    spec = re.search(r'class="lf-spec-line"[^>]*>(.*?)</p>', html, re.S)
    pains, benefits = [], []
    m = re.search(r"痛點[：:].*?</h[23]>(.*?)(?:功效|為什麼|相關搜尋)", html, re.S)
    if m:
        pains = lis(m.group(1))[:6]
    m = re.search(r"功效／好處.*?</h[23]>(.*?)(?:相關搜尋|為什麼|配方|成分)", html, re.S)
    if m:
        benefits = lis(m.group(1))[:8]
    ings = []
    for card in re.findall(
        r'class="lf-ing-card".*?<strong>(.*?)</strong>\s*<span>(.*?)</span>',
        html,
        re.S,
    ):
        ings.append({"name": strip(card[0]), "note": strip(card[1])})
    # dedupe by name
    seen, uniq = set(), []
    for ing in ings:
        if ing["name"] not in seen:
            seen.add(ing["name"])
            uniq.append(ing)
    ad = ROOT / "assets" / "products" / slug
    primary = None
    for cand in ("primary.png", "primary.jpg", "primary.webp", "packshot-clean.png"):
        if (ad / cand).exists():
            primary = str((ad / cand).relative_to(ROOT))
            break
    peripheral_kw = ("滑鼠", "mouse", "喇叭", "speaker", "收納", "thermometer", "紅茶", "茶", "溫度計")
    blob = name + slug
    return {
        "slug": slug,
        "name": name,
        "sku": sku_m.group(1) if sku_m else None,
        "price_now": now.group(1) if now else None,
        "price_was": was.group(1) if was else None,
        "eff_label": strip(label.group(1)) if label else "",
        "lead": strip(lead.group(1)) if lead else "",
        "spec_line": strip(spec.group(1)) if spec else "",
        "pain_points": pains,
        "benefits": benefits,
        "ingredients": uniq,
        "primary": primary,
        "is_peripheral": any(k.lower() in blob.lower() for k in peripheral_kw),
        "forbid_phrases": [
            "清熱四寶",
            "清返嚟",
            "上火暗瘡",
            "穿心蓮",
            "紫錐花",
            "蒲公英",
            "香蜂草",
        ],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()
    data = extract(args.slug)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
