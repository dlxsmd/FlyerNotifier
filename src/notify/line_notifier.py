"""LINE Messaging API v3 でチラシ画像を送信する."""

import logging

from src.models import Chirashi, StoreConfig
from src.utils.image_uploader import create_preview, upload_image

logger = logging.getLogger(__name__)


class LineNotifier:
    """LINE Messaging API v3でチラシ画像をプッシュ送信する."""

    def __init__(self, channel_access_token: str, user_id: str):
        self.user_id = user_id
        try:
            from linebot.v3.messaging import (
                ApiClient,
                Configuration,
                MessagingApi,
            )
            config = Configuration(access_token=channel_access_token)
            self._api_client = ApiClient(config)
            self._api = MessagingApi(self._api_client)
            self._available = True
        except ImportError:
            logger.warning(
                "line-bot-sdk がインストールされていません。"
                "LINE通知は無効です。"
            )
            self._available = False

    def send_chirashi(self, store: StoreConfig, chirashi: Chirashi) -> bool:
        """チラシのテキスト情報と画像をLINEで送信する."""
        if not self._available:
            return False

        if not chirashi.local_image_paths:
            logger.warning("送信する画像がありません: %s", store.name)
            return False

        try:
            from linebot.v3.messaging import (
                ImageMessage,
                PushMessageRequest,
                TextMessage,
            )

            pages = len(chirashi.local_image_paths)
            header = f"\U0001f4cb {store.name}\n{chirashi.title}({pages}p)"

            # テキスト + 画像（最大5メッセージ/リクエスト）
            messages = [TextMessage(text=header)]

            for img_path in chirashi.local_image_paths[:4]:
                original_url = upload_image(img_path)
                if not original_url:
                    continue

                preview_path = create_preview(img_path)
                preview_url = upload_image(preview_path)
                if not preview_url:
                    preview_url = original_url

                messages.append(ImageMessage(
                    original_content_url=original_url,
                    preview_image_url=preview_url,
                ))

            if len(messages) <= 1:
                logger.error("画像アップロード全失敗: %s", store.name)
                return False

            self._api.push_message(PushMessageRequest(
                to=self.user_id,
                messages=messages,
            ))

            logger.info(
                "LINE送信成功: %s (%d画像)",
                store.name, len(messages) - 1,
            )
            return True

        except Exception as e:
            logger.error("LINE送信失敗: %s", e)
            return False
