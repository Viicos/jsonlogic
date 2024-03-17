from __future__ import annotations

import functools
import operator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, ClassVar

from jsonlogic._compat import Self
from jsonlogic.core import JSONLogicSyntaxError, Operator
from jsonlogic.json_schema import from_json_schema, from_value
from jsonlogic.json_schema.resolvers import JSONSchemaPointerResolver, JSONSchemaResolver, Unresolvable
from jsonlogic.json_schema.types import AnyType, BooleanType, JSONSchemaType
from jsonlogic.typing import OperatorArgument
from jsonlogic.utils import UNSET, UnsetType

from ..typechecking import TypecheckContext, get_type

if TYPE_CHECKING:
    from _typeshed import SupportsAllComparisons


@dataclass
class Var(Operator):
    json_schema_resolver: ClassVar[type[JSONSchemaResolver]] = JSONSchemaPointerResolver

    variable_path: str | Operator

    default_value: OperatorArgument | UnsetType = UNSET

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        if len(arguments) not in {1, 2}:
            raise JSONLogicSyntaxError(f"{operator!r} expects one or two arguments, got {len(arguments)}")

        if not isinstance(arguments[0], (str, Operator)):
            raise JSONLogicSyntaxError(f"Variable path must be a string on an operator, got {type(arguments[0])}")

        if len(arguments) == 1:
            return cls(operator=operator, variable_path=arguments[0])
        return cls(operator=operator, variable_path=arguments[0], default_value=arguments[1])

    def typecheck(self, context: TypecheckContext) -> JSONSchemaType:
        if isinstance(self.variable_path, Operator):
            self.variable_path.typecheck(context)
            return AnyType()

        resolver = self.json_schema_resolver(context.data_stack)

        try:
            js_type = resolver.resolve(self.variable_path)
        except Unresolvable:
            if self.default_value is UNSET:
                context.add_diagnostic(
                    f"{self.variable_path} is unresolvable and not fallback value is provided",
                    "unresolvable_variable",
                    self,
                )
                return AnyType()
            if isinstance(self.default_value, Operator):
                return self.default_value.typecheck(context)
            return from_value(self.default_value, context.settings["literal_casts"])
        else:
            return from_json_schema(js_type, context.settings["variable_casts"])


@dataclass
class EqualityOperator(Operator):
    equality_func: ClassVar[Callable[[object, object], bool]]

    left: OperatorArgument
    right: OperatorArgument

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        if len(arguments) != 2:
            raise JSONLogicSyntaxError(f"{operator!r} expects two arguments, got {len(arguments)}")

        return cls(operator=operator, left=arguments[0], right=arguments[1])

    def typecheck(self, context: TypecheckContext) -> BooleanType:
        if isinstance(self.left, Operator):
            self.left.typecheck(context)
        if isinstance(self.right, Operator):
            self.right.typecheck(context)
        return BooleanType()


@dataclass
class EqualOperator(EqualityOperator):
    equality_func = operator.eq


@dataclass
class NotEqualOperator(EqualityOperator):
    equality_func = operator.ne


@dataclass
class IfOperator(Operator):
    if_elses: list[tuple[OperatorArgument, OperatorArgument]]
    leading_else: OperatorArgument

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        if len(arguments) % 2 == 1:
            raise JSONLogicSyntaxError(f"{operator!r} expects an odd number of arguments, got {len(arguments)}")
        return cls(operator=operator, if_elses=list(zip(arguments[::2], arguments[1::2])), leading_else=arguments[-1])

    def typecheck(self, context: TypecheckContext) -> JSONSchemaType:
        for i, (cond, _) in enumerate(self.if_elses, start=1):
            cond_type = get_type(cond, context)
            if not isinstance(cond_type, BooleanType):
                context.add_diagnostic(f"Condition {i} should be a boolean", "argument_type", self)

        return functools.reduce(operator.or_, (get_type(rv, context) for _, rv in self.if_elses)) | get_type(
            self.leading_else, context
        )


@dataclass
class ComparableOperator(Operator):
    operator_func: ClassVar[Callable[[SupportsAllComparisons, SupportsAllComparisons], bool]]

    left: OperatorArgument
    right: OperatorArgument

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        if len(arguments) != 2:
            raise JSONLogicSyntaxError(f"{operator!r} expects two arguments, got {len(arguments)}")

        return cls(operator=operator, left=arguments[0], right=arguments[1])

    def typecheck(self, context: TypecheckContext) -> BooleanType:
        left_type = get_type(self.left, context)
        right_type = get_type(self.right, context)

        if not left_type.comparable_with(right_type):
            context.add_diagnostic(f"Cannot compare {left_type.name} with {right_type.name}", "not_comparable", self)

        return BooleanType()

    def apply(self, data) -> bool:
        left = self.left
        if isinstance(left, Operator):
            left = left.apply(data)
        right = self.right
        if isinstance(right, Operator):
            right = right.apply(data)

        return self.operator_func(left, right)


@dataclass
class GreaterThan(ComparableOperator):
    operator_func = operator.gt


@dataclass
class GreaterThanOrEqual(ComparableOperator):
    operator_func = operator.ge


@dataclass
class LessThan(ComparableOperator):
    operator_func = operator.lt


@dataclass
class LessThanOrEqual(ComparableOperator):
    operator_func = operator.le
