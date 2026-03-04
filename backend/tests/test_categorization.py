"""
Tests para los módulos de IA: PatternDB, IntelligentCategorizer, LearningEngine,
y CacheManager.
"""
import json
import sys
import os
import pytest

# Allow imports from backend/modules when running from backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_pattern_db(tmp_path):
    from modules.pattern_db import PatternDB
    return PatternDB(patterns_path=str(tmp_path / "patterns.json"))


@pytest.fixture()
def tmp_learning_engine(tmp_path):
    from modules.pattern_db import PatternDB
    from modules.intelligent_categorizer import IntelligentCategorizer
    from modules.learning_engine import LearningEngine

    db = PatternDB(patterns_path=str(tmp_path / "patterns.json"))
    cat = IntelligentCategorizer(pattern_db=db)
    return LearningEngine(
        pattern_db=db,
        intelligent_categorizer=cat,
        log_path=str(tmp_path / "log.json"),
    )


@pytest.fixture()
def tmp_cache_manager(tmp_path):
    from modules.cache_manager import CacheManager
    return CacheManager(
        cache_file=str(tmp_path / "cache.json"),
        meta_file=str(tmp_path / "meta.json"),
    )


# ---------------------------------------------------------------------------
# PatternDB tests
# ---------------------------------------------------------------------------

class TestPatternDB:
    def test_learn_and_lookup(self, tmp_pattern_db):
        tmp_pattern_db.learn("exness", "Inversiones", "Trading")
        result = tmp_pattern_db.lookup("Pago EXNESS TRADING CLP")
        assert result is not None
        assert result["categoria"] == "Inversiones"

    def test_confidence_improves_with_repetition(self, tmp_pattern_db):
        for _ in range(10):
            tmp_pattern_db.learn("netflix", "Plataformas / Suscripciones", "Streaming")
        pattern = tmp_pattern_db.lookup("NETFLIX mensual")
        assert pattern["confianza"] > 0.95

    def test_forget_pattern(self, tmp_pattern_db):
        tmp_pattern_db.learn("spotify", "Plataformas / Suscripciones", "Streaming")
        assert tmp_pattern_db.forget("spotify") is True
        assert tmp_pattern_db.lookup("SPOTIFY") is None

    def test_top_patterns(self, tmp_pattern_db):
        for _ in range(5):
            tmp_pattern_db.learn("uber", "Movilización", "Transporte")
        for _ in range(3):
            tmp_pattern_db.learn("jumbo", "Alimentación", "Supermercado")
        top = tmp_pattern_db.top_patterns(2)
        assert top[0]["pattern"] == "uber"
        assert top[0]["veces_visto"] == 5

    def test_avg_confidence(self, tmp_pattern_db):
        tmp_pattern_db.learn("exness", "Inversiones", "Trading")
        tmp_pattern_db.learn("uber", "Movilización", "Transporte")
        assert 0 < tmp_pattern_db.avg_confidence() <= 1.0


# ---------------------------------------------------------------------------
# IntelligentCategorizer tests
# ---------------------------------------------------------------------------

class TestIntelligentCategorizer:
    def test_exness_always_investments(self, tmp_pattern_db):
        from modules.intelligent_categorizer import IntelligentCategorizer
        tmp_pattern_db.learn("exness", "Inversiones", "Trading")
        cat = IntelligentCategorizer(pattern_db=tmp_pattern_db)
        categoria, subcategoria, confianza = cat.categorize("EXNESS TRADING")
        assert categoria == "Inversiones"
        assert confianza > 0

    def test_unknown_description_returns_no_category(self, tmp_pattern_db):
        from modules.intelligent_categorizer import IntelligentCategorizer
        cat = IntelligentCategorizer(pattern_db=tmp_pattern_db)
        categoria, _, confianza = cat.categorize("XYZZYQUUX123")
        assert categoria == "Sin Categoría"
        assert confianza == 0.0

    def test_amount_in_range_boosts_confidence(self, tmp_pattern_db):
        from modules.intelligent_categorizer import IntelligentCategorizer
        tmp_pattern_db.learn("netflix", "Plataformas / Suscripciones", "Streaming")
        cat = IntelligentCategorizer(pattern_db=tmp_pattern_db)
        _, _, conf_in = cat.categorize("NETFLIX", monto=15_000)
        _, _, conf_out = cat.categorize("NETFLIX", monto=50_000_000)
        assert conf_in >= conf_out


# ---------------------------------------------------------------------------
# LearningEngine tests
# ---------------------------------------------------------------------------

class TestLearningEngine:
    def test_record_correction_updates_pattern_db(self, tmp_learning_engine):
        result = tmp_learning_engine.record_correction(
            movement_id="mov-001",
            descripcion="EXNESS",
            categoria="Inversiones",
            subcategoria="Trading",
        )
        assert result["categoria"] == "Inversiones"
        assert result["veces_visto"] == 1

    def test_confidence_improves_after_many_corrections(self, tmp_learning_engine):
        for _ in range(10):
            tmp_learning_engine.record_correction(
                movement_id="mov-001",
                descripcion="NETFLIX",
                categoria="Plataformas / Suscripciones",
                subcategoria="Streaming",
            )
        stats = tmp_learning_engine.get_stats()
        top = {p["pattern"]: p for p in stats["top_patterns"]}
        assert top["netflix"]["confianza"] > 0.95

    def test_auto_categorize_batch_skips_already_categorized(self, tmp_learning_engine):
        movements = [
            {"descripcion": "UBER", "categoria": "Movilización", "monto": 5000},
            {"descripcion": "NETFLIX", "categoria": "", "monto": 15000},
        ]
        result = tmp_learning_engine.auto_categorize_batch(movements)
        assert result[0]["categoria"] == "Movilización"  # untouched

    def test_get_stats_returns_expected_fields(self, tmp_learning_engine):
        tmp_learning_engine.record_correction("m1", "EXNESS", "Inversiones", "Trading")
        stats = tmp_learning_engine.get_stats()
        assert "patterns_learned" in stats
        assert "confidence_avg" in stats
        assert "top_patterns" in stats
        assert "recent_learning" in stats
        assert "total_corrections" in stats
        assert stats["patterns_learned"] == 1
        assert stats["total_corrections"] == 1


# ---------------------------------------------------------------------------
# CacheManager tests
# ---------------------------------------------------------------------------

class TestCacheManager:
    def test_cache_starts_stale(self, tmp_cache_manager):
        assert tmp_cache_manager.is_stale() is True

    def test_set_and_get_movements(self, tmp_cache_manager):
        payload = {"movimientos": [{"fecha": "2025-01-10", "monto": 5000}], "total": 1}
        tmp_cache_manager.set_movements(payload)
        result = tmp_cache_manager.get_movements()
        assert result is not None
        assert len(result["movimientos"]) == 1

    def test_invalidate_makes_cache_stale(self, tmp_cache_manager):
        payload = {"movimientos": [], "total": 0}
        tmp_cache_manager.set_movements(payload)
        assert tmp_cache_manager.is_valid() is True
        tmp_cache_manager.invalidate()
        assert tmp_cache_manager.is_stale() is True

    def test_date_index_search(self, tmp_cache_manager):
        movements = [
            {"fecha": "2025-01-10", "monto": 100},
            {"fecha": "2025-01-20", "monto": 200},
            {"fecha": "2025-02-05", "monto": 300},
        ]
        tmp_cache_manager.set_movements({"movimientos": movements})
        jan = tmp_cache_manager.search_by_date(year="2025", month="01")
        assert len(jan) == 2

    def test_upload_invalidates_cache(self, tmp_cache_manager):
        tmp_cache_manager.set_movements({"movimientos": [{"fecha": "2025-01-01"}]})
        assert tmp_cache_manager.is_valid() is True
        # Simular upload → invalidar
        tmp_cache_manager.invalidate()
        assert tmp_cache_manager.is_stale() is True
