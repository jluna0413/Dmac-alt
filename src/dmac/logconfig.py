import logging


def configure_logging(level: str = "INFO") -> None:
    levelno = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=levelno, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
