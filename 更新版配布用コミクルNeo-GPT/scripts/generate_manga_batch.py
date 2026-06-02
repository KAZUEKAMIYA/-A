#!/usr/bin/env python3
"""
漫画100ページをOpenAI gpt-image-2で一括生成するスクリプト
page_prompts_1_50.md と page_prompts_51_100.md からプロンプトを読み取り、
panels/ に page_01.png ~ page_100.png を生成する。

--char-ref でキャラクター参照画像を指定すると、images.edit() を使って
キャラクターの外見を一貫して維持する。
"""
import argparse
import io
import os
import re
import sys
import time
from pathlib import Path
from PIL import Image

# Windows cp932 対策: stdout/stderrをUTF-8で強制出力
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
from openai_image_gen import load_env, generate_image

load_env()

BASE = Path(__file__).parent.parent


def check_page_ok(path: str) -> bool:
    """生成直後の構造チェック: サイズ ≥ 50KB かつ 寸法 = 1024×1536"""
    if not os.path.exists(path):
        return False
    if os.path.getsize(path) < 50 * 1024:
        print(f"  WARN: ファイルサイズ不足 ({os.path.getsize(path)//1024}KB < 50KB)")
        return False
    try:
        with Image.open(path) as img:
            if img.size != (1024, 1536):
                print(f"  WARN: 寸法異常 {img.size} (期待値: 1024x1536)")
                return False
    except Exception as e:
        print(f"  WARN: 画像読み込みエラー: {e}")
        return False
    return True


def find_char_refs(char_ref_dir: str = None) -> list:
    """キャラ参照フォルダから画像ファイルを収集する"""
    if not char_ref_dir:
        return []
    p = Path(char_ref_dir)
    if not p.exists():
        print(f"WARN: キャラ参照フォルダが見つかりません: {char_ref_dir}")
        return []
    refs = sorted(p.glob("*.png")) + sorted(p.glob("*.jpg")) + sorted(p.glob("*.jpeg"))
    if refs:
        print(f"キャラ参照画像 {len(refs)} 枚を検出:")
        for r in refs:
            print(f"  - {r.name}")
    return [str(r) for r in refs]


def extract_pages(text):
    """## Page XX -- title パターンで分割"""
    pages = []
    pattern = re.compile(
        r"## Page (\d+)[^\n]*\n\n(.*?)(?=\n## Page \d+|\Z)", re.DOTALL
    )
    for m in pattern.finditer(text):
        num = int(m.group(1))
        prompt = m.group(2).strip()
        pages.append((num, prompt))
    return sorted(pages, key=lambda x: x[0])


def main():
    parser = argparse.ArgumentParser(description="漫画ページ一括生成")
    parser.add_argument("--slug", default="saru-marketing-daizen",
                        help="出力フォルダ名 (output/<slug>/)")
    parser.add_argument("--char-ref", default=None,
                        help="キャラクター参照画像フォルダパス（フォルダ内の全画像を参照）")
    parser.add_argument("--char-ref-files", nargs="+", default=None,
                        help="キャラクター参照画像パス（個別ファイル指定、複数可）")
    args = parser.parse_args()

    OUT_DIR = BASE / "output" / args.slug / "panels"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    PROMPT_FILES = [
        BASE / "output" / args.slug / "page_prompts_1_50.md",
        BASE / "output" / args.slug / "page_prompts_51_100.md",
    ]

    # キャラ参照画像の収集
    ref_images = []
    if args.char_ref:
        ref_images = find_char_refs(args.char_ref)
    if args.char_ref_files:
        ref_images.extend(args.char_ref_files)

    all_pages = []
    for pf in PROMPT_FILES:
        if pf.exists():
            text = pf.read_text(encoding="utf-8")
            all_pages.extend(extract_pages(text))
        else:
            print(f"WARN: {pf} not found, skipping")

    total = len(all_pages)
    print(f"漫画ページ {total} 件を検出しました")
    if ref_images:
        print(f"キャラ参照画像: {len(ref_images)} 枚 → images.edit() モードで生成")

    generated = 0
    failed = 0
    skipped_pages = []  # スキップしたページ番号を記録

    for i, (num, prompt) in enumerate(all_pages):
        fname = f"page_{num:02d}.png"
        out_path = OUT_DIR / fname

        if out_path.exists():
            print(f"[{i+1}/{total}] スキップ（既存）: {fname}")
            generated += 1
            continue

        print(f"\n[{i+1}/{total}] 生成中: {fname}")

        # 即時チェック付き生成（最大3回）
        ok = False
        for attempt in range(1, 4):
            success = generate_image(prompt, str(out_path), 1024, 1536,
                                     reference_images=ref_images if ref_images else None)
            if success and check_page_ok(str(out_path)):
                ok = True
                break
            if attempt < 3:
                print(f"  RETRY ({attempt}/3): 構造NG → 再生成")
                time.sleep(3)
            else:
                print(f"  ERROR: 3回試行後もNG → スキップ: {fname}")
                skipped_pages.append(num)
                # 壊れたファイルを削除（次回実行時に「既存」と誤判定されないよう）
                if os.path.exists(str(out_path)):
                    os.remove(str(out_path))
                    print(f"  CLEANUP: 破損ファイルを削除しました: {fname}")

        if ok:
            generated += 1
        else:
            failed += 1

        # API rate limit対策
        if i < len(all_pages) - 1:
            time.sleep(3)

    # manga_compiled.md 生成
    section_map = {
        1: "## プロローグ\n",
        13: "## 第1章 コンテンツビジネスの始め方\n",
        28: "## 第2章 Instagram集客の完全攻略\n",
        43: "## 第3章 セールスの極意\n",
        58: "## 第4章 ファネル構築と完全自動化\n",
        73: "## 第5章 事業拡大とスケール戦略\n",
        88: "## エピローグ\n",
    }

    lines = ["# 漫画\n\n"]
    for num, _ in all_pages:
        if num in section_map:
            lines.append(f"\n{section_map[num]}\n")
        lines.append(f"![Page {num:02d}](panels/page_{num:02d}.png)\n\n")

    compiled = BASE / "output" / "saru-marketing-daizen" / "manga_compiled.md"
    compiled.write_text("".join(lines), encoding="utf-8")
    print(f"\nmanga_compiled.md 生成完了: {compiled}")
    print(f"\n=== 完了 ===")
    print(f"成功: {generated}/{total} 枚")
    print(f"失敗: {failed}/{total} 枚")

    # スキップページの報告
    if skipped_pages:
        print(f"\n⚠️ 以下のページは3回試行してもNG判定のためスキップしました:")
        for p in skipped_pages:
            print(f"  - Page {p:02d}: 構造チェックNG（サイズ不足 or 寸法異常）")
        print("個別に再生成が必要な場合はページ番号を指定してください。")
    else:
        print("\n✅ 全ページ構造チェック通過。")


if __name__ == "__main__":
    main()
