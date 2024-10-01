from __future__ import annotations

from jsonlogic.registry import OperatorRegistry

from .operators import (
    Division,
    Equal,
    GreaterThan,
    GreaterThanOrEqual,
    If,
    LessThan,
    LessThanOrEqual,
    Map,
    Minus,
    Modulo,
    Multiply,
    NotEqual,
    Plus,
    Var,
)

__all__ = (
    "Division",
    "Equal",
    "GreaterThan",
    "GreaterThanOrEqual",
    "If",
    "LessThan",
    "LessThanOrEqual",
    "Map",
    "Minus",
    "Modulo",
    "Multiply",
    "NotEqual",
    "Plus",
    "Var",
    "operator_registry",
)

operator_registry = OperatorRegistry()
"""The default operator registry."""

operator_registry.register("var", Var)
operator_registry.register("==", Equal)
operator_registry.register("!=", NotEqual)
operator_registry.register("if", If)
operator_registry.register(">", GreaterThan)
operator_registry.register(">=", GreaterThanOrEqual)
operator_registry.register("<", LessThan)
operator_registry.register("<=", LessThanOrEqual)
operator_registry.register("+", Plus)
operator_registry.register("-", Minus)
operator_registry.register("/", Division)
operator_registry.register("*", Multiply)
operator_registry.register("%", Modulo)
operator_registry.register("map", Map)
