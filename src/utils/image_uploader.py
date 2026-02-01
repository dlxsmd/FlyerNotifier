"""画像をHTTPS URLにアップロードする.

LINE ImageMessage は公開HTTPS URLが必須のため、
catbox.moe（登録不要）にアップロードしてURLを取得する。
"""

import logging

import requests
from PIL import Image

logger = logging.getLogger(__name__)


def upload_image(file_path: str) -> str | None:
    """画像をcatbox.moeにアップロードし、HTTPS URLを返す."""
    try:
        with open(file_path, "rb") as f:
            resp = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f},
                timeout=60,
            )
        resp.raise_for_status()
        url = resp.text.strip()
        logger.info("画像アップロード成功: %s", url)
        return url
    except Exception as e:
        logger.error("画像アップロード失敗 (%s): %s", file_path, e)
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
