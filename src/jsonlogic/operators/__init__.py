from jsonlogic.registry import OperatorRegistry

from .operators import (
    EqualOperator,
    GreaterThan,
    GreaterThanOrEqual,
    IfOperator,
    LessThan,
    LessThanOrEqual,
    NotEqualOperator,
    Var,
)

operator_registry = OperatorRegistry()
"""The operator registry."""

operator_registry.register("var", Var)
operator_registry.register("==", EqualOperator)
operator_registry.register("!=", NotEqualOperator)
operator_registry.register("if", IfOperator)
operator_registry.register(">", GreaterThan)
operator_registry.register(">=", GreaterThanOrEqual)
operator_registry.register("<", LessThan)
operator_registry.register("<=", LessThanOrEqual)
