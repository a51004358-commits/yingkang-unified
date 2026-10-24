# VG6 直向詳圖 — batch resume guide

Goal: give every ykimed product page the same 6-panel Vita Green–style detail stack used on 炎必清 (`yanbiqing-60caps-y5`).

## Progress file (source of truth)

`scripts/vg6-progress.json`

- `products.<slug>.status`: `pending` | `queued` | `in_progress` | `done` | `failed`
- `products.<slug>.panels`: per-panel ok/fail notes
- `current_batch`: slugs actively being worked
- `stats`: done / pending / failed counts

## Resume

Parent: re-dispatch executor with:

> continue vg6 from progress.json

Executor should:

1. Read `scripts/vg6-progress.json`.
2. Skip any slug with `status=done` (including `yanbiqing-60caps-y5`).
3. Retry `failed` panels once, then continue.
4. Pick next ~10 `pending` (prefer `primary.*` + rich efficacy copy).
5. For each product: GenerateImage ×6 (9:16) → save to `assets/products/<slug>/detail/vg6-01.jpg`…`06.jpg` → rewrite HTML detail stack → update progress.
6. Git commit + push every 3 products (or ~15 min): `vg6 detail batch: <slugs>`.
7. On time budget end: finish current product, push, update `/workspace/vg6-ALL-HANDOFF.md`.

## Panel brief (same as 炎必清)

| # | File | Content |
|---|------|---------|
| 1 | vg6-01.jpg | Hero + packshot + price (was/now) + WhatsApp 查詢 6222 7238 |
| 2 | vg6-02.jpg | Elegant Asian woman holding product + benefit headline |
| 3 | vg6-03.jpg | Ingredients / formula infographic |
| 4 | vg6-04.jpg | Science 3-step pain→damage→product helps |
| 5 | vg6-05.jpg | 3 generic role endorsements (no real celebrities) |
| 6 | vg6-06.jpg | Comparison table vs common alternatives (4 rows) |

Style: premium HK supplement, beige/gold, sharp Traditional Chinese, commercial photography, mobile vertical 9:16. Brand 盈康. WhatsApp must say WhatsApp and 6222 7238. No Cap.231 disclaimer lines. CTA is WhatsApp 查詢, never 加入購物車.

Use `primary.*` as `reference_image_paths` when present.

## HTML pattern

Replace the whole `#product-detail-images` / `.pdp-detail-stack` block with the VG6 six-figure stack (see `products/yanbiqing-60caps-y5.html`).

## Live example

https://www.ykimed.com/products/yanbiqing-60caps-y5.html

---

## SUPERSEDED (2026-10-24)
Miles decided: stop cloning 炎必清 mold. Use **careful per-SKU prompts** instead.
See `scripts/vg6-careful-README.md` and `/workspace/vg6-CAREFUL-HANDOFF.md`.
Keep `yanbiqing-60caps-y5` as-is. Resume via `scripts/vg6-careful-progress.json`.
