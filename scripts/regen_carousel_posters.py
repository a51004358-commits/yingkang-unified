#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate homepage carousel posters with real product/brand photos on the right."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "assets" / "posters"
PHONE = "6222 7238"
W, H = 1440, 400
LEFT_W = 560

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


def soft_left_fade(panel: Image.Image, fade_px: int = 120) -> Image.Image:
    panel = panel.convert("RGBA")
    w, h = panel.size
    fade_px = min(fade_px, w)
    alpha = panel.split()[-1]
    grad = Image.new("L", (w, 1), 255)
    gpx = grad.load()
    for x in range(fade_px):
        gpx[x, 0] = int(255 * (x / fade_px))
    grad = grad.resize((w, h), Image.Resampling.BILINEAR)
    new_a = ImageChops.multiply(alpha, grad)
    panel.putalpha(new_a)
    return panel


def rounded_shadow(product: Image.Image, max_h: int = 340, max_w: int = 520) -> Image.Image:
    product = product.convert("RGBA")
    product = ImageEnhance.Contrast(product).enhance(1.05)
    product = ImageEnhance.Color(product).enhance(1.08)
    fitted = contain_fit(product, max_w, max_h)
    shadow = Image.new("RGBA", (max_w + 40, max_h + 40), (0, 0, 0, 0))
    mask = fitted.split()[-1]
    sh_layer = Image.new("RGBA", fitted.size, (0, 0, 0, 90))
    sh_layer.putalpha(mask)
    sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(12))
    shadow.paste(sh_layer, (24, 28), sh_layer)
    shadow.paste(fitted, (12, 8), fitted)
    return shadow


def make_base(bg):
    img = Image.new("RGB", (W, H), bg)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, 0, LEFT_W, H], fill=(0, 0, 0, 55))
    for i in range(80):
        a = int(40 * (1 - i / 80))
        od.line([(LEFT_W + i, 0), (LEFT_W + i, H)], fill=(0, 0, 0, a))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def draw_text_panel(img, bg, fg, t1, t2, t3):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([48, 40, 148, 74], radius=6, fill=(255, 255, 255))
    d.text((60, 46), "盈康", fill=bg, font=font(20, True))
    d.text((48, 100), t1, fill=fg, font=font(48, True))
    d.text((48, 175), t2, fill=fg, font=font(26, True))
    d.text((48, 230), t3, fill=fg, font=font(20))
    return img


def paste_right_photo(base, photo):
    right_w = W - LEFT_W + 60
    panel = cover_fit(photo, right_w, H)
    panel = soft_left_fade(panel, fade_px=140)
    out = base.convert("RGBA")
    out.alpha_composite(panel, (LEFT_W - 60, 0))
    return out


def paste_product_float(base, product, bg_accent=None, extra=None):
    out = base.convert("RGBA")
    deco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    accent = bg_accent or (255, 255, 255)
    orb = Image.new("RGBA", (520, 520), (0, 0, 0, 0))
    ImageDraw.Draw(orb).ellipse([0, 0, 520, 520], fill=(*accent, 45))
    deco.alpha_composite(orb, (W - 560, -40))
    orb2 = Image.new("RGBA", (280, 280), (0, 0, 0, 0))
    ImageDraw.Draw(orb2).ellipse([0, 0, 280, 280], fill=(255, 255, 255, 35))
    deco.alpha_composite(orb2, (W - 320, 180))
    out = Image.alpha_composite(out, deco)

    packs = [p for p in ([product] + (extra or [])) if p is not None]
    if len(packs) == 1:
        positions = [(LEFT_W + 40, 10, 620, 380)]
    elif len(packs) == 2:
        positions = [(LEFT_W + 20, 30, 420, 340), (W - 420, 50, 380, 320)]
    else:
        positions = [
            (LEFT_W + 10, 40, 340, 300),
            (LEFT_W + 280, 20, 360, 320),
            (W - 280, 50, 250, 280),
        ]
    for im, (x, y, mw, mh) in zip(packs, positions):
        shadowed = rounded_shadow(im, max_h=mh, max_w=mw)
        sx = x + (mw + 40 - shadowed.size[0]) // 2
        sy = y + (mh + 40 - shadowed.size[1]) // 2
        out.alpha_composite(shadowed, (max(0, sx), max(0, sy)))
    return out


def open_img(rel: str) -> Image.Image:
    p = REPO / rel
    if not p.exists():
        raise FileNotFoundError(p)
    return Image.open(p)


def save(img, name):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    img.convert("RGB").save(path, "JPEG", quality=90, optimize=True)
    print(f"wrote {path} ({path.stat().st_size} bytes)")
    return path


def build_all():
    posters = [
        ("01-hero.jpg", (229, 119, 0), (255, 255, 255), "盈康", "香港輕養生・膏布・口服・噴霧", "先瀏覽產品・有問題再查詢 " + PHONE, "hero"),
        ("02-celebrity.jpg", (20, 60, 100), (255, 255, 255), "名人推薦", "尹淑梅中醫師・從醫五十多年", "三代從醫・榮登世界名人錄／傑出英才錄", "celebrity"),
        ("03-yanbiqing.jpg", (180, 40, 40), (255, 255, 255), "強力炎必清", "清熱不傷胃・香港製造", "已售出 400+・HKTVmall 熱賣", "yanbiqing"),
        ("04-patch.jpg", (90, 50, 20), (255, 245, 230), "一條根膏布系列", "舒緩腰腿酸痛・外用方便", "金門／台灣一條根・多規格可選", "patch"),
        ("05-trust.jpg", (30, 90, 60), (255, 255, 255), "可信賴的本地品牌", "HKTVmall 專營店・Price 商戶", "WhatsApp／電話 " + PHONE, "trust"),
        ("06-liuwei.jpg", (100, 40, 80), (255, 255, 255), "六味地黃丸", "滋陰補腎・傳統複方", "350粒／雙瓶裝・香港製造", "liuwei"),
    ]

    yan = open_img("assets/products/yanbiqing-60caps-y5/primary.png")
    patch = open_img("assets/products/zuogu-gaobu-10pcs-x11-yk400/primary.png")
    liuwei = open_img("assets/products/liuwei-dihuang-350caps-yk396/primary.png")
    mieshi = open_img("assets/products/mieshitong-gaobu-bevidan-10pcs-yk402/primary.png")
    portrait = open_img("assets/yinshumei/portrait.jpg")
    hero = open_img("assets/hero.jpg")
    logo = open_img("assets/logo.png")
    liuwei_extra = None
    for cand in (
        "assets/products/liuwei-dihuang-350caps-yk396/gallery-2.jpg",
        "assets/products/liuwei-dihuang-350caps-yk396/gallery-1.png",
    ):
        cp = REPO / cand
        if cp.exists():
            liuwei_extra = Image.open(cp)
            break

    for fname, bg, fg, t1, t2, t3, key in posters:
        base = make_base(bg)
        if key == "hero":
            right = paste_right_photo(base, hero)
            dim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(dim).rectangle([LEFT_W - 40, 0, W, H], fill=(*bg, 70))
            right = Image.alpha_composite(right, dim)
            right = paste_product_float(right, yan, bg_accent=(255, 200, 120), extra=[patch, liuwei])
            lg = contain_fit(logo, 160, 50)
            right.alpha_composite(lg, (W - 190, H - 70))
            img = draw_text_panel(right, bg, fg, t1, t2, t3)
        elif key == "celebrity":
            right = paste_right_photo(base, portrait)
            tint = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(tint).rectangle([LEFT_W - 40, 0, W, H], fill=(20, 40, 80, 50))
            right = Image.alpha_composite(right, tint)
            img = draw_text_panel(right, bg, fg, t1, t2, t3)
        elif key == "yanbiqing":
            right = paste_product_float(base, yan, bg_accent=(255, 180, 160))
            img = draw_text_panel(right, bg, fg, t1, t2, t3)
        elif key == "patch":
            right = paste_product_float(base, patch, bg_accent=(220, 180, 120), extra=[mieshi])
            img = draw_text_panel(right, bg, fg, t1, t2, t3)
        elif key == "trust":
            right = paste_product_float(base, patch, bg_accent=(120, 200, 160), extra=[yan, mieshi])
            lg = contain_fit(logo, 200, 60)
            right.alpha_composite(lg, (W - 240, 30))
            img = draw_text_panel(right, bg, fg, t1, t2, t3)
        elif key == "liuwei":
            extras = [liuwei_extra] if liuwei_extra is not None else None
            right = paste_product_float(base, liuwei, bg_accent=(200, 140, 180), extra=extras)
            img = draw_text_panel(right, bg, fg, t1, t2, t3)
        else:
            img = draw_text_panel(base, bg, fg, t1, t2, t3)
        save(img, fname)
    print("done")


if __name__ == "__main__":
    build_all()
