"""Shared test fixtures."""
import os

# Set BEFORE config.py imports at collection time.
os.environ.setdefault("ZFIR_JWT_SECRET", "test-secret-" + ("x" * 40))
os.environ.setdefault("ZFIR_DB_PASSWORD", "test")
