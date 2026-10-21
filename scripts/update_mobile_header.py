#!/usr/bin/env python3
"""Batch-replace topbar/nav/search chrome with mobile m-header + drawer."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
WA = "https://wa.me/85262227238"
WA_MEMBER = WA + "?text=" + quote("我想登入會員／查詢訂單")
WA_CART = WA + "?text=" + quote("我想查詢購物／下單")

ICO_MENU = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M3 6h18v2H3V6zm0 5h18v2H3v-2zm0 5h18v2H3v-2z"/></svg>'
)
ICO_SEARCH = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5 '
    "6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 "
    '4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 '
    '9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>'
)
ICO_USER = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 '
    "9.2 4.5 9.2 7.2 11.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 "
    '4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/></svg>'
)
ICO_CART = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M7 18c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm10 '
    "0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM7.2 14.8h9.9c.8 "
    "0 1.5-.5 1.7-1.2l2.5-7.2c.1-.4 0-.8-.3-1.1-.2-.2-.5-.4-.8-.4H6.2L5.5 "
    '3H2v2h2.2l2.7 9.2c-.5.5-.9 1.3-.9 2.1 0 1.7 1.3 3 3 3h10v-2H9c-.6 '
    '0-1-.4-1-1 0-.1 0-.2.1-.3l.1-.5z"/></svg>'
)
ICO_CLOSE = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M18.3 5.7 12 12l6.3 6.3-1.4 1.4L10.6 13.4 4.3 '
    '19.7 2.9 18.3 9.2 12 2.9 5.7 4.3 4.3l6.3 6.3 6.3-6.3z"/></svg>'
)

HEADER_RE = re.compile(
    r'<header class="topbar">.*?</div>\s*</div>\s*'  # search-overlay closing
    r'(?=\n\S|\n<div class="carousel|\n<div class="catalog|\n<main|\n<section|\n<article|\n<div class="wrap|\n<div class="hb-|\n<div class="ysm-|\n<div class="page-|\n<a class="|\n<div class="lf-|\n<div class="product|\n<div class="banner|\n<div class="proof|\n<div class="faq|\n<div class="about|\n<p class="crumb)',
    re.S,
)
# More reliable: from <header class="topbar"> through search-overlay inclusive
BLOCK_RE = re.compile(
    r'<header class="topbar">[\s\S]*?<div class="search-overlay"[^>]*>[\s\S]*?</div>\s*</div>',
    re.S,
)

SCRIPT_RE = re.compile(
    r'<script>\s*\(function\(\)\{\s*var ov=document\.getElementById\([\'"]search-overlay[\'"]\);[\s\S]*?\}\)\(\);\s*</script>',
    re.S,
)

PROMO_RE = re.compile(
    r'<div class="promo-strip">[\s\S]*?</div>\s*(?=\n<a class="ysm-home-teaser|\n<section class="wrap")',
    re.S,
)

def depth_of(path: Path) -> int:
    return len(path.relative_to(ROOT).parts) - 1

def prefix_for(path: Path) -> str:
    return "../" * depth_of(path)

def current_key(path: Path) -> str | None:
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    if rel == "index.html":
        return None
    if rel.startswith("products/"):
        return "products"
    if rel.startswith("healthblog/") or rel.startswith("pages/healthblog"):
        return "healthblog"
    if rel.startswith("yinshumei/"):
        return "yinshumei"
    if rel == "faq.html":
        return "faq"
    if rel == "about.html":
        return "about"
    return None

def cur(key: str | None, want: str) -> str:
    return ' aria-current="page"' if key == want else ""

def build_chrome(path: Path) -> str:
    p = prefix_for(path)
    k = current_key(path)
    home = f"{p}index.html"
    products = f"{p}products/index.html"
    yin = f"{p}yinshumei/"
    blog = f"{p}healthblog/"
    faq = f"{p}faq.html"
    about = f"{p}about.html"
    css_js = f"{p}assets/"

    return f'''<header class="m-header" id="site-header">
  <div class="m-bar">
    <div class="m-bar-left">
      <button type="button" class="ico-btn" id="nav-toggle" aria-label="開啟選單" aria-expanded="false" aria-controls="nav-drawer">{ICO_MENU}</button>
      <button type="button" class="ico-btn" id="open-search" aria-label="搜尋">{ICO_SEARCH}</button>
    </div>
    <a class="m-logo" href="{home}">
      <img src="{css_js}logo.png" alt="盈康" width="36" height="36">
      <span class="brand-name">盈康</span>
    </a>
    <div class="m-bar-right">
      <a class="ico-btn" href="{WA_MEMBER}" target="_blank" rel="noopener" title="會員服務經 WhatsApp 查詢" aria-label="會員">{ICO_USER}</a>
      <a class="ico-btn" href="{WA_CART}" target="_blank" rel="noopener" title="購物／查詢經 WhatsApp" aria-label="購物車">{ICO_CART}</a>
      <a class="m-wa-desk" href="{WA}" target="_blank" rel="noopener" title="WhatsApp 6222 7238">6222 7238</a>
    </div>
  </div>
</header>
<nav class="nav" aria-label="主選單">
  <div class="nav-inner">
    <a href="{products}"{cur(k, "products")}>所有產品</a>
    <a href="{yin}"{cur(k, "yinshumei")}>尹淑梅專區</a>
    <a href="{blog}"{cur(k, "healthblog")}>健康庫</a>
    <a href="{faq}"{cur(k, "faq")}>常見問題</a>
    <a href="{about}"{cur(k, "about")}>關於我們</a>
    <a href="{WA}" target="_blank" rel="noopener">聯絡我們</a>
  </div>
</nav>
<div class="drawer-backdrop" id="drawer-backdrop" hidden></div>
<aside class="nav-drawer" id="nav-drawer" aria-hidden="true" aria-label="網站選單">
  <div class="drawer-head">
    <span>盈康</span>
    <button type="button" class="ico-btn" id="nav-close" aria-label="關閉選單">{ICO_CLOSE}</button>
  </div>
  <div class="drawer-block">
    <h2 class="drawer-h">目錄</h2>
    <ul class="drawer-list">
      <li><a href="{products}"{cur(k, "products")}>所有產品</a></li>
      <li><a href="{yin}"{cur(k, "yinshumei")}>尹淑梅專區</a></li>
      <li><a href="{blog}"{cur(k, "healthblog")}>健康庫</a></li>
      <li><a href="{faq}"{cur(k, "faq")}>常見問題</a></li>
      <li><a href="{about}"{cur(k, "about")}>關於我們</a></li>
      <li><a href="{WA}" target="_blank" rel="noopener">聯絡我們（WhatsApp）</a></li>
    </ul>
  </div>
  <div class="drawer-block">
    <h2 class="drawer-h">分類</h2>
    <ul class="drawer-list">
      <li><a href="{products}">所有產品</a></li>
      <li><a href="{products}?cat={quote("膏布外用")}">膏布系列</a></li>
      <li><a href="{products}?cat={quote("口服膠囊")}">口服系列</a></li>
      <li><a href="{products}?cat={quote("噴霧滴劑")}">噴霧系列</a></li>
      <li><a href="{yin}">尹淑梅專區</a></li>
    </ul>
  </div>
</aside>
<div class="announce">香港本地健康品牌｜膏布・口服・噴霧</div>
<div class="search-overlay" id="search-overlay" role="dialog" aria-label="搜尋">
  <div class="search-panel">
    <form action="{products}" method="get">
      <input type="search" name="q" placeholder="搜尋產品名稱…" aria-label="搜尋">
    </form>
    <p class="hint">亦可 WhatsApp 6222 7238 直接查詢。按 Esc 關閉。</p>
  </div>
</div>'''

NEW_PROMO = '''<div class="promo-strip promo-grid-2x2" aria-label="精選入口">
  <a class="promo-tile tile-a" href="products/index.html">
    <h3>所有產品</h3>
    <p>膏布・口服・噴霧一覽</p>
    <span class="tile-cta">瀏覽 →</span>
  </a>
  <a class="promo-tile tile-b" href="yinshumei/">
    <h3>尹淑梅專區</h3>
    <p>教授理念與品牌故事</p>
    <span class="tile-cta">了解更多 →</span>
  </a>
  <a class="promo-tile tile-c" href="healthblog/">
    <h3>健康庫</h3>
    <p>輕養生日常小知識</p>
    <span class="tile-cta">瀏覽 →</span>
  </a>
  <a class="promo-tile tile-d" href="about.html">
    <h3>關於我們</h3>
    <p>香港本地健康品牌</p>
    <span class="tile-cta">了解更多 →</span>
  </a>
</div>
'''

FLOAT_CHAT = (
    '<a class="float-chat" href="https://wa.me/85262227238" target="_blank" '
    'rel="noopener" title="WhatsApp 6222 7238" aria-label="WhatsApp 聯絡">💬</a>\n'
)

def process(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    orig = text
    m = BLOCK_RE.search(text)
    if not m:
        print("SKIP (no block):", path.relative_to(ROOT))
        return False
    chrome = build_chrome(path)
    text = text[: m.start()] + chrome + text[m.end() :]

    # Replace inline search script with shared site.js (once)
    p = prefix_for(path)
    script_tag = f'<script src="{p}assets/site.js" defer></script>'
    if SCRIPT_RE.search(text):
        text = SCRIPT_RE.sub(script_tag, text, count=1)
    elif f'assets/site.js' not in text:
        # insert before </body>
        text = text.replace("</body>", script_tag + "\n</body>", 1)

    # Homepage promo + float chat
    if path.name == "index.html" and path.parent == ROOT:
        if PROMO_RE.search(text):
            text = PROMO_RE.sub(NEW_PROMO, text, count=1)
        if 'class="float-chat"' not in text:
            text = text.replace('<a class="back-top"', FLOAT_CHAT + '<a class="back-top"', 1)

    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False

def main() -> None:
    changed = 0
    for path in sorted(ROOT.rglob("*.html")):
        if "class=\"topbar\"" not in path.read_text(encoding="utf-8") and "m-header" not in path.read_text(encoding="utf-8"):
            # re-read once
            pass
        t = path.read_text(encoding="utf-8")
        if 'class="topbar"' not in t and 'class="m-header"' not in t:
            print("NO HEADER:", path.relative_to(ROOT))
            continue
        if process(path):
            changed += 1
            print("OK", path.relative_to(ROOT))
        else:
            print("UNCH", path.relative_to(ROOT))
    print("Changed:", changed)

if __name__ == "__main__":
    main()
