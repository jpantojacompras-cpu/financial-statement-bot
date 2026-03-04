"""
conftest.py – Mock heavy optional dependencies so tests can run without them.
"""
import sys
from unittest.mock import MagicMock

# camelot-py is an optional PDF table extraction library. It is not required
# by the modules under test (PatternDB, IntelligentCategorizer, LearningEngine,
# CacheManager) but is imported transitively via modules/__init__.py →
# file_reader.py. Mock it here so the tests can run in environments where
# camelot is not installed.
if "camelot" not in sys.modules:
    sys.modules["camelot"] = MagicMock()
