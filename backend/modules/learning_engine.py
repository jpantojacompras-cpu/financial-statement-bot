import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from .pattern_db import PatternDB
from .intelligent_categorizer import IntelligentCategorizer
from .constants import MONTH_NAMES


LEARNING_LOG_PATH = Path("backend/data/learning_log.json")


class LearningEngine:
    """
    Motor de aprendizaje.
    Registra correcciones del usuario, actualiza PatternDB y puede
    aplicar el patrón aprendido a movimientos similares en batch.
    """

    def __init__(
        self,
        pattern_db: PatternDB = None,
        intelligent_categorizer: IntelligentCategorizer = None,
        log_path: str = None,
    ):
        self.pattern_db = pattern_db if pattern_db is not None else PatternDB()
        self.categorizer = (
            intelligent_categorizer
            if intelligent_categorizer is not None
            else IntelligentCategorizer(pattern_db=self.pattern_db)
        )
        self.log_path = Path(log_path) if log_path else LEARNING_LOG_PATH
        self.log: List[dict] = self._load_log()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_correction(
        self,
        movement_id: str,
        descripcion: str,
        categoria: str,
        subcategoria: str,
        monto: float = None,
        banco: str = None,
        fecha: str = None,
    ) -> dict:
        """
        Registra una corrección del usuario y actualiza el PatternDB.

        Returns: dict con el patrón aprendido y confianza resultante
        """
        mes = None
        if fecha:
            try:
                parts = fecha.replace("/", "-").split("-")
                if len(parts) >= 2:
                    mes_num = int(parts[1])
                    mes = MONTH_NAMES[mes_num - 1]
            except (ValueError, IndexError):
                pass

        pattern_entry = self.pattern_db.learn(
            pattern=descripcion,
            categoria=categoria,
            subcategoria=subcategoria,
            monto=monto,
            banco=banco,
            mes=mes,
        )

        log_entry = {
            "movement_id": movement_id,
            "descripcion": descripcion,
            "categoria": categoria,
            "subcategoria": subcategoria,
            "timestamp": datetime.now().isoformat(),
        }
        self.log.append(log_entry)
        self._save_log()

        return {
            "pattern": descripcion,
            "categoria": categoria,
            "subcategoria": subcategoria,
            "confianza": pattern_entry.get("confianza", 0),
            "veces_visto": pattern_entry.get("veces_visto", 1),
        }

    def auto_categorize_batch(
        self, movements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Autocategoriza una lista de movimientos usando IntelligentCategorizer.
        Retorna los movimientos con 'categoria', 'subcategoria' y 'confianza'
        actualizados (sólo para los que no tienen categoría o tienen baja
        confianza).
        """
        updated = []
        for mov in movements:
            desc = mov.get("descripcion", "")
            monto = mov.get("monto")
            banco = mov.get("institucion")
            fecha = mov.get("fecha")

            existing_cat = mov.get("categoria", "").strip()
            if existing_cat and existing_cat.lower() != "sin categoría":
                updated.append(mov)
                continue

            categoria, subcategoria, confianza = self.categorizer.categorize(
                descripcion=desc, monto=monto, banco=banco, fecha=fecha
            )
            mov_copy = dict(mov)
            mov_copy["categoria"] = categoria
            mov_copy["subcategoria"] = subcategoria
            mov_copy["confianza"] = confianza
            updated.append(mov_copy)

        return updated

    def get_stats(self) -> dict:
        """Retorna estadísticas del sistema de aprendizaje."""
        total_patterns = len(self.pattern_db)
        avg_conf = self.pattern_db.avg_confidence()
        top = self.pattern_db.top_patterns(10)
        recent = self.log[-100:]

        return {
            "patterns_learned": total_patterns,
            "confidence_avg": avg_conf,
            "top_patterns": top,
            "recent_learning": recent,
            "total_corrections": len(self.log),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_log(self) -> List[dict]:
        if self.log_path.exists():
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  LearningEngine: Error cargando log: {e}")
        return []

    def _save_log(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(self.log, f, ensure_ascii=False, indent=2)
