#!/usr/bin/env python3
"""分割したHTMLスライド断片を統合して、提出用/発表用HTMLを生成する。"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT.parent

DECKS = {
    "発表用": {
        "source_dir": ROOT / "発表用",
        "output": OUTPUT_DIR / "発表用スライド_軽め.html",
    },
    "課題提出用": {
        "source_dir": ROOT / "課題提出用",
        "output": OUTPUT_DIR / "課題提出用スライド_詳細版.html",
    },
}


SLIDE_OPEN_RE = re.compile(r'<div class="([^"]*\bslide\b[^"]*)" data-slide="\d+">')
PAGE_NUM_RE = re.compile(r'<span class="page-num">.*?</span>')


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def ordered_section_paths(source_dir: Path) -> list[Path]:
    paths = sorted(source_dir.glob("[0-9][0-9]_*.html"))
    if not paths:
        raise FileNotFoundError(f"section files not found: {source_dir}")
    return paths


def renumber_slides(html: str) -> str:
    slide_index = 0

    def replace_slide_open(match: re.Match[str]) -> str:
        nonlocal slide_index
        classes = match.group(1).split()
        classes = [name for name in classes if name != "active"]
        if slide_index == 0:
            classes.append("active")
        replacement = f'<div class="{" ".join(classes)}" data-slide="{slide_index}">'
        slide_index += 1
        return replacement

    html = SLIDE_OPEN_RE.sub(replace_slide_open, html)
    total_slides = slide_index
    page_index = 0

    def replace_page_num(_: re.Match[str]) -> str:
        nonlocal page_index
        page_index += 1
        return f'<span class="page-num">{page_index} / {total_slides}</span>'

    return PAGE_NUM_RE.sub(replace_page_num, html)


def build_deck(name: str) -> Path:
    config = DECKS[name]
    source_dir = config["source_dir"]
    before = read_text(source_dir / "template_before.html")
    after = read_text(source_dir / "template_after.html")
    sections = [read_text(path).strip() for path in ordered_section_paths(source_dir)]
    html = before.rstrip() + "\n" + "\n\n".join(sections) + "\n" + after.lstrip()
    html = renumber_slides(html)
    output = config["output"]
    write_text(output, html)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="分割スライドHTMLを統合する")
    parser.add_argument(
        "--deck",
        choices=[*DECKS.keys(), "all"],
        default="all",
        help="生成するデッキ",
    )
    args = parser.parse_args()

    names = DECKS.keys() if args.deck == "all" else [args.deck]
    for name in names:
        output = build_deck(name)
        print(f"built: {output}")


if __name__ == "__main__":
    main()
