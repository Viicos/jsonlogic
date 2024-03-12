from __future__ import annotations

import functools
import operator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, ClassVar

from jsonlogic._compat import Self
from jsonlogic.core import Operator
from jsonlogic.json_schema import from_json_schema, from_value
from jsonlogic.json_schema.resolvers import JSONSchemaPointerResolver, JSONSchemaResolver, Unresolvable
from jsonlogic.json_schema.types import AnyType, BooleanType, JSONSchemaType
from jsonlogic.typing import OperatorArgument
from jsonlogic.utils import UNSET, Unset

from .typechecking import TypecheckError, get_type

if TYPE_CHECKING:
    from _typeshed import SupportsAllComparisons


@dataclass
class Var(Operator):
    json_schema_resolver: ClassVar[type[JSONSchemaResolver]] = JSONSchemaPointerResolver

    variable_path: str | Operator

    default_value: OperatorArgument | Unset = UNSET

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        assert len(arguments) in (1, 2)
        assert isinstance(arguments[0], (str, Operator))
        if len(arguments) == 1:
            return cls(operator=operator, variable_path=arguments[0])
        return cls(operator=operator, variable_path=arguments[0], default_value=arguments[1])

    def typecheck(self, data_schema: dict[str, Any]) -> JSONSchemaType:
        if isinstance(self.variable_path, Operator):
            self.variable_path.typecheck(data_schema)
            return AnyType()

        resolver = self.json_schema_resolver(data_schema)

        try:
            js_type = resolver.resolve(self.variable_path)
            return from_json_schema(js_type)
        except Unresolvable as e:
            if isinstance(self.default_value, Unset):
                raise TypecheckError("Unresolvable reference", self) from e
            if isinstance(self.default_value, Operator):
                self.default_value.typecheck(data_schema)
                return AnyType()
            return from_value(self.default_value)


@dataclass
class EqualityOperator(Operator):
    equality_func: ClassVar[Callable[[object, object], bool]]

    left: OperatorArgument
    right: OperatorArgument

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        assert len(arguments) == 2
        return cls(operator=operator, left=arguments[0], right=arguments[1])

    def typecheck(self, data_schema: dict[str, Any]) -> JSONSchemaType:
        if isinstance(self.left, Operator):
            self.left.typecheck(data_schema)
        if isinstance(self.right, Operator):
            self.right.typecheck(data_schema)
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
        assert len(arguments) % 2 == 1
        return cls(operator=operator, if_elses=list(zip(arguments[::2], arguments[1::2])), leading_else=arguments[-1])

    def typecheck(self, data_schema: dict[str, Any]) -> JSONSchemaType:
        for cond, _ in self.if_elses:
            cond_type = get_type(cond, data_schema)
            if not isinstance(cond_type, BooleanType):
                raise TypecheckError("should be boolean", self)

        return functools.reduce(operator.or_, (get_type(rv, data_schema) for _, rv in self.if_elses)) | get_type(
            self.leading_else, data_schema
        )


@dataclass
class ComparableOperator(Operator):
    operator_func: ClassVar[Callable[[SupportsAllComparisons, SupportsAllComparisons], bool]]

    left: OperatorArgument
    right: OperatorArgument

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        assert len(arguments) == 2
        # TODO validate valid primitives (e.g. array probably not valid)
        # Maybe not necessary, `typecheck` will handle it
        return cls(operator=operator, left=arguments[0], right=arguments[1])

    def typecheck(self, data_schema: dict[str, Any]) -> JSONSchemaType:
        left_type = get_type(self.left, data_schema)
        right_type = get_type(self.right, data_schema)

        if not left_type.comparable_with(right_type):
            raise TypecheckError("Cannot compare types", self)

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
