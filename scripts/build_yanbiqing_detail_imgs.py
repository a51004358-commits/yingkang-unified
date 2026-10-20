#!/usr/bin/env python3
"""v4.1: Six-panel photo-first 詳圖 for 強力炎必清.

Customer critique fixes:
- Full-bleed spokesperson-v4 hero (product in hand), minimal overlay
- Punchy short copy (not 說明書)
- Full-bleed botanical ingredients chapter + large photo bubbles
- Alternating rhythms (photo / sparse / macro / trust)
- blister-macro quality chapter; yinshumei philosophy; WA browse-first

Cap.231 soft TC. No Vita marks / #1 / clinical % / disease cure claims.
AI person = 虛構視覺.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "assets/products/yanbiqing-60caps-y5"
OUT = PROD / "detail"
AI = PROD / "ai"
BUB = OUT / "bubbles"
PORTRAIT = ROOT / "assets/yinshumei/portrait.jpg"
LOGO = ROOT / "assets/logo.png"

W = 1500  # master; export 750w
SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
SERIF_R = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SANS_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
IDX = 4

INK = (38, 32, 28)
MUTED = (100, 90, 80)
GOLD = (196, 154, 88)
GOLD_LT = (230, 205, 155)
ORANGE = (196, 108, 48)
ORANGE_DK = (126, 72, 28)
WHITE = (255, 255, 255)
CREAM = (255, 250, 242)


def font(size: int, bold: bool = False, serif: bool = False) -> ImageFont.FreeTypeFont:
    path = (SERIF_B if bold else SERIF_R) if serif else (SANS_B if bold else SANS_R)
    return ImageFont.truetype(path, size, index=IDX)


def tw(d, t, f) -> int:
    b = d.textbbox((0, 0), t, font=f)
    return b[2] - b[0]


def th(d, t, f) -> int:
    b = d.textbbox((0, 0), t or " ", font=f)
    return b[3] - b[1]


def cover(path: Path, w: int, h: int, focus=(0.5, 0.35)) -> Image.Image:
    im = Image.open(path).convert("RGB")
    scale = max(w / im.width, h / im.height)
    nw, nh = int(im.width * scale + 0.5), int(im.height * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, min(int((nw - w) * focus[0]), nw - w))
    top = max(0, min(int((nh - h) * focus[1]), nh - h))
    return im.crop((left, top, left + w, top + h))


def bottom_scrim(im: Image.Image, from_ratio=0.62, color=(255, 246, 232), max_a=220) -> Image.Image:
    w, h = im.size
    start = int(h * from_ratio)
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = ov.load()
    for y in range(start, h):
        t = (y - start) / max(h - start - 1, 1)
        a = int(max_a * (t ** 1.2))
        for x in range(w):
            px[x, y] = (*color, a)
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def top_bar(im: Image.Image, hbar=88, alpha=200) -> Image.Image:
    w, h = im.size
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rectangle((0, 0, w, hbar), fill=(28, 22, 18, alpha))
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def soft_chip(draw, text, cx, y, fnt, fill_bg=WHITE, fill_fg=ORANGE_DK, pad_x=28, pad_y=14):
    ww = tw(draw, text, fnt)
    hh = th(draw, text, fnt)
    box = (cx - ww // 2 - pad_x, y, cx + ww // 2 + pad_x, y + hh + pad_y * 2)
    draw.rounded_rectangle(box, radius=18, fill=fill_bg, outline=GOLD, width=2)
    draw.text((cx - ww // 2, y + pad_y), text, font=fnt, fill=fill_fg)
    return box[3]


def circle_photo(path: Path, diameter: int) -> Image.Image:
    photo = ImageOps.fit(Image.open(path).convert("RGB"), (diameter, diameter), Image.Resampling.LANCZOS)
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter - 1, diameter - 1), fill=255)
    pad = 16
    out = Image.new("RGBA", (diameter + pad * 2, diameter + pad * 2), (0, 0, 0, 0))
    glow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((0, 0, out.size[0] - 1, out.size[1] - 1), fill=(255, 228, 170, 90))
    out = Image.alpha_composite(out, glow.filter(ImageFilter.GaussianBlur(10)))
    circ = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    circ.paste(photo, (0, 0))
    circ.putalpha(mask)
    out.paste(circ, (pad, pad), circ)
    d = ImageDraw.Draw(out)
    d.ellipse((pad - 4, pad - 4, pad + diameter + 3, pad + diameter + 3), outline=GOLD, width=5)
    return out


def rounded_cover(path: Path, w: int, h: int, radius=28, focus=(0.5, 0.4)) -> Image.Image:
    photo = cover(path, w, h, focus)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(photo, (0, 0))
    out.putalpha(mask)
    ring = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(ring).rounded_rectangle((2, 2, w - 3, h - 3), radius=radius, outline=(*GOLD, 255), width=3)
    return Image.alpha_composite(out, ring)


def parchment_strip(h: int) -> Image.Image:
    yy, xx = np.mgrid[0:h, 0:W].astype(np.float32)
    r = np.sqrt((xx - W * 0.5) ** 2 + (yy - h * 0.2) ** 2)
    r = (r / (r.max() + 1e-6)) ** 0.85
    c1 = np.array([255, 250, 242], np.float32)
    c2 = np.array([236, 220, 190], np.float32)
    out = c1 * (1 - r)[:, :, None] + c2 * r[:, :, None]
    out += np.random.default_rng(5).normal(0, 2.0, out.shape)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


# ---- panels ----

def panel_01_hero() -> Image.Image:
    """Full-bleed spokesperson-v4; product large in hand; minimal text."""
    H = 2000
    im = cover(AI / "spokesperson-v4.jpg", W, H, focus=(0.48, 0.30))
    im = ImageEnhance.Contrast(im).enhance(1.05)
    im = ImageEnhance.Color(im).enhance(1.04)
    im = top_bar(im, 80, 185)
    # Soft feathered scrim — readable title zone without a hard PowerPoint plaque
    im = bottom_scrim(im, 0.72, (255, 248, 238), 175)
    # Extra very soft mid wash only behind title band
    wash = Image.new("RGBA", (W, 2000), (0, 0, 0, 0))
    px = wash.load()
    for y in range(1380, 1680):
        t = (y - 1380) / 300
        # peak soft cream in the middle of the title band
        a = int(70 * (1 - abs(t - 0.35) * 1.6))
        a = max(0, min(90, a))
        for x in range(W):
            px[x, y] = (255, 248, 236, a)
    im = Image.alpha_composite(im.convert("RGBA"), wash).convert("RGB")
    draw = ImageDraw.Draw(im)

    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA")
        logo.thumbnail((140, 40), Image.Resampling.LANCZOS)
        im_r = im.convert("RGBA")
        im_r.paste(logo, (36, 20), logo)
        im = im_r.convert("RGB")
        draw = ImageDraw.Draw(im)
    draw.text((200, 24), "盈康", font=font(28, True, False), fill=GOLD_LT)

    # ONE title + one short line — sit in soft zone
    f_title = font(78, True, True)
    title = "強力炎必清"
    draw.text(((W - tw(draw, title, f_title)) // 2, 1440), title, font=f_title, fill=INK)

    f_sub = font(32, False, True)
    sub = "草本日常輕養生 · 60粒"
    soft_chip(draw, sub, W // 2, 1555, f_sub, fill_bg=(255, 252, 247), fill_fg=ORANGE_DK)

    f_ai = font(20, False, False)
    ai = "形象為虛構視覺，非真實名人代言"
    draw.text(((W - tw(draw, ai, f_ai)) // 2, 1900), ai, font=f_ai, fill=MUTED)
    return im


def panel_02_benefits() -> Image.Image:
    """3 big short soft benefits on matching lifestyle photo cards — not a manual."""
    H = 1750
    # chapter: cool-morning still darkened (matches 清熱 chapter)
    bg = cover(AI / "lifestyle-qingre.jpg", W, H, focus=(0.45, 0.40))
    bg = ImageEnhance.Brightness(bg).enhance(0.55)
    bg = ImageEnhance.Color(bg).enhance(0.95)
    # leave photo visible at edges; parchment center less dominant
    parch = parchment_strip(H)
    im = Image.blend(bg, parch, 0.35)
    draw = ImageDraw.Draw(im)

    f_h = font(56, True, True)
    t = "日常想輕一點"
    draw.text(((W - tw(draw, t, f_h)) // 2, 60), t, font=f_h, fill=INK)

    # v4.1: each photo chapter matches its headline (semantic + visual)
    cards = [
        (AI / "lifestyle-qingre.jpg", (0.35, 0.40), "日常清熱節奏", "寫進作息，先了解再說"),
        (AI / "lifestyle-season.jpg", (0.42, 0.35), "換季想舒適", "冷暖交替，留意自己"),
        (AI / "lifestyle-dining.jpg", (0.45, 0.45), "應酬後想輕一點", "外賣應酬多的日子"),
    ]
    # 3 vertical big cards spanning width with huge photo
    y = 180
    card_h = 480
    gap = 36
    f_c = font(40, True, True)
    f_p = font(28, False, False)
    for path, focus, title, body in cards:
        # full-width photo band with sparse text overlay
        photo = cover(path, W - 80, card_h - 20, focus=focus)
        # dark left scrim for text
        band = Image.new("RGBA", (W - 80, card_h - 20), (0, 0, 0, 0))
        band.paste(photo, (0, 0))
        scrim = Image.new("RGBA", (W - 80, card_h - 20), (0, 0, 0, 0))
        px = scrim.load()
        bw = W - 80
        for x in range(bw):
            a = int(160 * max(0, 1 - x / (bw * 0.55)))
            for yy in range(card_h - 20):
                px[x, yy] = (25, 18, 12, a)
        band = Image.alpha_composite(band, scrim)
        # gold frame
        framed = Image.new("RGBA", (W - 80, card_h - 20), (0, 0, 0, 0))
        framed = Image.alpha_composite(framed, band)
        rd = ImageDraw.Draw(framed)
        rd.rounded_rectangle((1, 1, W - 82, card_h - 22), radius=24, outline=(*GOLD, 255), width=4)
        # mask rounded
        mask = Image.new("L", (W - 80, card_h - 20), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, W - 81, card_h - 21), radius=24, fill=255)
        tmp = Image.new("RGBA", (W - 80, card_h - 20), (0, 0, 0, 0))
        tmp.paste(framed, (0, 0))
        tmp.putalpha(mask)
        # re-apply gold on top
        ring = Image.new("RGBA", (W - 80, card_h - 20), (0, 0, 0, 0))
        ImageDraw.Draw(ring).rounded_rectangle((2, 2, W - 84, card_h - 24), radius=24, outline=(*GOLD, 255), width=4)
        tmp = Image.alpha_composite(Image.merge("RGBA", (*tmp.split()[:3], mask)), ring)

        im_r = im.convert("RGBA")
        im_r.paste(tmp, (40, y), tmp)
        im = im_r.convert("RGB")
        draw = ImageDraw.Draw(im)
        draw.text((80, y + 140), title, font=f_c, fill=WHITE)
        draw.text((80, y + 220), body, font=f_p, fill=(235, 225, 210))
        y += card_h + gap

    f_cap = font(20, False, False)
    cap = "生活節奏描述 · 非診斷治療之用（Cap.231）"
    draw.text(((W - tw(draw, cap, f_cap)) // 2, H - 55), cap, font=f_cap, fill=MUTED)
    return im


def panel_03_ingredients() -> Image.Image:
    """Full-bleed herbs-hero + 4 LARGE photo bubbles — not a form table."""
    H = 2200
    # top half: full-bleed botanical hero
    hero_h = 900
    top = cover(AI / "herbs-hero.jpg", W, hero_h, focus=(0.5, 0.45))
    top = ImageEnhance.Contrast(top).enhance(1.06)
    top = bottom_scrim(top, 0.55, (255, 248, 236), 200)
    # bottom: soft parchment continuing chapter
    bottom = parchment_strip(H - hero_h + 80)
    im = Image.new("RGB", (W, H), CREAM)
    im.paste(top, (0, 0))
    im.paste(bottom.crop((0, 0, W, H - hero_h + 80)), (0, hero_h - 80))
    draw = ImageDraw.Draw(im)

    f_h = font(58, True, True)
    t = "四味草本"
    draw.text(((W - tw(draw, t, f_h)) // 2, 720), t, font=f_h, fill=INK)
    f_sub = font(28, False, True)
    s = "構想說明 · 以標籤為準"
    soft_chip(draw, s, W // 2, 810, f_sub)

    ings = [
        ("andro.jpg", "穿心蓮", "傳統清熱草本"),
        ("melissa.jpg", "香蜂草", "溫和顧脾胃感"),
        ("echinacea.jpg", "紫錐花", "換季節奏常見"),
        ("dandelion.jpg", "蒲公英", "清熱利濕敘述"),
    ]
    # 2x2 LARGE bubbles
    gap = 40
    cell_w = (W - 100 - gap) // 2
    start_y = 920
    f_name = font(36, True, True)
    f_why = font(26, False, False)
    for i, (fn, name, why) in enumerate(ings):
        col, row = i % 2, i // 2
        cx = 50 + col * (cell_w + gap) + cell_w // 2
        cy = start_y + row * 560 + 200
        bub = circle_photo(BUB / fn, 320)
        im_r = im.convert("RGBA")
        im_r.paste(bub, (cx - bub.width // 2, cy - bub.height // 2), bub)
        im = im_r.convert("RGB")
        draw = ImageDraw.Draw(im)
        draw.text((cx - tw(draw, name, f_name) // 2, cy + 200), name, font=f_name, fill=INK)
        soft_chip(draw, why, cx, cy + 260, f_why, fill_bg=(255, 244, 228), fill_fg=ORANGE_DK, pad_x=22, pad_y=10)

    f_foot = font(20, False, False)
    foot = "※ 不構成診斷、治療或預防疾病之聲稱"
    draw.text(((W - tw(draw, foot, f_foot)) // 2, H - 55), foot, font=f_foot, fill=MUTED)
    return im


def panel_04_macro() -> Image.Image:
    """blister-macro full chapter + sparse quality overlays."""
    H = 1700
    im = cover(AI / "blister-macro.jpg", W, H, focus=(0.5, 0.45))
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = top_bar(im, 70, 160)
    im = bottom_scrim(im, 0.70, (255, 248, 236), 210)
    draw = ImageDraw.Draw(im)

    f_h = font(54, True, True)
    t = "看得見的細節"
    draw.text(((W - tw(draw, t, f_h)) // 2, 1200), t, font=f_h, fill=INK)

    specs = ["香港製造", "口服膠囊", "60粒裝"]
    f_s = font(30, True, False)
    x0 = 180
    y = 1340
    for sp in specs:
        ww = tw(draw, sp, f_s)
        draw.rounded_rectangle((x0, y, x0 + ww + 56, y + 70), radius=20, fill=WHITE, outline=GOLD, width=3)
        draw.text((x0 + 28, y + 18), sp, font=f_s, fill=ORANGE_DK)
        x0 += ww + 80

    f_sub = font(24, False, False)
    sub = "盈康 · 先瀏覽規格"
    draw.text(((W - tw(draw, sub, f_sub)) // 2, 1520), sub, font=f_sub, fill=MUTED)
    return im


def panel_05_usage() -> Image.Image:
    """Huge margins dosage — Cap.231 once. Sparse, not crowded."""
    H = 1500
    # soft macro wash
    bg = cover(AI / "blister-macro.jpg", W, H, focus=(0.55, 0.45))
    bg = ImageEnhance.Brightness(bg).enhance(0.85)
    bg = ImageEnhance.Color(bg).enhance(1.05)
    # keep photo readable; light parchment veil only for plaque contrast
    parch = parchment_strip(H)
    im = Image.blend(bg, parch, 0.28)
    im = bottom_scrim(im, 0.15, (255, 248, 236), 90)
    draw = ImageDraw.Draw(im)

    f_h = font(52, True, True)
    t = "怎麼服用"
    draw.text(((W - tw(draw, t, f_h)) // 2, 120), t, font=f_h, fill=INK)

    # one huge dosage plaque
    draw.rounded_rectangle((120, 320, W - 120, 700), radius=32, fill=WHITE, outline=GOLD, width=4)
    f_big = font(44, True, True)
    big = "每日 3 次 · 每次 2 粒"
    draw.text(((W - tw(draw, big, f_big)) // 2, 420), big, font=f_big, fill=ORANGE_DK)
    f_n = font(28, False, False)
    n1 = "溫水送服 · 以標籤為準"
    draw.text(((W - tw(draw, n1, f_n)) // 2, 530), n1, font=f_n, fill=MUTED)
    n2 = "孕婦／兒童／長期病患者請先咨詢"
    draw.text(((W - tw(draw, n2, f_n)) // 2, 590), n2, font=f_n, fill=MUTED)

    # three sparse steps
    steps = ["讀標籤", "定時段", "配作息"]
    f_s = font(30, True, False)
    for i, st in enumerate(steps):
        x = 280 + i * 380
    for i, st in enumerate(steps):
        x = 280 + i * 380
        draw.ellipse((x, 820, x + 64, 884), fill=ORANGE)
        ns = str(i + 1)
        f_num = font(28, True, False)
        draw.text((x + 32 - tw(draw, ns, f_num) // 2, 834), ns, font=f_num, fill=WHITE)
        draw.text((x + 84, 836), st, font=f_s, fill=INK)

    # Cap.231 once
    draw.rectangle((0, H - 180, W, H), fill=(42, 36, 32))
    f_c = font(20, False, False)
    cap = "此產品並不供作診斷、治療或預防任何疾病之用。（Cap.231）"
    draw.text(((W - tw(draw, cap, f_c)) // 2, H - 110), cap, font=f_c, fill=(220, 214, 208))
    return im


def panel_06_trust() -> Image.Image:
    """Yinshumei philosophy ONLY + WA; AI disclaimer again."""
    H = 1800
    # soft lifestyle / spokesperson blur chapter
    bg = cover(AI / "spokesperson-v4.jpg", W, H, focus=(0.48, 0.25))
    bg = ImageEnhance.Brightness(bg).enhance(0.78)
    bg = ImageEnhance.Color(bg).enhance(1.05)
    # almost full photo chapter; light veil only behind cards
    im = bg
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(veil).rectangle((60, 150, W - 60, 1160), fill=(255, 248, 236, 55))
    im = Image.alpha_composite(im.convert("RGBA"), veil.filter(ImageFilter.GaussianBlur(8))).convert("RGB")
    draw = ImageDraw.Draw(im)

    f_h = font(50, True, True)
    t = "理念可依"
    draw.text(((W - tw(draw, t, f_h)) // 2, 70), t, font=f_h, fill=INK)

    # philosophy card
    draw.rounded_rectangle((80, 180, W - 80, 720), radius=28, fill=WHITE, outline=GOLD, width=3)
    if PORTRAIT.exists():
        portrait = Image.open(PORTRAIT).convert("RGB")
        side = min(portrait.size)
        left = (portrait.size[0] - side) // 2
        top = max(0, (portrait.size[1] - side) // 2 - 15)
        portrait = portrait.crop((left, top, left + side, top + side)).resize((320, 320), Image.Resampling.LANCZOS)
        mask = Image.new("L", (320, 320), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 319, 319), fill=255)
        circ = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
        circ.paste(portrait, (0, 0))
        circ.putalpha(mask)
        ring = Image.new("RGBA", (340, 340), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse((2, 2, 337, 337), outline=GOLD, width=5)
        im_r = im.convert("RGBA")
        im_r.paste(ring, (120, 230), ring)
        im_r.paste(circ, (130, 240), circ)
        im = im_r.convert("RGB")
        draw = ImageDraw.Draw(im)

    f_who = font(34, True, True)
    draw.text((520, 280), "尹淑梅中醫師", font=f_who, fill=ORANGE_DK)
    f_meta = font(24, False, False)
    draw.text((520, 350), "從醫五十多年 · 香港註冊中醫師", font=f_meta, fill=MUTED)
    f_q = font(30, False, True)
    q = "支持「說明可查、日常可依」"
    draw.text((520, 430), q, font=f_q, fill=INK)
    f_d = font(22, False, False)
    draw.text((520, 510), "理念認同，非療效保證", font=f_d, fill=MUTED)

    # WA CTA
    draw.rounded_rectangle((80, 800, W - 80, 1100), radius=28, fill=ORANGE)
    draw.rounded_rectangle((92, 812, W - 92, 1088), radius=22, outline=GOLD_LT, width=3)
    f_cta = font(40, True, True)
    c1 = "想了解規格？"
    c2 = "WhatsApp 6222 7238"
    draw.text(((W - tw(draw, c1, f_cta)) // 2, 860), c1, font=f_cta, fill=WHITE)
    draw.text(((W - tw(draw, c2, f_cta)) // 2, 950), c2, font=f_cta, fill=WHITE)
    f_soft = font(24, False, False)
    soft = "瀏覽為主 · 無即時扣款結帳"
    draw.text(((W - tw(draw, soft, f_soft)) // 2, 1030), soft, font=f_soft, fill=(255, 230, 210))

    draw.rectangle((0, 1280, W, H), fill=(40, 34, 30))
    f_c = font(20, False, False)
    lines = [
        "此產品並不供作診斷、治療或預防任何疾病之用。",
        "詳圖人物為虛構視覺，非真實名人代言。",
    ]
    yy = 1400
    for ln in lines:
        draw.text(((W - tw(draw, ln, f_c)) // 2, yy), ln, font=f_c, fill=(220, 214, 208))
        yy += 50
    return im


def stitch(panels):
    total = sum(p.height for p in panels)
    out = Image.new("RGB", (W, total), WHITE)
    y = 0
    for p in panels:
        out.paste(p, (0, y))
        y += p.height
    return out


def export(im: Image.Image, stem: str) -> Image.Image:
    im2 = ImageEnhance.Sharpness(im).enhance(1.04)
    im2.save(OUT / f"{stem}.png", "PNG", optimize=True)
    h750 = int(im2.height * 750 / im2.width)
    jpg = im2.resize((750, h750), Image.Resampling.LANCZOS).convert("RGB")
    jp = OUT / f"{stem}.jpg"
    jpg.save(jp, "JPEG", quality=92, optimize=True, progressive=True)
    print(f"wrote {jp.name} {jpg.size} {jp.stat().st_size // 1024}KB")
    return im2


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for req in (
        "spokesperson-v4.jpg",
        "herbs-hero.jpg",
        "blister-macro.jpg",
        "herbs-grid.jpg",
        "lifestyle-qingre.jpg",
        "lifestyle-season.jpg",
        "lifestyle-dining.jpg",
    ):
        assert (AI / req).exists(), req

    specs = [
        ("01-hero", panel_01_hero),
        ("02-benefits", panel_02_benefits),
        ("03-ingredients", panel_03_ingredients),
        ("04-macro", panel_04_macro),
        ("05-usage", panel_05_usage),
        ("06-trust-cta", panel_06_trust),
    ]
    masters = []
    for name, fn in specs:
        print("building", name)
        masters.append(export(fn(), name))

    # remove obsolete panel names from prior versions
    obsolete = [
        "02-lifestyle", "04-lifestyle", "04-usage-specs", "05-usage-specs",
        "05-endorse-cta", "03-ingredients-old",
    ]
    keep = {s[0] for s in specs}
    for p in OUT.glob("0*.jpg"):
        stem = p.stem
        if stem not in keep:
            print("remove stale", p.name)
            p.unlink(missing_ok=True)
            (OUT / f"{stem}.png").unlink(missing_ok=True)
    for p in OUT.glob("0*.png"):
        if p.stem not in keep:
            p.unlink(missing_ok=True)

    tall = stitch(masters)
    tall750 = tall.resize((750, int(tall.height * 750 / tall.width)), Image.Resampling.LANCZOS)
    longp = OUT / "detail-long-full.jpg"
    tall750.save(longp, "JPEG", quality=91, optimize=True, progressive=True)
    print(f"wrote {longp.name} {tall750.size} {longp.stat().st_size // 1024}KB")
    (OUT / "detail-long-full.png").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
