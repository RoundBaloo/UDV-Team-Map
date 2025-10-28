import logging

logger = logging.getLogger("udv-sync")

# если логгер ещё не настроен (чтобы не дублировать хендлеры при повторных импортах)
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

    # чтобы логи не улетали в корневой логгер uvicorn и не дублировались
    logger.propagate = False
