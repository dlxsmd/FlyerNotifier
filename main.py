#!/usr/bin/env python3
"""Shufoo! チラシ画像LINE送信."""

import logging
import sys

from src.config import AppConfig
from src.notify.line_notifier import LineNotifier
from src.shufoo.client import ShufooClient
from src.shufoo.downloader import ChirashiDownloader
from src.utils.logging_config import setup_logging


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("=== チラシ送信 開始 ===")

    try:
        config = AppConfig()
        config.load()
        stores = config.stores
        if not stores:
            logger.warning("有効な店舗がありません")
            return

        line_cfg = config.line_config
        line = LineNotifier(
            channel_access_token=line_cfg["channel_access_token"],
            user_id=line_cfg["user_id"],
        )
        shufoo = ShufooClient()
        downloader = ChirashiDownloader()

        for store in stores:
            logger.info("--- %s ---", store.name)
            try:
                chirashis = shufoo.fetch_chirashi_list(store)
                if not chirashis:
                    logger.info("  チラシなし")
                    continue

                for chirashi in chirashis:
                    chirashi = downloader.download(chirashi)
                    if not chirashi.local_image_paths:
                        logger.warning("  画像取得失敗")
                        continue
                    line.send_chirashi(store, chirashi)

            except Exception as e:
                logger.error("  %s エラー: %s", store.name, e)
                continue

        downloader.cleanup_old_images(days=3)

    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical("致命的エラー: %s", e, exc_info=True)
        sys.exit(1)

    logger.info("=== チラシ送信 終了 ===")


if __name__ == "__main__":
    main()
