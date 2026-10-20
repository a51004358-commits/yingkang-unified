#!/usr/bin/env python3
"""Build Vita-Green-style long-form detail PNGs for 強力炎必清 60粒.
Cap.231-safe: no disease claims, no VG trademarks, no fake stats/testimonials.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/products/yanbiqing-60caps-y5/detail"
PROD = ROOT / "assets/products/yanbiqing-60caps-y5/primary.png"
PORTRAIT = ROOT / "assets/yinshumei/portrait.jpg"
LOGO = ROOT / "assets/logo.png"
POSTER = ROOT / "assets/posters/03-yanbiqing-sq.jpg"

W = 900  # mobile-friendly long-form width
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
IDX = 4  # Noto Sans CJK HK

# Brand palette (盈康 warm, not Vita Green teal clone)
CREAM = (255, 250, 245)
CREAM2 = (255, 244, 232)
ORANGE = (217, 104, 34)
ORANGE_DK = (126, 65, 10)
INK = (45, 42, 38)
MUTED = (102, 96, 90)
LINE = (232, 214, 196)
WHITE = (255, 255, 255)
SOFT_GREEN = (236, 245, 238)
SOFT_BLUE = (240, 246, 250)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REG
    return ImageFont.truetype(path, size, index=IDX)


def round_rect(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


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


def text_w(draw, text, fnt) -> int:
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0]


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


def draw_wrapped(draw, text, x, y, fnt, fill, max_w, line_gap=8) -> int:
    lines = wrap_text(draw, text, fnt, max_w)
    yy = y
    for ln in lines:
        draw.text((x, yy), ln, font=fnt, fill=fill)
        bb = draw.textbbox((0, 0), ln or " ", font=fnt)
        yy += (bb[3] - bb[1]) + line_gap
    return yy


def gradient_bg(h: int, c1=CREAM, c2=CREAM2) -> Image.Image:
    im = Image.new("RGB", (W, h), c1)
    px = im.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        for x in range(W):
            px[x, y] = (r, g, b)
    return im


def soft_shadow(size, radius=28, opacity=70) -> Image.Image:
    w, h = size
    sh = Image.new("RGBA", (w + radius * 2, h + radius * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.rounded_rectangle(
        (radius // 2, radius // 2, w + radius * 1.5, h + radius * 1.5),
        radius=24,
        fill=(0, 0, 0, opacity),
    )
    return sh.filter(ImageFilter.GaussianBlur(radius))


def panel_hero() -> Image.Image:
    H = 1280
    im = gradient_bg(H, (255, 252, 248), (255, 236, 214))
    draw = ImageDraw.Draw(im)

    # top brand strip
    draw.rectangle((0, 0, W, 72), fill=ORANGE)
    logo = fit_contain(Image.open(LOGO), 140, 40)
    # white-ish plate for logo
    paste_center(im, logo, 90, 36)
    f_brand = font(22, True)
    draw.text((170, 22), "盈康 · 香港本地健康品牌", font=f_brand, fill=WHITE)

    # eyebrow
    f_eye = font(26, True)
    eye = "口服膠囊 · 香港製造"
    ew = text_w(draw, eye, f_eye)
    round_rect(draw, (W // 2 - ew // 2 - 22, 110, W // 2 + ew // 2 + 22, 158), 20, WHITE, LINE, 2)
    draw.text(((W - ew) // 2, 120), eye, font=f_eye, fill=ORANGE_DK)

    # title
    f_title = font(56, True)
    title = "強力炎必清 60粒"
    tw = text_w(draw, title, f_title)
    draw.text(((W - tw) // 2, 190), title, font=f_title, fill=INK)

    f_sub = font(28, False)
    sub = "草本日常輕養生｜說明可查、日常可依"
    sw = text_w(draw, sub, f_sub)
    draw.text(((W - sw) // 2, 270), sub, font=f_sub, fill=MUTED)

    # product with soft pedestal
    prod = fit_contain(Image.open(PROD), 620, 620)
    # pedestal ellipse
    ped = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(ped)
    pd.ellipse((150, 980, 750, 1120), fill=(217, 104, 34, 35))
    im = Image.alpha_composite(im.convert("RGBA"), ped).convert("RGB")
    draw = ImageDraw.Draw(im)

    # shadow then product
    sh = soft_shadow((prod.width, prod.height), 36, 55)
    im_rgba = im.convert("RGBA")
    sx = (W - sh.width) // 2
    sy = 340
    im_rgba.paste(sh, (sx, sy + 40), sh)
    paste_center(im_rgba, prod, W // 2, 640)
    im = im_rgba.convert("RGB")
    draw = ImageDraw.Draw(im)

    # bottom soft bullets (Cap.231-safe)
    bullets = [
        "穿心蓮 · 香蜂草 · 紫錐花 · 蒲公英 等草本構想",
        "一般健康產品說明，並非診斷、治療或預防疾病之用",
        "瀏覽為主｜需要時 WhatsApp 6222 7238 確認規格",
    ]
    y = 1060
    f_b = font(22, False)
    for b in bullets:
        bw = text_w(draw, "・" + b, f_b)
        draw.text(((W - bw) // 2, y), "・" + b, font=f_b, fill=ORANGE_DK)
        y += 42

    return im



def draw_icon(draw, kind, cx, cy, r=40):
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=CREAM2, outline=LINE, width=2)
    if kind == "moon":
        draw.ellipse((cx - 18, cy - 20, cx + 14, cy + 20), fill=ORANGE)
        draw.ellipse((cx - 6, cy - 20, cx + 26, cy + 20), fill=CREAM2)
    elif kind == "bowl":
        draw.ellipse((cx - 26, cy - 8, cx + 26, cy + 22), outline=ORANGE, width=4)
        draw.arc((cx - 26, cy - 4, cx + 26, cy + 26), 0, 180, fill=ORANGE, width=4)
        draw.line((cx - 30, cy - 2, cx + 30, cy - 2), fill=ORANGE, width=3)
        for dx in (-10, 0, 10):
            draw.arc((cx + dx - 6, cy - 28, cx + dx + 6, cy - 10), 200, 340, fill=ORANGE, width=2)
    elif kind == "leaf":
        draw.ellipse((cx - 8, cy - 28, cx + 22, cy + 18), fill=ORANGE)
        draw.line((cx, cy + 18, cx, cy - 10), fill=WHITE, width=2)
        draw.line((cx, cy, cx + 14, cy - 8), fill=WHITE, width=2)
        draw.line((cx, cy + 8, cx + 12, cy + 2), fill=WHITE, width=2)
    elif kind == "home":
        draw.polygon([(cx, cy - 26), (cx - 28, cy - 2), (cx + 28, cy - 2)], fill=ORANGE)
        draw.rectangle((cx - 18, cy - 2, cx + 18, cy + 24), fill=ORANGE)
        draw.rectangle((cx - 6, cy + 4, cx + 6, cy + 24), fill=CREAM2)


def panel_lifestyle() -> Image.Image:
    H = 1180
    im = gradient_bg(H, WHITE, CREAM)
    draw = ImageDraw.Draw(im)

    f_h = font(42, True)
    t = "這些日常場景，你也熟悉嗎？"
    draw.text(((W - text_w(draw, t, f_h)) // 2, 60), t, font=f_h, fill=INK)

    f_note = font(20, False)
    note = "以下為生活節奏描述，並非針對任何疾病的建議。"
    draw.text(((W - text_w(draw, note, f_note)) // 2, 130), note, font=f_note, fill=MUTED)

    cards = [
        ("moon", "熬夜節奏", "加班、追劇後\n想把作息調回穩定"),
        ("bowl", "飲食偏油", "應酬、外賣較多的日子\n想輕一點"),
        ("leaf", "換季作息", "冷暖交替時\n留意個人舒適度"),
        ("home", "居家備存", "先了解規格\n需要時再查詢選購"),
    ]
    # 2x2
    gap = 28
    card_w = (W - 80 - gap) // 2
    card_h = 360
    start_y = 190
    f_c = font(30, True)
    f_p = font(22, False)
    for i, (ico, title, body) in enumerate(cards):
        col = i % 2
        row = i // 2
        x0 = 40 + col * (card_w + gap)
        y0 = start_y + row * (card_h + gap)
        round_rect(draw, (x0, y0, x0 + card_w, y0 + card_h), 22, WHITE, LINE, 2)
        cx, cy = x0 + card_w // 2, y0 + 90
        draw_icon(draw, ico, cx, cy, 48)
        tw = text_w(draw, title, f_c)
        draw.text((x0 + (card_w - tw) // 2, y0 + 170), title, font=f_c, fill=ORANGE_DK)
        yy = y0 + 230
        for ln in body.split("\n"):
            lw = text_w(draw, ln, f_p)
            draw.text((x0 + (card_w - lw) // 2, yy), ln, font=f_p, fill=MUTED)
            yy += 34

    # bottom strip
    round_rect(draw, (40, 1040, W - 40, 1130), 16, SOFT_GREEN, None)
    f_s = font(24, True)
    s = "把草本膠囊納入日常節奏 · 先瀏覽、再決定"
    draw.text(((W - text_w(draw, s, f_s)) // 2, 1068), s, font=f_s, fill=(46, 110, 72))
    return im


def panel_ingredients() -> Image.Image:
    H = 1500
    im = gradient_bg(H, CREAM, WHITE)
    draw = ImageDraw.Draw(im)

    f_h = font(42, True)
    t = "主要草本成分"
    draw.text(((W - text_w(draw, t, f_h)) // 2, 50), t, font=f_h, fill=INK)
    f_sub = font(22, False)
    s = "配方構想說明僅供參考，實際以包裝標籤為準"
    draw.text(((W - text_w(draw, s, f_sub)) // 2, 115), s, font=f_sub, fill=MUTED)

    # left product, right list intro band
    prod = fit_contain(Image.open(PROD), 380, 380)
    im_r = im.convert("RGBA")
    sh = soft_shadow((prod.width, prod.height), 28, 50)
    im_r.paste(sh, (40, 180), sh)
    im_r.paste(prod, (60, 190), prod)
    im = im_r.convert("RGB")
    draw = ImageDraw.Draw(im)

    round_rect(draw, (460, 210, W - 40, 520), 18, WHITE, LINE, 2)
    f_b = font(26, True)
    f_p = font(22, False)
    lines = [
        "四味常見養生草本構想",
        "穿心蓮｜香蜂草",
        "紫錐花｜蒲公英",
        "",
        "屬一般健康產品說明",
        "不涉及療效保證",
    ]
    yy = 240
    for i, ln in enumerate(lines):
        f = f_b if i == 0 else f_p
        c = ORANGE_DK if i == 0 else MUTED
        if ln:
            draw.text((490, yy), ln, font=f, fill=c)
        yy += 40

    ings = [
        ("穿心蓮", "Andrographis", "傳統清熱草本，常見於日常養生配方說明。"),
        ("香蜂草", "Melissa", "溫和草本，配方中顧及脾胃感受的常見搭配。"),
        ("紫錐花", "Echinacea", "季節轉換期常出現的免疫草本成分敘述。"),
        ("蒲公英", "Dandelion", "傳統清熱利濕草本，用於日常配方說明。"),
    ]
    y0 = 560
    f_name = font(30, True)
    f_lat = font(20, False)
    f_why = font(22, False)
    for i, (name, lat, why) in enumerate(ings):
        y = y0 + i * 210
        round_rect(draw, (40, y, W - 40, y + 190), 18, WHITE, LINE, 2)
        # number badge
        draw.ellipse((70, y + 55, 150, y + 135), fill=CREAM2, outline=ORANGE, width=3)
        num = f"{i+1:02d}"
        f_n = font(28, True)
        nw = text_w(draw, num, f_n)
        draw.text((110 - nw // 2, y + 78), num, font=f_n, fill=ORANGE_DK)
        draw.text((180, y + 40), name, font=f_name, fill=INK)
        draw.text((180, y + 85), lat, font=f_lat, fill=ORANGE)
        draw_wrapped(draw, why, 180, y + 120, f_why, MUTED, W - 260, 6)

    f_foot = font(20, False)
    foot = "※ 成分敘述不構成診斷、治療或預防任何疾病之聲稱"
    draw.text(((W - text_w(draw, foot, f_foot)) // 2, 1430), foot, font=f_foot, fill=MUTED)
    return im


def panel_usage_specs() -> Image.Image:
    H = 1480
    im = gradient_bg(H, WHITE, SOFT_BLUE)
    draw = ImageDraw.Draw(im)

    f_h = font(42, True)
    t = "建議用法與產品規格"
    draw.text(((W - text_w(draw, t, f_h)) // 2, 50), t, font=f_h, fill=INK)

    # dosage hero card
    round_rect(draw, (40, 130, W - 40, 430), 22, CREAM2, LINE, 2)
    f_big = font(36, True)
    big = "成人：每日 3 次，每次 2 粒"
    draw.text(((W - text_w(draw, big, f_big)) // 2, 170), big, font=f_big, fill=ORANGE_DK)
    f_n = font(24, False)
    n1 = "溫水送服。請以包裝標籤為準。"
    n2 = "孕婦、兒童及長期病患者請先咨詢專業意見。"
    draw.text(((W - text_w(draw, n1, f_n)) // 2, 240), n1, font=f_n, fill=MUTED)
    draw.text(((W - text_w(draw, n2, f_n)) // 2, 280), n2, font=f_n, fill=MUTED)

    steps = ["先讀標籤成分與注意事項", "選定固定時段（如早／午／晚）", "配合喝水與作息，不自行加倍"]
    f_s = font(24, True)
    for i, st in enumerate(steps):
        x = 70 + i * 270
        y = 340
        draw.ellipse((x, y, x + 44, y + 44), fill=ORANGE)
        f_num = font(22, True)
        ns = str(i + 1)
        draw.text((x + 22 - text_w(draw, ns, f_num) // 2, y + 8), ns, font=f_num, fill=WHITE)
        # wrap short
        draw_wrapped(draw, st, x + 54, y + 6, font(20, False), INK, 200, 4)

    # how to rhythm
    f_h2 = font(32, True)
    draw.text((40, 480), "把服用寫進日常節奏", font=f_h2, fill=INK)
    stages = [
        ("第 1 日", "依標籤開始；配合喝水與規律作息，感受個人舒適度。"),
        ("第 1 週", "寫進固定時段（如早晚），比臨時想起更易持續。"),
        ("日常節奏", "與飲食、睡眠一併調整。不適請停止並咨詢醫護。"),
    ]
    f_st = font(26, True)
    f_bd = font(22, False)
    for i, (title, body) in enumerate(stages):
        y = 540 + i * 130
        round_rect(draw, (40, y, W - 40, y + 110), 14, WHITE, LINE, 2)
        draw.rectangle((40, y, 56, y + 110), fill=ORANGE)
        draw.text((80, y + 22), title, font=f_st, fill=ORANGE_DK)
        draw_wrapped(draw, body, 80, y + 60, f_bd, MUTED, W - 160, 4)

    # specs table
    draw.text((40, 960), "產品規格", font=f_h2, fill=INK)
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
    f_th = font(22, True)
    f_td = font(22, False)
    for i, (th, td) in enumerate(rows):
        bg = CREAM if i % 2 == 0 else WHITE
        draw.rectangle((40, y, W - 40, y + 52), fill=bg, outline=LINE)
        draw.text((60, y + 12), th, font=f_th, fill=ORANGE_DK)
        draw.text((280, y + 12), td, font=f_td, fill=INK)
        y += 52

    f_cap = font(18, False)
    cap = "此產品並不供作診斷、治療或預防任何疾病之用。（Cap.231）"
    draw.text(((W - text_w(draw, cap, f_cap)) // 2, 1410), cap, font=f_cap, fill=MUTED)
    return im


def panel_endorse_cta() -> Image.Image:
    H = 1180
    im = gradient_bg(H, CREAM2, WHITE)
    draw = ImageDraw.Draw(im)

    f_h = font(40, True)
    t = "名人理念推薦"
    draw.text(((W - text_w(draw, t, f_h)) // 2, 50), t, font=f_h, fill=INK)

    # portrait card
    round_rect(draw, (40, 130, W - 40, 560), 22, WHITE, LINE, 2)
    portrait = Image.open(PORTRAIT).convert("RGB")
    # crop center square-ish
    pw, ph = portrait.size
    side = min(pw, ph)
    left = (pw - side) // 2
    top = (ph - side) // 2
    portrait = portrait.crop((left, top, left + side, top + side))
    portrait = portrait.resize((280, 280), Image.Resampling.LANCZOS)
    # circular mask
    mask = Image.new("L", (280, 280), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 280, 280), fill=255)
    circ = Image.new("RGBA", (280, 280), (0, 0, 0, 0))
    circ.paste(portrait, (0, 0))
    circ.putalpha(mask)
    im_r = im.convert("RGBA")
    im_r.paste(circ, (80, 180), circ)
    im = im_r.convert("RGB")
    draw = ImageDraw.Draw(im)

    f_who = font(28, True)
    draw.text((400, 200), "尹淑梅中醫師", font=f_who, fill=ORANGE_DK)
    f_meta = font(20, False)
    draw_wrapped(
        draw,
        "從醫五十多年・香港註冊中醫師\n香港中國醫藥研究院榮譽院長\n香港中國醫藥學會永遠榮譽會長",
        400,
        250,
        f_meta,
        MUTED,
        420,
        6,
    )

    f_quote = font(24, False)
    quote = "支持盈康「說明可查、日常可依」的輕養生理念。"
    draw_wrapped(draw, quote, 80, 490, f_quote, INK, W - 160, 6)

    f_disc = font(18, False)
    disc = "推薦反映品牌理念認同，並非對單一療效之醫學保證。本頁不使用未核實個人療效見證。"
    draw_wrapped(draw, disc, 80, 560, f_disc, MUTED, W - 160, 4)  # may overflow card — extend note below

    # trust row
    trusts = [("香港製造", "本地品質把關"), ("草本配方", "成分說明可查"), ("瀏覽為主", "無即時扣款結帳"), ("客服備援", "WhatsApp 查詢")]
    f_tt = font(24, True)
    f_ts = font(18, False)
    for i, (a, b) in enumerate(trusts):
        x = 40 + i * 210
        round_rect(draw, (x, 640, x + 195, 760), 14, WHITE, LINE, 2)
        aw = text_w(draw, a, f_tt)
        draw.text((x + (195 - aw) // 2, 670), a, font=f_tt, fill=ORANGE_DK)
        bw = text_w(draw, b, f_ts)
        draw.text((x + (195 - bw) // 2, 715), b, font=f_ts, fill=MUTED)

    # CTA band
    round_rect(draw, (40, 800, W - 40, 1020), 22, ORANGE)
    f_cta = font(32, True)
    c1 = "想了解規格或庫存？"
    c2 = "WhatsApp 6222 7238"
    draw.text(((W - text_w(draw, c1, f_cta)) // 2, 840), c1, font=f_cta, fill=WHITE)
    draw.text(((W - text_w(draw, c2, f_cta)) // 2, 900), c2, font=f_cta, fill=WHITE)
    f_soft = font(20, False)
    soft = "瀏覽為主｜本頁不含即時扣款結帳｜亦可於 HKTVmall 瀏覽"
    draw.text(((W - text_w(draw, soft, f_soft)) // 2, 970), soft, font=f_soft, fill=(255, 230, 210))

    # Cap.231 footer band
    draw.rectangle((0, 1060, W, H), fill=(55, 50, 46))
    f_c = font(16, False)
    cap = (
        "此產品沒有根據《藥劑業及毒藥條例》或《中醫藥條例》註冊。"
        "為此產品作出的任何聲稱亦沒有為進行該等註冊而接受評核。"
        "此產品並不供作診斷、治療或預防任何疾病之用。"
    )
    draw_wrapped(draw, cap, 40, 1085, f_c, (220, 214, 208), W - 80, 4)
    return im


def stitch(panels: list[Image.Image], gap: int = 0) -> Image.Image:
    total_h = sum(p.height for p in panels) + gap * (len(panels) - 1)
    out = Image.new("RGB", (W, total_h), WHITE)
    y = 0
    for p in panels:
        out.paste(p, (0, y))
        y += p.height + gap
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    panels = [
        ("01-hero.png", panel_hero()),
        ("02-lifestyle.png", panel_lifestyle()),
        ("03-ingredients.png", panel_ingredients()),
        ("04-usage-specs.png", panel_usage_specs()),
        ("05-endorse-cta.png", panel_endorse_cta()),
    ]
    paths = []
    for name, im in panels:
        # lightly sharpen for mobile crispness
        im2 = ImageEnhance.Sharpness(im).enhance(1.08)
        path = OUT / name
        im2.save(path, "PNG", optimize=True)
        paths.append(path)
        print(f"wrote {path} {im2.size}")

    tall = stitch([p for _, p in panels], gap=0)
    # 750w mobile long-form + progressive JPEGs for web
    tall_750 = tall.resize((750, int(tall.height * 750 / tall.width)), Image.Resampling.LANCZOS)
    tall_path = OUT / "detail-long-full.png"
    tall_750.save(tall_path, "PNG", optimize=True)
    tall_750.save(OUT / "detail-long-full.jpg", "JPEG", quality=85, optimize=True, progressive=True)
    print(f"wrote {tall_path} {tall_750.size}")
    for name, im in panels:
        im750 = im.resize((750, int(im.height * 750 / im.width)), Image.Resampling.LANCZOS)
        jp = OUT / name.replace(".png", ".jpg")
        im750.convert("RGB").save(jp, "JPEG", quality=86, optimize=True, progressive=True)
        print(f"wrote {jp} {im750.size}")


if __name__ == "__main__":
    main()
