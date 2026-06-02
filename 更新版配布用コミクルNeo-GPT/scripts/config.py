"""
電子書籍+漫画 完全自動生成システム - 設定ファイル

パス・画像サイズ・原稿設定等の共通設定。
"""

import os
from pathlib import Path

# === パス設定 ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# === 画像サイズ（OpenAI gpt-image-2 サポートサイズ） ===
ILLUSTRATION_SIZE_LANDSCAPE = (1536, 1024)  # 挿絵: 横長デフォルト
ILLUSTRATION_SIZE_SQUARE    = (1024, 1024)  # 挿絵: 正方形
ILLUSTRATION_SIZE_PORTRAIT  = (1024, 1536)  # 挿絵: 縦長
MANGA_SIZE                  = (1024, 1536)  # 漫画: 縦長固定
CHARACTER_SHEET_SIZE        = (1024, 1536)  # キャラシート: 縦長

# 後方互換用エイリアス
ILLUSTRATION_SIZE = ILLUSTRATION_SIZE_LANDSCAPE

# === 原稿設定 ===
TARGET_WORD_COUNT = 25000
CHAPTER_COUNT = 5
WORDS_PER_CHAPTER = (4000, 5000)
INTRO_OUTRO_WORDS = (1200, 1500)


def get_output_dir(slug: str) -> Path:
    """テーマslugに対応する出力ディレクトリを返す。存在しなければ作成する。"""
    d = OUTPUT_DIR / slug
    d.mkdir(parents=True, exist_ok=True)
    return d
