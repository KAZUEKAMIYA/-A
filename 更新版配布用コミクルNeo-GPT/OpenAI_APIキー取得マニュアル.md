# OpenAI APIキー 取得マニュアル

このシステムを使うために、OpenAIのAPIキーが1つ必要になります。
このマニュアル通りに進めれば、**5〜10分**で取得・設定が完了します。

---

## 全体の流れ

```
① OpenAIアカウントを作る（持っていれば飛ばしてOK）
   ↓
② 支払い方法（クレジットカード）を登録する
   ↓
③ 組織認証（Organization Verification）を行う
   ↓
④ APIキーを発行する
   ↓
⑤ このフォルダの「.env」ファイルにキーを貼り付ける
```

---

## ① OpenAIアカウントを作る

すでにChatGPTのアカウントがある方は、そのアカウントでログインできます。**②へ進んでOK**です。

1. [https://platform.openai.com/signup](https://platform.openai.com/signup) にアクセス
2. メールアドレス・Googleアカウント・Microsoftアカウントなどでサインアップ
3. メール認証を完了させる

> ⚠ ChatGPTの月額プラン（Plus/Pro）と、APIの料金は **別物** です。APIは別途、使った分だけ課金される従量制です。

---

## ② 支払い方法（クレジットカード）を登録する

APIを使うには、**先払い（Prepaid Credits）** 方式でクレジットを購入する必要があります。

### 手順

1. [https://platform.openai.com/](https://platform.openai.com/) にログイン
2. 画面右上の歯車アイコン（⚙️）→ **Settings** をクリック
3. 左メニューから **Billing**（請求）をクリック
4. **Add payment method**（支払い方法を追加）でクレジットカードを登録
5. **Add to credit balance**（クレジット残高を追加）から金額を入金
   - 最低 **$5（約750円）** から購入できます
   - 初回は **$10〜$20** 程度入れておくと安心です（電子書籍1冊で目安 $3〜$8 ほど消費）

### 自動チャージ（任意・便利）

- 「Auto recharge」を ON にすると、残高が一定額を下回ったときに自動でチャージされます
- 配布されたツールを長く使いたい場合は ON 推奨

---

## ③ 組織認証（Organization Verification）

`gpt-image-2`（このシステムが使う画像生成モデル）は、**組織認証が完了していないと使えない場合**があります。

### 手順

1. [https://platform.openai.com/](https://platform.openai.com/) にログイン
2. 画面右上の歯車アイコン（⚙️）→ **Settings** をクリック
3. 左メニュー → **Organization** → **General**（または **Verifications**）
4. **Verify Organization**（組織を認証する）ボタンをクリック
5. 案内に従って身分証明書（運転免許証・パスポートなど）の画像をアップロード
6. 顔写真の自撮りを撮影してアップロード
7. 数分〜数時間で認証完了のメールが届く

> ⚠ この手順は **画像生成APIを使うために必要** です。テキスト生成のみなら不要ですが、このシステムは画像生成を使うので必ず行ってください。

> ⚠ 認証が不要だった場合はこのステップをスキップしてOK。後でエラーが出たら戻ってきて認証してください。

---

## ④ APIキーを発行する

1. [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys) にアクセス
2. **Create new secret key**（新しいシークレットキーを作成）ボタンをクリック
3. 以下を入力：
   - **Name**（キーの名前）：例 `comicru-neo-gpt`（自由に決めてOK）
   - **Project**：Default のままでOK
   - **Permissions**：`All` のまま
4. **Create secret key** をクリック
5. **`sk-...` で始まる長い文字列が表示されるので、必ずコピーして安全な場所に保管**
   - ⚠ このキーは **一度しか表示されません**。閉じてしまうと二度と見られないので、必ずこの時点でコピーしてください。
   - ⚠ パスワードと同じくらい重要です。**絶対に他人に教えない・SNSやGitHubに貼り付けない**でください。

---

## ⑤ このフォルダの「.env」ファイルにキーを貼り付ける

### 手順

1. このフォルダ（`配布用コミクルNeo-GPT`）の中にある **`.env` ファイル** をテキストエディタ（メモ帳・VSCode・TextEditなど）で開く
   - `.env` が見えない場合は、Finder/エクスプローラーで「隠しファイルを表示」をONにしてください

2. 中身が次のようになっています：
   ```
   # OpenAI API設定
   # 取得先: https://platform.openai.com/api-keys
   OPENAI_API_KEY=		
			
   OPENAI_IMAGE_MODEL=gpt-image-2

   # 出力設定
   OUTPUT_DIR=output
   ```

3. `OPENAI_API_KEY=` の **`=` の右側** に、④でコピーしたキーを貼り付けます：
   ```
   OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz1234567890...
   ```
   - **スペース・改行を入れない**でください
   - キー全体（`sk-` から最後まで）を貼り付けてください

4. **保存**してエディタを閉じる

---

## 動作確認

ターミナル（コマンドプロンプト/PowerShell/Terminal）でこのフォルダに移動して、次のコマンドを実行：

```bash
python -c "
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('.env'))
key = os.getenv('OPENAI_API_KEY', '未設定')
print('KEY:', key[:20] + '...' if key != '未設定' else '❌ 未設定')
"
```

`KEY: sk-proj-abc...` のように表示されれば成功です。

---

## よくあるトラブル

| 症状 | 原因 / 対処 |
|------|-----------|
| `OPENAI_API_KEY が設定されていません` と出る | `.env` の `=` の右側にキーが貼られていない／スペースが入っている／ファイルを保存していない |
| `403` / `must be verified` エラー | ③の組織認証が未完了。Settings → Organization → Verifications から認証してください |
| `429` / `quota exceeded` エラー | ②の残高が0になっている。Billing から追加チャージしてください |
| `model gpt-image-2 not found` | キーの権限が制限されている、または認証未完了。④でキー作成時に Permissions を `All` にしたか確認 |
| キーをなくした | キーは再表示できないので、④の手順で **新しいキーを作り直す** ＋ 古いキーは画面から Revoke（削除）する |

---

## 料金の目安

`gpt-image-2` の単価は OpenAI の公式ページで確認できます：
[https://openai.com/api/pricing/](https://openai.com/api/pricing/)

このシステムは1冊あたり画像 **約48枚**（挿絵28枚＋漫画20枚）を生成します。
1冊あたりの目安は **$3〜$8** 程度（為替・モデル単価により変動）。

> ⚠ 料金は OpenAI 側の改定で変わる可能性があります。最新の単価は必ず公式ページで確認してください。

---

## キーの安全な保管

- **`.env` ファイルは絶対に他人に渡さない**でください（キーが入っているため）
- **GitHubやクラウドストレージに `.env` をアップロードしない**でください（同梱の `.gitignore` で除外済み）
- 万が一キーが漏れた場合は、すぐに [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys) で該当キーを **Revoke**（無効化）して、新しいキーを作り直してください

---

これで準備完了です！ ターミナルでこのフォルダに移動して、`claude` コマンドを実行すれば自動生成が始められます。
