# VG6 Careful — 逐格精心寫 prompt（非炎必清模具）

Miles decision (2026-10-24): **do NOT** only restore HKTVmall, and **do NOT** clone 炎必清 structure onto every SKU. Every product gets **6 carefully written prompts** from **that** product page’s real copy.

## Keep as-is
- `yanbiqing-60caps-y5` — hand-crafted gold standard. **Never regenerate.**

## Quality bar (from 炎必清 VG6, style only — not content)

| # | Role | Must be true to THIS SKU |
|---|------|---------------------------|
| 01 | Hero + packshot + price (was/now) + WhatsApp 查詢 6222 7238 | Real name, real price from HTML, real pack via `reference_image_paths` |
| 02 | Lifestyle + product in use / held | Real pain points / benefit headline from efficacy copy |
| 03 | Ingredients / formula / features grid | **ONLY** ingredients listed on that product page. If &lt;4, show fewer — **never invent** 清熱四寶 herbs. Peripherals → feature icons, not herbs. |
| 04 | Mechanism / how-it-helps / setup | True to product (pain→help, sleep→restore, plug-in→use). **Never** paste 上火炎症三步驟 / 清返嚟 unless that SKU truly has them. |
| 05 | Social proof (generic roles, no real celebrities) | Roles that fit the audience of THIS product |
| 06 | Comparison / why choose | Real alternatives for THIS category (涼茶 vs 安宮; 外用油 vs 百痛敵; 有線滑鼠 vs 靜音無線) |

**Visual style (shared):** 9:16, soft beige/cream + champagne gold, premium HK commercial, sharp Traditional Chinese on-image text, brand 盈康, WhatsApp CTA (never 加入購物車). No Cap.231 soft disclaimer on private site.

**Hard forbid mold phrases unless page truly uses them:** `清熱四寶`, `清返嚟`, `上火暗瘡`, `穿心蓮／紫錐花／蒲公英／香蜂草`, and any invented 四寶/四珍/四要 herb lists.

## Pipeline files
- `scripts/vg6_extract_facts.py` — parse product HTML → facts JSON
- `scripts/vg6-careful/prompts/<slug>.json` — **hand-written** 6 panel prompts + alts (source of truth per SKU)
- `scripts/vg6-careful-progress.json` — resume tracker
- `scripts/vg6_update_html.py` — rewrite detail stack (existing)
- `scripts/vg6_careful_apply.py` — copy generated jpgs into `assets/.../detail/vg6-0N.jpg` + run HTML update

## Per-SKU workflow
1. `python3 scripts/vg6_extract_facts.py <slug>` → review facts
2. **Carefully write** `scripts/vg6-careful/prompts/<slug>.json` (6 distinct prompts; cite real ingredients only)
3. GenerateImage ×6 with `aspect_ratio=9:16` + `reference_image_paths=[primary]`
4. `python3 scripts/vg6_careful_apply.py <slug> --from-dir <gen_dir>`
5. Mark progress; commit+push every 2–3 SKUs

## Pilot (this run)
1. `angong-niuhuang-1pills-mk380` — herbal/OTC (was wrongly given 清熱四珍 + 清返嚟)
2. `baitongdi-60caps-k0019` — oral supplement (was wrongly given 威靈仙/防風…; real page has 碧容健/銀杏)
3. `wireless-mouse-mk401` — non-supplement peripheral (must not use medicine mold)

Live: https://www.ykimed.com/products/<slug>.html

## Resume remaining (~118)
Exclude `yanbiqing-60caps-y5`. Read `vg6-careful-progress.json` for `pending`. Prefer SKUs whose old alts still contain 清熱四寶/清返嚟/invented herbs. Same careful prompt writing — **no batch template clone**.
