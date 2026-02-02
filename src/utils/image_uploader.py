"""画像をHTTPS URLにアップロードする.

LINE ImageMessage は公開HTTPS URLが必須のため、
catbox.moe（登録不要）にアップロードしてURLを取得する。
"""

import logging
import time

import requests
from PIL import Image

logger = logging.getLogger(__name__)


def upload_image(file_path: str, max_retries: int = 3) -> str | None:
    """画像をcatbox.moeにアップロードし、HTTPS URLを返す.

    Args:
        file_path: アップロードする画像のパス
        max_retries: 最大リトライ回数（デフォルト: 3）

    Returns:
        アップロード成功時はHTTPS URL、失敗時はNone
    """
    for attempt in range(max_retries):
        try:
            with open(file_path, "rb") as f:
                resp = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": f},
                    timeout=120,  # タイムアウトを120秒に延長
                )
            resp.raise_for_status()
            url = resp.text.strip()
            logger.info("画像アップロード成功: %s", url)
            return url
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # 5秒、10秒、15秒と増加
                logger.warning(
                    "画像アップロードタイムアウト (%s): リトライ %d/%d (待機: %d秒)",
                    file_path, attempt + 1, max_retries, wait_time
                )
                time.sleep(wait_time)
            else:
                logger.error("画像アップロード失敗 (%s): タイムアウト (最大リトライ回数に到達)", file_path)
                return None
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                logger.warning(
                    "画像アップロードエラー (%s): %s - リトライ %d/%d (待機: %d秒)",
                    file_path, e, attempt + 1, max_retries, wait_time
                )
                time.sleep(wait_time)
            else:
                logger.error("画像アップロード失敗 (%s): %s", file_path, e)
                return None
        except Exception as e:
            logger.error("画像アップロード失敗 (%s): %s", file_path, e)
            return None

    return None


def create_preview(file_path: str, max_width: int = 240) -> str:
    """プレビュー用にリサイズした画像を作成し、パスを返す."""
    img = Image.open(file_path)
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    preview_path = file_path.rsplit(".", 1)[0] + "_preview.jpg"
    img.save(preview_path, "JPEG", quality=80)
    return preview_path
