"""
Sistema de logging centralizado para la aplicación.
"""
import logging
import sys
from backend.config import LOG_LEVEL


def setup_logging() -> logging.Logger:
    """Configura y retorna el logger principal de la aplicación."""
    level = getattr(logging, LOG_LEVEL, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Silenciar loggers muy verbosos de librerías externas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)

    return logging.getLogger("financial_bot")


logger = setup_logging()
