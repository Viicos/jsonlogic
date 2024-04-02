from __future__ import annotations

import functools
import operator
from dataclasses import dataclass
from typing import Any, Callable, ClassVar, cast

from jsonlogic._compat import Self
from jsonlogic.core import JSONLogicSyntaxError, Operator
from jsonlogic.json_schema import as_json_schema, from_json_schema, from_value
from jsonlogic.json_schema.resolvers import Unresolvable
from jsonlogic.json_schema.types import AnyType, ArrayType, BinaryOp, BooleanType, JSONSchemaType, UnsupportedOperation
from jsonlogic.typing import OperatorArgument
from jsonlogic.utils import UNSET, UnsetType

from ..typechecking import TypecheckContext, get_type


@dataclass
class Var(Operator):
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

        resolver = context.json_schema_resolver

        default_value_type: JSONSchemaType | None
        if self.default_value is not UNSET:
            default_value_type = (
                self.default_value.typecheck(context)
                if isinstance(self.default_value, Operator)
                else from_value(self.default_value, context.settings["literal_casts"])
            )
        else:
            default_value_type = None

        try:
            schema = resolver.resolve(self.variable_path)
        except Unresolvable:
            if self.default_value is UNSET:
                context.add_diagnostic(
                    f"{self.variable_path} is unresolvable and not fallback value is provided",
                    "unresolvable_variable",
                    self,
                )
                return AnyType()

            # We emit a diagnostic but as a warning, as this will not fail at runtime
            context.add_diagnostic(
                f"{self.variable_path} is unresolvable", "unresolvable_variable", self, type="warning"
            )
            return default_value_type  # type: ignore
        else:
            js_type = from_json_schema(schema, context.settings["variable_casts"])
            if default_value_type is not None:
                return js_type | default_value_type
            return js_type


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
class Equal(EqualityOperator):
    equality_func = operator.eq


@dataclass
class NotEqual(EqualityOperator):
    equality_func = operator.ne


@dataclass
class If(Operator):
    if_elses: list[tuple[OperatorArgument, OperatorArgument]]
    leading_else: OperatorArgument

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        if len(arguments) % 2 == 0:
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
class BinaryOperator(Operator):
    operator_func: ClassVar[Callable[[Any, Any], Any]]
    operator_symbol: ClassVar[BinaryOp]

    left: OperatorArgument
    right: OperatorArgument

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        if len(arguments) != 2:
            raise JSONLogicSyntaxError(f"{operator!r} expects two arguments, got {len(arguments)}")

        return cls(operator=operator, left=arguments[0], right=arguments[1])

    def typecheck(self, context: TypecheckContext) -> JSONSchemaType:
        left_type = get_type(self.left, context)
        right_type = get_type(self.right, context)

        try:
            return left_type.binary_op(right_type, self.operator_symbol)
        except UnsupportedOperation:
            context.add_diagnostic(
                f'Operator "{self.operator_symbol}" not supported for types {left_type.name} and {right_type.name}',
                "operator",
                self,
            )

        return AnyType()

    def apply(self, data) -> bool:
        left = self.left
        if isinstance(left, Operator):
            left = left.apply(data)
        right = self.right
        if isinstance(right, Operator):
            right = right.apply(data)

        return self.operator_func(left, right)


@dataclass
class GreaterThan(BinaryOperator):
    operator_func = operator.gt
    operator_symbol = ">"


@dataclass
class GreaterThanOrEqual(BinaryOperator):
    operator_func = operator.ge
    operator_symbol = ">="


@dataclass
class LessThan(BinaryOperator):
    operator_func = operator.lt
    operator_symbol = "<"


@dataclass
class LessThanOrEqual(BinaryOperator):
    operator_func = operator.le
    operator_symbol = "<="


@dataclass
class Division(BinaryOperator):
    operator_func = operator.truediv
    operator_symbol = "/"


@dataclass
class Modulo(BinaryOperator):
    operator_func = operator.mod
    operator_symbol = "%"


@dataclass
class Plus(Operator):
    arguments: list[OperatorArgument]

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        # Having a unary + is a bit useless, but we might not error here in the future
        if not len(arguments) >= 2:
            raise JSONLogicSyntaxError(f"{operator!r} expects at least two arguments, got {len(arguments)}")
        return cls(operator=operator, arguments=arguments)

    def typecheck(self, context: TypecheckContext) -> JSONSchemaType:
        types = (get_type(obj, context) for obj in self.arguments)
        result_type = next(types)

        for i, typ in enumerate(types, start=1):
            try:
                result_type = result_type.binary_op(typ, "+")
            except UnsupportedOperation:
                if len(self.arguments) == 2:
                    msg = f'Operator "+" not supported for types {result_type.name} and {typ.name}'
                else:
                    msg = f'Operator "+" not supported for types {result_type.name} (argument {i}) and {typ.name} (argument {i + 1})'  # noqa: E501
                context.add_diagnostic(
                    msg,
                    "operator",
                    self,
                )
                return AnyType()

        return result_type


@dataclass
class Minus(Operator):
    left: OperatorArgument
    right: OperatorArgument | UnsetType = UNSET

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        if len(arguments) not in {1, 2}:
            raise JSONLogicSyntaxError(f"{operator!r} expects one or two arguments, got {len(arguments)}")

        if len(arguments) == 1:
            return cls(operator=operator, left=arguments[0])
        return cls(operator=operator, left=arguments[0], right=arguments[1])

    def typecheck(self, context: TypecheckContext) -> JSONSchemaType:
        left_type = get_type(self.left, context)
        if self.right is UNSET:
            try:
                return left_type.unary_op("-")
            except UnsupportedOperation:
                context.add_diagnostic(
                    f'Operator "-" not supported for type {left_type.name}',
                    "operator",
                    self,
                )
                return AnyType()

        right_type = get_type(self.right, context)

        try:
            return left_type.binary_op(right_type, "-")
        except UnsupportedOperation:
            context.add_diagnostic(
                f'Operator "-" not supported for type {left_type.name} and {right_type.name}',
                "operator",
                self,
            )
            return AnyType()


@dataclass
class Map(Operator):
    vars: OperatorArgument
    func: OperatorArgument

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        if len(arguments) not in {1, 2}:
            raise JSONLogicSyntaxError(f"{operator!r} expects two arguments, got {len(arguments)}")

        return cls(operator=operator, vars=arguments[0], func=arguments[1])

    def typecheck(self, context: TypecheckContext) -> JSONSchemaType:
        vars_type = get_type(self.vars, context)
        if not isinstance(vars_type, ArrayType):
            context.add_diagnostic(f"The first argument must be of type array, got {vars_type}", "argument_type", self)
            return AnyType()

        vars_type = cast(ArrayType[JSONSchemaType], vars_type)
        with context.data_stack.push(as_json_schema(vars_type.elements_type, context.settings["variable_casts"])):
            func_type = get_type(self.func, context)

        return ArrayType(func_type)
