"""Human-readable rendering for Pydantic v2 validation errors.

Ported from CyberFraud. Turns raw entries like:

    {"type": "string_too_long", "loc": ["body", "complainant", "phone"],
     "msg": "String should have at most 10 characters",
     "ctx": {"max_length": 10}}

into plain sentences the operator can act on. The field-label
dictionary starts small in Phase 0 and grows as domain fields land
in later phases.
"""
from __future__ import annotations

from typing import Any


# Field labels for zeroFIR. Extend as Phase 1+ fields land.
LABELS: dict[str, str] = {
    "username": "Username",
    "password": "Password",
    "full_name": "Full Name",
    "email": "Email",
    "mobile": "Mobile",
    "role": "Role",
}


_PLACEHOLDERS = ("n", "m", "o", "p")


def _pattern_key_and_positions(loc: tuple[Any, ...]) -> tuple[str, list[int]]:
    parts = [p for p in loc if p != "body"]
    positions: list[int] = []
    key_parts: list[str] = []
    for p in parts:
        if isinstance(p, int):
            positions.append(p)
            if key_parts:
                key_parts[-1] += "[]"
        else:
            key_parts.append(str(p))
    return ".".join(key_parts), positions


def _label_for_loc(loc: tuple[Any, ...]) -> str:
    key, positions = _pattern_key_and_positions(loc)
    if key in LABELS:
        label = LABELS[key]
        for i, pos in enumerate(positions):
            if i < len(_PLACEHOLDERS):
                label = label.replace("{" + _PLACEHOLDERS[i] + "}", str(pos + 1))
        return label
    parts = [p for p in loc if p != "body"]
    words: list[str] = []
    for p in parts:
        if isinstance(p, int):
            words.append(f"#{p + 1}")
        else:
            words.append(str(p).replace("_", " ").title())
    return " ".join(words) if words else "Value"


def _clause_for_type(err_type: str, msg: str, ctx: dict) -> str:
    if err_type == "missing":
        return "is required."
    if err_type == "string_too_short":
        n = ctx.get("min_length")
        return f"must be at least {n} characters long." if n else "is too short."
    if err_type == "string_too_long":
        n = ctx.get("max_length")
        return f"must be at most {n} characters long." if n else "is too long."
    if err_type in ("string_pattern_mismatch", "pattern"):
        return "is not in the correct format."
    if err_type in ("int_parsing", "int_type", "int_from_float"):
        return "must be a whole number."
    if err_type in ("float_parsing", "decimal_parsing", "float_type"):
        return "must be a number."
    if err_type in ("date_from_datetime_parsing", "date_parsing", "date_type"):
        return "must be a valid date."
    if err_type == "greater_than_equal":
        return f"must be {ctx.get('ge')} or greater."
    if err_type == "less_than_equal":
        return f"must be {ctx.get('le')} or less."
    if err_type == "greater_than":
        return f"must be greater than {ctx.get('gt')}."
    if err_type == "less_than":
        return f"must be less than {ctx.get('lt')}."
    if err_type == "value_error":
        stripped = msg.removeprefix("Value error, ")
        return stripped if stripped.endswith(".") else stripped + "."
    if err_type == "type_error":
        return "has an invalid value."
    if err_type in ("enum", "literal_error"):
        expected = ctx.get("expected")
        return f"must be one of: {expected}." if expected else "must be one of the allowed values."
    if err_type == "email":
        return "is not a valid email address."
    return (msg[:1].lower() + msg[1:] + ".") if msg else "is invalid."


def to_friendly(errors: list[dict]) -> list[str]:
    out: list[str] = []
    for err in errors:
        loc = tuple(err.get("loc", ()))
        etype = str(err.get("type", ""))
        msg = str(err.get("msg", ""))
        ctx = err.get("ctx") or {}
        label = _label_for_loc(loc)
        clause = _clause_for_type(etype, msg, ctx)
        out.append(f"{label} {clause}".strip())
    return out
