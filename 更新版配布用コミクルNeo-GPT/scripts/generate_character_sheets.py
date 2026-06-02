#!/usr/bin/env python3
"""
キャラクターシート（全身立ち絵）一括生成スクリプト

character_prompts.md から全キャラクターの外見定義を読み取り、
各キャラの全身立ち絵を生成して キャラ参照/<slug>/characters/ に保存する。

主人公の参照画像が既にある場合（キャラ参照/ フォルダに手動配置済み）はスキップし、
自動生成サブキャラのみ生成する。

使用方法:
    python scripts/generate_character_sheets.py --slug my-book
    python scripts/generate_character_sheets.py --slug my-book --main-ref "キャラ参照/主人公名/主人公名.png"
"""
import argparse
import io
import re
import sys
import time
from pathlib import Path

# Windows cp932 対策: stdout/stderrをUTF-8で強制出力
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
from openai_image_gen import load_env, generate_image

load_env()

BASE = Path(__file__).parent.parent

# キャラシート生成用の共通スタイル指示
CHAR_SHEET_STYLE = (
    "Full-body character reference sheet on a plain white background. "
    "Single character standing in a neutral front-facing pose, showing the full outfit from head to toe. "
    "Clean line art, modern anime/manga style, full color, vibrant colors. "
    "No other characters, no background scenery, no text, no speech bubbles. "
    "This is a character design reference sheet for maintaining visual consistency."
)


def parse_character_prompts(md_path: Path) -> list:
    """
    character_prompts.md を解析して [(name, english_name, description), ...] を返す。
    フォーマット: ## キャラ名 (EnglishName) のヘッダ + 続くテキストが外見定義
    """
    text = md_path.read_text(encoding="utf-8")
    characters = []

    # ## で始まるヘッダを分割
    sections = re.split(r'^## ', text, flags=re.MULTILINE)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        lines = section.split("\n", 1)
        header = lines[0].strip()
        description = lines[1].strip() if len(lines) > 1 else ""

        if not description:
            continue

        # ヘッダからキャラ名を抽出: "主人公名 (HeroName) — 主人公" → name="主人公名", en="HeroName"
        # または "ユウキ (Yuuki)" → name="ユウキ", en="Yuuki"
        name_match = re.match(r'([^\(（]+?)[\s]*[\(（]([^\)）]+)[\)）]', header)
        if name_match:
            name = name_match.group(1).strip()
            en_name = name_match.group(2).strip()
        else:
            name = header.split("—")[0].split("-")[0].strip()
            en_name = name

        characters.append((name, en_name, description))

    return characters


def main():
    parser = argparse.ArgumentParser(description="キャラクターシート一括生成")
    parser.add_argument("--slug", required=True, help="出力フォルダ名 (output/<slug>/)")
    parser.add_argument("--prompts", default=None,
                        help="character_prompts.md のパス（デフォルト: output/<slug>/character_prompts.md）")
    parser.add_argument("--main-ref", nargs="*", default=None,
                        help="主人公の既存参照画像パス（これらのキャラはシート生成をスキップ）")
    parser.add_argument("--skip-names", nargs="*", default=None,
                        help="シート生成をスキップするキャラ名（既に参照画像がある場合）")
    args = parser.parse_args()

    out_dir = BASE / "output" / args.slug / "characters"
    out_dir.mkdir(parents=True, exist_ok=True)

    # character_prompts.md の場所
    prompts_path = Path(args.prompts) if args.prompts else (BASE / "output" / args.slug / "character_prompts.md")
    if not prompts_path.exists():
        print(f"ERROR: {prompts_path} が見つかりません", file=sys.stderr)
        sys.exit(1)

    characters = parse_character_prompts(prompts_path)
    print(f"キャラクター {len(characters)} 名を検出:")
    for name, en, desc in characters:
        print(f"  - {name} ({en}): {desc[:50]}...")

    # スキップ対象
    skip_names = set(args.skip_names or [])

    # 既存の主人公参照画像をコピー（シンボリックリンクではなく情報として記録）
    if args.main_ref:
        for ref_path in args.main_ref:
            p = Path(ref_path)
            if p.exists():
                print(f"主人公参照画像（既存）: {p.name}")

    generated = 0
    skipped = 0

    for name, en_name, description in characters:
        # スキップ判定
        if name in skip_names or en_name in skip_names:
            print(f"\n[スキップ] {name} ({en_name}) - skip-names で除外")
            skipped += 1
            continue

        # ファイル名: 英語名をスネークケースに
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', en_name).lower().strip('_')
        filename = f"{safe_name}.png"
        out_path = out_dir / filename

        if out_path.exists():
            print(f"\n[スキップ] {name} ({en_name}) - 既存:{filename}")
            skipped += 1
            continue

        # キャラシート生成プロンプト
        prompt = f"{CHAR_SHEET_STYLE}\n\nCharacter: {description}"

        print(f"\n[生成中] {name} ({en_name}) → {filename}")
        success = generate_image(prompt, str(out_path), 1024, 1536)

        if success:
            generated += 1
            print(f"  OK: {filename}")
        else:
            print(f"  ERROR: {filename} 生成失敗")

        time.sleep(3)

    # 結果表示
    print(f"\n=== キャラシート生成完了 ===")
    print(f"生成: {generated} 枚")
    print(f"スキップ: {skipped} 枚")
    print(f"保存先: {out_dir}")

    # 全参照画像の一覧を出力（後続スクリプトで使用）
    all_refs = sorted(out_dir.glob("*.png"))
    if args.main_ref:
        for ref_path in args.main_ref:
            p = Path(ref_path)
            if p.exists() and p not in all_refs:
                all_refs.insert(0, p)

    print(f"\n全キャラ参照画像 ({len(all_refs)} 枚):")
    for r in all_refs:
        print(f"  {r}")


if __name__ == "__main__":
    main()
