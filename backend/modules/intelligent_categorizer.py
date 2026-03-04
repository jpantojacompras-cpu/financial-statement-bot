from typing import Tuple, Optional
from .pattern_db import PatternDB
from .categorization_service import CategorizationService


class IntelligentCategorizer:
    """
    Motor de categorización inteligente.
    Usa PatternDB (aprendizaje) + reglas predefinidas + contexto
    (banco, mes, monto) para dar una categoría con puntuación de
    confianza 0-100.
    """

    # Rangos de montos típicos (CLP) por categoría
    AMOUNT_RANGES: dict = {
        "Inversiones": (1_000, 10_000_000),
        "Deudas": (10_000, 5_000_000),
        "Cuentas básicas": (1_000, 500_000),
        "Alimentación": (500, 200_000),
        "Movilización": (500, 100_000),
        "Salud": (1_000, 500_000),
        "Plataformas / Suscripciones": (1_000, 50_000),
        "Entretención / Deporte": (1_000, 200_000),
        "Compras": (1_000, 1_000_000),
        "Mascotas": (1_000, 200_000),
    }

    # Patrones contextuales por mes (1-indexed)
    SEASONAL_HINTS: dict = {
        1: ["Inversiones", "Deudas"],            # Enero
        6: ["Entretención / Deporte"],            # Junio
        7: ["Entretención / Deporte"],            # Julio
        12: ["Compras", "Entretención / Deporte"],# Diciembre
    }

    def __init__(
        self,
        pattern_db: PatternDB = None,
        categorization_service: CategorizationService = None,
    ):
        self.pattern_db = pattern_db if pattern_db is not None else PatternDB()
        self.cat_service = categorization_service if categorization_service is not None else CategorizationService()

    def categorize(
        self,
        descripcion: str,
        monto: float = None,
        banco: str = None,
        fecha: str = None,
    ) -> Tuple[str, str, float]:
        """
        Categoriza un movimiento.

        Returns:
            (categoria, subcategoria, confianza)  donde confianza ∈ [0, 100]
        """
        if not descripcion:
            return "Sin Categoría", "Sin Subcategoría", 0.0

        desc_lower = descripcion.lower()
        mes = self._extract_month(fecha)

        # 1. PatternDB (aprendizaje del usuario) – máxima prioridad
        pattern_match = self.pattern_db.lookup(descripcion)
        if pattern_match:
            base_conf = pattern_match.get("confianza", 0.8) * 100
            confianza = self._adjust_confidence(
                base_conf, pattern_match["categoria"], monto, banco, mes
            )
            return (
                pattern_match["categoria"],
                pattern_match["subcategoria"],
                round(confianza, 1),
            )

        # 2. Servicio de categorización existente (patrones predefinidos)
        categoria, subcategoria = self.cat_service.categorize(descripcion)

        if categoria not in ("Sin Categoría",):
            base_conf = 65.0
            confianza = self._adjust_confidence(base_conf, categoria, monto, banco, mes)
            return categoria, subcategoria, round(confianza, 1)

        # 3. Sin categoría
        return "Sin Categoría", "Sin Subcategoría", 0.0

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _adjust_confidence(
        self,
        base: float,
        categoria: str,
        monto: Optional[float],
        banco: Optional[str],
        mes: Optional[int],
    ) -> float:
        """Ajusta la confianza según contexto."""
        conf = base

        # Bonus si el monto está en el rango típico de la categoría
        if monto is not None and categoria in self.AMOUNT_RANGES:
            lo, hi = self.AMOUNT_RANGES[categoria]
            if lo <= abs(monto) <= hi:
                conf = min(conf + 5, 99)
            else:
                conf = max(conf - 10, 10)

        # Bonus estacional
        if mes is not None and mes in self.SEASONAL_HINTS:
            if categoria in self.SEASONAL_HINTS[mes]:
                conf = min(conf + 3, 99)

        return conf

    @staticmethod
    def _extract_month(fecha: Optional[str]) -> Optional[int]:
        """Extrae el número de mes de una fecha ISO (YYYY-MM-DD o similar)."""
        if not fecha:
            return None
        try:
            parts = fecha.replace("/", "-").split("-")
            if len(parts) >= 2:
                return int(parts[1])
        except (ValueError, IndexError):
            pass
        return None
