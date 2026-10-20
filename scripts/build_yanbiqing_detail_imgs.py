#!/usr/bin/env python3
"""Build Vita-feel long-form detail images for 強力炎必清 60粒 (v2).

Premium cream+gold retail rhythm. Cap.231 soft TC. No Vita trademarks,
no #1/clinical %, no fake testimonials, no claim-dense collage packshot.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PROD_DIR = ROOT / "assets/products/yanbiqing-60caps-y5"
OUT = PROD_DIR / "detail"
PACK = PROD_DIR / "packshot-clean.png"
BEDS = OUT / "beds"
BUB = OUT / "bubbles"
PORTRAIT = ROOT / "assets/yinshumei/portrait.jpg"
LOGO = ROOT / "assets/logo.png"

W = 1200  # master width; export 750w JPEG
SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
SERIF_R = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SANS_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
IDX = 4  # HK

# Palette: cream + warm gold + deep ink; muted Yingkang orange accent
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
    if serif:
        path = SERIF_B if bold else SERIF_R
    else:
        path = SANS_B if bold else SANS_R
    return ImageFont.truetype(path, size, index=IDX)


def text_w(draw, text, fnt) -> int:
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0]


def text_h(draw, text, fnt) -> int:
    b = draw.textbbox((0, 0), text or " ", font=fnt)
    return b[3] - b[1]


def wrap_text(draw, text: str, fnt, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        cur = ""
        for ch in para:
            trial = cur + ch
            if text_w(draw, trial, fnt) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
    return lines


def draw_wrapped(draw, text, x, y, fnt, fill, max_w, line_gap=6) -> int:
    yy = y
    for ln in wrap_text(draw, text, fnt, max_w):
        draw.text((x, yy), ln, font=fnt, fill=fill)
        yy += text_h(draw, ln or " ", fnt) + line_gap
    return yy


def radial_bg(h: int, c1=CREAM, c2=CREAM_DEEP, cx_ratio=0.5, cy_ratio=0.35) -> Image.Image:
    yy, xx = np.mgrid[0:h, 0:W].astype(np.float32)
    cx, cy = W * cx_ratio, h * cy_ratio
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    r = (r / (r.max() + 1e-6)) ** 0.82
    out = np.zeros((h, W, 3), np.float32)
    for i in range(3):
        out[:, :, i] = c1[i] * (1 - r) + c2[i] * r
    rng = np.random.default_rng(17)
    out += rng.normal(0, 2.2, out.shape)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def soft_shadow(size, radius=32, opacity=55) -> Image.Image:
    w, h = size
    sh = Image.new("RGBA", (w + radius * 2, h + radius * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.ellipse(
        (radius // 2, h // 2 + radius // 3, w + radius * 1.5, h + radius * 1.6),
        fill=(40, 25, 10, opacity),
    )
    return sh.filter(ImageFilter.GaussianBlur(radius))


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


def gold_plaque(draw, box, radius=22):
    """Outer gold hairline + cream fill."""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=radius, fill=WHITE, outline=GOLD, width=3)
    draw.rounded_rectangle(
        (x0 + 5, y0 + 5, x1 - 5, y1 - 5), radius=radius - 2, outline=GOLD_LT, width=1
    )


def circle_bubble(photo: Image.Image, diameter: int, ring=True) -> Image.Image:
    photo = photo.convert("RGB").resize((diameter, diameter), Image.Resampling.LANCZOS)
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter - 1, diameter - 1), fill=255)
    out = Image.new("RGBA", (diameter + 12, diameter + 12), (0, 0, 0, 0))
    circ = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    circ.paste(photo, (0, 0))
    circ.putalpha(mask)
    # soft glow behind
    glow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((0, 0, diameter + 11, diameter + 11), fill=(255, 230, 180, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(6))
    out = Image.alpha_composite(out, glow)
    out.paste(circ, (6, 6), circ)
    if ring:
        d = ImageDraw.Draw(out)
        d.ellipse((4, 4, diameter + 7, diameter + 7), outline=GOLD, width=3)
        d.ellipse((7, 7, diameter + 4, diameter + 4), outline=GOLD_LT, width=1)
    return out


def cover_fill(path: Path, w: int, h: int) -> Image.Image:
    im = Image.open(path).convert("RGB")
    scale = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.Resampling.LANCZOS)
    left = (im.width - w) // 2
    top = (im.height - h) // 2
    return im.crop((left, top, left + w, top + h))


def panel_hero() -> Image.Image:
    H = 1680
    # Photo bed + radial overlay
    bed = cover_fill(BEDS / "marble-herbs.jpg", W, H)
    veil = radial_bg(H, (255, 252, 246), (245, 228, 200))
    im = Image.blend(bed, veil, 0.42)
    # top gold-cream brand band
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, W, 88), fill=(48, 38, 30))
    if LOGO.exists():
        logo = fit_contain(Image.open(LOGO), 160, 44)
        # brighten on dark bar
        paste_center(im.convert("RGBA"), logo, 100, 44)  # type ignore via reassign
        im_r = im.convert("RGBA")
        paste_center(im_r, logo, 100, 44)
        im = im_r.convert("RGB")
        draw = ImageDraw.Draw(im)
    f_brand = font(24, True, False)
    draw.text((190, 28), "盈康 · 香港本地健康品牌", font=f_brand, fill=GOLD_LT)

    # eyebrow pill
    f_eye = font(26, True, False)
    eye = "口服膠囊 · 香港製造"
    ew = text_w(draw, eye, f_eye)
    pill = (W // 2 - ew // 2 - 28, 120, W // 2 + ew // 2 + 28, 172)
    gold_plaque(draw, pill, 20)
    draw.text(((W - ew) // 2, 132), eye, font=f_eye, fill=ORANGE_DK)

    # title serif
    f_title = font(64, True, True)
    title = "強力炎必清 60粒"
    tw = text_w(draw, title, f_title)
    draw.text(((W - tw) // 2, 200), title, font=f_title, fill=INK)

    f_sub = font(28, False, True)
    sub = "草本日常輕養生"
    sw = text_w(draw, sub, f_sub)
    draw.text(((W - sw) // 2, 285), sub, font=f_sub, fill=MUTED)

    # packshot
    pack = fit_contain(Image.open(PACK), 720, 900)
    im_r = im.convert("RGBA")
    sh = soft_shadow((pack.width, pack.height), 40, 60)
    sx = (W - sh.width) // 2
    sy = 340
    im_r.paste(sh, (sx, sy + 50), sh)
    paste_center(im_r, pack, W // 2, 780)
    im = im_r.convert("RGB")
    draw = ImageDraw.Draw(im)

    # soft bullets — few words
    bullets = [
        "穿心蓮 · 香蜂草 · 紫錐花 · 蒲公英",
        "瀏覽為主｜需要時 WhatsApp 6222 7238",
    ]
    y = 1280
    f_b = font(26, False, False)
    for b in bullets:
        bw = text_w(draw, b, f_b)
        # soft chip
        chip = (W // 2 - bw // 2 - 24, y - 6, W // 2 + bw // 2 + 24, y + 40)
        draw.rounded_rectangle(chip, radius=16, fill=(255, 252, 246, ), outline=LINE, width=1)
        # pillow RGB only — redraw
        draw.rounded_rectangle(chip, radius=16, fill=WHITE, outline=LINE, width=1)
        draw.text(((W - bw) // 2, y), b, font=f_b, fill=ORANGE_DK)
        y += 64

    # bottom gold hairline
    draw.rectangle((80, H - 36, W - 80, H - 32), fill=GOLD_LT)
    return im


def panel_lifestyle() -> Image.Image:
    H = 1580
    im = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(im)

    f_h = font(48, True, True)
    t = "這些日常節奏，你也熟悉嗎？"
    draw.text(((W - text_w(draw, t, f_h)) // 2, 56), t, font=f_h, fill=INK)
    f_note = font(22, False, False)
    note = "生活節奏描述，並非針對任何疾病的建議。"
    draw.text(((W - text_w(draw, note, f_note)) // 2, 125), note, font=f_note, fill=MUTED)

    cards = [
        (BEDS / "night-desk.jpg", "熬夜節奏", "加班、追劇後，想把作息調回穩定"),
        (BEDS / "marble-herbs.jpg", "飲食偏油", "應酬、外賣較多的日子，想輕一點"),
        (BEDS / "seasonal-window.jpg", "換季作息", "冷暖交替時，留意個人舒適度"),
        (BEDS / "packshot-studio.jpg", "居家備存", "先了解規格，需要時再查詢"),
    ]
    gap = 28
    card_w = (W - 80 - gap) // 2
    card_h = 580
    start_y = 180
    f_c = font(30, True, True)
    f_p = font(22, False, False)
    for i, (bed, title, body) in enumerate(cards):
        col, row = i % 2, i // 2
        x0 = 40 + col * (card_w + gap)
        y0 = start_y + row * (card_h + gap)
        # photo top
        photo_h = 340
        photo = cover_fill(bed, card_w - 8, photo_h)
        # rounded mask approx via paste into plaque
        gold_plaque(draw, (x0, y0, x0 + card_w, y0 + card_h), 20)
        # photo with slight inset
        im.paste(photo, (x0 + 4, y0 + 4))
        # cream caption band
        draw.rectangle((x0 + 4, y0 + photo_h + 4, x0 + card_w - 4, y0 + card_h - 4), fill=WHITE)
        tw = text_w(draw, title, f_c)
        draw.text((x0 + (card_w - tw) // 2, y0 + photo_h + 30), title, font=f_c, fill=ORANGE_DK)
        draw_wrapped(draw, body, x0 + 28, y0 + photo_h + 85, f_p, MUTED, card_w - 56, 6)

    # bottom soft strip
    draw.rounded_rectangle((40, H - 100, W - 40, H - 40), radius=16, fill=(236, 245, 238))
    f_s = font(24, True, False)
    s = "把草本膠囊納入日常 · 先瀏覽、再決定"
    draw.text(((W - text_w(draw, s, f_s)) // 2, H - 82), s, font=f_s, fill=(46, 100, 70))
    return im


def panel_ingredients() -> Image.Image:
    H = 1720
    im = radial_bg(H, CREAM, (255, 255, 255))
    draw = ImageDraw.Draw(im)

    f_h = font(48, True, True)
    t = "主要草本成分"
    draw.text(((W - text_w(draw, t, f_h)) // 2, 50), t, font=f_h, fill=INK)
    f_sub = font(22, False, False)
    s = "配方構想說明僅供參考，實際以包裝標籤為準"
    draw.text(((W - text_w(draw, s, f_sub)) // 2, 118), s, font=f_sub, fill=MUTED)

    # large packshot left
    pack = fit_contain(Image.open(PACK), 420, 520)
    im_r = im.convert("RGBA")
    sh = soft_shadow((pack.width, pack.height), 28, 50)
    im_r.paste(sh, (50, 180), sh)
    im_r.paste(pack, (70, 190), pack)
    im = im_r.convert("RGB")
    draw = ImageDraw.Draw(im)

    gold_plaque(draw, (540, 220, W - 50, 560), 18)
    f_b = font(28, True, True)
    f_p = font(24, False, False)
    lines = ["四味常見養生草本", "穿心蓮｜香蜂草", "紫錐花｜蒲公英", "", "一般健康產品說明", "不涉及療效保證"]
    yy = 260
    for i, ln in enumerate(lines):
        if not ln:
            yy += 18
            continue
        f = f_b if i == 0 else f_p
        c = ORANGE_DK if i == 0 else MUTED
        draw.text((580, yy), ln, font=f, fill=c)
        yy += 42

    ings = [
        ("andro.jpg", "穿心蓮", "Andrographis", "傳統清熱草本，常見於日常養生配方。"),
        ("melissa.jpg", "香蜂草", "Melissa", "溫和草本，顧及脾胃感受的常見搭配。"),
        ("echinacea.jpg", "紫錐花", "Echinacea", "季節轉換期常見的免疫草本敘述。"),
        ("dandelion.jpg", "蒲公英", "Dandelion", "傳統清熱利濕草本，用於日常說明。"),
    ]
    y0 = 600
    f_name = font(32, True, True)
    f_lat = font(20, False, False)
    f_why = font(22, False, False)
    for i, (fn, name, lat, why) in enumerate(ings):
        y = y0 + i * 250
        gold_plaque(draw, (40, y, W - 40, y + 230), 18)
        bub = circle_bubble(Image.open(BUB / fn), 160)
        im_r = im.convert("RGBA")
        im_r.paste(bub, (70, y + 30), bub)
        im = im_r.convert("RGB")
        draw = ImageDraw.Draw(im)
        draw.text((280, y + 50), name, font=f_name, fill=INK)
        draw.text((280, y + 100), lat, font=f_lat, fill=GOLD_DK)
        draw_wrapped(draw, why, 280, y + 140, f_why, MUTED, W - 360, 6)

    return im


def panel_usage_specs() -> Image.Image:
    H = 1560
    im = radial_bg(H, WHITE, (240, 246, 250), 0.5, 0.2)
    draw = ImageDraw.Draw(im)

    f_h = font(48, True, True)
    t = "建議用法與產品規格"
    draw.text(((W - text_w(draw, t, f_h)) // 2, 50), t, font=f_h, fill=INK)

    gold_plaque(draw, (50, 130, W - 50, 360), 22)
    f_big = font(36, True, True)
    big = "成人：每日 3 次，每次 2 粒"
    draw.text(((W - text_w(draw, big, f_big)) // 2, 175), big, font=f_big, fill=ORANGE_DK)
    f_n = font(24, False, False)
    for i, line in enumerate(["溫水送服。請以包裝標籤為準。", "孕婦、兒童及長期病患者請先咨詢專業意見。"]):
        draw.text(((W - text_w(draw, line, f_n)) // 2, 250 + i * 40), line, font=f_n, fill=MUTED)

    # 3 steps
    steps = ["先讀標籤", "固定時段", "配合作息"]
    f_s = font(26, True, False)
    for i, st in enumerate(steps):
        x = 140 + i * 340
        y = 400
        draw.ellipse((x, y, x + 56, y + 56), fill=ORANGE)
        f_num = font(24, True, False)
        ns = str(i + 1)
        draw.text((x + 28 - text_w(draw, ns, f_num) // 2, y + 12), ns, font=f_num, fill=WHITE)
        draw.text((x + 70, y + 14), st, font=f_s, fill=INK)

    f_h2 = font(34, True, True)
    draw.text((50, 500), "寫進日常節奏", font=f_h2, fill=INK)
    stages = [
        ("第 1 日", "依標籤開始；配合喝水與規律作息。"),
        ("第 1 週", "寫進固定時段，比臨時想起更易持續。"),
        ("日常", "與飲食、睡眠一併調整。不適請停止並咨詢醫護。"),
    ]
    f_st = font(26, True, False)
    f_bd = font(22, False, False)
    for i, (title, body) in enumerate(stages):
        y = 570 + i * 120
        gold_plaque(draw, (50, y, W - 50, y + 100), 14)
        draw.rectangle((50, y, 66, y + 100), fill=GOLD)
        draw.text((90, y + 20), title, font=f_st, fill=ORANGE_DK)
        draw_wrapped(draw, body, 90, y + 56, f_bd, MUTED, W - 180, 4)

    draw.text((50, 960), "產品規格", font=f_h2, fill=INK)
    rows = [
        ("產品名稱", "強力炎必清 60粒"),
        ("品牌", "盈康"),
        ("分類", "口服膠囊"),
        ("建議用法", "成人每日 3 次，每次 2 粒"),
        ("保存", "陰涼乾爽處（約 25°C 以下）"),
        ("參考售價", "HK$199"),
        ("客服備援", "WhatsApp 6222 7238"),
    ]
    y = 1020
    f_th = font(22, True, False)
    f_td = font(22, False, False)
    for i, (th, td) in enumerate(rows):
        bg = CREAM if i % 2 == 0 else WHITE
        draw.rectangle((50, y, W - 50, y + 52), fill=bg, outline=LINE)
        draw.text((70, y + 12), th, font=f_th, fill=ORANGE_DK)
        draw.text((320, y + 12), td, font=f_td, fill=INK)
        y += 52

    # Cap.231 once here (also reinforced on panel 05 footer)
    f_cap = font(18, False, False)
    cap = "此產品並不供作診斷、治療或預防任何疾病之用。（Cap.231）"
    draw.text(((W - text_w(draw, cap, f_cap)) // 2, H - 50), cap, font=f_cap, fill=MUTED)
    return im


def panel_endorse_cta() -> Image.Image:
    H = 1520
    im = radial_bg(H, CREAM_DEEP, WHITE)
    draw = ImageDraw.Draw(im)

    f_h = font(44, True, True)
    t = "名人理念推薦"
    draw.text(((W - text_w(draw, t, f_h)) // 2, 48), t, font=f_h, fill=INK)

    gold_plaque(draw, (50, 120, W - 50, 520), 22)
    portrait = Image.open(PORTRAIT).convert("RGB")
    pw, ph = portrait.size
    side = min(pw, ph)
    left = (pw - side) // 2
    top = max(0, (ph - side) // 2 - 20)
    portrait = portrait.crop((left, top, left + side, top + side)).resize((300, 300), Image.Resampling.LANCZOS)
    mask = Image.new("L", (300, 300), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 300, 300), fill=255)
    circ = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    circ.paste(portrait, (0, 0))
    circ.putalpha(mask)
    # gold ring
    ring = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((2, 2, 317, 317), outline=GOLD, width=4)
    im_r = im.convert("RGBA")
    im_r.paste(ring, (80, 160), ring)
    im_r.paste(circ, (90, 170), circ)
    im = im_r.convert("RGB")
    draw = ImageDraw.Draw(im)

    f_who = font(30, True, True)
    draw.text((440, 180), "尹淑梅中醫師", font=f_who, fill=ORANGE_DK)
    f_meta = font(20, False, False)
    draw_wrapped(
        draw,
        "從醫五十多年・香港註冊中醫師\n香港中國醫藥研究院榮譽院長",
        440,
        235,
        f_meta,
        MUTED,
        640,
        6,
    )
    f_quote = font(26, False, True)
    quote = "支持盈康「說明可查、日常可依」的輕養生理念。"
    draw_wrapped(draw, quote, 90, 400, f_quote, INK, W - 180, 8)
    f_disc = font(18, False, False)
    disc = "理念認同，非療效保證。本頁不使用未核實個人療效見證。"
    draw_wrapped(draw, disc, 90, 470, f_disc, MUTED, W - 180, 4)

    trusts = [
        ("香港製造", "本地品質把關"),
        ("草本配方", "成分說明可查"),
        ("瀏覽為主", "無即時扣款結帳"),
        ("客服備援", "WhatsApp 查詢"),
    ]
    f_tt = font(24, True, False)
    f_ts = font(18, False, False)
    for i, (a, b) in enumerate(trusts):
        x = 50 + i * 280
        gold_plaque(draw, (x, 560, x + 260, 700), 14)
        aw = text_w(draw, a, f_tt)
        draw.text((x + (260 - aw) // 2, 595), a, font=f_tt, fill=ORANGE_DK)
        bw = text_w(draw, b, f_ts)
        draw.text((x + (260 - bw) // 2, 645), b, font=f_ts, fill=MUTED)

    # CTA — soft, no cart
    draw.rounded_rectangle((50, 740, W - 50, 980), radius=22, fill=ORANGE)
    # gold inner hairline
    draw.rounded_rectangle((58, 748, W - 58, 972), radius=18, outline=GOLD_LT, width=2)
    f_cta = font(34, True, True)
    c1 = "想了解規格或庫存？"
    c2 = "WhatsApp 6222 7238"
    draw.text(((W - text_w(draw, c1, f_cta)) // 2, 790), c1, font=f_cta, fill=WHITE)
    draw.text(((W - text_w(draw, c2, f_cta)) // 2, 860), c2, font=f_cta, fill=WHITE)
    f_soft = font(20, False, False)
    soft = "瀏覽為主｜本頁不含即時扣款結帳｜亦可於 HKTVmall 瀏覽"
    draw.text(((W - text_w(draw, soft, f_soft)) // 2, 930), soft, font=f_soft, fill=(255, 230, 210))

    # Cap.231 footer band (primary legal band)
    draw.rectangle((0, 1040, W, H), fill=(48, 42, 38))
    f_c = font(17, False, False)
    cap = (
        "此產品沒有根據《藥劑業及毒藥條例》或《中醫藥條例》註冊。"
        "為此產品作出的任何聲稱亦沒有為進行該等註冊而接受評核。"
        "此產品並不供作診斷、治療或預防任何疾病之用。"
    )
    draw_wrapped(draw, cap, 50, 1080, f_c, (220, 214, 208), W - 100, 5)
    return im


def stitch(panels: list[Image.Image], gap: int = 0) -> Image.Image:
    total_h = sum(p.height for p in panels) + gap * (len(panels) - 1)
    out = Image.new("RGB", (W, total_h), WHITE)
    y = 0
    for p in panels:
        out.paste(p, (0, y))
        y += p.height + gap
    return out


def export_web(im: Image.Image, stem: str):
    """Save master PNG at W, and 750w progressive JPEG q91."""
    im2 = ImageEnhance.Sharpness(im).enhance(1.06)
    png = OUT / f"{stem}.png"
    im2.save(png, "PNG", optimize=True)
    h750 = int(im2.height * 750 / im2.width)
    jpg = im2.resize((750, h750), Image.Resampling.LANCZOS).convert("RGB")
    jp = OUT / f"{stem}.jpg"
    jpg.save(jp, "JPEG", quality=91, optimize=True, progressive=True)
    print(f"wrote {jp.name} {jpg.size} {jp.stat().st_size // 1024}KB")
    return im2, jpg


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert PACK.exists(), f"missing {PACK}"
    panels_spec = [
        ("01-hero", panel_hero),
        ("02-lifestyle", panel_lifestyle),
        ("03-ingredients", panel_ingredients),
        ("04-usage-specs", panel_usage_specs),
        ("05-endorse-cta", panel_endorse_cta),
    ]
    masters = []
    for name, fn in panels_spec:
        print("building", name)
        im = fn()
        master, _ = export_web(im, name)
        masters.append(master)

    tall = stitch(masters, gap=0)
    tall_750 = tall.resize((750, int(tall.height * 750 / tall.width)), Image.Resampling.LANCZOS)
    # no PNG long (too big); JPEG only for long
    long_jpg = OUT / "detail-long-full.jpg"
    tall_750.save(long_jpg, "JPEG", quality=90, optimize=True, progressive=True)
    print(f"wrote {long_jpg.name} {tall_750.size} {long_jpg.stat().st_size // 1024}KB")
    # remove stale detail-long-full.png if present
    stale = OUT / "detail-long-full.png"
    if stale.exists():
        stale.unlink()
        print("removed stale detail-long-full.png")


if __name__ == "__main__":
    main()
