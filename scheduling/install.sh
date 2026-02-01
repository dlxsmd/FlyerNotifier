#!/bin/bash
# launchdエージェントのインストールスクリプト
set -e

PLIST_NAME="net.yuki.sale-notification.plist"
PLIST_SRC="$(cd "$(dirname "$0")" && pwd)/$PLIST_NAME"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME"

# ログディレクトリ作成
mkdir -p /Users/yuki/SaleNotification/logs

# 既にロード済みならアンロード
launchctl unload "$PLIST_DST" 2>/dev/null || true

# plistファイルをコピー
cp "$PLIST_SRC" "$PLIST_DST"

# バリデーション
plutil -lint "$PLIST_DST"

# ロード
launchctl load "$PLIST_DST"

echo "インストール完了: $PLIST_NAME"
echo "ステータス確認: launchctl list | grep sale-notification"
echo "手動実行: python3 /Users/yuki/SaleNotification/main.py"
echo ""
echo "アンインストール:"
echo "  launchctl unload $PLIST_DST"
echo "  rm $PLIST_DST"
