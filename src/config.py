"""設定ファイル読み込み."""

import logging
from pathlib import Path

import yaml

from src.models import StoreConfig

logger = logging.getLogger(__name__)


class AppConfig:
    """config.yamlを読み込み、型付きの設定を提供する."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._raw: dict = {}
        self._stores: list[StoreConfig] = []

    def load(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"設定ファイルが見つかりません: {self.config_path}\n"
                "config.yaml を作成してください。"
            )
        with open(self.config_path, encoding="utf-8") as f:
            self._raw = yaml.safe_load(f)
        self._validate()
        self._parse_stores()
        logger.info("設定読み込み: %s", self.config_path)

    def _validate(self) -> None:
        if "stores" not in self._raw or not self._raw["stores"]:
            raise ValueError("少なくとも1店舗を登録してください")
        if "line" not in self._raw:
            raise ValueError("line設定が必要です")

    def _parse_stores(self) -> None:
        self._stores = []
        for s in self._raw["stores"]:
            store = StoreConfig(
                name=s["name"],
                shop_id=str(s["shopId"]),
                enabled=s.get("enabled", True),
            )
            self._stores.append(store)

    @property
    def stores(self) -> list[StoreConfig]:
        return [s for s in self._stores if s.enabled]

    @property
    def line_config(self) -> dict:
        return self._raw.get("line", {})
