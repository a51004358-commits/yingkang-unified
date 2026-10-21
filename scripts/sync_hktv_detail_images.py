#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync HKTVmall photosTabImages (詳圖) onto ykimed product pages.

For each products/*.html (except index), parse the HKTVmall SKU, fetch the
PDP (cached), extract photosTabImages, download unique highest-res images into
assets/products/{slug}/detail/hktv-NN.{ext}, and insert/replace the
.pdp-detail#product-detail-images block (same structure as yanbiqing).
"""
from __future__ import annotations

import json
import re
import time
import hashlib
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta

REPO = Path("/workspace/yingkang-unified")
PRODUCTS_DIR = REPO / "products"
ASSETS = REPO / "assets" / "products"
CACHE_DIR = Path("/workspace/agent-tools/hktv-pdp")
REPORT = Path("/workspace/agent-tools/hktv-detail-sync-report.md")
HKTV_PDP = "https://www.hktvmall.com/hktv/zh/p/{sku}"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
WORKERS = 3
SLEEP_BETWEEN = 0.35
CACHE_MAX_AGE_HOURS = 48
SKU_RE = re.compile(
    r"https://www\.hktvmall\.com/hktv/zh/p/(H6838001_S_[A-Za-z0-9_-]+)"
)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
DETAIL_BLOCK_RE = re.compile(
    r"\s*<!--\s*HKTVmall[^\n]*-->\s*"
    r'<div class="lf-section pdp-detail" id="product-detail-images">.*?</div>\s*',
    re.S,
)
# Also match block without the HTML comment
DETAIL_BLOCK_RE2 = re.compile(
    r'\s*<div class="lf-section pdp-detail" id="product-detail-images">.*?</div>\s*',
    re.S,
)

SIZE_PREF = {
    "1200Wx1200H": 1200,
    "600Wx600H": 600,
    "515Wx515H": 515,
    "300Wx300H": 300,
}


def list_products() -> list[Path]:
    return sorted(
        p for p in PRODUCTS_DIR.glob("*.html") if p.name != "index.html"
    )


def parse_sku(html: str) -> str | None:
    m = SKU_RE.search(html)
    return m.group(1) if m else None


def parse_h1(html: str) -> str:
    m = H1_RE.search(html)
    if not m:
        return "產品"
    text = re.sub(r"<[^>]+>", "", m.group(1))
    text = re.sub(r"\s+", " ", text).strip()
    return text or "產品"


def short_name(full: str) -> str:
    """Strip common pack-size suffixes for alt text (match yanbiqing style)."""
    s = full
    s = re.sub(
        r"\s*\d+\s*(粒|片|包|盒|支|瓶|ml|mL|ML|克|g|G|套|件|入).*$",
        "",
        s,
    ).strip()
    s = re.sub(r"\s*[xX×]\s*\d+\s*.*$", "", s).strip()
    return s or full


def cache_path(sku: str) -> Path:
    return CACHE_DIR / f"{sku}.html"


def cache_fresh(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 1000:
        return False
    age = time.time() - path.stat().st_mtime
    return age < CACHE_MAX_AGE_HOURS * 3600


def fetch_html(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
        },
    )
    with urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="replace")


def get_pdp_html(sku: str) -> tuple[str | None, str]:
    """Return (html, status) where status is cached|fetched|failed:..."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = cache_path(sku)
    if cache_fresh(path):
        return path.read_text(encoding="utf-8", errors="replace"), "cached"
    url = HKTV_PDP.format(sku=sku)
    last_err = None
    for attempt in range(3):
        try:
            html = fetch_html(url)
            if len(html) < 500:
                last_err = f"too short ({len(html)})"
                time.sleep(1.0)
                continue
            path.write_text(html, encoding="utf-8")
            return html, "fetched"
        except Exception as e:
            last_err = str(e)
            time.sleep(1.2 * (attempt + 1))
    # stale cache fallback
    if path.exists() and path.stat().st_size > 1000:
        return path.read_text(encoding="utf-8", errors="replace"), "stale-cache"
    return None, f"failed:{last_err}"


def extract_product_data_blob(html: str) -> dict | None:
    """Extract productData JSON object from PDP HTML."""
    m = re.search(r"var\s+productData\s*=\s*(\{)", html)
    if not m:
        return None
    start = m.start(1)
    # brace-match; strings may contain braces — walk with string awareness
    i = start
    depth = 0
    in_str = False
    esc = False
    quote = ""
    while i < len(html):
        ch = html[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
        else:
            if ch in ('"', "'"):
                in_str = True
                quote = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    blob = html[start : i + 1]
                    try:
                        return json.loads(blob)
                    except json.JSONDecodeError:
                        # try unescape common JS issues
                        try:
                            return json.loads(blob.replace("\\'", "'"))
                        except json.JSONDecodeError:
                            return None
        i += 1
    return None


def extract_photos_tab_images(html: str) -> list[dict]:
    """Return list of {format, url} from photosTabImages, preserving order."""
    data = extract_product_data_blob(html)
    if data and isinstance(data.get("photosTabImages"), list):
        out = []
        for item in data["photosTabImages"]:
            if isinstance(item, dict) and item.get("url"):
                out.append(
                    {
                        "format": str(item.get("format") or ""),
                        "url": str(item["url"]).replace("\\/", "/"),
                    }
                )
            elif isinstance(item, str) and item.startswith("http"):
                out.append({"format": "", "url": item.replace("\\/", "/")})
        if out:
            return out

    # Fallback: regex on photosTabImages array literal
    m = re.search(r'"photosTabImages"\s*:\s*(\[)', html)
    if not m:
        return []
    start = m.start(1)
    i = start
    depth = 0
    in_str = False
    esc = False
    quote = ""
    while i < len(html):
        ch = html[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
        else:
            if ch in ('"', "'"):
                in_str = True
                quote = ch
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    arr = html[start : i + 1]
                    try:
                        parsed = json.loads(arr)
                    except json.JSONDecodeError:
                        return []
                    out = []
                    for item in parsed:
                        if isinstance(item, dict) and item.get("url"):
                            out.append(
                                {
                                    "format": str(item.get("format") or ""),
                                    "url": str(item["url"]).replace("\\/", "/"),
                                }
                            )
                    return out
        i += 1
    return []


def image_basename_key(url: str) -> str:
    """Dedupe key: basename without size suffix like _1200 / _600."""
    name = url.split("?")[0].rstrip("/").split("/")[-1]
    name = re.sub(r"_(?:1200|600|515|300|96|65)(?=\.(?:png|jpe?g|webp)$)", "", name, flags=re.I)
    return name.lower()


def pick_best_urls(items: list[dict]) -> list[str]:
    """Prefer 1200Wx1200H / highest-res unique by basename, keep first-seen order."""
    # Group by basename preserving order of first appearance
    groups: dict[str, list[dict]] = {}
    order: list[str] = []
    for it in items:
        key = image_basename_key(it["url"])
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(it)

    def score(it: dict) -> int:
        fmt = it.get("format") or ""
        if fmt in SIZE_PREF:
            return SIZE_PREF[fmt]
        m = re.search(r"_(\d+)\.(?:png|jpe?g|webp)(?:\?|$)", it["url"], re.I)
        if m:
            return int(m.group(1))
        # format like 1200Wx1200H already handled; try WxH
        m2 = re.search(r"(\d+)W[xX](\d+)H", fmt)
        if m2:
            return int(m2.group(1))
        return 0

    urls = []
    for key in order:
        best = max(groups[key], key=score)
        urls.append(best["url"])
    return urls


def sniff_ext(data: bytes, url: str) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    m = re.search(r"\.(png|jpe?g|webp)(?:\?|$)", url, re.I)
    if m:
        return m.group(1).lower().replace("jpeg", "jpg")
    return "png"


def download_bytes(url: str) -> bytes | None:
    candidates = [url]
    # try size variants if primary fails
    for size in ("1200", "600", "515"):
        alt = re.sub(r"_(\d+)\.(png|jpe?g|webp)", rf"_{size}.\2", url, count=1, flags=re.I)
        if alt not in candidates:
            candidates.append(alt)
    for u in candidates:
        try:
            req = Request(
                u,
                headers={
                    "User-Agent": UA,
                    "Referer": "https://www.hktvmall.com/",
                    "Accept": "image/*,*/*;q=0.8",
                },
            )
            with urlopen(req, timeout=40) as resp:
                data = resp.read()
            if len(data) >= 500:
                return data
        except (URLError, HTTPError, TimeoutError, OSError):
            continue
    return None


def save_detail_images(slug: str, urls: list[str]) -> list[Path]:
    dest_dir = ASSETS / slug / "detail"
    dest_dir.mkdir(parents=True, exist_ok=True)
    # Clear previous hktv-NN.* so numbering stays clean
    for old in dest_dir.glob("hktv-*"):
        if old.is_file():
            old.unlink()
    saved: list[Path] = []
    for i, url in enumerate(urls, 1):
        data = download_bytes(url)
        if not data:
            continue
        ext = sniff_ext(data, url)
        path = dest_dir / f"hktv-{i:02d}.{ext}"
        path.write_bytes(data)
        saved.append(path)
        time.sleep(0.1)
    return saved


def build_detail_html(slug: str, sku: str, name: str, images: list[Path]) -> str:
    alt_base = short_name(name)
    figures = []
    for i, img in enumerate(images, 1):
        rel = f"../assets/products/{slug}/detail/{img.name}"
        loading = "eager" if i == 1 else "lazy"
        figures.append(
            f'      <figure class="pdp-detail-fig">\n'
            f'        <img src="{rel}" alt="{alt_base}｜詳圖 {i}" '
            f'width="1024" height="1024" loading="{loading}">\n'
            f"      </figure>"
        )
    stack = "\n".join(figures)
    return (
        f"\n  <!-- HKTVmall {sku} 主圖／詳圖（店舖自家素材） -->\n"
        f'  <div class="lf-section pdp-detail" id="product-detail-images">\n'
        f"    <h2>產品<span class=\"accent\">詳圖</span></h2>\n"
        f'    <p class="ml-soft" style="margin-top:0;margin-bottom:0.85rem">'
        f"以下詳圖取自 HKTVmall 盈康店舖同一 SKU（{sku}），可直向滑動瀏覽。</p>\n"
        f'    <div class="pdp-detail-stack">\n'
        f"{stack}\n"
        f"    </div>\n"
        f"  </div>\n"
    )


def insert_or_replace_detail(html: str, block: str) -> str:
    # Replace existing detail block if present
    if DETAIL_BLOCK_RE.search(html):
        return DETAIL_BLOCK_RE.sub("\n" + block, html, count=1)
    if DETAIL_BLOCK_RE2.search(html):
        return DETAIL_BLOCK_RE2.sub("\n" + block, html, count=1)

    # Prefer after ml-trust (yanbiqing layout)
    m = re.search(
        r'(<div class="ml-trust"[^>]*>.*?</div>\s*</div>)',
        html,
        re.S,
    )
    if m:
        pos = m.end()
        return html[:pos] + block + html[pos:]

    # After lf-top closing
    m = re.search(r'(<div class="lf-top">.*?</div>\s*</div>\s*</div>)', html, re.S)
    # Better: find lf-top then match its closing by depth — simpler heuristic:
    # insert before first lf-section that is NOT inside lf-top, or before pdp-tabs
    m_tabs = re.search(r'\n\s*<div class="lf-section"[^>]*id="pdp-tabs"', html)
    if m_tabs:
        return html[: m_tabs.start()] + block + html[m_tabs.start() :]

    m_sec = re.search(r'\n\s*<div class="lf-section"', html)
    if m_sec:
        # Find the first lf-section AFTER lf-top ends.
        # lf-top starts once; skip any lf-section before lf-top end.
        lf = re.search(r'<div class="lf-top">', html)
        if lf:
            # naive: find </div> that closes lf-top by looking for blank line + lf-section
            # Use: after the buy column closes — search from lf-top
            rest = html[lf.end() :]
            # Find first \n  <div class="lf-section" in full html after lf-top block
            # Count depth from lf-top
            depth = 1
            i = lf.end()
            in_str = False  # not needed for HTML tags roughly
            while i < len(html) and depth > 0:
                if html.startswith("<div", i):
                    depth += 1
                    i += 4
                    continue
                if html.startswith("</div>", i):
                    depth -= 1
                    i += 6
                    if depth == 0:
                        # skip whitespace
                        j = i
                        while j < len(html) and html[j] in " \t\r\n":
                            j += 1
                        return html[:j] + block + html[j:]
                    continue
                i += 1

        return html[: m_sec.start()] + block + html[m_sec.start() :]

    # Fallback: before footer
    m_foot = re.search(r"<footer\b", html, re.I)
    if m_foot:
        return html[: m_foot.start()] + block + "\n" + html[m_foot.start() :]
    return html.rstrip() + "\n" + block + "\n"


def process_one(page: Path) -> dict:
    slug = page.stem
    html = page.read_text(encoding="utf-8", errors="replace")
    sku = parse_sku(html)
    name = parse_h1(html)
    result = {
        "slug": slug,
        "sku": sku or "",
        "name": name,
        "status": "",
        "n_images": 0,
        "reason": "",
    }
    if not sku:
        result["status"] = "failed"
        result["reason"] = "no SKU link in page"
        return result

    pdp, fetch_status = get_pdp_html(sku)
    time.sleep(SLEEP_BETWEEN)
    if pdp is None:
        result["status"] = "failed"
        result["reason"] = fetch_status
        return result

    items = extract_photos_tab_images(pdp)
    if not items:
        result["status"] = "skipped"
        result["reason"] = "no photosTabImages"
        return result

    urls = pick_best_urls(items)
    if not urls:
        result["status"] = "skipped"
        result["reason"] = "photosTabImages empty after dedupe"
        return result

    saved = save_detail_images(slug, urls)
    if not saved:
        result["status"] = "failed"
        result["reason"] = f"download failed for {len(urls)} urls"
        return result

    block = build_detail_html(slug, sku, name, saved)
    new_html = insert_or_replace_detail(html, block)
    if new_html != html:
        page.write_text(new_html, encoding="utf-8")
    result["status"] = "updated"
    result["n_images"] = len(saved)
    result["reason"] = f"{fetch_status}; {len(saved)} images"
    return result


def main() -> None:
    pages = list_products()
    print(f"Products: {len(pages)}", flush=True)
    results = []
    # Sequential is safer for politeness; light concurrency for downloads only inside each
    for i, page in enumerate(pages, 1):
        print(f"[{i}/{len(pages)}] {page.name} ...", flush=True)
        try:
            r = process_one(page)
        except Exception as e:
            r = {
                "slug": page.stem,
                "sku": "",
                "name": "",
                "status": "failed",
                "n_images": 0,
                "reason": f"exception: {e}",
            }
        results.append(r)
        print(f"  -> {r['status']} {r.get('sku','')} n={r['n_images']} {r['reason']}", flush=True)

    updated = [r for r in results if r["status"] == "updated"]
    skipped = [r for r in results if r["status"] == "skipped"]
    failed = [r for r in results if r["status"] == "failed"]

    hk = timezone(timedelta(hours=8))
    now = datetime.now(hk).strftime("%Y-%m-%d %H:%M:%S HKT (Asia/Hong_Kong)")
    lines = [
        f"# HKTVmall 詳圖 sync report",
        f"",
        f"Generated: {now}",
        f"",
        f"## Counts",
        f"",
        f"- Total products: {len(results)}",
        f"- Updated (got photosTabImages): {len(updated)}",
        f"- Skipped (no photosTabImages): {len(skipped)}",
        f"- Failed: {len(failed)}",
        f"",
        f"## Updated",
        f"",
    ]
    for r in updated:
        lines.append(f"- `{r['slug']}` — `{r['sku']}` — {r['n_images']} images — {r['name']}")
    lines += ["", "## Skipped (no photosTabImages)", ""]
    for r in skipped:
        lines.append(f"- `{r['slug']}` — `{r['sku']}` — {r['name']}")
    lines += ["", "## Failed", ""]
    if not failed:
        lines.append("(none)")
    else:
        for r in failed:
            lines.append(f"- `{r['slug']}` — `{r['sku']}` — {r['reason']}")
    lines.append("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nDone. updated={len(updated)} skipped={len(skipped)} failed={len(failed)}")
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
