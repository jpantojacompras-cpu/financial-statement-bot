import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


PATTERNS_PATH = Path("backend/data/patterns.json")

# Confidence scoring constants
_BASE_CONFIDENCE = 0.5        # Minimum confidence for a new pattern
_CONFIDENCE_INCREMENT = 0.05  # Per-observation confidence increase
_MAX_CONFIDENCE = 0.99        # Ceiling for learned confidence


class PatternDB:
    """
    Base de datos de patrones aprendidos con confianza.
    Almacena patrones de descripción → categoría con estadísticas.
    """

    def __init__(self, patterns_path: str = None):
        self.patterns_path = Path(patterns_path) if patterns_path else PATTERNS_PATH
        self.patterns: Dict[str, dict] = self._load()

    def _load(self) -> Dict[str, dict]:
        if self.patterns_path.exists():
            try:
                with open(self.patterns_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  PatternDB: Error cargando patrones: {e}")
        return {}

    def _save(self):
        self.patterns_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.patterns_path, "w", encoding="utf-8") as f:
            json.dump(self.patterns, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def learn(
        self,
        pattern: str,
        categoria: str,
        subcategoria: str,
        monto: float = None,
        banco: str = None,
        mes: str = None,
    ) -> dict:
        """Registra o actualiza un patrón aprendido."""
        key = pattern.lower().strip()
        existing = self.patterns.get(key, {})

        veces = existing.get("veces_visto", 0) + 1
        confianza = min(_MAX_CONFIDENCE, _BASE_CONFIDENCE + veces * _CONFIDENCE_INCREMENT)

        montos_tipicos: List[float] = existing.get("montos_tipicos", [])
        if monto is not None:
            montos_tipicos = (montos_tipicos + [monto])[-50:]  # keep last 50

        bancos: List[str] = existing.get("bancos", [])
        if banco and banco not in bancos:
            bancos.append(banco)

        meses: List[str] = existing.get("meses", [])
        if mes and mes not in meses:
            meses.append(mes)

        self.patterns[key] = {
            "categoria": categoria,
            "subcategoria": subcategoria,
            "veces_visto": veces,
            "confianza": round(confianza, 4),
            "montos_tipicos": montos_tipicos,
            "bancos": bancos,
            "meses": meses,
            "last_updated": datetime.now().isoformat(),
        }
        self._save()
        return self.patterns[key]

    def lookup(self, descripcion: str) -> Optional[dict]:
        """Busca el patrón más relevante para una descripción."""
        desc_lower = descripcion.lower()
        best_match = None
        best_len = 0
        for key, data in self.patterns.items():
            if key in desc_lower and len(key) > best_len:
                best_len = len(key)
                best_match = data
        return best_match

    def forget(self, pattern: str) -> bool:
        """Elimina un patrón aprendido."""
        key = pattern.lower().strip()
        if key in self.patterns:
            del self.patterns[key]
            self._save()
            return True
        return False

    def all_patterns(self) -> Dict[str, dict]:
        return dict(self.patterns)

    def top_patterns(self, n: int = 10) -> List[dict]:
        """Retorna los N patrones más vistos."""
        sorted_patterns = sorted(
            self.patterns.items(),
            key=lambda x: x[1].get("veces_visto", 0),
            reverse=True,
        )
        return [{"pattern": k, **v} for k, v in sorted_patterns[:n]]

    def avg_confidence(self) -> float:
        if not self.patterns:
            return 0.0
        total = sum(p.get("confianza", 0) for p in self.patterns.values())
        return round(total / len(self.patterns), 4)

    def __len__(self) -> int:
        return len(self.patterns)
