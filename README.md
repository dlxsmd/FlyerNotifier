# SaleNotification

Shufoo!のチラシ画像を自動取得し、AIで分析してレシピ提案をLINEに送信するアプリケーションです。

## 機能

- 🏪 Shufoo!から指定店舗のチラシ画像を自動取得
- 📱 LINE Messaging APIでチラシ画像を送信
- 🤖 AI（Gemini / DeepSeek）でチラシをOCR分析
- 🍳 特売商品から自動でレシピを提案
- ⏰ GitHub Actionsで毎朝10時に自動実行

## セットアップ

### 1. 依存関係のインストール

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. ローカル実行用の設定（開発時）

`config.yaml.example` をコピーして `config.yaml` を作成：

```bash
cp config.yaml.example config.yaml
```

`config.yaml` を編集して以下を設定：

- **店舗情報**: Shufoo!のshopId
- **LINE認証情報**: channel_access_token, user_id
- **AI設定**: provider（gemini/deepseek）とAPIキー

### 3. ローカルで実行

```bash
python main.py
```

## GitHub Actionsで毎朝10時に自動実行する設定

### 1. GitHubリポジトリを作成

このプロジェクトをGitHubにpushします（プライベートリポジトリ推奨）。

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/SaleNotification.git
git push -u origin main
```

### 2. GitHub Secretsを設定

GitHubリポジトリの `Settings` → `Secrets and variables` → `Actions` → `New repository secret` から以下のシークレットを追加：

| シークレット名 | 説明 | 例 |
|--------------|------|-----|
| `STORE_NAME` | 店舗名 | `サミット/弦巻通り店` |
| `STORE_SHOP_ID` | ShufooのshopId | `264240` |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINEのチャネルアクセストークン | `abcdef...` |
| `LINE_USER_ID` | LINEのユーザーID | `U1234567...` |
| `AI_PROVIDER` | AIプロバイダー | `gemini` または `deepseek` |
| `AI_API_KEY` | AIのAPIキー | Gemini: `AIza...` / DeepSeek: `sk-...` |
| `AI_MODEL` | 使用するモデル（省略可） | Gemini: `gemini-2.0-flash` / DeepSeek: `deepseek-chat` |

#### Gemini使用時の例：

```
STORE_NAME=サミット/弦巻通り店
STORE_SHOP_ID=264240
LINE_CHANNEL_ACCESS_TOKEN=YOUR_LINE_TOKEN
LINE_USER_ID=YOUR_LINE_USER_ID
AI_PROVIDER=gemini
AI_API_KEY=AIzaSy...
AI_MODEL=gemini-2.0-flash
```

#### DeepSeek使用時の例：

```
STORE_NAME=サミット/弦巻通り店
STORE_SHOP_ID=264240
LINE_CHANNEL_ACCESS_TOKEN=YOUR_LINE_TOKEN
LINE_USER_ID=YOUR_LINE_USER_ID
AI_PROVIDER=deepseek
AI_API_KEY=sk-...
AI_MODEL=deepseek-chat
```

### 3. ワークフローの動作確認

設定が完了すると、毎朝10時（日本時間）に自動実行されます。

手動で実行してテストする場合：

1. GitHubリポジトリの `Actions` タブを開く
2. `Daily Chirashi Notification` ワークフローを選択
3. `Run workflow` → `Run workflow` をクリック

### 4. ログの確認

実行結果は `Actions` タブから確認できます。エラーが発生した場合はログがアーティファクトとして保存されます。

## LINE Messaging APIの設定

1. [LINE Developers Console](https://developers.line.biz/) でMessaging APIチャネルを作成
2. チャネルアクセストークンを発行
3. Webhook設定を無効化（受信は不要）
4. LINEアプリで公式アカウントを友だち追加
5. ユーザーIDを取得（[LINE公式アカウント](https://manager.line.biz/)から確認可能）

## AI APIの設定

### Gemini API

1. [Google AI Studio](https://aistudio.google.com/app/apikey) でAPIキーを作成
2. `AI_PROVIDER=gemini`, `AI_API_KEY=YOUR_KEY` を設定

### DeepSeek API

1. [DeepSeek Platform](https://platform.deepseek.com/) でAPIキーを作成
2. `AI_PROVIDER=deepseek`, `AI_API_KEY=YOUR_KEY` を設定

## トラブルシューティング

### GitHub Actionsが実行されない

- リポジトリの `Actions` タブで有効化されているか確認
- Secretsが正しく設定されているか確認
- 手動実行でエラーログを確認

### チラシが取得できない

- Shufoo!のshopIdが正しいか確認
- 店舗にチラシが公開されているか確認

### LINEに送信されない

- LINE channel_access_tokenが有効か確認
- user_idが正しいか確認
- LINE公式アカウントを友だち追加しているか確認

## ライセンス

MIT License

## 開発者向け情報

- Python 3.13
- 依存パッケージ: requests, PyYAML, Pillow, line-bot-sdk, google-genai, openai
- 画像ホスティング: catbox.moe（匿名アップロード）
