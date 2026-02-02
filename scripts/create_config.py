#!/usr/bin/env python3
"""
GitHub Actions環境変数からconfig.yamlを生成するスクリプト
"""
import os
import yaml
from pathlib import Path


def create_config():
    """環境変数から config.yaml を生成"""

    # 必須環境変数のチェック
    required_vars = [
        'STORE_NAME',
        'STORE_SHOP_ID',
        'LINE_CHANNEL_ACCESS_TOKEN',
        'LINE_USER_ID',
        'AI_PROVIDER',
        'AI_API_KEY'
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # AI provider設定
    provider = os.getenv('AI_PROVIDER', 'gemini')

    # モデル名のデフォルト値
    if provider == 'gemini':
        default_model = 'gemini-2.0-flash'
    elif provider == 'deepseek':
        default_model = 'deepseek-chat'
    else:
        default_model = 'gemini-2.0-flash'

    # config構造を作成
    config = {
        'stores': [
            {
                'name': os.getenv('STORE_NAME'),
                'shopId': os.getenv('STORE_SHOP_ID'),
                'enabled': True
            }
        ],
        'line': {
            'channel_access_token': os.getenv('LINE_CHANNEL_ACCESS_TOKEN'),
            'user_id': os.getenv('LINE_USER_ID')
        },
        'ai': {
            'provider': provider
        }
    }

    # AI provider別の設定
    if provider == 'gemini':
        config['ai']['gemini'] = {
            'api_key': os.getenv('AI_API_KEY'),
            'model': os.getenv('AI_MODEL', default_model)
        }
    elif provider == 'deepseek':
        config['ai']['deepseek'] = {
            'api_key': os.getenv('AI_API_KEY'),
            'model': os.getenv('AI_MODEL', default_model),
            'base_url': os.getenv('AI_BASE_URL', 'https://api.deepseek.com')
        }

    # config.yamlに書き込み
    config_path = Path(__file__).parent.parent / 'config.yaml'
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"✅ config.yaml created successfully at {config_path}")
    print(f"   Store: {config['stores'][0]['name']}")
    print(f"   AI Provider: {provider}")


if __name__ == '__main__':
    create_config()
