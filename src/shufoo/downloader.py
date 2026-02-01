"""チラシ画像ダウンローダー（タイル結合方式）.

Shufoo!のチラシ画像はタイル分割で提供される:
  URL: {base_url}/{page}_{zoom}_{tile}.jpg

各タイルをダウンロードしPILで結合して完全なページ画像を生成する。
タイルは左上から右方向に並び、行末で次の行に折り返す。
"""

import io
import logging
import math
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import requests
from PIL import Image

from src.models import Chirashi

logger = logging.getLogger(__name__)


class ChirashiDownloader:
    """チラシ画像をローカルにダウンロードする."""

    def __init__(self, base_dir: str = "data/images", timeout: int = 30):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.session = requests.Session()

    def download(self, chirashi: Chirashi) -> Chirashi:
        """チラシの画像をダウンロードする.

        タイル情報がある場合はタイルを結合、なければ直接URLからダウンロード。
        """
        save_dir = (
            self.base_dir / chirashi.store.shop_id / chirashi.chirashi_id
        )
        save_dir.mkdir(parents=True, exist_ok=True)

        tile_info = getattr(chirashi, "_tile_info", None)
        if tile_info and tile_info.get("pages"):
            local_paths = self._download_tiles(tile_info, save_dir)
        elif chirashi.image_urls:
            local_paths = self._download_direct(chirashi, save_dir)
        else:
            local_paths = []

        chirashi.local_image_paths = local_paths
        logger.info(
            "%s: %d枚の画像を取得",
            chirashi.store.name,
            len(local_paths),
        )
        return chirashi

    def _download_tiles(
        self, tile_info: dict, save_dir: Path
    ) -> list[str]:
        """タイル画像をダウンロードして結合する."""
        base_url = tile_info["base_url"]
        zoom = tile_info["zoom"]
        local_paths = []

        for page_info in tile_info["pages"]:
            page_num = page_info["page"]
            tile_count = page_info["tile_count"]
            local_path = save_dir / f"page_{page_num + 1}.jpg"

            # 既にダウンロード済みならスキップ
            if local_path.exists() and local_path.stat().st_size > 10000:
                local_paths.append(str(local_path))
                logger.debug("キャッシュ使用: %s", local_path)
                continue

            # 全タイルをダウンロード
            tiles: list[Image.Image] = []
            for tile_idx in range(tile_count):
                tile_url = f"{base_url}/{page_num}_{zoom}_{tile_idx}.jpg"
                try:
                    resp = self.session.get(tile_url, timeout=self.timeout)
                    if resp.status_code != 200:
                        logger.debug(
                            "タイル取得失敗 (HTTP %d): %s",
                            resp.status_code, tile_url,
                        )
                        break
                    img = Image.open(io.BytesIO(resp.content))
                    tiles.append(img)
                except Exception as e:
                    logger.debug(
                        "タイル取得エラー (%d_%d_%d): %s",
                        page_num, zoom, tile_idx, e,
                    )
                    break

            if not tiles:
                continue

            # タイルを結合
            stitched = self._stitch_tiles(tiles)
            if stitched:
                stitched.save(str(local_path), "JPEG", quality=95)
                local_paths.append(str(local_path))
                logger.info(
                    "ページ%d: %dタイル結合 → %dx%d (%dKB)",
                    page_num + 1, len(tiles),
                    stitched.width, stitched.height,
                    local_path.stat().st_size // 1024,
                )

        return local_paths

    def _stitch_tiles(self, tiles: list[Image.Image]) -> Image.Image | None:
        """タイル画像をグリッド状に結合する."""
        if not tiles:
            return None
        if len(tiles) == 1:
            return tiles[0]

        num_cols = self._detect_columns(tiles)
        num_rows = math.ceil(len(tiles) / num_cols)

        # 各列の幅・各行の高さを計算
        col_widths = []
        for col in range(num_cols):
            w = 0
            for row in range(num_rows):
                idx = row * num_cols + col
                if idx < len(tiles):
                    w = max(w, tiles[idx].width)
            col_widths.append(w)

        row_heights = []
        for row in range(num_rows):
            h = 0
            for col in range(num_cols):
                idx = row * num_cols + col
                if idx < len(tiles):
                    h = max(h, tiles[idx].height)
            row_heights.append(h)

        total_w = sum(col_widths)
        total_h = sum(row_heights)

        canvas = Image.new("RGB", (total_w, total_h), (255, 255, 255))

        y = 0
        for row in range(num_rows):
            x = 0
            for col in range(num_cols):
                idx = row * num_cols + col
                if idx < len(tiles):
                    canvas.paste(tiles[idx], (x, y))
                x += col_widths[col]
            y += row_heights[row]

        return canvas

    def _detect_columns(self, tiles: list[Image.Image]) -> int:
        """タイルの幅パターンから列数を自動検出する.

        右端のタイルは基準幅より狭いことを利用して行の区切りを検出する。
        全タイルが同一幅の場合はtile_countの約数から推定する。
        """
        if len(tiles) <= 1:
            return 1

        base_width = tiles[0].width

        # 基準幅より狭いタイルを探す → 行の右端
        for i in range(1, len(tiles)):
            if tiles[i].width < base_width:
                return i + 1  # 0..i がfirst rowの i+1 タイル
                # ただし i が先頭タイルの次(=1)で狭い場合、2列
                # i=2 で狭い場合、3列（tiles 0,1,2 が1行目）

        # 全タイル同一幅 → tile_countの約数から推定
        n = len(tiles)
        base_h = tiles[0].height
        best_cols = n  # fallback: 1行
        best_ratio_diff = float("inf")

        for cols in range(1, n + 1):
            if n % cols != 0:
                continue
            rows = n // cols
            aspect = (cols * base_width) / (rows * base_h)
            # チラシは縦長（aspect ratio 0.6〜0.8程度）が一般的
            diff = abs(aspect - 0.7)
            if diff < best_ratio_diff:
                best_ratio_diff = diff
                best_cols = cols

        return best_cols

    def _download_direct(
        self, chirashi: Chirashi, save_dir: Path
    ) -> list[str]:
        """直接URLから画像をダウンロードする."""
        local_paths = []

        for i, url in enumerate(chirashi.image_urls):
            local_path = save_dir / f"page_{i + 1}.jpg"

            if local_path.exists() and local_path.stat().st_size > 1000:
                local_paths.append(str(local_path))
                continue

            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 404:
                    break
                resp.raise_for_status()

                if len(resp.content) < 10000:
                    logger.debug(
                        "画像が小さすぎます（%dB）: %s",
                        len(resp.content), url,
                    )
                    continue

                with open(local_path, "wb") as f:
                    f.write(resp.content)
                local_paths.append(str(local_path))

            except requests.RequestException as e:
                logger.debug("直接ダウンロード失敗: %s", e)
                break

        return local_paths

    def cleanup_old_images(self, days: int = 3) -> None:
        """指定日数以上前の画像を削除する."""
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0

        for shop_dir in self.base_dir.iterdir():
            if not shop_dir.is_dir():
                continue
            for chirashi_dir in shop_dir.iterdir():
                if not chirashi_dir.is_dir():
                    continue
                mtime = datetime.fromtimestamp(chirashi_dir.stat().st_mtime)
                if mtime < cutoff:
                    shutil.rmtree(chirashi_dir)
                    removed += 1

        if removed:
            logger.info("古い画像を%d件削除しました", removed)
