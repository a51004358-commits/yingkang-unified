#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch HKTVmall product photos for SKUs listed in missing-images.md and wire them into HTML."""
from __future__ import annotations

import re
import time
import concurrent.futures
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

REPO = Path("/workspace/yingkang-unified")
MISSING = REPO / "missing-images.md"
PRODUCTS_DIR = REPO / "products"
ASSETS = REPO / "assets" / "products"
INDEX = PRODUCTS_DIR / "index.html"
HKTV_PDP = "https://www.hktvmall.com/hktv/zh/p/{sku}"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
WORKERS = 4
BATCH_SLEEP = 0.8

SIZE_RANK = {
    "1200": 1200,
    "600": 600,
    "515": 515,
    "300": 300,
    "96": 96,
    "65": 65,
}

def parse_missing(path: Path) -> list[tuple[str, str, str]]:
    """Return list of (slug, name, sku)."""
    items = []
    pat = re.compile(
        r"`([a-z0-9\-]+)\.html`\s*—\s*(.+?)\s*—\s*`(H6838001_S_[A-Za-z0-9_-]+)`"
    )
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pat.search(line)
        if m:
            items.append((m.group(1), m.group(2).strip(), m.group(3)))
    return items

def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="replace")

def extract_product_image_urls(html: str) -> list[str]:
    """Collect product image URLs from PDP HTML.

    Prefer modern uploadProductImage CDN URLs; also accept legacy
    images.hktv-img.com packshots and og:image (common on older SKUs).
    Ignore storeLogo / uploadStoreImage / banners.
    """
    urls: list[str] = []
    urls += re.findall(
        r"https://cdn(?:-media|-mms)\.hktvmall\.com/[^\"\'\s<>]*uploadProductImage[^\"\'\s<>]*",
        html,
        flags=re.I,
    )
    for m in re.finditer(
        r"property=[\"\']og:image(?::secure_url)?[\"\'][^>]*content=[\"\']([^\"\']+)",
        html,
        flags=re.I,
    ):
        urls.append(m.group(1))
    for m in re.finditer(
        r"content=[\"\']([^\"\']+)[\"\'][^>]*property=[\"\']og:image",
        html,
        flags=re.I,
    ):
        urls.append(m.group(1))
    urls += re.findall(
        r"https://images\.hktv-img\.com/images/HKTV/[^\"\'\s<>\\]+",
        html,
        flags=re.I,
    )
    seen = set()
    out = []
    for u in urls:
        u = u.replace("\\/", "/")
        low = u.lower()
        if any(
            x in low
            for x in (
                "uploadstoreimage",
                "storelogo",
                "optionalbanner",
                "/landing/",
                "favicon",
            )
        ):
            continue
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out

def pick_primary_url(urls: list[str]) -> str | None:
    if not urls:
        return None
    scored = []
    for u in urls:
        m = re.search(r"_(\d+)\.(png|jpg|jpeg|webp)(?:\?|$)", u, re.I)
        if m:
            size = int(m.group(1))
            ext = m.group(2).lower()
        else:
            m2 = re.search(r"\.(png|jpg|jpeg|webp)(?:\?|$)", u, re.I)
            size = 500  # bare
            ext = (m2.group(1).lower() if m2 else "png")
        scored.append((size, u, ext))
    # prefer _1200 then largest
    scored.sort(key=lambda t: t[0], reverse=True)
    for size, u, ext in scored:
        if size == 1200:
            return u
    return scored[0][1]

def expand_candidates(url: str) -> list[str]:
    candidates = [url]
    if "_1200." in url:
        candidates += [
            url.replace("_1200.", "_600."),
            url.replace("_1200.", "_515."),
            url.replace("_1200.", "_300."),
            re.sub(r"_1200\.", ".", url),
        ]
    # legacy images.hktv-img.com often uses _01_1200.jpg style
    if "images.hktv-img.com" in url and re.search(r"_\d+\.(png|jpg|jpeg|webp)", url, re.I):
        for size in ("1200", "600", "515", "300"):
            alt = re.sub(r"_(\d+)\.(png|jpg|jpeg|webp)", rf"_{size}.\2", url, count=1, flags=re.I)
            if alt not in candidates:
                candidates.append(alt)
    extras = []
    for u in candidates:
        if "cdn-mms.hktvmall.com" in u:
            extras.append(
                u.replace(
                    "cdn-mms.hktvmall.com/hktv/mms/",
                    "cdn-media.hktvmall.com/hktv-mms/HKTV/mms/",
                )
            )
        if "cdn-media.hktvmall.com" in u:
            extras.append(
                u.replace(
                    "cdn-media.hktvmall.com/hktv-mms/HKTV/mms/",
                    "cdn-mms.hktvmall.com/hktv/mms/",
                )
            )
    # de-dupe
    seen = set()
    out = []
    for u in candidates + extras:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out

def sniff_ext(data: bytes, url: str) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    m = re.search(r"\.(png|jpg|jpeg|webp)(?:\?|$)", url, re.I)
    if m:
        return m.group(1).lower().replace("jpeg", "jpg")
    return "png"

def download(url: str, dest_dir: Path) -> Path | None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    # skip if already have a primary.*
    for name in ("primary.png", "primary.jpg", "primary.webp", "primary.jpeg"):
        p = dest_dir / name
        if p.exists() and p.stat().st_size > 1000:
            return p

    for u in expand_candidates(url):
        try:
            req = Request(
                u,
                headers={"User-Agent": UA, "Referer": "https://www.hktvmall.com/"},
            )
            with urlopen(req, timeout=30) as resp:
                data = resp.read()
            if len(data) < 500:
                continue
            ext = sniff_ext(data, u)
            dest = dest_dir / f"primary.{ext}"
            dest.write_bytes(data)
            return dest
        except (URLError, HTTPError, TimeoutError, OSError):
            continue
    return None

def process_one(item: tuple[str, str, str]) -> dict:
    slug, name, sku = item
    result = {
        "slug": slug,
        "name": name,
        "sku": sku,
        "ok": False,
        "path": None,
        "reason": "",
    }
    dest_dir = ASSETS / slug
    # already filled?
    for name_f in ("primary.png", "primary.jpg", "primary.webp", "primary.jpeg"):
        p = dest_dir / name_f
        if p.exists() and p.stat().st_size > 1000:
            result["ok"] = True
            result["path"] = p
            result["reason"] = "already present"
            return result

    pdp = HKTV_PDP.format(sku=sku)
    html = None
    last_err = None
    for attempt in range(2):
        try:
            html = fetch_html(pdp)
            break
        except Exception as e:
            last_err = e
            time.sleep(1.2)
    if html is None:
        result["reason"] = f"PDP fetch failed: {last_err}"
        return result

    urls = extract_product_image_urls(html)
    primary = pick_primary_url(urls)
    if not primary:
        result["reason"] = "no uploadProductImage URL in PDP"
        return result

    path = None
    for attempt in range(2):
        path = download(primary, dest_dir)
        if path:
            break
        time.sleep(1.0)
    if not path:
        result["reason"] = f"download failed for {primary}"
        return result

    result["ok"] = True
    result["path"] = path
    result["reason"] = f"downloaded {path.name} from {primary}"
    return result

def update_product_page(slug: str, rel_img: str) -> bool:
    page = PRODUCTS_DIR / f"{slug}.html"
    if not page.exists():
        return False
    text = page.read_text(encoding="utf-8")
    # only replace main product image (#main-img / class main), not header logo
    new_text, n = re.subn(
        r'(<img\s+class="main"\s+id="main-img"\s+src=")[^"]+(")',
        rf"\1{rel_img}\2",
        text,
        count=1,
    )
    if n == 0:
        # alternate attribute order
        new_text, n = re.subn(
            r'(<img\s+id="main-img"[^>]*\ssrc=")[^"]+(")',
            rf"\1{rel_img}\2",
            text,
            count=1,
        )
    if n == 0:
        return False
    page.write_text(new_text, encoding="utf-8")
    return True

def update_index(slug: str, rel_img: str, index_text: str) -> str:
    """Replace logo.png inside the card whose href is slug.html."""
    # Match the card block for this slug and swap its img src if logo
    pat = re.compile(
        rf'(<a class="plist-card" href="{re.escape(slug)}\.html"[^>]*>.*?'
        rf'<img src=")([^"]+)(")',
        re.S,
    )

    def repl(m):
        return m.group(1) + rel_img + m.group(3)

    new_text, n = pat.subn(repl, index_text, count=1)
    return new_text if n else index_text

def main():
    items = parse_missing(MISSING)
    print(f"Parsed {len(items)} missing SKUs")
    if not items:
        print("Nothing to do")
        return

    results = []
    # process in batches with limited concurrency
    for i in range(0, len(items), WORKERS):
        batch = items[i : i + WORKERS]
        print(f"Batch {i // WORKERS + 1}: {[s for s, _, _ in batch]}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = [ex.submit(process_one, it) for it in batch]
            for f in concurrent.futures.as_completed(futs):
                r = f.result()
                status = "OK" if r["ok"] else "FAIL"
                print(f"  [{status}] {r['slug']} — {r['reason']}")
                results.append(r)
        time.sleep(BATCH_SLEEP)

    ok = [r for r in results if r["ok"]]
    fail = [r for r in results if not r["ok"]]
    print(f"\nDownload summary: {len(ok)} ok, {len(fail)} failed")

    # Update HTML
    index_text = INDEX.read_text(encoding="utf-8")
    html_ok = 0
    for r in ok:
        path: Path = r["path"]
        rel = f"../assets/products/{r['slug']}/{path.name}"
        if update_product_page(r["slug"], rel):
            html_ok += 1
        index_text = update_index(r["slug"], rel, index_text)
    INDEX.write_text(index_text, encoding="utf-8")
    print(f"Updated {html_ok} product pages + products/index.html")

    # Rewrite missing-images.md
    lines = [
        "# 缺圖產品清單",
        "",
    ]
    if fail:
        lines.append("以下產品頁暫以 logo／素底 placeholder 顯示，待補產品圖。")
        lines.append("")
        for r in fail:
            lines.append(
                f"- `{r['slug']}.html` — {r['name']} — `{r['sku']}`  "
                f"（失敗原因：{r['reason']}）"
            )
        lines.append("")
        lines.append(f"合計仍缺圖：{len(fail)} 件（已成功補圖 {len(ok)} 件）")
    else:
        lines.append(f"狀態：全部 {len(ok)} 件缺圖產品已補上 HKTVmall 產品圖。")
        lines.append("")
        lines.append(f"合計缺圖：0 件")
    MISSING.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Rewrote {MISSING}")

    # write a small report
    report = REPO / "scripts" / "_fill_images_report.txt"
    with report.open("w", encoding="utf-8") as f:
        f.write(f"ok={len(ok)} fail={len(fail)}\n")
        for r in ok:
            f.write(f"OK\t{r['slug']}\t{r['path']}\t{r['reason']}\n")
        for r in fail:
            f.write(f"FAIL\t{r['slug']}\t{r['sku']}\t{r['reason']}\n")
    print(f"Report: {report}")

if __name__ == "__main__":
    main()
