#!/usr/bin/env python3
"""
claudecode-nani 漫画ページ一括生成スクリプト
--char-ref でキャラクター参照画像フォルダを指定可能。
"""
import argparse
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

BASE_DIR  = Path(__file__).parent.parent
PROMPTS   = BASE_DIR / "output/claudecode-nani/page_prompts.md"
OUT_DIR   = BASE_DIR / "output/claudecode-nani/panels"
SCRIPT    = BASE_DIR / "scripts/openai_image_gen.py"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def extract_pages(text):
    """## Page XX — title\n\n{prompt} パターンで分割"""
    pages = []
    pattern = re.compile(r'## (Page \d+)[^\n]*\n\n(.*?)(?=\n---|\Z)', re.DOTALL)
    for m in pattern.finditer(text):
        page_label = m.group(1).strip()   # "Page 01"
        prompt     = m.group(2).strip()
        num = re.search(r'\d+', page_label)
        if num:
            pages.append((int(num.group()), page_label, prompt))
    return sorted(pages, key=lambda x: x[0])

def collect_char_refs(char_ref_dir: str = None) -> list:
    """キャラ参照フォルダから画像パスを収集"""
    if not char_ref_dir:
        return []
    p = Path(char_ref_dir)
    if not p.exists():
        return []
    refs = sorted(p.glob("*.png")) + sorted(p.glob("*.jpg")) + sorted(p.glob("*.jpeg"))
    return [str(r) for r in refs]


def main():
    parser = argparse.ArgumentParser(description="漫画ページ一括生成")
    parser.add_argument("--char-ref", default=None,
                        help="キャラクター参照画像フォルダパス")
    args = parser.parse_args()

    ref_images = collect_char_refs(args.char_ref)
    if ref_images:
        print(f"キャラ参照画像 {len(ref_images)} 枚を使用 → images.edit() モード")

    text  = PROMPTS.read_text(encoding='utf-8')
    pages = extract_pages(text)
    total = len(pages)
    print(f"漫画ページ {total} 件を検出しました")

    for i, (num, label, prompt) in enumerate(pages):
        fname    = f"page_{num:02d}.png"
        out_path = OUT_DIR / fname

        if out_path.exists():
            print(f"[{i+1}/{total}] スキップ（既存）: {fname}")
            continue

        print(f"\n[{i+1}/{total}] 生成中: {fname} ({label})")

        cmd = [sys.executable, str(SCRIPT),
               "--prompt", prompt,
               "--output", str(out_path),
               "--width",  "1024",
               "--height", "1536"]
        if ref_images:
            cmd.extend(["--reference"] + ref_images)

        result = subprocess.run(cmd, capture_output=False, text=True)
        if result.returncode != 0:
            print(f"  ERROR: 生成失敗 → {fname}")
        else:
            print(f"  OK: {fname}")

        time.sleep(3)

    # manga_compiled.md 生成
    lines = [
        "# 漫画: ClaudeCodeって何？\n",
        "## 第1章 出会い\n",
    ]
    chapter_map = {
        1:  "## 第1章 出会い\n",
        5:  "## 第2章 共同開発\n",
        9:  "## 第3章 壁とブレイクスルー\n",
        13: "## 第4章 成長と可能性\n",
        17: "## 第5章 未来へ\n",
    }
    lines = ["# 漫画: ClaudeCodeって何？\n\n"]
    for num, label, _ in pages:
        if num in chapter_map:
            lines.append(f"\n{chapter_map[num]}\n")
        lines.append(f"![{label}](panels/page_{num:02d}.png)\n\n")

    compiled = BASE_DIR / "output/claudecode-nani/manga_compiled.md"
    compiled.write_text("".join(lines), encoding='utf-8')
    print(f"\nmanga_compiled.md 生成完了: {compiled}")

    generated = sum(1 for n, _, _ in pages if (OUT_DIR / f"page_{n:02d}.png").exists())
    print(f"\n=== 完了 ===")
    print(f"生成ページ: {generated}/{total} 枚")

if __name__ == "__main__":
    main()
