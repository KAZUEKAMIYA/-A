#!/usr/bin/env python3
"""
claudecode-nani 全挿絵一括生成スクリプト
"""
import io
import re
import os
import sys
import subprocess
import time
from pathlib import Path

# Windows cp932 対策: stdout/stderrをUTF-8で強制出力
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent.parent
MANUSCRIPT = BASE_DIR / "output/claudecode-nani/manuscript_raw.md"
OUT_DIR    = BASE_DIR / "output/claudecode-nani/images"
SCRIPT     = BASE_DIR / "scripts/openai_image_gen.py"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STYLE = (
    "Clean flat design infographic, soft pastel colors, rounded shapes, "
    "modern Japanese ebook illustration aesthetic. "
    "Color palette: primary #4A90D9 (blue), accent #F5A623 (orange), sub #7ED321 (green). "
    "Background: white. Landscape orientation. "
    "All text in the image MUST be in Japanese (日本語). "
)

def parse_tag(tag_str):
    """<!-- [TYPE: key=val | key=val] --> を辞書に変換"""
    m = re.match(r'<!--\s*\[(\w+):\s*(.*?)\]\s*-->', tag_str, re.DOTALL)
    if not m:
        return None, None
    tag_type = m.group(1)
    raw = m.group(2)
    params = {}
    for part in raw.split('|'):
        part = part.strip()
        if '=' in part:
            k, _, v = part.partition('=')
            params[k.strip()] = v.strip()
    return tag_type, params

def build_prompt(tag_type, params):
    title    = params.get('title', '')
    elements = params.get('elements', '')
    desc     = params.get('description', '')
    pattern  = params.get('pattern', 'illustration')
    elems    = [e.strip() for e in elements.split(',') if e.strip()]

    if tag_type == 'HEADER_IMAGE':
        body = (
            f'Chapter header illustration for Japanese ebook. '
            f'Large title text reads "{title}" in bold Japanese. '
            f'Visual elements: {", ".join(elems)}. {desc}. '
            f'Style: flat design, chapter header, landscape (3:2 ratio, 1200x800px).'
        )
    elif pattern == 'flow-horizontal':
        arrows = ' → '.join([f'text reads "{e}"' for e in elems])
        body = f'Horizontal flow diagram with arrows: {arrows}. Title text reads "{title}". {desc}.'
    elif pattern == 'flow-vertical':
        steps = ', '.join([f'step text reads "{e}"' for e in elems])
        body = f'Vertical flow diagram with downward arrows: {steps}. Title text reads "{title}". {desc}.'
    elif pattern == 'before-after':
        left  = elems[0] if len(elems) > 0 else ''
        right = elems[1] if len(elems) > 1 else ''
        body  = f'Side by side comparison. Left panel label "Before" with text reads "{left}". Right panel label "After" with text reads "{right}". Title text reads "{title}". {desc}.'
    elif pattern == 'stairs':
        steps = ', '.join([f'stair {i+1} text reads "{e}"' for i, e in enumerate(elems)])
        body  = f'Step-by-step staircase diagram ascending left to right: {steps}. Title text reads "{title}". {desc}.'
    elif pattern == 'radial':
        center = title
        nodes  = ', '.join([f'node text reads "{e}"' for e in elems])
        body   = f'Radial diagram. Central circle text reads "{center}". Surrounding nodes: {nodes}. {desc}.'
    elif pattern == 'comparison-table':
        cards = ', '.join([f'card text reads "{e}"' for e in elems])
        body  = f'Card comparison layout: {cards}. Title text reads "{title}". {desc}.'
    elif pattern == 'cycle':
        nodes = ', '.join([f'node text reads "{e}"' for e in elems])
        body  = f'Circular cycle diagram with clockwise arrows: {nodes}. Title text reads "{title}". {desc}.'
    elif pattern == 'pyramid':
        layers = ', '.join([f'layer text reads "{e}"' for e in elems])
        body   = f'Triangle pyramid diagram: {layers} from top to bottom. Title text reads "{title}". {desc}.'
    elif pattern == 'list-vertical':
        items = ', '.join([f'item text reads "{e}"' for e in elems])
        body  = f'Vertical checklist with checkboxes: {items}. Title text reads "{title}". {desc}.'
    elif pattern == 'list-dense':
        items = ', '.join([f'item text reads "{e}"' for e in elems])
        body  = f'Dense vertical list: {items}. Title text reads "{title}". {desc}.'
    elif pattern == 'list-horizontal':
        items = ', '.join([f'item text reads "{e}"' for e in elems])
        body  = f'Horizontal list of cards: {items}. Title text reads "{title}". {desc}.'
    elif pattern == 'tree':
        branch_parts = ", ".join(['text reads "' + e + '"' for e in elems])
        body = f'Tree/hierarchy diagram. Root text reads "{title}". Branches: {branch_parts}. {desc}.'
    elif pattern == 'layers':
        items = ', '.join([f'layer text reads "{e}"' for e in elems])
        body  = f'Layered stack diagram from top to bottom: {items}. Title text reads "{title}". {desc}.'
    elif pattern == 'network':
        nodes = ', '.join([f'node text reads "{e}"' for e in elems])
        body  = f'Network diagram with connecting lines: {nodes}. Title text reads "{title}". {desc}.'
    elif pattern == 'matrix':
        items = ', '.join([f'cell text reads "{e}"' for e in elems])
        body  = f'2x2 matrix diagram: {items}. Title text reads "{title}". {desc}.'
    elif pattern == 'triangle':
        vertex_parts = ", ".join(['vertex text reads "' + e + '"' for e in elems])
        body = f'Triangle diagram with 3 vertices: {vertex_parts}. Title text reads "{title}". {desc}.'
    elif pattern == 'scale-circles':
        circles = ', '.join([f'circle text reads "{e}"' for e in elems])
        body    = f'Scale of circles from small to large: {circles}. Title text reads "{title}". {desc}.'
    else:
        items = ', '.join([f'text reads "{e}"' for e in elems])
        body  = f'Infographic diagram. {items}. Title text reads "{title}". {desc}.'

    return STYLE + body

def main():
    text = MANUSCRIPT.read_text(encoding='utf-8')
    tag_pat = re.compile(r'<!--\s*\[(HEADER_IMAGE|INLINE_IMAGE):.*?\]\s*-->', re.DOTALL)
    tags = list(tag_pat.finditer(text))
    total = len(tags)
    print(f"画像タグ {total} 件を検出しました")

    prompts_log = []
    mapping = {}  # tag_str -> filename

    # 章ごとのカウンタ
    ch = 0
    img_counter = {}

    for i, m in enumerate(tags):
        tag_str   = m.group(0)
        tag_type, params = parse_tag(tag_str)
        if tag_type is None:
            continue
        title   = params.get('title', f'image_{i}')
        pattern = params.get('pattern', 'illustration')

        # ファイル名生成
        if tag_type == 'HEADER_IMAGE':
            ch += 1
            img_counter[ch] = 0
            fname = f"ch{ch:02d}_header.png"
        else:
            img_counter.setdefault(ch, 0)
            img_counter[ch] += 1
            fname = f"ch{ch:02d}_img{img_counter[ch]:02d}.png"

        out_path = OUT_DIR / fname
        mapping[tag_str] = (fname, title)

        prompt = build_prompt(tag_type, params)
        prompts_log.append(f"## {fname}\n**{title}**\n\n{prompt}\n")

        if out_path.exists():
            print(f"[{i+1}/{total}] スキップ（既存）: {fname}")
            continue

        print(f"\n[{i+1}/{total}] 生成中: {fname}")
        print(f"  タイトル: {title}")

        result = subprocess.run(
            [sys.executable, str(SCRIPT),
             "--prompt", prompt,
             "--output", str(out_path),
             "--width", "1536", "--height", "1024"],
            capture_output=False,
            text=True
        )
        if result.returncode != 0:
            print(f"  ERROR: 生成失敗 → {fname}")
        else:
            print(f"  OK: {fname} 生成完了")

        # レート制限対策
        time.sleep(3)

    # プロンプトログ保存
    log_path = BASE_DIR / "output/claudecode-nani/image_prompts.md"
    log_path.write_text("# 画像プロンプトログ\n\n" + "\n".join(prompts_log), encoding='utf-8')
    print(f"\nプロンプトログ保存: {log_path}")

    # manuscript.md 生成（画像タグ→リンクに置換）
    manuscript_out = text
    for tag_str, (fname, title) in mapping.items():
        manuscript_out = manuscript_out.replace(tag_str, f"![{title}](images/{fname})")

    out_md = BASE_DIR / "output/claudecode-nani/manuscript.md"
    out_md.write_text(manuscript_out, encoding='utf-8')
    print(f"manuscript.md 生成完了: {out_md}")

    # 生成結果サマリ
    generated = sum(1 for _, (fname, _) in mapping.items() if (OUT_DIR / fname).exists())
    print(f"\n=== 完了 ===")
    print(f"生成画像: {generated}/{total} 枚")

if __name__ == "__main__":
    main()
