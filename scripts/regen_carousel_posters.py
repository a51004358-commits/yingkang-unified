#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate homepage carousel posters as large-cell ~1:1 squares (Suntory-style layout, 盈康 brand)."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "assets" / "posters"
PHONE = "6222 7238"
# Large-cell square (mobile full-bleed; desktop may center-crop to 2:1)
W, H = 1080, 1080

FONT_R = Path("/home/box/.local/share/fonts/LZNotoSansTC-Regular.ttf")
FONT_B = Path("/home/box/.local/share/fonts/LZNotoSansTC-Bold.ttf")
FONT_CJK_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_CJK_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def font(sz: int, bold: bool = False):
    preferred = FONT_B if bold else FONT_R
    if preferred.exists():
        try:
            return ImageFont.truetype(str(preferred), sz)
        except Exception:
            pass
    for idx in (4, 3, 1, 0):
        try:
            return ImageFont.truetype(FONT_CJK_B if bold else FONT_CJK_R, sz, index=idx)
        except Exception:
            continue
    return ImageFont.load_default()


def cover_fit(im: Image.Image, tw: int, th: int) -> Image.Image:
    im = im.convert("RGBA")
    sw, sh = im.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return im.crop((left, top, left + tw, top + th))


def contain_fit(im: Image.Image, tw: int, th: int, pad_rgba=(0, 0, 0, 0)) -> Image.Image:
    im = im.convert("RGBA")
    sw, sh = im.size
    scale = min(tw / sw, th / sh)
    nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (tw, th), pad_rgba)
    canvas.paste(im, ((tw - nw) // 2, (th - nh) // 2), im)
    return canvas


def rounded_shadow(product: Image.Image, max_w: int, max_h: int) -> Image.Image:
    product = product.convert("RGBA")
    product = ImageEnhance.Contrast(product).enhance(1.06)
    product = ImageEnhance.Color(product).enhance(1.08)
    fitted = contain_fit(product, max_w, max_h)
    pad = 36
    shadow = Image.new("RGBA", (max_w + pad * 2, max_h + pad * 2), (0, 0, 0, 0))
    mask = fitted.split()[-1]
    sh_layer = Image.new("RGBA", fitted.size, (0, 0, 0, 100))
    sh_layer.putalpha(mask)
    sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(16))
    shadow.paste(sh_layer, (pad + 10, pad + 18), sh_layer)
    shadow.paste(fitted, (pad, pad), fitted)
    return shadow


def gradient_bg(c1, c2) -> Image.Image:
    """Vertical soft gradient from c1 (top) to c2 (bottom)."""
    img = Image.new("RGB", (W, H), c1)
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        # ease toward bottom accent
        t = t * t * (3 - 2 * t)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        for x in range(W):
            px[x, y] = (r, g, b)
    return img.convert("RGBA")


def draw_centered_text(d: ImageDraw.ImageDraw, text: str, y: int, fill, fnt, max_w: int = 920):
    bbox = d.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    d.text((x, y), text, fill=fill, font=fnt)
    return bbox[3] - bbox[1]


def draw_wrapped_centered(d, text, y, fill, fnt, max_w=900, line_gap=10):
    """Simple wrap by character count for CJK-friendly lines."""
    lines = []
    cur = ""
    for ch in text:
        trial = cur + ch
        bb = d.textbbox((0, 0), trial, font=fnt)
        if bb[2] - bb[0] <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    cy = y
    for line in lines:
        h = draw_centered_text(d, line, cy, fill, fnt, max_w)
        cy += h + line_gap
    return cy


def make_square_poster(bg_top, bg_bot, fg, title, subtitle, tip, visual: Image.Image, mode="product"):
    """Text upper third, large visual mid-bottom — Suntory-like product poster cell."""
    base = gradient_bg(bg_top, bg_bot)

    # Soft decorative orbs behind product zone
    deco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(deco)
    od.ellipse([W // 2 - 420, 380, W // 2 + 420, 1080], fill=(255, 255, 255, 28))
    od.ellipse([W // 2 - 280, 520, W // 2 + 280, 1080], fill=(255, 255, 255, 22))
    base = Image.alpha_composite(base, deco)

    d = ImageDraw.Draw(base)

    # Brand pill (top center)
    pill_w, pill_h = 160, 48
    px0, py0 = (W - pill_w) // 2, 48
    d.rounded_rectangle([px0, py0, px0 + pill_w, py0 + pill_h], radius=24, fill=(255, 255, 255))
    brand_f = font(26, True)
    bb = d.textbbox((0, 0), "盈康", font=brand_f)
    bx = (W - (bb[2] - bb[0])) // 2
    d.text((bx, py0 + 8), "盈康", fill=bg_top, font=brand_f)

    # Title block — upper area (kept mostly inside desktop 2:1 safe middle)
    y = 130
    y += draw_centered_text(d, title, y, fg, font(72, True)) + 18
    y = draw_wrapped_centered(d, subtitle, y, fg, font(34, True), max_w=880, line_gap=8)
    y += 8
    tip_fill = (*fg[:3],) if len(fg) == 3 else fg
    # slightly softer tip using white-ish with opacity via blend color
    tip_color = tuple(int(c * 0.92 + 255 * 0.08) for c in tip_fill)
    draw_wrapped_centered(d, tip, y, tip_color, font(26), max_w=860, line_gap=6)

    # Visual zone: middle-lower (product / portrait / collage)
    zone_top = 380
    zone_h = 620
    zone_w = 860

    if mode == "photo":
        # Full-bleed soft photo in lower area with fade
        photo = cover_fit(visual, W, zone_h + 80)
        # fade top of photo into bg
        fade = Image.new("L", (W, zone_h + 80), 255)
        fp = fade.load()
        for yy in range(140):
            fp_row = int(255 * (yy / 140))
            for xx in range(W):
                fp[xx, yy] = fp_row
        photo.putalpha(fade)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.alpha_composite(photo, (0, zone_top - 40))
        # darken a bit for text contrast already done above
        dim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(dim).rectangle([0, zone_top - 40, W, H], fill=(*bg_bot, 40))
        base = Image.alpha_composite(base, layer)
        base = Image.alpha_composite(base, dim)
    elif mode == "empty":
        # orbs only; caller pastes collage afterward
        pass
    elif mode == "collage":
        pass
    else:
        # single product float
        shadowed = rounded_shadow(visual, max_w=zone_w, max_h=zone_h - 40)
        sx = (W - shadowed.size[0]) // 2
        sy = zone_top + (zone_h - shadowed.size[1]) // 2 - 10
        base.alpha_composite(shadowed, (sx, max(zone_top - 20, sy)))

    return base


def paste_collage(base: Image.Image, packs: list[Image.Image], zone_top=400) -> Image.Image:
    out = base.convert("RGBA")
    n = len(packs)
    if n == 1:
        slots = [(W // 2, zone_top + 40, 720, 560)]
    elif n == 2:
        slots = [(W // 2 - 220, zone_top + 60, 420, 500), (W // 2 + 220, zone_top + 80, 400, 480)]
    else:
        slots = [
            (W // 2 - 280, zone_top + 100, 340, 420),
            (W // 2, zone_top + 40, 400, 500),
            (W // 2 + 280, zone_top + 110, 320, 400),
        ]
    for im, (cx, top, mw, mh) in zip(packs, slots):
        shadowed = rounded_shadow(im, max_w=mw, max_h=mh)
        sx = cx - shadowed.size[0] // 2
        sy = top
        out.alpha_composite(shadowed, (max(0, sx), max(0, sy)))
    return out


def open_img(rel: str) -> Image.Image:
    p = REPO / rel
    if not p.exists():
        raise FileNotFoundError(p)
    return Image.open(p)


def save(img: Image.Image, name: str):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    rgb = img.convert("RGB")
    rgb.save(path, "JPEG", quality=88, optimize=True)
    print(f"wrote {path} {rgb.size} ({path.stat().st_size} bytes)")
    return path


def build_all():
    yan = open_img("assets/products/yanbiqing-60caps-y5/primary.png")
    patch = open_img("assets/products/zuogu-gaobu-10pcs-x11-yk400/primary.png")
    liuwei = open_img("assets/products/liuwei-dihuang-350caps-yk396/primary.png")
    mieshi = open_img("assets/products/mieshitong-gaobu-bevidan-10pcs-yk402/primary.png")
    portrait = open_img("assets/yinshumei/portrait.jpg")
    hero = open_img("assets/hero.jpg")

    liuwei_extra = None
    for cand in (
        "assets/products/liuwei-dihuang-350caps-yk396/gallery-2.jpg",
        "assets/products/liuwei-dihuang-350caps-yk396/gallery-1.png",
    ):
        cp = REPO / cand
        if cp.exists():
            liuwei_extra = Image.open(cp)
            break

    specs = [
        # fname, bg_top, bg_bot, fg, title, subtitle, tip, key
        ("01-hero.jpg", (232, 119, 34), (210, 90, 20), (255, 255, 255),
         "盈康", "香港輕養生・膏布・口服・噴霧", "先瀏覽產品・有問題再查詢 " + PHONE, "hero"),
        ("02-celebrity.jpg", (24, 70, 110), (18, 45, 80), (255, 255, 255),
         "名人推薦", "尹淑梅中醫師・從醫五十多年", "三代從醫・榮登世界名人錄／傑出英才錄", "celebrity"),
        ("03-yanbiqing.jpg", (190, 45, 45), (140, 30, 30), (255, 255, 255),
         "強力炎必清", "清熱不傷胃・香港製造", "已售出 400+・HKTVmall 熱賣", "yanbiqing"),
        ("04-patch.jpg", (110, 65, 30), (70, 40, 18), (255, 245, 230),
         "一條根膏布系列", "舒緩腰腿酸痛・外用方便", "金門／台灣一條根・多規格可選", "patch"),
        ("05-trust.jpg", (36, 110, 75), (24, 70, 50), (255, 255, 255),
         "可信賴的本地品牌", "HKTVmall 專營店・Price 商戶", "WhatsApp／電話 " + PHONE, "trust"),
        ("06-liuwei.jpg", (120, 50, 95), (80, 30, 65), (255, 255, 255),
         "六味地黃丸", "滋陰補腎・傳統複方", "350粒／雙瓶裝・香港製造", "liuwei"),
    ]

    for fname, bg_top, bg_bot, fg, title, subtitle, tip, key in specs:
        if key == "hero":
            # soft hero photo under text + product collage
            base = make_square_poster(bg_top, bg_bot, fg, title, subtitle, tip, hero, mode="photo")
            # strengthen brand color wash over photo
            wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(wash).rectangle([0, 360, W, H], fill=(*bg_bot, 55))
            base = Image.alpha_composite(base, wash)
            img = paste_collage(base, [yan, patch, liuwei], zone_top=420)
        elif key == "celebrity":
            img = make_square_poster(bg_top, bg_bot, fg, title, subtitle, tip, portrait, mode="photo")
            # keep portrait readable: lighter wash
            wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(wash).rectangle([0, 0, W, 360], fill=(*bg_top, 70))
            img = Image.alpha_composite(img, wash)
            # redraw text over wash
            d = ImageDraw.Draw(img)
            pill_w, pill_h = 160, 48
            px0, py0 = (W - pill_w) // 2, 48
            d.rounded_rectangle([px0, py0, px0 + pill_w, py0 + pill_h], radius=24, fill=(255, 255, 255))
            brand_f = font(26, True)
            bb = d.textbbox((0, 0), "盈康", font=brand_f)
            d.text(((W - (bb[2] - bb[0])) // 2, py0 + 8), "盈康", fill=bg_top, font=brand_f)
            y = 130
            y += draw_centered_text(d, title, y, fg, font(72, True)) + 18
            y = draw_wrapped_centered(d, subtitle, y, fg, font(34, True), max_w=880, line_gap=8)
            tip_color = tuple(int(c * 0.92 + 255 * 0.08) for c in fg)
            draw_wrapped_centered(d, tip, y + 8, tip_color, font(26), max_w=860, line_gap=6)
        elif key == "yanbiqing":
            base = make_square_poster(bg_top, bg_bot, fg, title, subtitle, tip, yan, mode="product")
            img = base
        elif key == "patch":
            base = make_square_poster(bg_top, bg_bot, fg, title, subtitle, tip, patch, mode="empty")
            # clear product from empty mode — make_square with empty skips product;
            # use collage of two patches
            # rebuild without product in make — mode empty still draws orbs
            img = paste_collage(base, [patch, mieshi], zone_top=400)
        elif key == "trust":
            base = make_square_poster(bg_top, bg_bot, fg, title, subtitle, tip, patch, mode="empty")
            img = paste_collage(base, [yan, patch, mieshi], zone_top=400)
        elif key == "liuwei":
            packs = [liuwei]
            if liuwei_extra is not None:
                packs.append(liuwei_extra)
            base = make_square_poster(bg_top, bg_bot, fg, title, subtitle, tip, liuwei, mode="empty")
            img = paste_collage(base, packs, zone_top=400)
        else:
            img = make_square_poster(bg_top, bg_bot, fg, title, subtitle, tip, yan, mode="product")
        save(img, fname)

    print("done — canvas", W, "x", H)


if __name__ == "__main__":
    build_all()
