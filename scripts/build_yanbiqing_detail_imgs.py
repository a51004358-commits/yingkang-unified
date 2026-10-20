#!/usr/bin/env python3
"""v3: Vita-feel long-form 詳圖 for 強力炎必清 60粒.

Photo-first chapters: AI spokesperson hero, soft benefits on photo beds,
herbs-grid ingredient bubbles, lifestyle desk, usage, trust/WA.
Cap.231 soft TC. No Vita marks / #1 / clinical % / fake testimonials.
AI person labeled as fictional visual, not named celebrity endorsement.
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
PACK = PROD / "packshot-clean.png"
PORTRAIT = ROOT / "assets/yinshumei/portrait.jpg"
LOGO = ROOT / "assets/logo.png"

W = 1200
SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
SERIF_R = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SANS_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
IDX = 4

CREAM = (255, 250, 242)
CREAM_DEEP = (245, 232, 210)
GOLD = (196, 154, 88)
GOLD_LT = (228, 198, 140)
GOLD_DK = (140, 100, 48)
INK = (42, 36, 30)
MUTED = (110, 98, 86)
ORANGE = (196, 108, 48)
ORANGE_DK = (126, 72, 28)
WHITE = (255, 255, 255)
LINE = (220, 198, 168)


def font(size: int, bold: bool = False, serif: bool = False) -> ImageFont.FreeTypeFont:
    path = (SERIF_B if bold else SERIF_R) if serif else (SANS_B if bold else SANS_R)
    return ImageFont.truetype(path, size, index=IDX)


def tw(draw, text, fnt) -> int:
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0]


def th(draw, text, fnt) -> int:
    b = draw.textbbox((0, 0), text or " ", font=fnt)
    return b[3] - b[1]


def wrap(draw, text: str, fnt, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        cur = ""
        for ch in para:
            trial = cur + ch
            if tw(draw, trial, fnt) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
    return lines


def draw_wrapped(draw, text, x, y, fnt, fill, max_w, gap=6) -> int:
    yy = y
    for ln in wrap(draw, text, fnt, max_w):
        draw.text((x, yy), ln, font=fnt, fill=fill)
        yy += th(draw, ln or " ", fnt) + gap
    return yy


def cover(path: Path, w: int, h: int, focus=(0.5, 0.4)) -> Image.Image:
    im = Image.open(path).convert("RGB")
    scale = max(w / im.width, h / im.height)
    nw, nh = int(im.width * scale + 0.5), int(im.height * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = int((nw - w) * focus[0])
    top = int((nh - h) * focus[1])
    left = max(0, min(left, nw - w))
    top = max(0, min(top, nh - h))
    return im.crop((left, top, left + w, top + h))


def radial_overlay(h: int, c1=(255, 248, 236), c2=(232, 210, 175), opacity=0.55) -> Image.Image:
    yy, xx = np.mgrid[0:h, 0:W].astype(np.float32)
    cx, cy = W * 0.5, h * 0.3
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    r = (r / (r.max() + 1e-6)) ** 0.85
    out = np.zeros((h, W, 3), np.float32)
    for i in range(3):
        out[:, :, i] = c1[i] * (1 - r) + c2[i] * r
    rng = np.random.default_rng(11)
    out += rng.normal(0, 1.8, out.shape)
    rgb = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    # return as RGBA with uniform-ish opacity controlled by caller via blend
    return rgb


def parchment(h: int) -> Image.Image:
    """Soft parchment with noise — for non-photo chapter fills that still aren't flat."""
    base = radial_overlay(h)
    # faint gold veins
    overlay = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    rng = np.random.default_rng(3)
    for _ in range(55):
        x0 = int(rng.integers(0, W))
        y0 = int(rng.integers(0, h))
        pts = [(x0, y0)]
        for _i in range(6):
            x0 += int(rng.integers(-50, 55))
            y0 += int(rng.integers(-8, 40))
            pts.append((x0, y0))
        d.line(pts, fill=(180, 160, 120, 28), width=int(rng.integers(1, 3)))
    return Image.alpha_composite(base.convert("RGBA"), overlay.filter(ImageFilter.GaussianBlur(1))).convert("RGB")


def gradient_veil(im: Image.Image, top_a=180, bot_a=40, color=(20, 14, 10)) -> Image.Image:
    """Dark-to-light veil for text legibility over photos."""
    w, h = im.size
    veil = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = veil.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        a = int(top_a * (1 - t) + bot_a * t)
        for x in range(w):
            px[x, y] = (*color, a)
    # also bottom band for footer text
    return Image.alpha_composite(im.convert("RGBA"), veil).convert("RGB")


def bottom_scrim(im: Image.Image, from_y_ratio=0.55, color=(255, 248, 236), max_a=210) -> Image.Image:
    w, h = im.size
    start = int(h * from_y_ratio)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = overlay.load()
    for y in range(start, h):
        t = (y - start) / max(h - start - 1, 1)
        a = int(max_a * (t ** 1.15))
        for x in range(w):
            px[x, y] = (*color, a)
    return Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")


def gold_plaque(draw, box, radius=20, fill=WHITE):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=GOLD, width=3)
    draw.rounded_rectangle((x0 + 5, y0 + 5, x1 - 5, y1 - 5), radius=max(radius - 2, 4), outline=GOLD_LT, width=1)


def fit_contain(im: Image.Image, box_w: int, box_h: int) -> Image.Image:
    im = im.convert("RGBA")
    im.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)
    return im


def paste_center(base: Image.Image, overlay: Image.Image, cx: int, cy: int):
    x = cx - overlay.width // 2
    y = cy - overlay.height // 2
    if overlay.mode == "RGBA":
        base.paste(overlay, (x, y), overlay)
    else:
        base.paste(overlay, (x, y))


def soft_shadow(size, radius=28, opacity=55) -> Image.Image:
    w, h = size
    sh = Image.new("RGBA", (w + radius * 2, h + radius * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.ellipse((radius // 2, int(h * 0.55), w + radius * 1.5, h + radius * 1.5), fill=(40, 25, 10, opacity))
    return sh.filter(ImageFilter.GaussianBlur(radius))


def circle_photo(path: Path, diameter: int) -> Image.Image:
    photo = ImageOps.fit(Image.open(path).convert("RGB"), (diameter, diameter), Image.Resampling.LANCZOS)
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter - 1, diameter - 1), fill=255)
    pad = 14
    out = Image.new("RGBA", (diameter + pad * 2, diameter + pad * 2), (0, 0, 0, 0))
    glow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((2, 2, diameter + pad * 2 - 3, diameter + pad * 2 - 3), fill=(255, 230, 180, 80))
    glow = glow.filter(ImageFilter.GaussianBlur(8))
    out = Image.alpha_composite(out, glow)
    circ = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    circ.paste(photo, (0, 0))
    circ.putalpha(mask)
    out.paste(circ, (pad, pad), circ)
    d = ImageDraw.Draw(out)
    d.ellipse((pad - 3, pad - 3, pad + diameter + 2, pad + diameter + 2), outline=GOLD, width=4)
    d.ellipse((pad, pad, pad + diameter - 1, pad + diameter - 1), outline=GOLD_LT, width=1)
    return out


def rounded_photo(path: Path, w: int, h: int, radius=24, focus=(0.5, 0.4)) -> Image.Image:
    photo = cover(path, w, h, focus=focus)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(photo, (0, 0))
    out.putalpha(mask)
    # gold ring
    ring = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(ring).rounded_rectangle((1, 1, w - 2, h - 2), radius=radius, outline=GOLD + (255,), width=3)
    return Image.alpha_composite(out, ring)


# ---------- panels ----------

def panel_01_hero() -> Image.Image:
    """Full-bleed AI spokesperson + title overlay. Not tiny blister on cream."""
    H = 1680
    im = cover(AI / "spokesperson.jpg", W, H, focus=(0.48, 0.28))
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = ImageEnhance.Color(im).enhance(1.05)
    # top dark brand bar
    draw_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(draw_layer)
    d.rectangle((0, 0, W, 92), fill=(30, 24, 20, 210))
    # bottom cream scrim for title readability
    im = bottom_scrim(im, 0.58, (255, 246, 232), 225)
    # soft top vignette
    topv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = topv.load()
    for y in range(160):
        a = int(90 * (1 - y / 160))
        for x in range(W):
            px[x, y] = (20, 14, 10, a)
    im = Image.alpha_composite(im.convert("RGBA"), topv)
    im = Image.alpha_composite(im, draw_layer).convert("RGB")
    draw = ImageDraw.Draw(im)

    if LOGO.exists():
        logo = fit_contain(Image.open(LOGO), 150, 42)
        im_r = im.convert("RGBA")
        paste_center(im_r, logo, 95, 46)
        im = im_r.convert("RGB")
        draw = ImageDraw.Draw(im)
    f_brand = font(24, True, False)
    draw.text((180, 30), "盈康 · 香港本地健康品牌", font=f_brand, fill=GOLD_LT)

    # eyebrow
    f_eye = font(26, True, False)
    eye = "口服膠囊 · 香港製造"
    ew = tw(draw, eye, f_eye)
    pill = (W // 2 - ew // 2 - 28, 920, W // 2 + ew // 2 + 28, 972)
    gold_plaque(draw, pill, 20, fill=(255, 252, 246))
    draw.text(((W - ew) // 2, 932), eye, font=f_eye, fill=ORANGE_DK)

    f_title = font(66, True, True)
    title = "強力炎必清 60粒"
    draw.text(((W - tw(draw, title, f_title)) // 2, 1000), title, font=f_title, fill=INK)

    f_sub = font(30, False, True)
    sub = "草本日常輕養生｜說明可查、日常可依"
    draw.text(((W - tw(draw, sub, f_sub)) // 2, 1090), sub, font=f_sub, fill=MUTED)

    # small packshot floating lower-right for product clarity
    if PACK.exists():
        pack = fit_contain(Image.open(PACK), 280, 360)
        im_r = im.convert("RGBA")
        sh = soft_shadow((pack.width, pack.height), 22, 50)
        im_r.paste(sh, (W - pack.width - 70, 1180), sh)
        im_r.paste(pack, (W - pack.width - 50, 1160), pack)
        im = im_r.convert("RGB")
        draw = ImageDraw.Draw(im)

    f_ai = font(18, False, False)
    ai_line = "形象為虛構視覺，非真實名人代言"
    draw.text(((W - tw(draw, ai_line, f_ai)) // 2, 1580), ai_line, font=f_ai, fill=MUTED)

    f_b = font(22, False, False)
    chip = "瀏覽為主｜WhatsApp 6222 7238"
    cw = tw(draw, chip, f_b)
    gold_plaque(draw, (W // 2 - cw // 2 - 22, 1485, W // 2 + cw // 2 + 22, 1540), 16, fill=WHITE)
    draw.text(((W - cw) // 2, 1498), chip, font=f_b, fill=ORANGE_DK)
    return im


def panel_02_benefits() -> Image.Image:
    """Why browse — soft benefit lines on REAL photo cards (no doodle icons)."""
    H = 1620
    # full-bleed lifestyle chapter bg
    bg = cover(AI / "lifestyle-desk.jpg", W, H, focus=(0.5, 0.45))
    bg = ImageEnhance.Brightness(bg).enhance(0.72)
    bg = ImageEnhance.Color(bg).enhance(0.9)
    # parchment radial blend so cards pop
    parch = parchment(H)
    im = Image.blend(bg, parch, 0.55)
    draw = ImageDraw.Draw(im)

    f_h = font(48, True, True)
    t = "為什麼想了解炎必清？"
    draw.text(((W - tw(draw, t, f_h)) // 2, 48), t, font=f_h, fill=INK)
    f_note = font(22, False, False)
    note = "以下為生活節奏與配方構想說明，並非診斷、治療或預防疾病之用。"
    draw.text(((W - tw(draw, note, f_note)) // 2, 120), note, font=f_note, fill=MUTED)

    # photo sources for each card
    cards = [
        (AI / "lifestyle-desk.jpg", (0.35, 0.4), "日常清熱草本節奏", "把草本膠囊寫進日常作息，先了解再說。"),
        (BUB / "echinacea.jpg", (0.5, 0.45), "換季時節想維持舒適", "冷暖交替時，留意個人舒適度。"),
        (BUB / "melissa.jpg", (0.5, 0.5), "飲食應酬後想輕一點", "應酬、外賣較多的日子，想輕一點。"),
        (BUB / "dandelion.jpg", (0.5, 0.45), "居家備存先了解規格", "先看標籤與說明，需要時再查詢選購。"),
    ]
    gap = 26
    card_w = (W - 80 - gap) // 2
    card_h = 620
    start_y = 180
    f_c = font(30, True, True)
    f_p = font(22, False, False)
    for i, (path, focus, title, body) in enumerate(cards):
        col, row = i % 2, i // 2
        x0 = 40 + col * (card_w + gap)
        y0 = start_y + row * (card_h + gap)
        photo_h = 360
        rp = rounded_photo(path, card_w, photo_h, radius=18, focus=focus)
        # plaque under
        gold_plaque(draw, (x0, y0, x0 + card_w, y0 + card_h), 20, fill=(255, 252, 246))
        im_r = im.convert("RGBA")
        im_r.paste(rp, (x0, y0), rp)
        im = im_r.convert("RGB")
        draw = ImageDraw.Draw(im)
        # caption
        draw.rectangle((x0 + 3, y0 + photo_h - 2, x0 + card_w - 3, y0 + card_h - 3), fill=WHITE)
        twt = tw(draw, title, f_c)
        draw.text((x0 + (card_w - twt) // 2, y0 + photo_h + 28), title, font=f_c, fill=ORANGE_DK)
        draw_wrapped(draw, body, x0 + 28, y0 + photo_h + 90, f_p, MUTED, card_w - 56, 6)

    f_cap = font(18, False, False)
    cap = "※ 一般健康產品說明（Cap.231）· 不構成療效保證"
    draw.text(((W - tw(draw, cap, f_cap)) // 2, H - 48), cap, font=f_cap, fill=MUTED)
    return im


def panel_03_ingredients() -> Image.Image:
    """MAIN ask — 4 luminous PHOTO circles from herbs-grid + soft benefit lines."""
    H = 1780
    # chapter bg: soft crop of herbs-grid blurred + parchment
    herb_bg = cover(AI / "herbs-grid.jpg", W, H, focus=(0.5, 0.5))
    herb_bg = herb_bg.filter(ImageFilter.GaussianBlur(6))
    herb_bg = ImageEnhance.Brightness(herb_bg).enhance(1.08)
    herb_bg = ImageEnhance.Color(herb_bg).enhance(1.1)
    parch = parchment(H)
    im = Image.blend(herb_bg, parch, 0.35)
    draw = ImageDraw.Draw(im)

    f_h = font(46, True, True)
    t = "主要草本成分"
    draw.text(((W - tw(draw, t, f_h)) // 2, 44), t, font=f_h, fill=INK)
    f_sub = font(24, False, True)
    s = "配方構想說明 · 實際以包裝標籤為準"
    draw.text(((W - tw(draw, s, f_sub)) // 2, 112), s, font=f_sub, fill=MUTED)

    ings = [
        ("andro.jpg", "穿心蓮", "Andrographis", "傳統清熱草本，常見於日常養生配方"),
        ("melissa.jpg", "香蜂草", "Melissa", "溫和草本，顧及脾胃感受的常見搭配"),
        ("echinacea.jpg", "紫錐花", "Echinacea", "換季節奏期常見的免疫草本敘述"),
        ("dandelion.jpg", "蒲公英", "Dandelion", "傳統清熱利濕草本，用於日常說明"),
    ]
    f_name = font(34, True, True)
    f_lat = font(22, False, False)
    f_why = font(24, False, False)
    y0 = 190
    for i, (fn, name, lat, why) in enumerate(ings):
        y = y0 + i * 370
        gold_plaque(draw, (40, y, W - 40, y + 340), 22, fill=(255, 252, 246))
        bub = circle_photo(BUB / fn, 220)
        im_r = im.convert("RGBA")
        im_r.paste(bub, (70, y + 50), bub)
        im = im_r.convert("RGB")
        draw = ImageDraw.Draw(im)
        # number badge
        draw.ellipse((W - 140, y + 40, W - 70, y + 110), fill=CREAM_DEEP, outline=GOLD, width=3)
        num = f"{i+1:02d}"
        f_n = font(26, True, False)
        draw.text((W - 105 - tw(draw, num, f_n) // 2, y + 58), num, font=f_n, fill=ORANGE_DK)
        draw.text((360, y + 70), name, font=f_name, fill=INK)
        draw.text((360, y + 125), lat, font=f_lat, fill=GOLD_DK)
        # soft benefit line in gold-edged chip
        chip_y = y + 190
        draw.rounded_rectangle((360, chip_y, W - 90, chip_y + 90), radius=14, fill=(255, 244, 228), outline=GOLD_LT, width=2)
        draw_wrapped(draw, why, 390, chip_y + 28, f_why, ORANGE_DK, W - 500, 4)

    f_foot = font(18, False, False)
    foot = "※ 成分敘述不構成診斷、治療或預防任何疾病之聲稱"
    draw.text(((W - tw(draw, foot, f_foot)) // 2, H - 46), foot, font=f_foot, fill=MUTED)
    return im


def panel_04_lifestyle() -> Image.Image:
    """Full-bleed lifestyle desk + packshot rhythm."""
    H = 1480
    im = cover(AI / "lifestyle-desk.jpg", W, H, focus=(0.55, 0.45))
    im = ImageEnhance.Contrast(im).enhance(1.05)
    im = bottom_scrim(im, 0.62, (255, 248, 236), 230)
    # slight top brand tint
    top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(top).rectangle((0, 0, W, 70), fill=(30, 24, 20, 160))
    im = Image.alpha_composite(im.convert("RGBA"), top).convert("RGB")
    draw = ImageDraw.Draw(im)

    f_h = font(46, True, True)
    t = "寫進日常的輕養生節奏"
    draw.text(((W - tw(draw, t, f_h)) // 2, 100), t, font=f_h, fill=WHITE)
    f_sub = font(24, False, False)
    sub = "一杯水 · 一板膠囊 · 先瀏覽規格再決定"
    # soft chip for sub
    sw = tw(draw, sub, f_sub)
    draw.rounded_rectangle((W // 2 - sw // 2 - 20, 170, W // 2 + sw // 2 + 20, 220), radius=14, fill=(255, 252, 246, ))
    draw.rounded_rectangle((W // 2 - sw // 2 - 20, 170, W // 2 + sw // 2 + 20, 220), radius=14, fill=WHITE, outline=GOLD, width=2)
    draw.text(((W - sw) // 2, 182), sub, font=f_sub, fill=MUTED)

    if PACK.exists():
        pack = fit_contain(Image.open(PACK), 360, 460)
        im_r = im.convert("RGBA")
        sh = soft_shadow((pack.width, pack.height), 30, 55)
        im_r.paste(sh, ((W - sh.width) // 2, 980), sh)
        paste_center(im_r, pack, W // 2, 1180)
        im = im_r.convert("RGB")
        draw = ImageDraw.Draw(im)

    lines = ["把服用放進固定時段", "配合作息與喝水習慣", "不適請停止並咨詢醫護"]
    f_l = font(24, True, False)
    y = 1280
    for ln in lines:
        lw = tw(draw, ln, f_l)
        gold_plaque(draw, (W // 2 - lw // 2 - 24, y, W // 2 + lw // 2 + 24, y + 48), 14, fill=WHITE)
        draw.text(((W - lw) // 2, y + 10), ln, font=f_l, fill=ORANGE_DK)
        y += 58
    return im


def panel_05_usage() -> Image.Image:
    H = 1520
    # soft photo wash behind parchment
    bg = cover(AI / "lifestyle-desk.jpg", W, H, focus=(0.4, 0.6))
    bg = ImageEnhance.Brightness(bg).enhance(1.2)
    bg = bg.filter(ImageFilter.GaussianBlur(12))
    im = Image.blend(bg, parchment(H), 0.7)
    draw = ImageDraw.Draw(im)

    f_h = font(46, True, True)
    t = "建議用法與產品規格"
    draw.text(((W - tw(draw, t, f_h)) // 2, 48), t, font=f_h, fill=INK)

    gold_plaque(draw, (50, 130, W - 50, 360), 22, fill=(255, 252, 246))
    f_big = font(36, True, True)
    big = "成人：每日 3 次，每次 2 粒"
    draw.text(((W - tw(draw, big, f_big)) // 2, 175), big, font=f_big, fill=ORANGE_DK)
    f_n = font(24, False, False)
    for i, line in enumerate(["溫水送服。請以包裝標籤為準。", "孕婦、兒童及長期病患者請先咨詢專業意見。"]):
        draw.text(((W - tw(draw, line, f_n)) // 2, 250 + i * 40), line, font=f_n, fill=MUTED)

    steps = ["先讀標籤", "固定時段", "配合作息"]
    f_s = font(26, True, False)
    for i, st in enumerate(steps):
        x = 150 + i * 340
        y = 400
        draw.ellipse((x, y, x + 56, y + 56), fill=ORANGE)
        f_num = font(24, True, False)
        ns = str(i + 1)
        draw.text((x + 28 - tw(draw, ns, f_num) // 2, y + 12), ns, font=f_num, fill=WHITE)
        draw.text((x + 72, y + 14), st, font=f_s, fill=INK)

    f_h2 = font(34, True, True)
    draw.text((50, 500), "產品規格", font=f_h2, fill=INK)
    rows = [
        ("產品名稱", "強力炎必清 60粒"),
        ("品牌", "盈康"),
        ("分類", "口服膠囊"),
        ("建議用法", "成人每日 3 次，每次 2 粒"),
        ("保存", "陰涼乾爽處（約 25°C 以下）"),
        ("參考售價", "HK$199"),
        ("客服備援", "WhatsApp 6222 7238"),
    ]
    y = 570
    f_th = font(22, True, False)
    f_td = font(22, False, False)
    for i, (a, b) in enumerate(rows):
        bgc = CREAM if i % 2 == 0 else WHITE
        draw.rectangle((50, y, W - 50, y + 54), fill=bgc, outline=LINE)
        draw.text((70, y + 14), a, font=f_th, fill=ORANGE_DK)
        draw.text((320, y + 14), b, font=f_td, fill=INK)
        y += 54

    # Cap.231 band
    draw.rectangle((0, H - 160, W, H), fill=(48, 42, 38))
    f_c = font(18, False, False)
    cap = (
        "此產品沒有根據《藥劑業及毒藥條例》或《中醫藥條例》註冊。"
        "為此產品作出的任何聲稱亦沒有為進行該等註冊而接受評核。"
        "此產品並不供作診斷、治療或預防任何疾病之用。"
    )
    draw_wrapped(draw, cap, 50, H - 130, f_c, (220, 214, 208), W - 100, 5)
    return im


def panel_06_trust_cta() -> Image.Image:
    H = 1580
    # soft spokesperson blur as premium bg chapter
    bg = cover(AI / "spokesperson.jpg", W, H, focus=(0.5, 0.35))
    bg = ImageEnhance.Brightness(bg).enhance(0.55)
    bg = bg.filter(ImageFilter.GaussianBlur(10))
    parch = parchment(H)
    im = Image.blend(bg, parch, 0.45)
    draw = ImageDraw.Draw(im)

    f_h = font(44, True, True)
    t = "理念推薦 · 查詢規格"
    draw.text(((W - tw(draw, t, f_h)) // 2, 48), t, font=f_h, fill=INK)

    # yinshumei philosophy card
    gold_plaque(draw, (50, 130, W - 50, 520), 22, fill=(255, 252, 246))
    if PORTRAIT.exists():
        portrait = Image.open(PORTRAIT).convert("RGB")
        pw, ph = portrait.size
        side = min(pw, ph)
        left = (pw - side) // 2
        top = max(0, (ph - side) // 2 - 20)
        portrait = portrait.crop((left, top, left + side, top + side)).resize((280, 280), Image.Resampling.LANCZOS)
        mask = Image.new("L", (280, 280), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 280, 280), fill=255)
        circ = Image.new("RGBA", (280, 280), (0, 0, 0, 0))
        circ.paste(portrait, (0, 0))
        circ.putalpha(mask)
        ring = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse((2, 2, 297, 297), outline=GOLD, width=4)
        im_r = im.convert("RGBA")
        im_r.paste(ring, (80, 170), ring)
        im_r.paste(circ, (90, 180), circ)
        im = im_r.convert("RGB")
        draw = ImageDraw.Draw(im)

    f_who = font(30, True, True)
    draw.text((430, 190), "尹淑梅中醫師", font=f_who, fill=ORANGE_DK)
    f_meta = font(20, False, False)
    draw_wrapped(draw, "從醫五十多年・香港註冊中醫師\n香港中國醫藥研究院榮譽院長", 430, 245, f_meta, MUTED, 640, 6)
    f_quote = font(26, False, True)
    draw_wrapped(draw, "支持盈康「說明可查、日常可依」的輕養生理念。", 90, 400, f_quote, INK, W - 180, 8)
    f_disc = font(18, False, False)
    draw_wrapped(draw, "理念認同，非療效保證。形象圖為虛構視覺，非真實名人代言。", 90, 470, f_disc, MUTED, W - 180, 4)

    trusts = [("香港製造", "本地品質把關"), ("草本配方", "成分說明可查"), ("瀏覽為主", "無即時扣款結帳"), ("客服備援", "WhatsApp 查詢")]
    f_tt = font(24, True, False)
    f_ts = font(18, False, False)
    for i, (a, b) in enumerate(trusts):
        x = 50 + i * 280
        gold_plaque(draw, (x, 560, x + 260, 700), 14, fill=WHITE)
        draw.text((x + (260 - tw(draw, a, f_tt)) // 2, 595), a, font=f_tt, fill=ORANGE_DK)
        draw.text((x + (260 - tw(draw, b, f_ts)) // 2, 645), b, font=f_ts, fill=MUTED)

    draw.rounded_rectangle((50, 740, W - 50, 980), radius=22, fill=ORANGE)
    draw.rounded_rectangle((58, 748, W - 58, 972), radius=18, outline=GOLD_LT, width=2)
    f_cta = font(34, True, True)
    c1, c2 = "想了解規格或庫存？", "WhatsApp 6222 7238"
    draw.text(((W - tw(draw, c1, f_cta)) // 2, 790), c1, font=f_cta, fill=WHITE)
    draw.text(((W - tw(draw, c2, f_cta)) // 2, 860), c2, font=f_cta, fill=WHITE)
    f_soft = font(20, False, False)
    soft = "瀏覽為主｜本頁不含即時扣款結帳｜亦可於 HKTVmall 瀏覽"
    draw.text(((W - tw(draw, soft, f_soft)) // 2, 930), soft, font=f_soft, fill=(255, 230, 210))

    draw.rectangle((0, 1040, W, H), fill=(40, 34, 30))
    f_c = font(17, False, False)
    cap = (
        "此產品沒有根據《藥劑業及毒藥條例》或《中醫藥條例》註冊。"
        "為此產品作出的任何聲稱亦沒有為進行該等註冊而接受評核。"
        "此產品並不供作診斷、治療或預防任何疾病之用。"
        "詳圖中人物形象為虛構視覺，非真實名人代言。"
    )
    draw_wrapped(draw, cap, 50, 1090, f_c, (220, 214, 208), W - 100, 5)
    return im


def stitch(panels: list[Image.Image]) -> Image.Image:
    total_h = sum(p.height for p in panels)
    out = Image.new("RGB", (W, total_h), WHITE)
    y = 0
    for p in panels:
        out.paste(p, (0, y))
        y += p.height
    return out


def export_web(im: Image.Image, stem: str):
    im2 = ImageEnhance.Sharpness(im).enhance(1.05)
    im2.save(OUT / f"{stem}.png", "PNG", optimize=True)
    h750 = int(im2.height * 750 / im2.width)
    jpg = im2.resize((750, h750), Image.Resampling.LANCZOS).convert("RGB")
    jp = OUT / f"{stem}.jpg"
    jpg.save(jp, "JPEG", quality=92, optimize=True, progressive=True)
    print(f"wrote {jp.name} {jpg.size} {jp.stat().st_size // 1024}KB")
    return im2


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    BUB.mkdir(parents=True, exist_ok=True)
    assert (AI / "spokesperson.jpg").exists()
    assert (AI / "herbs-grid.jpg").exists()
    assert (AI / "lifestyle-desk.jpg").exists()

    specs = [
        ("01-hero", panel_01_hero),
        ("02-benefits", panel_02_benefits),
        ("03-ingredients", panel_03_ingredients),
        ("04-lifestyle", panel_04_lifestyle),
        ("05-usage-specs", panel_05_usage),
        ("06-trust-cta", panel_06_trust_cta),
    ]
    masters = []
    for name, fn in specs:
        print("building", name)
        masters.append(export_web(fn(), name))

    # remove obsolete v2 panel filenames if present
    for obsolete in ("02-lifestyle", "05-endorse-cta"):
        for ext in (".jpg", ".png"):
            p = OUT / f"{obsolete}{ext}"
            if p.exists() and obsolete not in [s[0] for s in specs]:
                # keep if somehow still referenced — we update HTML; delete old names
                p.unlink()
                print("removed", p.name)

    tall = stitch(masters)
    tall_750 = tall.resize((750, int(tall.height * 750 / tall.width)), Image.Resampling.LANCZOS)
    long_jpg = OUT / "detail-long-full.jpg"
    tall_750.save(long_jpg, "JPEG", quality=91, optimize=True, progressive=True)
    print(f"wrote {long_jpg.name} {tall_750.size} {long_jpg.stat().st_size // 1024}KB")
    stale = OUT / "detail-long-full.png"
    if stale.exists():
        stale.unlink()


if __name__ == "__main__":
    main()
