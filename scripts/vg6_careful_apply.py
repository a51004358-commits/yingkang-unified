#!/usr/bin/env python3
"""Copy generated vg6-01..06 into assets and update HTML alts from prompt JSON."""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--from-dir", required=True, help="dir containing vg6-01.jpg .. vg6-06.jpg")
    args = ap.parse_args()
    slug = args.slug
    src = Path(args.from_dir)
    prompt_path = ROOT / "scripts/vg6-careful/prompts" / f"{slug}.json"
    if not prompt_path.exists():
        sys.exit(f"missing prompts: {prompt_path}")
    meta = json.loads(prompt_path.read_text(encoding="utf-8"))
    alts = [p["alt"] for p in meta["panels"]]
    if len(alts) != 6:
        sys.exit("need exactly 6 panels in prompt JSON")
    dest = ROOT / "assets/products" / slug / "detail"
    dest.mkdir(parents=True, exist_ok=True)
    for i in range(1, 7):
        name = f"vg6-{i:02d}.jpg"
        s = src / name
        if not s.exists():
            # also accept .png
            s = src / f"vg6-{i:02d}.png"
        if not s.exists():
            sys.exit(f"missing {name} in {src}")
        shutil.copy2(s, dest / f"vg6-{i:02d}.jpg")
        print(f"copied {s} -> {dest / f'vg6-{i:02d}.jpg'}")
    blurb = meta.get(
        "blurb",
        "六段直向詳圖（逐格按本產品文案製作），可直向滑動瀏覽。",
    )
    subprocess.check_call(
        [
            sys.executable,
            str(ROOT / "scripts/vg6_update_html.py"),
            slug,
            "--alts",
            *alts,
            "--blurb",
            blurb,
        ]
    )

if __name__ == "__main__":
    main()
