"""データモデル定義."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StoreConfig:
    """店舗設定."""
    name: str
    shop_id: str
    enabled: bool = True


@dataclass
class Chirashi:
    """Shufoo!から取得したチラシ."""
    chirashi_id: str
    store: StoreConfig
    title: str
    image_urls: list[str]
    publish_start: datetime
    publish_end: datetime
    local_image_paths: list[str] = field(default_factory=list)
