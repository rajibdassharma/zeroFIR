"""Import every model here so Base.metadata knows about all tables.

Never remove entries. Migration authors reference Base.metadata for
schema inspection, and seed.py's Base.metadata.create_all needs all
models registered.
"""
from models.user import User

__all__ = ["User"]
