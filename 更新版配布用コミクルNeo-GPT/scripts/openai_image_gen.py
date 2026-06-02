#!/usr/bin/env python3
"""
OpenAI gpt-image-2 画像生成スクリプト
.envからAPIキーとモデルを読み込み、プロンプトから画像を生成する。

使用方法:
    python scripts/openai_image_gen.py --prompt "プロンプト" --output output/image.png
    python scripts/openai_image_gen.py --prompt "プロンプト" --output output/image.png --width 1024 --height 1536
    python scripts/openai_image_gen.py --prompt "プロンプト" --output output/image.png --reference ref1.png ref2.png

gpt-image-2 のサポートサイズ: 1024x1024 / 1536x1024 / 1024x1536 / auto
任意の width/height を渡した場合は、最も近いアスペクト比のサポートサイズで生成し、
Pillowで指定サイズにリサイズして保存する。

--reference を指定すると images.edit() を使い、参照画像からキャラクターの外見を維持する。
"""

import argparse
import base64
import io
import os
import sys
from pathlib import Path

# Windows cp932 対策: stdout/stderrをUTF-8で強制出力
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def load_env(env_path=None):
    if env_path is None:
        env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

load_env()


def install_sdk():
    import subprocess
    print("openai SDK をインストール中...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai", "Pillow", "-q"])


SUPPORTED_SIZES = [
    (1024, 1024),  # square
    (1536, 1024),  # landscape
    (1024, 1536),  # portrait
]


def pick_api_size(width: int, height: int) -> str:
    """要求サイズに最も近いgpt-image-2サポートサイズを選ぶ"""
    target_ratio = width / height
    best = min(SUPPORTED_SIZES, key=lambda s: abs((s[0] / s[1]) - target_ratio))
    return f"{best[0]}x{best[1]}"


def generate_image(prompt: str, output_path: str, width: int = 1536, height: int = 1024,
                    reference_images: list = None) -> bool:
    """
    画像を生成する。

    Args:
        prompt: 画像生成プロンプト
        output_path: 出力ファイルパス
        width: 画像幅
        height: 画像高さ
        reference_images: キャラクター参照画像パスのリスト（指定時はimages.edit()を使用）
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model_name = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2")

    if not api_key or api_key == "your_api_key_here":
        print("ERROR: OPENAI_API_KEY が .env に設定されていません", file=sys.stderr)
        return False

    try:
        from openai import OpenAI
    except ImportError:
        install_sdk()
        from openai import OpenAI

    client = OpenAI(api_key=api_key)
    api_size = pick_api_size(width, height)

    # 参照画像の検証
    ref_paths = []
    if reference_images:
        for rp in reference_images:
            p = Path(rp)
            if p.exists():
                ref_paths.append(p)
            else:
                print(f"WARN: 参照画像が見つかりません: {rp}", file=sys.stderr)

    use_edit = len(ref_paths) > 0
    mode_label = f"edit (参照画像{len(ref_paths)}枚)" if use_edit else "generate"

    print(f"モデル: {model_name} ({mode_label})")
    print(f"出力先: {output_path}")
    print(f"要求サイズ: {width}x{height}  → API送信サイズ: {api_size}")
    print(f"プロンプト長: {len(prompt)}文字")
    if ref_paths:
        for rp in ref_paths:
            print(f"参照画像: {rp.name}")

    try:
        if use_edit:
            # images.edit() でキャラクター参照画像を渡す
            image_files = [open(str(rp), "rb") for rp in ref_paths]
            try:
                response = client.images.edit(
                    model=model_name,
                    image=image_files,
                    prompt=prompt,
                    size=api_size,
                    n=1,
                )
            finally:
                for f in image_files:
                    f.close()
        else:
            # 従来の images.generate()
            response = client.images.generate(
                model=model_name,
                prompt=prompt,
                size=api_size,
                n=1,
            )
    except Exception as e:
        print(f"ERROR: API呼び出し失敗: {e}", file=sys.stderr)
        return False

    if not response.data:
        print("ERROR: レスポンスに画像データが含まれていません", file=sys.stderr)
        return False

    item = response.data[0]
    image_bytes = None
    if getattr(item, "b64_json", None):
        image_bytes = base64.b64decode(item.b64_json)
    elif getattr(item, "url", None):
        import urllib.request
        with urllib.request.urlopen(item.url) as r:
            image_bytes = r.read()

    if image_bytes is None:
        print("ERROR: 画像データを取得できませんでした", file=sys.stderr)
        return False

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    api_w, api_h = map(int, api_size.split("x"))
    if (api_w, api_h) != (width, height):
        try:
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(image_bytes)).convert("RGB")
            img = img.resize((width, height), Image.LANCZOS)
            img.save(out_path, format="PNG")
            print(f"OK: {out_path} ({out_path.stat().st_size:,} bytes, リサイズ {api_size}→{width}x{height})")
            return True
        except ImportError:
            print("WARN: Pillow未インストール。APIサイズのまま保存します。", file=sys.stderr)

    with open(out_path, "wb") as f:
        f.write(image_bytes)
    print(f"OK: {out_path} ({len(image_bytes):,} bytes)")
    return True


def main():
    parser = argparse.ArgumentParser(description="OpenAI gpt-image-2で画像生成")
    parser.add_argument("--prompt", required=True, help="画像生成プロンプト")
    parser.add_argument("--output", required=True, help="出力ファイルパス (.png)")
    parser.add_argument("--width", type=int, default=1536, help="画像幅 (デフォルト: 1536)")
    parser.add_argument("--height", type=int, default=1024, help="画像高さ (デフォルト: 1024)")
    parser.add_argument("--reference", nargs="+", default=None,
                        help="キャラクター参照画像パス（複数指定可）。指定時はimages.edit()を使用")
    args = parser.parse_args()

    success = generate_image(args.prompt, args.output, args.width, args.height,
                             reference_images=args.reference)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
