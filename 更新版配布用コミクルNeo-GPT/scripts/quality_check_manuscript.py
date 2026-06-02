#!/usr/bin/env python3
"""Phase 4f: 原稿品質チェック（AIクリシェ自動修正）

機械的に処理できる修正を正規表現で実行し、
矢印（→←）を含む行番号をリストアップしてClaude側でEdit処理できるよう出力する。

使い方:
    python scripts/quality_check_manuscript.py <slug>
"""
import re
import sys
from pathlib import Path

def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else input("slug を入力: ")
    path = Path("output") / slug / "manuscript_raw.md"

    if not path.exists():
        print(f"[ERROR] ファイルが見つかりません: {path}")
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    fixes = {"ーー": 0, "note": 0, "bracket": 0, "newline": 0}
    result = []

    for i, line in enumerate(lines):
        original = line

        # 除外判定（見出し・画像タグ・\newpage）
        stripped = line.strip()
        is_excluded = (
            stripped.startswith("#") or
            stripped.startswith("<!--") or
            stripped.startswith("!") or
            stripped == r"\newpage"
        )

        if not is_excluded:
            # 1. ーー / ーーー / —— / ―― （複数連続の長音・横棒）→ … に置換
            line, n = re.subn(r'[ーｰ\-－—―]{2,}', '…', line)
            fixes["ーー"] += n

            # 2. ※（注釈マーク）→ 削除
            line, n = re.subn(r'※', '', line)
            fixes["note"] += n

            # 3. **「...」** → 「**...**」 / **（...）** → （**...**）（太字マーカーを括弧の内側に移動）
            line, n = re.subn(r'\*\*「(.*?)」\*\*', r'「**\1**」', line)
            fixes["bracket"] += n
            line, n = re.subn(r'\*\*（(.*?)）\*\*', r'（**\1**）', line)
            fixes["bracket"] += n

            # 3b. **...。...** の句点を全て bold の外に出す（split_by_kuten で ** が分断されるのを防ぐ）
            # 例: **文A。文B。** → **文A**。**文B**。
            def bold_kuten_split(m):
                content = m.group(1)
                parts = re.split(r'(。)', content)
                out, buf = '', ''
                for p in parts:
                    if p == '。':
                        out += '**' + buf + '**。'
                        buf = ''
                    else:
                        buf += p
                if buf:
                    out += '**' + buf + '**'
                return out
            new_line, n = re.subn(r'\*\*([^*]+)\*\*', bold_kuten_split, line)
            if n and '。' in line:
                line = new_line
                fixes["bracket"] += n

        result.append(line)

        # 4. 句点（。）直後に空行がない → 空行を1行追加
        if not is_excluded:
            if (line.rstrip().endswith('。') and
                    i + 1 < len(lines) and lines[i + 1].strip() != ''):
                result.append('\n')
                fixes["newline"] += 1

    # 上書き保存
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(result)

    # 矢印を含む行をリストアップ（Claude側でEdit処理）
    arrow_lines = [
        (i + 1, line.rstrip())
        for i, line in enumerate(result)
        if re.search(r'[→←]', line) and not line.strip().startswith('#')
    ]

    # 報告
    total = sum(fixes.values())
    if total == 0 and not arrow_lines:
        print("[Phase 4f] 原稿品質チェック完了: 修正なし")
    else:
        print(
            f"[Phase 4f] 原稿品質チェック完了: "
            f"ーー×{fixes['ーー']}件 / "
            f"※×{fixes['note']}件 / "
            f"括弧×{fixes['bracket']}件 / "
            f"句点空行×{fixes['newline']}件 修正"
        )

    if arrow_lines:
        print(f"\n=== 矢印変換が必要な行（→×{len(arrow_lines)}件・Claude側でEdit処理） ===")
        for lineno, content in arrow_lines:
            print(f"  Line {lineno}: {content}")
    else:
        print("矢印（→←）: 0件")

if __name__ == "__main__":
    main()
