"""
Configuración centralizada de la aplicación.
Lee variables de entorno con valores por defecto.
"""
import os

BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
MAX_FILES_PER_BATCH: int = int(os.getenv("MAX_FILES_PER_BATCH", "10"))
MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))

ALLOWED_ORIGINS: list = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
