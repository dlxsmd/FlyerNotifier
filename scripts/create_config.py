#!/usr/bin/env python3
"""
GitHub Actions環境変数からconfig.yamlを生成するスクリプト
"""
import os
import json
import yaml
from pathlib import Path


def create_config():
    """環境変数から config.yaml を生成"""

    # 必須環境変数のチェック
    required_vars = [
        'LINE_CHANNEL_ACCESS_TOKEN',
        'LINE_USER_ID'
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # 店舗設定の取得（JSON形式または従来形式）
    stores = []
    stores_json = os.getenv('STORES')

    if stores_json:
        # JSON形式の複数店舗設定
        try:
            # 改行やスペースを含む JSON にも対応
            stores_json_cleaned = stores_json.strip()
            stores_data = json.loads(stores_json_cleaned)

            if not isinstance(stores_data, list):
                raise ValueError("STORES must be a JSON array")

            for store in stores_data:
                stores.append({
                    'name': store['name'],
                    'shopId': str(store['shopId']),
                    'enabled': store.get('enabled', True)
                })
        except json.JSONDecodeError as e:
            # デバッグ用に最初の100文字を表示
            preview = stores_json_cleaned[:100] if len(stores_json_cleaned) <= 100 else stores_json_cleaned[:100] + "..."
            raise ValueError(
                f"Invalid JSON format in STORES environment variable: {e}\n"
                f"Received (first 100 chars): {preview}\n"
                f"Expected format: [{{'name':'店舗1','shopId':'123'}},{{'name':'店舗2','shopId':'456'}}]\n"
                f"Common issues:\n"
                f"  - Trailing commas in the array\n"
                f"  - Missing quotes around strings\n"
                f"  - Extra commas or brackets"
            )
        except KeyError as e:
            raise ValueError(f"Missing required field in STORES: {e}")
    else:
        # 従来形式の単一店舗設定（後方互換性）
        store_name = os.getenv('STORE_NAME')
        store_shop_id = os.getenv('STORE_SHOP_ID')

        if not store_name or not store_shop_id:
            raise ValueError(
                "Either STORES (JSON format) or both STORE_NAME and STORE_SHOP_ID are required.\n"
                "For multiple stores, use STORES='[{\"name\":\"店舗1\",\"shopId\":\"123\"},{\"name\":\"店舗2\",\"shopId\":\"456\"}]'"
            )

        stores.append({
            'name': store_name,
            'shopId': store_shop_id,
            'enabled': True
        })

    if not stores:
        raise ValueError("At least one store must be configured")

    # config構造を作成
    config = {
        'stores': stores,
        'line': {
            'channel_access_token': os.getenv('LINE_CHANNEL_ACCESS_TOKEN'),
            'user_id': os.getenv('LINE_USER_ID')
        }
    }

    # config.yamlに書き込み
    config_path = Path(__file__).parent.parent / 'config.yaml'
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"✅ config.yaml created successfully at {config_path}")
    print(f"   Stores ({len(stores)}): {', '.join([s['name'] for s in stores])}")


if __name__ == '__main__':
    create_config()
