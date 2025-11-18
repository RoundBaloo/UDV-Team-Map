from __future__ import annotations

import logging

"""Логгер для операций синхронизации (udv-sync)."""

logger = logging.getLogger("udv-sync")

# Инициализируем логгер только один раз, чтобы не дублировать хендлеры
if not logger.handlers:
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False
