from __future__ import annotations

from jsonlogic.registry import OperatorRegistry

from .operators import (
    DivisionOperator,
    EqualOperator,
    GreaterThan,
    GreaterThanOrEqual,
    IfOperator,
    LessThan,
    LessThanOrEqual,
    MinusOperator,
    ModuloOperator,
    NotEqualOperator,
    PlusOperator,
    Var,
)

__all__ = ("operator_registry",)

operator_registry = OperatorRegistry()
"""The default operator registry."""

operator_registry.register("var", Var)
operator_registry.register("==", EqualOperator)
operator_registry.register("!=", NotEqualOperator)
operator_registry.register("if", IfOperator)
operator_registry.register(">", GreaterThan)
operator_registry.register(">=", GreaterThanOrEqual)
operator_registry.register("<", LessThan)
operator_registry.register("<=", LessThanOrEqual)
operator_registry.register("+", PlusOperator)
operator_registry.register("-", MinusOperator)
operator_registry.register("/", DivisionOperator)
operator_registry.register("%", ModuloOperator)
