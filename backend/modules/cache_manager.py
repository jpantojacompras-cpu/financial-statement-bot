import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


CACHE_DIR = Path("backend/cache")
CACHE_FILE = CACHE_DIR / "movements_cache.json"
META_FILE = CACHE_DIR / "last_update.json"

# TTL constants
# When files change frequently, use a shorter TTL (1 hour).
# When the caller knows data is stable, a longer TTL (24 hours) can be passed.
DEFAULT_TTL_SECONDS = 3600      # 1 hour – default when files were recently modified
LONG_TTL_SECONDS = 86400        # 24 hours – suitable when no uploads are expected


class CacheManager:
    """
    Gestiona un caché de movimientos pre-procesados en disco.

    - El caché se invalida automáticamente cuando se sube/borra un archivo
      (llamar a ``invalidate()``).
    - TTL dinámico: 1 hora con cambios recientes, 24 horas sin cambios.
    - La escritura del caché también guarda un índice por fecha para búsquedas
      instantáneas.
    """

    def __init__(self, cache_file: str = None, meta_file: str = None):
        self.cache_file = Path(cache_file) if cache_file else CACHE_FILE
        self.meta_file = Path(meta_file) if meta_file else META_FILE
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Core cache operations
    # ------------------------------------------------------------------

    def is_valid(self) -> bool:
        """True si el caché existe y no ha caducado."""
        if not self.cache_file.exists() or not self.meta_file.exists():
            return False
        try:
            meta = self._load_meta()
            last_write = datetime.fromisoformat(meta.get("last_write", "2000-01-01"))
            ttl = meta.get("ttl_seconds", DEFAULT_TTL_SECONDS)
            return datetime.now() - last_write < timedelta(seconds=ttl)
        except Exception:
            return False

    def is_stale(self) -> bool:
        return not self.is_valid()

    def get_movements(self) -> Optional[Dict[str, Any]]:
        """Retorna el caché si es válido, None si está caducado."""
        if not self.is_valid():
            return None
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  CacheManager: Error leyendo caché: {e}")
            return None

    def set_movements(self, payload: Dict[str, Any], ttl_seconds: int = None):
        """Guarda movimientos en el caché."""
        ttl = ttl_seconds if ttl_seconds is not None else DEFAULT_TTL_SECONDS
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            self._save_meta(ttl)
            self._build_date_index(payload.get("movimientos", []))
            print(f"✅ CacheManager: caché guardado ({len(payload.get('movimientos', []))} movimientos, TTL={ttl}s)")
        except Exception as e:
            print(f"❌ CacheManager: Error guardando caché: {e}")

    def invalidate(self):
        """Invalida el caché (se llama al subir/borrar archivos)."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
            if self.meta_file.exists():
                self.meta_file.unlink()
            index_file = CACHE_DIR / "index_by_date.json"
            if index_file.exists():
                index_file.unlink()
            print("🗑️  CacheManager: caché invalidado")
        except Exception as e:
            print(f"⚠️  CacheManager: Error invalidando caché: {e}")

    # ------------------------------------------------------------------
    # Date index (instant lookups by year-month)
    # ------------------------------------------------------------------

    def search_by_date(self, year: str = None, month: str = None) -> List[dict]:
        """Búsqueda instantánea por año/mes usando el índice de fechas."""
        index_file = CACHE_DIR / "index_by_date.json"
        if not index_file.exists():
            return []
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index: Dict[str, List[dict]] = json.load(f)
            results: List[dict] = []
            for key, movements in index.items():
                if year and not key.startswith(year):
                    continue
                if month and year and key != f"{year}-{month}":
                    continue
                results.extend(movements)
            return results
        except Exception as e:
            print(f"⚠️  CacheManager: Error buscando por fecha: {e}")
            return []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_meta(self) -> dict:
        with open(self.meta_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_meta(self, ttl: int):
        meta = {
            "last_write": datetime.now().isoformat(),
            "ttl_seconds": ttl,
        }
        with open(self.meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f)

    def _build_date_index(self, movements: List[dict]):
        """Construye un índice { 'YYYY-MM': [mov, …] } para búsquedas rápidas."""
        index: Dict[str, List[dict]] = {}
        for mov in movements:
            fecha = mov.get("fecha", "")
            if fecha and len(fecha) >= 7:
                key = fecha[:7]  # YYYY-MM
                index.setdefault(key, []).append(mov)
        index_file = CACHE_DIR / "index_by_date.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False)
