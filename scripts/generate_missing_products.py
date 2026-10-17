#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate missing product pages to align with HKTVmall catalog (121 items)."""
from __future__ import annotations
import re
import html as htmlmod
from pathlib import Path
from urllib.parse import quote

REPO = Path("/workspace/yingkang-unified")
CATALOG = Path("/workspace/yingkang-hktvmall-catalog-2026-10-09.md")
PRODUCTS = REPO / "products"
ASSETS = REPO / "assets" / "products"
CSS_V = "20261017c"
BASE = "https://www.ykimed.com"
HKTV = "https://www.hktvmall.com/hktv/zh/p/{sku}"
WA = "https://wa.me/85262227238"
PHONE = "6222 7238"
CAP231 = (
    "此產品沒有根據《藥劑業及毒藥條例》或《中醫藥條例》註冊。"
    "為此產品作出的任何聲稱亦沒有為進行該等註冊而接受評核。"
    "此產品並不供作診斷、治療或預防任何疾病之用。"
)

EXISTING_CODES = {
    "hk102", "hky7389", "k0002", "k0003", "k0008", "k0009", "k0010", "k0012",
    "k0019", "k0020", "k0021", "k0024", "k0025", "k0031", "k0037", "k0038",
    "mk285", "mk294", "mk368", "y5", "yk395", "yk396", "yk400", "yk401",
    "yk402", "yk403", "yk404", "yk408", "yk470", "yk471",
}

NAME_OVERRIDES = {
    "H6838001_S_y5": "強力炎必清 60粒",
    "H6838001_S_K0012": "強力濃縮六味地黃丸 350粒×2",
    "H6838001_S_yk401": "金門一條根坐骨神經膏布 10片",
    "H6838001_S_K0025": "台灣一條根坐骨神經膏布 20片",
    "H6838001_S_k0037": "東京塔牌膚特靈 120ml×3",
    "H6838001_S_K0024": "台灣一條根坐骨神經膏布 30片",
    "H6838001_S_HKY7389": "坐骨神經丸 60粒",
    "H6838001_S_yk404": "膚特靈 120ml 噴霧",
    "H6838001_S_k0038": "蕥歡仙 60粒",
    "H6838001_S_MK294": "坐骨神經膏布 10片（7.5×11cm）",
    "H6838001_S_K0008": "坐骨神經丸 150粒",
    "H6838001_S_yk396": "強力濃縮六味地黃丸 350粒",
    "H6838001_S_yk402": "BEVIDAN 滅濕痛風痛膏布 10片",
    "H6838001_S_yk470": "花塔糖 50粒×4支",
    "H6838001_S_K0031": "BEVIDAN 滅濕痛風痛 60粒",
    "H6838001_S_yk408": "千里追風坐骨神徑痛油 50ml",
    "H6838001_S_k0019": "百痛敵 60粒",
    "H6838001_S_K0021": "活絡靈 2（60粒）",
    "H6838001_S_K0009": "BEVIDAN 滅濕痛風痛 150粒",
    "H6838001_S_K0010": "腦白金靈芝孢子腦活素 150粒",
    "H6838001_S_yk403": "滅濕痛風痛膏布 11×15cm（10片）",
    "H6838001_S_K0033": "滅濕痛風痛膏布 11×15cm（10片×2）",
    "H6838001_S_K0020": "尿酸清 GOUBUNE 60粒",
    "H6838001_S_y14": "坐骨神徑痛丸 60粒＋痛油 50ml",
    "H6838001_S_yk471": "強力炎必清 130粒珍寶裝",
    "H6838001_S_yk400": "坐骨神經膏布 7×11cm（10片）",
    "H6838001_S_yk135": "腦白金靈芝孢子腦活素 150粒×2",
    "H6838001_S_MK284": "療濕痛 60粒",
    "H6838001_S_K0003": "坐骨神徑痛丸 60粒",
    "H6838001_S_k0032": "滅濕痛風痛膏布 7×11cm（10片×3）",
    "H6838001_S_yk398": "北京牛黃解毒片 120片",
    "H6838001_S_y11": "坐骨神徑痛丸 60粒＋膏布 10片",
    "H6838001_S_K0014": "日本救心丹 100粒",
    "H6838001_S_y22": "坐骨神徑痛丸 150粒×2＋炎必清",
    "H6838001_S_MK349": "滅濕痛風痛活絡油 50ml",
    "H6838001_S_k0029": "通血丸 60粒",
    "H6838001_S_k0034": "滴膚堅 15ml×3",
    "H6838001_S_k0007": "速效坐骨神徑痛丸 150粒",
    "H6838001_S_K0023": "風痛骨剌丹 60粒",
    "H6838001_S_MK285": "健齒靈 60粒",
    "H6838001_S_y6": "坐骨神徑痛丸 150粒＋痛油 50ml",
    "H6838001_S_y21": "坐骨神徑痛丸 150粒×2＋痛油",
    "H6838001_S_k0043": "千里追風坐骨神徑痛油 50ml×3",
    "H6838001_S_K0006": "風澀骨剌丹 150粒",
    "H6838001_S_MK368": "鼻炎素 60粒",
    "H6838001_S_k0047": "滅濕痛活絡油 50ml×3",
    "H6838001_S_y25": "滅濕痛風痛油＋60粒",
    "H6838001_S_SP3": "坐骨神徑痛油 50ml×2",
    "H6838001_S_yk245": "紅外線額探溫度計",
    "H6838001_S_MK401": "ROCKTECH 無線靜音滑鼠",
    "H6838001_S_MK402": "Rocktech 藍牙喇叭",
    "H6838001_S_MK388": "一條根追風F骨膏布 11×15cm",
    "H6838001_S_MK387": "一條根追風F骨膏布 7×11cm",
    "H6838001_S_MK370": "健步虎潛丸 320粒",
    "H6838001_S_K0011": "兒童蟲草靈芝孢子腦活素 150粒",
    "H6838001_S_MK381": "八岐蛇千里追風油 50ml",
    "H6838001_S_MK385": "八岐蛇楓濕坐骨靈油 50ml",
    "H6838001_S_MK384": "八岐蛇破痛油 50ml",
    "H6838001_S_MK383": "八岐蛇肩頸刺骨靈油 50ml",
    "H6838001_S_MK389": "八岐蛇頸腰椎坐骨靈油 50ml",
    "H6838001_S_MK380": "北京安宮牛黃丸 1丸",
    "H6838001_S_HK01": "北京安宮牛黃丸 6丸",
    "H6838001_S_MK382": "北京安宮牛黃丸 3丸錦盒裝",
    "H6838001_S_k0017": "北京牛黃解毒片 120粒×3",
    "H6838001_S_yk472": "北京牛黃解毒片 120粒×7",
    "H6838001_S_y4": "坐骨舒緩四件組",
    "H6838001_S_y20": "坐骨神徑痛丸 150粒×2＋大膏布",
    "H6838001_S_y15": "坐骨神徑痛丸 60粒＋炎必清",
    "H6838001_S_y18": "坐骨神徑痛丸 60粒×3＋膏布",
    "H6838001_S_y17": "坐骨神徑痛丸 60粒×3＋痛油",
    "H6838001_S_y19": "坐骨神徑痛丸 60粒×3＋炎必清",
    "H6838001_S_MK344": "坐骨神經リマチ痛丸 100粒",
    "H6838001_S_y2": "坐骨神經丸 150粒＋膏布",
    "H6838001_S_y1": "坐骨神經膏布＋炎必清",
    "H6838001_S_MK290": "坐骨腰痛丸 60粒",
    "H6838001_S_k0042": "坐骨腰痛油 50ml×3",
    "H6838001_S_yk473": "威猛神油 10ml 噴霧",
    "H6838001_S_MK369": "尹淑梅久咳丸 120粒",
    "H6838001_S_HK011": "尹淑梅久咳調理丸 12盒",
    "H6838001_S_HK102": "尹淑梅久咳調理丸 60粒",
    "H6838001_S_MK292": "強力濃縮坐骨腰痛丸 150粒",
    "H6838001_S_MK390": "強力特效久咳丸 720粒",
    "H6838001_S_k0045": "活絡靈千里追風油 50ml×3",
    "H6838001_S_k0035": "想睡就睡 50粒",
    "H6838001_S_MK341": "懸掛式家居收納袋",
    "H6838001_S_MK397": "五鞭海狗丸 350粒",
    "H6838001_S_MK356": "朱砂本命佛（狗／豬）",
    "H6838001_S_MK358": "朱砂本命佛（雞）",
    "H6838001_S_MK359": "朱砂本命佛（馬）",
    "H6838001_S_MK360": "朱砂本命佛（鼠）",
    "H6838001_S_y23": "活絡靈油＋活絡靈2 60粒",
    "H6838001_S_yk410": "活絡靈千里追風油 50ml",
    "H6838001_S_yk395": "滴膚堅 Difugen 15ml",
    "H6838001_S_MK346": "特供金毫毛紅茶 30克",
    "H6838001_S_MK391": "特效強力久咳丸 720粒",
    "H6838001_S_y3": "坐骨舒緩三件組",
    "H6838001_S_y16": "炎必清＋活絡油雙效組",
    "H6838001_S_MK399": "強力特效久咳丸 6樽",
    "H6838001_S_y7": "坐骨神徑痛丸 150粒＋炎必清",
    "H6838001_S_y12": "坐骨神徑痛丸＋膏布＋痛油",
    "H6838001_S_y13": "坐骨四合一舒緩套裝",
    "H6838001_S_y8": "坐骨神經膏布＋痛油（大）",
    "H6838001_S_y9": "坐骨神經膏布＋痛油（小）",
    "H6838001_S_y10": "坐骨神經膏布＋炎必清",
    "H6838001_S_y27": "坐骨腰痛油＋腰痛丸",
    "H6838001_S_k0039": "濕痛骨剌丹 60粒",
    "H6838001_S_MK396": "金龍五鞭海狗丸 350粒",
    "H6838001_S_HK100": "強力特效久咳丸 60粒",
    "H6838001_S_yk407": "濃縮坐骨腰痛油 50ml",
    "H6838001_S_yk409": "風澀骨刺痛油 50ml",
    "H6838001_S_MK395": "美國脈通心脈通 100粒",
    "H6838001_S_HK101": "華霞堂久咳丸 60粒",
    "H6838001_S_MK400": "華霞堂久咳丸 3樽",
    "H6838001_S_MK386": "金虎王活絡油 50ml",
    "H6838001_S_yk474": "金鋼神油 10ml 噴霧",
    "H6838001_S_TT-TS-10-001": "電氣石貼布 7盒70片",
    "H6838001_S_k0002": "風澀骨剌丹 60粒",
    "H6838001_S_y26": "風澀骨剌痛油＋骨剌丹",
    "H6838001_S_K0044": "風澀骨剌痛油 50ml×3",
    "H6838001_S_k0026": "骨痛靈 60粒",
    "H6838001_S_k0049": "骨痛靈 60粒（德國里哈明）",
}

KEYWORD_SLUG = [
    ("強力炎必清", "yanbiqing"),
    ("六味地黃丸", "liuwei-dihuang"),
    ("金門一條根", "jinmen-yitiaogen"),
    ("台灣一條根", "taiwan-yitiaogen"),
    ("追風F骨膏布", "zhuifeng-fgu-gaobu"),
    ("一條根", "yitiaogen"),
    ("坐骨神經膏布", "zuogu-gaobu"),
    ("坐骨神經丸", "zuogu-wan"),
    ("坐骨神徑痛丸", "zuogu-tongwan"),
    ("坐骨神徑痛油", "zuogu-tongyou"),
    ("坐骨腰痛丸", "zuogu-yaotong-wan"),
    ("坐骨腰痛油", "zuogu-yaotong-oil"),
    ("坐骨舒緩四件組", "zuogu-4pcs-set"),
    ("坐骨舒緩三件組", "zuogu-3pcs-set"),
    ("坐骨四合一", "zuogu-4in1"),
    ("千里追風", "qianli-zhuifeng"),
    ("膚特靈", "futeiling"),
    ("蕥歡仙", "yahuanxian"),
    ("花塔糖", "huatatang"),
    ("滅濕痛風痛膏布", "mieshitong-gaobu"),
    ("滅濕痛風痛活絡油", "mieshitong-oil"),
    ("滅濕痛活絡油", "mieshitong-oil"),
    ("滅濕痛風痛油", "mieshitong-oil"),
    ("滅濕痛風痛", "mieshitong"),
    ("百痛敵", "baitongdi"),
    ("活絡靈", "huoluoling"),
    ("腦白金", "naobaijin"),
    ("靈芝孢子腦活素", "lingzhi-naohuosu"),
    ("尿酸清", "niaosuanqing"),
    ("風澀骨剌丹", "fengse-gucidan"),
    ("風涩骨剌丹", "fengse-gucidan"),
    ("風澀骨剌痛油", "fengse-gutong-oil"),
    ("風涩骨剌痛油", "fengse-gutong-oil"),
    ("風澀骨刺痛油", "fengse-gutong-oil"),
    ("風痛骨剌丹", "fengtong-gucidan"),
    ("濕痛骨剌丹", "shitong-gucidan"),
    ("鼻炎素", "biyan"),
    ("健齒靈", "jianchiling"),
    ("久咳調理丸", "jiuke-tiaoli"),
    ("久咳丸", "jiuke-wan"),
    ("滴膚堅", "difugen"),
    ("骨痛靈", "gutongling"),
    ("牛黃解毒片", "niuhuang-jiedu"),
    ("安宮牛黃丸", "angong-niuhuang"),
    ("救心丹", "jiuxin-dan"),
    ("療濕痛", "liaoshitong"),
    ("通血丸", "tongxue-wan"),
    ("健步虎潛丸", "jianbu-huqian"),
    ("八岐蛇", "baqi-she"),
    ("肩頸刺骨靈油", "jianjing-cigu-oil"),
    ("頸腰椎坐骨靈油", "jingyaozhui-oil"),
    ("楓濕坐骨靈油", "fengshi-zuogu-oil"),
    ("破痛油", "potong-oil"),
    ("想睡就睡", "xiangshui"),
    ("五鞭海狗丸", "wubian-haigou"),
    ("金龍五鞭", "jinlong-wubian"),
    ("脈通心脈通", "maitong"),
    ("金虎王", "jinhuwang"),
    ("威猛神油", "weimeng-shenyou"),
    ("金鋼神油", "jingang-shenyou"),
    ("電氣石貼布", "dianqishi-tiebu"),
    ("額探溫度計", "forehead-thermometer"),
    ("無線光學靜音滑鼠", "wireless-mouse"),
    ("藍牙喇叭", "bluetooth-speaker"),
    ("收納袋", "storage-bag"),
    ("本命佛", "benmingfo"),
    ("金毫毛紅茶", "jinmaomao-hongcha"),
    ("リマチ痛丸", "rimachi-wan"),
    ("炎必清＋活絡油", "yanbiqing-oil-set"),
    ("炎必清", "yanbiqing"),
    ("BEVIDAN", "bevidan"),
    ("東京塔牌", "tokyo-tower"),
    ("華霞堂", "huaxiatang"),
    ("尹淑梅", "yinshumei"),
]

def esc(s: str) -> str:
    return htmlmod.escape(str(s), quote=True)

def parse_catalog():
    text = CATALOG.read_text(encoding="utf-8")
    products = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 9:
            continue
        try:
            num = int(cols[0])
        except ValueError:
            continue
        sku = cols[8].strip("`").strip()
        if not sku.startswith("H6838001"):
            continue
        sold_raw = cols[4].strip()
        try:
            sold = int(sold_raw) if sold_raw not in ("—", "-", "") else 0
        except ValueError:
            sold = 0
        products.append({
            "num": num,
            "title": cols[1],
            "current": cols[2].replace("$", "").strip(),
            "original": cols[3].replace("$", "").strip(),
            "sold": sold,
            "sold_label": cols[5] if cols[5] not in ("—", "-") else "",
            "brand": cols[6] if cols[6] not in ("—", "-") else "盈康",
            "origin": cols[7] if cols[7] not in ("—", "N/A", "-") else "",
            "sku": sku,
            "code": sku.split("_")[-1].lower(),
        })
    return products

def short_title(p) -> str:
    if p["sku"] in NAME_OVERRIDES:
        return NAME_OVERRIDES[p["sku"]]
    t = p["title"]
    t = re.sub(r"^【[^】]+】", "", t)
    t = re.sub(r"^\[[^\]]+\]\s*", "", t)
    parts = [x.strip() for x in re.split(r"[｜|]", t) if x.strip()]
    if not parts:
        return t[:40]
    first = parts[0]
    brandish = any(k in first for k in ("漢堡里哈明", "公牛牌", "盈康 Ying", "德國", "塔牌"))
    name = parts[1] if brandish and len(parts) > 1 and len(first) < 28 else first
    name = name.replace("盈康 Ying Kang ", "").replace("Ying Kang ", "").replace("盈康 ", "")
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"---+.*$", "", name).strip()
    return name[:42].rstrip() if len(name) > 42 else name

def pack_size(title: str, name: str) -> str:
    for src in (name, title):
        for pat in [
            r"(\d+\s*粒(?:\s*[x×X]\s*\d+)?)",
            r"(\d+\s*片(?:\s*[x×X]\s*\d+)?)",
            r"(\d+\s*ml(?:\s*[x×X]\s*\d+)?)",
            r"(\d+\s*丸)",
            r"(\d+\s*盒)",
            r"(\d+\s*支)",
            r"(\d+\s*樽)",
            r"(\d+\s*克)",
        ]:
            m = re.search(pat, src, re.I)
            if m:
                return m.group(1).replace(" ", "").replace("x", "×").replace("X", "×")
    return "詳見規格"

def categorize(p) -> str:
    t = p["title"] + " " + short_title(p)
    if any(k in t for k in ("滑鼠", "喇叭", "收納袋", "本命佛", "朱砂", "溫度計", "額探",
                            "ROCKTECH", "Rocktech", "Bo hui", "紅茶", "電氣石")):
        return "周邊家品"
    if any(k in t for k in ("套裝", "組合", "雙效組", "三件組", "四合一", "週期裝", "超值分享")):
        return "套裝優惠"
    if ("+" in t or "＋" in t) and any(k in t for k in ("丸", "油", "膏布", "炎必清", "贈送", "活絡靈")):
        return "套裝優惠"
    if any(k in t for k in ("膏布", "貼布", "止痛貼", "鎮痛貼")):
        return "膏布外用"
    if any(k in t for k in ("噴霧", "噴掃", "活絡油", "痛油", "神油", "Difugen", "滴膚", "膚特靈")):
        return "噴霧滴劑"
    if re.search(r"\d+\s*ml", t, re.I) and any(k in t for k in ("油", "靈油", "追風")):
        return "噴霧滴劑"
    # multi-pack oils / Caps counted as 套裝 if clearly multi-unit promo
    if re.search(r"(50ML|50ml|120ml)\s*[x×X]\s*[23]", t) or re.search(r"[x×X]\s*3\s*盒", t):
        if "膏布" not in t:
            return "套裝優惠"
    if re.search(r"(粒|片)\s*[x×X]\s*[2-9]", t) and ("盒" in t or "支" in t or "瓶" in t or "樽" in t):
        return "套裝優惠"
    return "口服膠囊"

def form_label(cat: str) -> str:
    return {
        "膏布外用": "外用膏布",
        "噴霧滴劑": "外用／噴霧",
        "套裝優惠": "套裝",
        "周邊家品": "周邊",
        "口服膠囊": "口服",
    }.get(cat, "產品")

def usage_text(cat: str, name: str) -> str:
    if cat == "膏布外用":
        return "外用：清潔皮膚後貼於不適部位，按產品包裝指示更換。"
    if cat == "噴霧滴劑":
        if "噴" in name:
            return "外用：適量噴於清潔後皮膚；避免接觸眼睛與黏膜。"
        return "外用：適量塗抹於清潔後皮膚；避免接觸眼睛與破損皮膚。"
    if cat == "周邊家品":
        return "請依產品說明書操作；電子產品請注意電池與充電安全。"
    if cat == "套裝優惠":
        return "請分別依各單品包裝說明使用；有疑問可 WhatsApp 查詢。"
    return "成人：請依包裝標示服用；建議溫水送服。"

def intro_text(p, name: str, cat: str) -> str:
    parts = [x.strip() for x in re.split(r"[｜|]", p["title"]) if x.strip()]
    segs = []
    for seg in parts[1:] if len(parts) > 1 else []:
        if any(k in seg for k in ("最佳食用期", "關鍵詞", "商標", "圖片只供")):
            continue
        seg = re.sub(r"(專治|治療|根治|秒殺|神奇)", "", seg)
        if seg.strip():
            segs.append(seg.strip())
    if segs:
        desc = "、".join(segs[:2])
        if len(desc) > 110:
            desc = desc[:110].rstrip() + "…"
        return "「%s」為盈康香港輕養生目錄產品，規格重點包括：%s。詳情請以包裝及 HKTVmall 頁面為準。" % (name, desc)
    hints = {
        "膏布外用": "外用膏布，適合日常筋骨部位局部護理。",
        "噴霧滴劑": "外用配方，方便局部塗抹或噴灑護理。",
        "套裝優惠": "組合裝便於一併選購相關護理品項。",
        "周邊家品": "店舖周邊／生活用品，詳見規格說明。",
        "口服膠囊": "口服養生配方，請依包裝標示服用。",
    }
    return "「%s」%s品牌：%s。" % (name, hints.get(cat, "盈康目錄產品。"), p["brand"])

def audience_cards(cat: str) -> str:
    sets = {
        "膏布外用": [("🪑", "久坐腰腿痠脹"), ("🚗", "長途駕駛疲勞"), ("🪜", "上落樓梯乏力"), ("❄️", "天氣轉涼僵硬")],
        "噴霧滴劑": [("🧴", "局部外用護理"), ("🏃", "運動後舒緩"), ("💼", "辦公室肩頸"), ("🌙", "睡前放鬆按摩")],
        "口服膠囊": [("🪑", "久坐循環欠佳"), ("🌙", "作息不規律"), ("💪", "日常筋骨保養"), ("🌿", "養生調理習慣")],
        "套裝優惠": [("🎁", "一次備齊常用"), ("👨‍👩‍👧", "家人分享裝"), ("📅", "週期護理更方便"), ("💬", "可 WhatsApp 問用法")],
        "周邊家品": [("🏠", "家居日常使用"), ("🎒", "便攜外出"), ("🔧", "簡易操作"), ("📦", "店舖同步上架")],
    }
    cards = sets.get(cat, sets["口服膠囊"])
    return "".join(
        '<div class="lf-aud-card"><div class="ico">%s</div><p>%s</p></div>' % (a, b)
        for a, b in cards
    )

def feature_cards(cat: str, intro: str) -> str:
    snippets = intro[:60] + ("…" if len(intro) > 60 else "")
    items = [
        ("✨", "規格清晰", "以目錄現價與包裝規格為準，方便對照選購。"),
        ("🛡️", "日常護理", snippets),
        ("🌿", "品牌把關", "盈康香港輕養生 HKTVmall 店舖同步上架。"),
        ("💧", "查詢通道", "WhatsApp %s 僅作備用聯絡。" % PHONE),
    ]
    if cat == "周邊家品":
        items[1] = ("🛡️", "生活用品", "非藥品類商品，請依說明書使用。")
    return "".join(
        '<div class="lf-ben"><div class="ico">%s</div><h3>%s</h3><p>%s</p></div>' % (a, esc(b), esc(c))
        for a, b, c in items
    )

def known_ingredients(title: str) -> list:
    mapping = [
        ("穿心蓮", "傳統清熱草本，常見於喉嚨不適相關配方說明。"),
        ("紫錐花", "免疫草本，季節轉換期防護支援的常見成分。"),
        ("香蜂草", "溫和草本，清熱配方中常用以顧及脾胃感受。"),
        ("銀杏", "常見於末梢循環相關產品敘述。"),
        ("碧容健", "松樹皮萃取（Pycnogenol），常見抗氧化敘述成分。"),
        ("碧蘿芷", "松樹皮萃取，常見抗氧化敘述成分。"),
        ("Pycnogenol", "松樹皮萃取，常見抗氧化敘述成分。"),
        ("一條根", "台灣常見外用精油／膏布配方成分。"),
        ("艾草", "外用精油配方常見成分。"),
        ("薑油", "外用精油配方常見成分。"),
        ("靈芝", "傳統養生菌類，常見於腦部／活力相關配方。"),
        ("蟲草", "傳統養生菌類，常見於專注／體力相關敘述。"),
        ("納豆", "發酵豆類益生相關常見成分。"),
        ("山楂", "開胃消食相關傳統草本。"),
        ("牛黃", "傳統中成藥常見成分（以包裝標示為準）。"),
        ("熊膽", "傳統配方成分（以包裝標示為準；或標示人工替代）。"),
        ("蟾酥", "傳統強心類配方常見成分（以包裝標示為準）。"),
    ]
    found = []
    for k, v in mapping:
        if k in title and k not in [f[0] for f in found]:
            found.append((k, v))
        if len(found) >= 4:
            break
    return found

def ascii_slug(name: str, sku: str) -> str:
    tail = sku.split("_")[-1].lower()
    # sanitize tail for filesystem (TT-TS-10-001 -> tt-ts-10-001)
    tail = re.sub(r"[^a-z0-9\-]+", "-", tail).strip("-")
    parts = []
    rest = name
    for zh, en in KEYWORD_SLUG:
        if zh in rest:
            parts.append(en)
            rest = rest.replace(zh, "", 1)
    m = re.search(r"(\d+)\s*粒", name)
    if m:
        parts.append("%scaps" % m.group(1))
    m = re.search(r"(\d+)\s*片", name)
    if m:
        parts.append("%spcs" % m.group(1))
    m = re.search(r"(\d+)\s*ml", name, re.I)
    if m:
        parts.append("%sml" % m.group(1))
    m = re.search(r"(\d+)\s*丸", name)
    if m and "caps" not in "-".join(parts):
        parts.append("%spills" % m.group(1))
    m = re.search(r"[×xX]\s*(\d+)", name)
    if m:
        xpart = "x%s" % m.group(1)
        if xpart not in "-".join(parts):
            parts.append(xpart)
    if not parts:
        parts.append("product")
    slug = "-".join(parts) + "-" + tail
    slug = re.sub(r"[^a-z0-9\-]+", "-", slug.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:90]

def find_image(slug: str) -> tuple[str, bool]:
    """Return (web path relative to products/, has_real_image)."""
    folder = ASSETS / slug
    if folder.is_dir():
        for name in ("primary.png", "primary.jpg", "primary.webp", "primary.jpeg"):
            if (folder / name).exists():
                return "../assets/products/%s/%s" % (slug, name), True
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                return "../assets/products/%s/%s" % (slug, f.name), True
    return "../assets/logo.png", False

def load_existing_slug_map():
    """Map sku code -> existing filename slug (without .html)."""
    m = {}
    for f in PRODUCTS.glob("*.html"):
        if f.name == "index.html":
            continue
        text = f.read_text(encoding="utf-8")
        sm = re.search(r"H6838001_S_([A-Za-z0-9_-]+)", text)
        if sm:
            code = sm.group(1).lower()
            slug = f.stem
            m[code] = slug
    return m

HEADER = open("/workspace/yingkang-unified/products/yanbiqing-60caps-y5.html", encoding="utf-8").read()
# We build pages programmatically; keep shared chrome as functions.

def page_chrome_head(title, description, canonical):
    return """<!DOCTYPE html>
<html lang="zh-Hant-HK">
<head>
<meta name="google-site-verification" content="vWFxJ5mlWUgUCUnKELkO0L4Wo_IZAVfqZ7EQ6fkwOeY" />
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap" rel="stylesheet">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<link rel="stylesheet" href="../assets/site.css?v=%s">
</head>
<body>
""" % (esc(title), esc(description), esc(canonical), CSS_V)

def shared_header_nav():
    # Extract from template lines 16-79
    tpl = Path("/workspace/yingkang-unified/products/yanbiqing-60caps-y5.html").read_text(encoding="utf-8")
    start = tpl.index('<header class="m-header"')
    end = tpl.index('<div class="wrap">')
    return tpl[start:end]

def shared_footer():
    tpl = Path("/workspace/yingkang-unified/products/yanbiqing-60caps-y5.html").read_text(encoding="utf-8")
    start = tpl.index('<div class="footer-upper"')
    return tpl[start:]

def related_blocks(all_items, current_sku, cat, limit=4):
    same = [x for x in all_items if x["sku"] != current_sku and x["cat"] == cat]
    others = [x for x in all_items if x["sku"] != current_sku and x["cat"] != cat]
    picks = (same + others)[:limit]
    blocks = []
    for x in picks:
        img, _ = find_image(x["slug"])
        blocks.append(
            """<a class="banner-product-block" href="../products/%s.html">
  <div class="product-img"><img src="%s" alt="%s" loading="lazy"></div>
  <div class="product-text">
    <div class="product-title">%s</div>
    <div class="product-content">%s</div>
    <div class="product-price">HK$%s%s</div>
  </div>
</a>""" % (
                esc(x["slug"]),
                esc(img),
                esc(x["name"]),
                esc(x["name"]),
                esc(x["intro"][:70]),
                esc(x["current"]),
                (" · " + esc(x["sold_label"])) if x["sold_label"] else "",
            )
        )
    return "".join(blocks)

def render_product(p, slug, all_items, missing_images):
    name = p["name"]
    cat = p["cat"]
    form = form_label(cat)
    intro = p["intro"]
    img, has_img = find_image(slug)
    if not has_img:
        missing_images.append((slug, p["sku"], name))
    was = ""
    if p["original"] and p["original"] != p["current"]:
        was = ' <span class="price-was">HK$%s</span>' % esc(p["original"])
    sold = (' <span class="sold">%s</span>' % esc(p["sold_label"])) if p["sold_label"] else ""
    wa_q = quote("我想查詢：%s" % name)
    hktv = HKTV.format(sku=p["sku"])
    ings = known_ingredients(p["title"])
    if ings:
        ing_html = "".join(
            '<div class="lf-ing-card"><div class="dot">%d</div><div><strong>%s</strong><span>%s</span></div></div>'
            % (i + 1, esc(a), esc(b))
            for i, (a, b) in enumerate(ings)
        )
        ing_section = """
  <div class="lf-section">
    <h2>配方／成分<span class="accent">說明</span></h2>
    <div class="lf-ing-grid">%s</div>
    <p class="muted" style="font-size:0.88rem">以上成分說明取自品名常見敘述，並非檢測報告數據；請以包裝標示為準。</p>
  </div>""" % ing_html
    else:
        ing_section = """
  <div class="lf-section">
    <h2>配方／成分<span class="accent">說明</span></h2>
    <p>詳細成分配方請以產品包裝及 HKTVmall 商品頁為準。本頁不作未核實之檢測數據陳述。</p>
  </div>"""

    origin = p["origin"] or "—"
    meta = "%s — %s。HK$%s。盈康香港・WhatsApp %s" % (name, intro[:70], p["current"], PHONE)

    body = """
<div class="wrap">
  <p class="crumb"><a href="../index.html">首頁</a> › <a href="index.html">所有產品</a> › %s</p>

  <div class="lf-top">
    <div class="lf-gallery">
      <img class="main" id="main-img" src="%s" alt="%s">
    </div>
    <div class="lf-buy">
      <h1>%s</h1>
      <p class="lf-spec-line">%s · %s</p>
      <div class="lf-rating">★★★★☆ 目錄產品</div>
      <div class="price-row"><span class="price-now">HK$%s</span>%s%s</div>
      <span class="stock">有貨・可於 HKTVmall 選購</span>
      <p style="margin-top:1rem;color:#555">%s</p>
      <div class="cta-row" style="margin-top:1.1rem">
        <a class="lf-cta-hktv" href="%s" target="_blank" rel="noopener">於 HKTVmall 查看</a>
        <a class="lf-cta-wa" href="%s?text=%s" target="_blank" rel="noopener">💬 WhatsApp 查詢</a>
      </div>
      <p class="muted" style="font-size:0.85rem;margin-top:0.8rem">可經 HKTVmall 或 WhatsApp %s 確認庫存與用法。本站不設即時扣款結帳。</p>
    </div>
  </div>

  <div class="lf-section">
    <h2>您是否有以下<span class="accent">需要</span>？</h2>
    <div class="lf-audience">%s</div>
  </div>

  <div class="lf-section">
    <h2>產品<span class="accent">簡介</span></h2>
    <p>%s</p>
  </div>

  %s

  <div class="lf-section">
    <h2>產品<span class="accent">特點</span></h2>
    <div class="lf-benefits">%s</div>
  </div>

  <div class="lf-banner">
    <h3>盈康・輕養生日常</h3>
    <p>香港本地品牌｜說明可查、日常可依｜WhatsApp %s</p>
  </div>

  <div class="lf-section">
    <h2>用法與<span class="accent">保存</span></h2>
    <table class="lf-usage-table">
      <tr><th>建議用法</th><td>%s</td></tr>
      <tr><th>劑型</th><td>%s</td></tr>
      <tr><th>保存</th><td>請置於陰涼乾爽處（約 25°C 以下），避免陽光直射，並放於兒童接觸不到的地方。</td></tr>
      <tr><th>注意</th><td>孕婦、兒童及長期病患者請先諮詢專業意見。外用產品避免接觸眼睛與破損皮膚。本頁內容並非醫療建議。</td></tr>
    </table>
  </div>

  <div class="lf-section">
    <h2>產品<span class="accent">規格</span></h2>
    <table class="lf-spec-table">
      <tr><th>產品名稱</th><td>%s</td></tr>
      <tr><th>品牌</th><td>%s</td></tr>
      <tr><th>分類</th><td>%s · %s</td></tr>
      <tr><th>產地</th><td>%s</td></tr>
      <tr><th>SKU</th><td>%s</td></tr>
      <tr><th>售價</th><td>HK$%s（以 HKTVmall 當日為準）</td></tr>
      <tr><th>客服</th><td>WhatsApp %s（備用）</td></tr>
    </table>
  </div>

  <div class="lf-cap231">%s</div>

  <div class="lf-bottom-cta">
    <a class="lf-cta-wa" href="%s?text=%s" target="_blank" rel="noopener">💬 立即 WhatsApp 查詢 %s</a>
  </div>

  <div class="lf-section">
    <h2>名人<span class="accent">推薦</span></h2>
    <p>尹淑梅中醫師（從醫五十多年・香港註冊中醫師）支持盈康「說明可查、日常可依」的輕養生理念。其榮譽包括香港中國醫藥研究院榮譽院長、香港中國醫藥學會永遠榮譽會長，並榮登《世界名人錄》及傑出英才錄。</p>
    <p class="muted">推薦反映品牌理念認同，並非對單一療效之醫學保證。</p>
  </div>

  <div class="lf-section">
  <h2>相關<span class="accent">商品</span></h2>
  <div class="banner-product">%s</div>
</div>
</div>
""" % (
        esc(name),
        esc(img), esc(name),
        esc(name),
        esc(p["brand"]), esc(form),
        esc(p["current"]), was, sold,
        esc(intro),
        esc(hktv),
        WA, wa_q,
        PHONE,
        audience_cards(cat),
        esc(intro),
        ing_section,
        feature_cards(cat, intro),
        PHONE,
        esc(usage_text(cat, name)),
        esc(form),
        esc(name),
        esc(p["brand"]),
        esc(p["brand"]), esc(form),
        esc(origin),
        esc(p["sku"]),
        esc(p["current"]),
        PHONE,
        CAP231,
        WA, wa_q, esc(name),
        related_blocks(all_items, p["sku"], cat),
    )
    return page_chrome_head("%s｜盈康" % name, meta, "%s/products/%s.html" % (BASE, slug)) + shared_header_nav() + body + shared_footer()

def render_index(items):
    from collections import Counter
    counts = Counter(x["cat"] for x in items)
    cats_order = ["全部產品", "膏布外用", "口服膠囊", "噴霧滴劑", "套裝優惠", "周邊家品"]
    lis = []
    for c in cats_order:
        n = len(items) if c == "全部產品" else counts.get(c, 0)
        if c != "全部產品" and n == 0:
            continue
        href = "index.html" if c == "全部產品" else ("index.html?cat=" + quote(c))
        lis.append('<li><a href="%s" data-cat="%s"><span>%s</span><span class="cnt">%d</span></a></li>' % (href, esc(c), esc(c), n))
    # reuse index header from existing file structure
    tpl = Path("/workspace/yingkang-unified/products/index.html").read_text(encoding="utf-8")
    # rebuild fully for consistency
    head_end = tpl.index('<div class="catalog-layout">')
    # Use new header with updated count in description via string replace on template head
    head = tpl[:head_end]
    head = re.sub(r'content="盈康全部產品一覽：[^"]*"',
                  'content="盈康全部產品一覽：膏布、口服、外用噴霧、套裝與周邊。香港本地品牌・HKTVmall 可購。共 %d 件。"' % len(items),
                  head)
    # rebuild sidebar + main opening
    mid = """<div class="catalog-layout">
  <aside class="catalog-sidebar">
    <form class="side-search" action="index.html" method="get" id="side-search-form">
      <input type="search" name="q" id="side-q" placeholder="搜尋產品…" aria-label="搜尋產品">
      <button type="submit" aria-label="搜尋">🔍</button>
    </form>
    <div class="side-cat-title">分類</div>
    <ul class="side-cats" id="side-cats">
%s
    </ul>
  </aside>
  <main>
    <div class="catalog-toolbar">
      <p class="crumb"><a href="../index.html">首頁</a> / 所有產品</p>
      <div class="sort-ui">
        <label>商品排序 <select id="sort-select" aria-label="商品排序">
          <option>預設</option>
          <option>價格由低至高</option>
          <option>價格由高至低</option>
          <option>名稱</option>
        </select></label>
        <label>每頁顯示 <select aria-label="每頁顯示數量">
          <option>24</option>
          <option>48</option>
          <option selected>全部</option>
        </select></label>
      </div>
    </div>
    <h1 class="catalog-title" id="catalog-title">所有產品（%d）</h1>
    <div class="plist" id="plist">
""" % ("\n".join(lis), len(items))

    cards = []
    for x in items:
        img, has = find_image(x["slug"])
        badge = ""
        if x["cat"] == "套裝優惠":
            badge = '<span class="plist-badge blue">套裝優惠</span>'
        elif x["sold"] >= 100:
            badge = '<span class="plist-badge">熱賣</span>'
        cards.append("""<a class="plist-card" href="%s.html" data-cat="%s" data-name="%s">
  <div class="plist-img-wrap">
    %s
    <img src="%s" alt="%s" loading="lazy">
  </div>
  <div class="plist-name">%s</div>
  <div class="plist-size">%s</div>
  <p class="plist-price">HK$%s</p>
</a>""" % (
            esc(x["slug"]), esc(x["cat"]), esc(x["name"]),
            badge,
            esc(img), esc(x["name"]),
            esc(x["name"]),
            esc(x["size"]),
            esc(x["current"]),
        ))

    foot_start = tpl.index('<div class="footer-upper"')
    # keep footer + filter script from template, but ensure title count works
    foot = tpl[foot_start:]
    return head + mid + "\n".join(cards) + "\n    </div>\n  </main>\n</div>\n" + foot

def update_sitemap(slugs):
    sm = (REPO / "sitemap.xml").read_text(encoding="utf-8")
    # remove existing product/*.html urls
    sm2 = re.sub(
        r"  <url>\s*<loc>https://www\.ykimed\.com/products/[^<]+\.html</loc>.*?</url>\n?",
        "",
        sm,
        flags=re.S,
    )
    # insert product urls before healthblog posts or before closing urlset
    entries = []
    for slug in sorted(slugs):
        entries.append(
            "  <url>\n"
            "    <loc>https://www.ykimed.com/products/%s.html</loc>\n"
            "    <changefreq>weekly</changefreq>\n"
            "    <priority>0.8</priority>\n"
            "  </url>\n" % slug
        )
    # place after products/ listing url
    marker = "https://www.ykimed.com/products/</loc>"
    idx = sm2.find(marker)
    if idx < 0:
        raise SystemExit("products/ loc not found in sitemap")
    # find end of that url block
    end = sm2.find("</url>", idx) + len("</url>")
    sm2 = sm2[:end] + "\n" + "".join(entries) + sm2[end:]
    (REPO / "sitemap.xml").write_text(sm2, encoding="utf-8")

def main():
    catalog = parse_catalog()
    assert len(catalog) == 121, len(catalog)
    existing = load_existing_slug_map()
    print("Existing mapped:", len(existing))

    used_slugs = set(existing.values())
    items = []
    to_generate = []

    for p in catalog:
        name = short_title(p)
        cat = categorize(p)
        size = pack_size(p["title"], name)
        intro = intro_text(p, name, cat)
        code = p["code"]
        if code in EXISTING_CODES and code in existing:
            slug = existing[code]
        elif code in existing:
            slug = existing[code]
        else:
            slug = ascii_slug(name, p["sku"])
            base = slug
            n = 2
            while slug in used_slugs:
                slug = "%s-%d" % (base, n)
                n += 1
            used_slugs.add(slug)
            to_generate.append(p["sku"])
        used_slugs.add(slug)
        items.append({
            **p,
            "name": name,
            "cat": cat,
            "size": size,
            "intro": intro,
            "slug": slug,
        })

    missing_images = []
    # generate only new pages
    gen_count = 0
    for x in items:
        if x["sku"] not in to_generate and x["code"] in EXISTING_CODES:
            # still record missing image for index if needed
            _, has = find_image(x["slug"])
            if not has:
                missing_images.append((x["slug"], x["sku"], x["name"]))
            continue
        if x["code"] in EXISTING_CODES:
            continue
        html = render_product(x, x["slug"], items, missing_images)
        path = PRODUCTS / ("%s.html" % x["slug"])
        path.write_text(html, encoding="utf-8")
        gen_count += 1
        print("NEW", x["slug"], "←", x["name"])

    # rebuild index
    (PRODUCTS / "index.html").write_text(render_index(items), encoding="utf-8")
    update_sitemap([x["slug"] for x in items])

    # missing-images.md — only products without real images (new + old)
    miss_lines = ["# 缺圖產品清單", "", "以下產品頁暫以 logo／素底 placeholder 顯示，待補產品圖。", ""]
    # recompute all missing
    all_missing = []
    for x in items:
        _, has = find_image(x["slug"])
        if not has:
            all_missing.append(x)
    for x in all_missing:
        miss_lines.append("- `%s.html` — %s — `%s`" % (x["slug"], x["name"], x["sku"]))
    miss_lines.append("")
    miss_lines.append("合計缺圖：%d 件" % len(all_missing))
    (REPO / "missing-images.md").write_text("\n".join(miss_lines) + "\n", encoding="utf-8")

    print("Generated", gen_count, "new pages")
    print("Total products", len(items))
    print("Missing images", len(all_missing))
    # sanity
    htmls = [f for f in PRODUCTS.glob("*.html") if f.name != "index.html"]
    print("HTML product files on disk:", len(htmls))

if __name__ == "__main__":
    main()
