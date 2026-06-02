# 電子書籍+漫画 完全自動生成システム（GPT版）

テーマを入力するだけで、**リサーチ → 原稿25,000字 → 挿絵約30枚 → 漫画20ページ → 最終Word(DOCX)** を全自動で一気に生成するシステムです。

画像生成は **OpenAI gpt-image-2 API** を使用します。Chromeブラウザや外部サービスへのログインは不要です。

---

## 生成物の仕様

| 項目 | 内容 |
|------|------|
| 原稿 | 約25,000字（はじめに + 5章 + おわりに） |
| 挿絵 | 約28〜36枚（章ヘッダー + 本文中図解）<br>横長 1536x1024px / 正方形 1024x1024px / 縦長 1024x1536px から場面に応じて選択 |
| 漫画 | 20ページ（各章4ページ）**1024x1536px 縦長固定** |
| 最終出力 | `final_book.docx`（原稿+挿絵+漫画を統合したWord） |

---

## 必要な環境

### 1. Claude Code（必須）

Anthropicの公式CLI。このシステムの実行エンジンです。

```bash
# インストール（Node.js 18以上が必要）
npm install -g @anthropic-ai/claude-code
```

**Claude Proプラン以上**が必要です（APIトークンを大量に消費します）。

### 2. OpenAI API キー（必須） ★ 最重要

画像生成に使用します。Chromeやブラウザ操作は一切不要です。

📘 **詳しい取得手順は同梱の [`OpenAI_APIキー取得マニュアル.md`](OpenAI_APIキー取得マニュアル.md) を参照してください**（アカウント作成からキー発行・組織認証まで5〜10分で完了）。

#### ざっくり手順

1. [OpenAI Platform](https://platform.openai.com/api-keys) にアクセス
2. 「Create new secret key」をクリック
3. 発行されたキー（`sk-...`）をコピー
4. 同梱の `.env` ファイルの `OPENAI_API_KEY=` の右側に貼り付け

> ⚠ `gpt-image-2` を利用するには、OpenAI Platform 上での **Organization Verification（組織認証）** が必要な場合があります。エラーが出た場合は Settings → Organization → Verifications で認証を完了してください。

#### `.env` ファイルに設定

このフォルダ（`配布用コミクルNeo-GPT/`）直下に `.env` ファイルを作成して以下を記述：

```
OPENAI_API_KEY=sk-...（取得したキー）
OPENAI_IMAGE_MODEL=gpt-image-2
```

#### 動作確認

```bash
# APIキーが正しく設定されているか確認
python -c "
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('.env'))
print('KEY:', os.getenv('OPENAI_API_KEY', '未設定')[:20] + '...')
"
```

### 3. Pandoc（必須）

Markdown → DOCX変換に使用します。

```bash
# Windows（winget）
winget install pandoc

# Mac（Homebrew）
brew install pandoc

# 確認
pandoc --version
```

### 4. Python パッケージ（必須）

```bash
pip install python-docx Pillow openai python-dotenv
```

---

## セットアップ手順（まとめ）

### Step 1: 事前準備（初回のみ）

```
1. Node.js 18以上をインストール
2. Claude Codeをインストール: npm install -g @anthropic-ai/claude-code
3. Pandocをインストール: winget install pandoc（Mac: brew install pandoc）
4. Pythonパッケージをインストール: pip install python-docx Pillow openai python-dotenv
5. OpenAI APIキーを取得して .env ファイルに設定（上記参照）
```

### Step 2: 毎回の起動手順

```
1. ターミナルを開いてこのフォルダに移動：
   cd "配置した場所/配布用コミクルNeo-GPT"
2. Claude Codeを起動：
   claude
```

Chrome・ブラウザ・外部サービスへのログインは不要です。

### Step 3: テーマを入力して実行

Claude Codeのプロンプトで以下のように入力：

```
「AIを使った副業の始め方」のテーマで電子書籍と漫画を自動生成してください
```

これだけでPhase 0〜8が自動実行されます。

---

## 実行フロー（全自動）

```
Phase 0: 初回セットアップ（★ ここだけユーザー操作）
   │  テーマ・参考資料の入力
   │  OpenAI APIキー確認（.envを自動読み込み）
   ▼
Phase 1: 参考資料の受け取り → 自動
   ▼
Phase 2: 深層リサーチ（YouTube/note/SNS/競合/読者の声）→ 自動
   ▼
Phase 3: 構成設計（目次 + カラーパレット）→ 自動
   ▼
Phase 4: 原稿執筆（25,000字 + 画像タグ）→ 自動
   ▼
Phase 5: 挿絵プロンプト生成 → 自動
   ▼
Phase 5b: 挿絵画像生成（OpenAI gpt-image-2 API で1枚ずつ生成・保存）→ 自動
   ▼
Phase 6: 中間DOCX変換（Pandoc + 後処理）→ 自動
   ▼
Phase 7: 漫画化（ストーリー → キャラ設定 → ページ別プロンプト → OpenAI gpt-image-2 で生成）→ 自動
   ▼
Phase 8: 最終DOCX統合 → final_book.docx 完成！
```

### Phase 0 で行うこと

#### Claude Code起動前にやること（初回のみ）

1. `.env` ファイルに `OPENAI_API_KEY` を設定する

#### Claude Code起動後

2. テーマを入力する（例：「AIを使った副業の始め方」）
3. カラーモードを選択（フルカラー / 白黒。デフォルト: フルカラー）
4. コマ割りテンプレートフォルダを指定（任意）
5. 漫画の配置位置を選択（デフォルト: 章末）
6. 各章の漫画ページ数を指定（デフォルト: 3〜5ページ）

**上記を済ませれば、以降は一切の操作不要で全自動完走します。**

> **途中で止まった場合**: Claude Codeのチャット欄に「続けて」と入力してEnterを押してください。

---

## 出力ファイル構成

実行後、`output/{テーマslug}/` に以下が生成されます：

```
output/{slug}/
├── research.md                        # リサーチ結果
├── manuscript_raw.md                  # 原稿（画像タグ付き）
├── manuscript.md                      # 原稿（画像参照付き）
├── manuscript.docx                    # 中間Word
├── image_prompts.md                   # 挿絵プロンプト集
├── images/                            # 挿絵画像（28〜36枚）
├── story_structure.md                 # 漫画ストーリー構成
├── character_prompts.md               # キャラクター設定
├── page_prompts.md                    # 漫画ページ別プロンプト
├── characters/                        # キャラクターシート画像
├── panels/                            # 漫画ページ画像（20枚・1024x1536縦長）
├── manga_compiled.md                  # 統合Markdown
└── final_book.docx                    # ★ 最終成果物
```

---

## 画像サイズ仕様

| 用途 | サイズ | 向き |
|------|--------|------|
| 章ヘッダー、flow-horizontal、before-after、comparison-table 等 | 1536x1024 | 横長 |
| radial、pyramid、tree、illustration 等（要素数中程度） | 1024x1024 | 正方形 |
| layers、list-vertical、flow-vertical 等（要素数多） | 1024x1536 | 縦長 |
| **漫画ページ（全ページ）** | **1024x1536 固定** | **必ず縦長** |

`scripts/openai_image_gen.py` は任意の width/height を受け取り、最も近いサポートサイズで生成 → Pillow で指定サイズにリサイズします。

---

## サンプル出力

`sample/` フォルダに「AI×ゲームで収益を上げる方法」で実行した際の中間生成物を収録しています。

| ファイル | 内容 |
|---------|------|
| `research.md` | リサーチ結果 |
| `image_prompts.md` | 挿絵プロンプト（28枚分） |
| `page_prompts.md` | 漫画プロンプト（20ページ分） |
| `story_structure.md` | 漫画ストーリー構成 |
| `character_prompts.md` | キャラクター設定 |

---

## トラブルシューティング

### OpenAI API 関連

| 問題 | 対処法 |
|------|--------|
| `OPENAI_API_KEY が設定されていません` | `.env` ファイルに `OPENAI_API_KEY=sk-...` を記述したか確認 |
| `403` / 組織認証エラー | OpenAI Platform → Settings → Organization → Verifications で組織認証を完了 |
| `モデルが見つかりません（404）` | APIキーの権限と `OPENAI_IMAGE_MODEL=gpt-image-2` の指定を確認 |
| 画像データが返されない | プロンプトを短縮・シンプル化して再試行。「続けて」と入力で再実行 |
| `openai not installed` | `pip install openai` を実行 |
| APIキーの確認方法 | `echo $OPENAI_API_KEY`（Mac/Linux）または `echo %OPENAI_API_KEY%`（Windows） |

### 画像生成関連

| 問題 | 対処法 |
|------|--------|
| 画像が生成されない | OpenAI APIの利用制限（レート制限）の可能性。しばらく待ってから「続けて」 |
| 漫画のキャラが毎ページ違う顔になる | gpt-image-2 はテキスト→画像のため、CSVプロンプト内のキャラ外見記述を詳細化することで改善（髪・服・体型・年齢を毎ページ同一文言で書く） |
| 画像のサイズが指定と異なる | gpt-image-2 のサポートサイズは 1024x1024 / 1536x1024 / 1024x1536 のみ。任意サイズは自動リサイズされます |
| 漫画が縦長にならない | `generate_manga.py` 内の `SIZE = "1024x1536"` を確認 |

### 実行中に止まった場合

Claude Codeのチャット欄に **「続けて」** と入力してEnterを押してください。

#### 止まる主な原因と対策

| 原因 | 症状 | 対策 |
|------|------|------|
| OpenAI APIのレート制限 | 画像生成中に応答が止まる | 「続けて」と入力。制限が解除されれば再開 |
| コンテキストウィンドウの圧迫 | 長時間動いた後に途切れる | 「続けて」で再開。改善しない場合はClaude Codeを再起動して「途中から再開して」 |
| Claude Proの使用制限 | 「レート制限に達しました」等のメッセージ | しばらく待ってから「続けて」と入力 |

### その他

| 問題 | 対処法 |
|------|--------|
| Pandocが見つからない | `pandoc --version` で確認。なければ `winget install pandoc`（Win）/ `brew install pandoc`（Mac） |
| python-docxがない | `pip install python-docx Pillow` を実行 |
| `.env` ファイルが読み込まれない | Claude Codeをこのフォルダ（`.env` があるフォルダ）から起動しているか確認 |

---

## フォルダ構成

```
配布用コミクルNeo-GPT/
├── README.md                          # ← このファイル
├── .env                               # OpenAI APIキー（要作成）
├── .claude/
│   ├── CLAUDE.md                      # プロジェクト設定
│   ├── settings.json                  # Claude Code設定
│   └── skills/
│       ├── ebook-manga-auto-ss/       # ★ メインスキル（全フェーズ制御）
│       ├── ebook-deji/                # 一気通貫スキル（A5・赤太字版）
│       ├── ebook-auto/                # オーケストレーター
│       ├── ebook-research/            # 5層リサーチ
│       ├── ebook-manuscript/          # 原稿執筆
│       ├── ebook-image-gen/           # 挿絵画像生成
│       ├── ebook-manga/               # 漫画化
│       └── ebook-docx/                # 最終DOCX統合
├── scripts/
│   ├── openai_image_gen.py            # ★ OpenAI gpt-image-2 画像生成
│   ├── build_docx.py                  # DOCX構築
│   ├── generate_illustrations.py      # 挿絵一括生成
│   ├── generate_manga.py              # 漫画一括生成
│   ├── gen_images_claudecode.py       # サンプル: claudecode-nani 挿絵
│   ├── gen_manga_claudecode.py        # サンプル: claudecode-nani 漫画
│   └── config.py
├── キャラ参照/                        # キャラクター画像（任意）
├── コマ割りテンプレ (1024 x 1536 px)/ # 漫画コマ割りテンプレ（漫画ページと同一サイズ・10種類）
├── output/                            # 生成物の出力先
└── sample/                            # サンプル出力（参考用）
```

### スキル構成

| スキル | 役割 | 必須度 |
|--------|------|--------|
| `ebook-manga-auto-ss` | メイン制御（Phase 0〜8） | 必須 |
| `ebook-deji` | 一気通貫（A5・Meiryo・赤太字） | 必須 |
| `ebook-auto` | オーケストレーター | 必須 |

> 画像生成は同梱の `scripts/openai_image_gen.py` を全スキルから呼び出す方式です（`OPENAI_API_KEY` のみで動作）。
> Geminiベースの旧版 `nanobanana-deji` / `nanobanana-pro` スキルは含まれていません。

---

## 注意事項

- **Claude Proプラン以上**が必要です（大量のトークンを消費します）
- **OpenAI API は従量課金**です。`gpt-image-2` の単価は OpenAI Platform の Pricing ページで最新情報を確認してください
- **組織認証（Organization Verification）** が必要な場合があります（gpt-image-2 利用時）
- 1回の実行で約 **48枚の画像**（挿絵28枚 + 漫画20枚）を生成します
- 最終DOCXは約 **40〜50MB** になります（画像埋め込みのため）
- 全工程の所要時間は約 **30〜60分** です（画像生成の処理時間を含む）
- Chromeブラウザや外部サービスへのログインは不要です

