"""Shufoo! APIクライアント - チラシ一覧取得.

Shufoo!のチラシ画像はタイル方式で提供される:
  URL: https://ipqcache2.shufoo.net/c/{YYYY}/{MM}/{DD}/{chirashiId}/index/img/{page}_{zoom}_{tile}.jpg

  - chirashiId: チラシ固有ID（dataLayer/リンクから取得）
  - page: ページ番号（0始まり）
  - zoom: ズームレベル（100=等倍, 200=2倍）
  - tile: タイル番号（左上から右方向、次の行へ）

注意: 店舗ページ上のタイルURL（ipqcache2）は広告用であり、
      店舗のチラシIDはリンクパターンまたはdataLayerから取得する。
      日付パスは直近7日間をHEADリクエストで探索して特定する。
"""

import logging
import re
from datetime import datetime, timedelta

import requests

from src.models import Chirashi, StoreConfig

logger = logging.getLogger(__name__)

IMAGE_BASE_URL = "https://ipqcache2.shufoo.net"


class ShufooClient:
    """Shufoo!からチラシデータを取得するクライアント."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/json",
            "Accept-Language": "ja,en;q=0.9",
        })

    def fetch_chirashi_list(
        self, store: StoreConfig, max_count: int = 3
    ) -> list[Chirashi]:
        """指定店舗の最新チラシ一覧を取得する."""
        chirashis = []
        try:
            chirashis = self._fetch_from_shop_page(store, max_count)
        except Exception as e:
            logger.error("チラシ取得失敗 (%s): %s", store.name, e)

        logger.info("%s: %d件のチラシを取得", store.name, len(chirashis))
        return chirashis[:max_count]

    def _fetch_from_shop_page(
        self, store: StoreConfig, max_count: int
    ) -> list[Chirashi]:
        """店舗詳細ページからチラシ情報を抽出する."""
        url = f"https://www.shufoo.net/pntweb/shopDetail/{store.shop_id}/"
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        html = resp.text

        # チラシIDを抽出（リンクパターン + dataLayer）
        chirashi_ids = self._extract_chirashi_ids(html, store)
        if not chirashi_ids:
            logger.warning("チラシIDが見つかりません: %s", store.name)
            return []

        # タイトル抽出
        title_match = re.search(
            r"['\"]content_title['\"]\s*:\s*['\"]([^'\"]+)['\"]", html
        )
        title = title_match.group(1) if title_match else store.name

        results = []
        for chirashi_id in chirashi_ids[:max_count]:
            # 日付パスを探索してタイル情報を取得
            tile_info = self._find_tiles_with_date_probe(chirashi_id)
            if not tile_info:
                continue

            date_path = tile_info["date_path"]
            pub_date = datetime.strptime(date_path, "%Y/%m/%d")

            chirashi = Chirashi(
                chirashi_id=chirashi_id,
                store=store,
                title=title,
                image_urls=[],
                publish_start=pub_date,
                publish_end=pub_date + timedelta(days=3),
            )
            chirashi._tile_info = tile_info
            results.append(chirashi)

        return results

    def _extract_chirashi_ids(
        self, html: str, store: StoreConfig
    ) -> list[str]:
        """HTMLから店舗のチラシIDを抽出する.

        リンクパターンとdataLayerの両方から取得し、重複を除去する。
        """
        ids: list[str] = []
        seen: set[str] = set()

        # 方法1: 店舗固有のリンクパターン
        link_pattern = re.compile(
            rf"/pntweb/shopDetail/{re.escape(store.shop_id)}/(\d+)/"
        )
        for m in link_pattern.finditer(html):
            cid = m.group(1)
            if cid not in seen:
                seen.add(cid)
                ids.append(cid)

        # 方法2: dataLayer の chirashiId
        for pattern in [
            r"chirashiId\s*:\s*['\"](\d+)['\"]",
            r"siteCatalyst_chirashiId\s*:\s*['\"](\d+)['\"]",
        ]:
            m = re.search(pattern, html)
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                ids.append(m.group(1))

        return ids

    def _find_tiles_with_date_probe(
        self, chirashi_id: str, zoom: int = 200
    ) -> dict | None:
        """直近の日付を探索してタイルの存在する日付パスを特定し、タイル情報を返す.

        Returns:
            {
                "base_url": str,
                "zoom": int,
                "date_path": str,
                "pages": [{"page": 0, "tile_count": 6}, ...]
            }
            or None if no tiles found.
        """
        today = datetime.now().date()

        for days_ago in range(8):
            date = today - timedelta(days=days_ago)
            date_path = date.strftime("%Y/%m/%d")
            base_url = (
                f"{IMAGE_BASE_URL}/c/{date_path}/{chirashi_id}/index/img"
            )

            # タイル0の存在確認
            test_url = f"{base_url}/0_{zoom}_0.jpg"
            try:
                resp = self.session.head(test_url, timeout=10)
                if resp.status_code != 200:
                    continue
            except requests.RequestException:
                continue

            # タイルが見つかった → 全ページ・タイルを探索
            result = self._discover_tiles(chirashi_id, date_path, zoom)
            if result["pages"]:
                result["date_path"] = date_path
                return result

        logger.warning(
            "タイルが見つかりません: chirashi %s", chirashi_id
        )
        return None

    def _discover_tiles(
        self, chirashi_id: str, date_path: str, zoom: int = 200
    ) -> dict:
        """タイル画像の構成（ページ数・タイル数）を探索する.

        Returns:
            {
                "base_url": str,
                "zoom": int,
                "pages": [
                    {"page": 0, "tile_count": 6},
                    {"page": 1, "tile_count": 6},
                ]
            }
        """
        base_url = f"{IMAGE_BASE_URL}/c/{date_path}/{chirashi_id}/index/img"
        result = {"base_url": base_url, "zoom": zoom, "pages": []}

        for page in range(10):
            # まずタイル0の存在を確認
            test_url = f"{base_url}/{page}_{zoom}_0.jpg"
            try:
                resp = self.session.head(test_url, timeout=10)
                if resp.status_code != 200:
                    break
            except requests.RequestException:
                break

            # タイル数を探索
            tile_count = 0
            for tile in range(20):
                tile_url = f"{base_url}/{page}_{zoom}_{tile}.jpg"
                try:
                    resp = self.session.head(tile_url, timeout=10)
                    if resp.status_code == 200:
                        tile_count += 1
                    else:
                        break
                except requests.RequestException:
                    break

            result["pages"].append({"page": page, "tile_count": tile_count})

        logger.info(
            "chirashi %s: %dページ, zoom=%d",
            chirashi_id, len(result["pages"]), zoom,
        )
        return result
