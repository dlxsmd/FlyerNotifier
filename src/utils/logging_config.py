"""ロギング設定."""

import logging
from pathlib import Path


def setup_logging(log_dir: str = "logs", level: int = logging.INFO) -> None:
    """コンソールとファイルの両方にログ出力を設定する."""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # ファイルハンドラ
    file_handler = logging.FileHandler(
        log_path / "app.log", encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
