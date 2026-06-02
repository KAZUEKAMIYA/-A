#!/usr/bin/env python3
"""
manuscript_raw.mdの画像タグを読み取り、全挿絵をOpenAI gpt-image-2で生成する。
"""
import io
import re
import os
import sys
import time
from pathlib import Path

# Windows cp932 対策: stdout/stderrをUTF-8で強制出力
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
from openai_image_gen import load_env, generate_image

load_env()

SLUG = "gengo-ryoku"
BASE = Path(__file__).parent.parent
MANUSCRIPT = BASE / "output" / SLUG / "manuscript_raw.md"
IMAGES_DIR = BASE / "output" / SLUG / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# カラーパレット
PRIMARY = "#4A6CF7"
ACCENT = "#FF6B6B"
SUB = "#54C8A8"

STYLE = (
    "Clean flat design infographic illustration, soft pastel colors, rounded shapes, "
    "modern Japanese ebook aesthetic. "
    f"Color palette: primary blue {PRIMARY}, accent red-orange {ACCENT}, teal {SUB}. "
    "White or very light gray background. "
    "All text elements in the image must be written in Japanese (日本語). "
    "High quality, crisp, professional. Landscape orientation."
)

MANGA_STYLE = (
    "IMPORTANT: FULL COLOR manga illustration. Vibrant rich colors, colored backgrounds, "
    "colored clothing, colored hair, colored skin tones. Modern digital manga/webtoon style. "
    "All speech bubbles and text in Japanese (日本語)."
)


def tag_to_filename(index: int, tag_type: str, title: str) -> str:
    """タグ情報からファイル名を生成"""
    # タイトルから英数字・ハイフンのみのslugを生成
    clean = re.sub(r'[^\w\s-]', '', title)
    clean = re.sub(r'\s+', '_', clean.strip())[:30]
    prefix = "header" if tag_type == "HEADER_IMAGE" else "img"
    return f"{index:02d}_{prefix}_{clean}.png"


def build_prompt(tag_type: str, pattern: str, title: str, elements: str, description: str) -> str:
    elem_list = [e.strip() for e in elements.split(",")]

    if tag_type == "HEADER_IMAGE":
        elems_str = ", ".join(f'text reads "{e}"' for e in elem_list)
        return (
            f"Chapter header illustration for Japanese ebook. "
            f'Large bold Japanese title text reads "{title}". '
            f"Visual elements: {elems_str}. "
            f"Scene: {description}. "
            f"{STYLE} Landscape 3:2 ratio."
        )

    # INLINE_IMAGE パターン別
    elems_quoted = [f'text reads "{e}"' for e in elem_list]

    if pattern == "before-after":
        p = (f'Before/After comparison infographic. '
             f'Left panel labeled {elems_quoted[0] if elems_quoted else "Before"}, '
             f'right panel labeled {elems_quoted[1] if len(elems_quoted)>1 else "After"}. '
             f'Title: text reads "{title}". {description}.')
    elif pattern == "flow-horizontal":
        arrows = " → ".join(elems_quoted)
        p = f'Horizontal flow diagram with arrows: {arrows}. Title: text reads "{title}". {description}.'
    elif pattern == "flow-vertical":
        steps = ", then ".join(elems_quoted)
        p = f'Vertical step-by-step flow diagram: {steps}. Title: text reads "{title}". {description}.'
    elif pattern == "stairs":
        steps = ", ".join(elems_quoted)
        p = f'Staircase step diagram ascending from left to right, each step: {steps}. Title: text reads "{title}". {description}.'
    elif pattern == "cycle":
        nodes = ", ".join(elems_quoted)
        p = f'Circular cycle diagram with nodes connected by arrows: {nodes}. Title: text reads "{title}". {description}.'
    elif pattern == "pyramid":
        layers = ", ".join(elems_quoted)
        p = f'Triangle pyramid diagram with layers from top to base: {layers}. Title: text reads "{title}". {description}.'
    elif pattern == "radial":
        center = elems_quoted[0] if elems_quoted else f'text reads "{title}"'
        surrounding = ", ".join(elems_quoted[1:]) if len(elems_quoted) > 1 else ", ".join(elems_quoted)
        p = f'Radial mind-map diagram. Center circle {center}. Surrounding nodes: {surrounding}. Title: text reads "{title}". {description}.'
    elif pattern == "triangle":
        verts = ", ".join(elems_quoted)
        p = f'Triangle diagram with vertices or sections: {verts}. Title: text reads "{title}". {description}.'
    elif pattern in ("comparison-table", "matrix"):
        items = ", ".join(elems_quoted)
        p = f'Comparison table or matrix infographic with sections: {items}. Title: text reads "{title}". {description}.'
    elif pattern == "layers":
        layers = ", ".join(elems_quoted)
        p = f'Layered stack diagram with layers from top to bottom: {layers}. Title: text reads "{title}". {description}.'
    elif pattern == "tree":
        nodes = ", ".join(elems_quoted)
        p = f'Hierarchical tree diagram with nodes: {nodes}. Title: text reads "{title}". {description}.'
    elif pattern == "honeycomb":
        cells = ", ".join(elems_quoted)
        p = f'Honeycomb hexagonal grid diagram with cells labeled: {cells}. Title: text reads "{title}". {description}.'
    elif pattern == "scale-circles":
        items = ", ".join(elems_quoted)
        p = f'Bubble/circle size comparison chart showing: {items}. Title: text reads "{title}". {description}.'
    elif pattern == "gantt":
        items = ", ".join(elems_quoted)
        p = f'Gantt chart or weekly schedule timeline with items: {items}. Title: text reads "{title}". {description}.'
    elif pattern == "illustration":
        items = ", ".join(elem_list)
        p = f'Illustrative scene featuring: {items}. {description}. Friendly manga-inspired illustration style.'
    else:
        items = ", ".join(elems_quoted)
        p = f'Infographic diagram ({pattern} style) with elements: {items}. Title: text reads "{title}". {description}.'

    return f"{p} {STYLE}"


def main():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    pattern = re.compile(
        r'<!-- \[(HEADER_IMAGE|INLINE_IMAGE): '
        r'pattern=([^\|]+) \| '
        r'title=([^\|]+) \| '
        r'elements=([^\|]+) \| '
        r'description=([^\]]+)\] -->'
    )

    tags = list(pattern.finditer(text))
    print(f"画像タグ数: {len(tags)}枚")

    results = []
    for i, m in enumerate(tags, 1):
        tag_type = m.group(1).strip()
        pat = m.group(2).strip()
        title = m.group(3).strip()
        elements = m.group(4).strip()
        description = m.group(5).strip()

        filename = tag_to_filename(i, tag_type, title)
        out_path = IMAGES_DIR / filename

        if out_path.exists():
            print(f"[{i:02d}/{len(tags)}] スキップ（既存）: {filename}")
            results.append((m.group(0), filename, True))
            continue

        prompt = build_prompt(tag_type, pat, title, elements, description)
        print(f"\n[{i:02d}/{len(tags)}] {filename}")

        success = generate_image(str(prompt), str(out_path), 1536, 1024)
        results.append((m.group(0), filename, success))

        if not success:
            print(f"  → 失敗、スキップして続行")

        # API レート制限対策
        if i < len(tags):
            time.sleep(2)

    # manuscript.md を生成（画像タグ→画像リンクに置換）
    new_text = text
    for original_tag, filename, success in results:
        if success:
            # タイトルを抽出
            m = re.search(r'title=([^\|]+)', original_tag)
            alt = m.group(1).strip() if m else filename
            new_tag = f"![{alt}](images/{filename})"
        else:
            new_tag = f"<!-- 画像生成失敗: {filename} -->"
        new_text = new_text.replace(original_tag, new_tag, 1)

    out_md = BASE / "output" / SLUG / "manuscript.md"
    out_md.write_text(new_text, encoding="utf-8")
    print(f"\nmanuscript.md 生成完了: {out_md}")

    success_count = sum(1 for _, _, s in results if s)
    print(f"\n完了: {success_count}/{len(tags)} 枚生成成功")


if __name__ == "__main__":
    main()
