from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generic, Literal, NoReturn, TypeVar, overload

from jsonlogic._compat import Self, TypeAlias, TypeVarTuple, Unpack

JSONSchemaPrimitiveTypeT = TypeVar(
    "JSONSchemaPrimitiveTypeT",
    "AnyType",
    "BooleanType",
    "NumberType",
    "IntegerType",
    "StringType",
    "DatetimeType",
    "DateType",
    "DurationType",
    "NullType",
)
JSONSchemaTypeT = TypeVar("JSONSchemaTypeT", bound="JSONSchemaType")

BinaryOp: TypeAlias = Literal[">", ">=", "<", "<=", "+", "-", "*", "/", "%"]
UnaryOp: TypeAlias = Literal["-", "bool"]


class UnsupportedOperation(Exception):
    pass


def unpack_union(
    func: Callable[[JSONSchemaTypeT, JSONSchemaPrimitiveType, BinaryOp], JSONSchemaType], /
) -> Callable[[JSONSchemaTypeT, JSONSchemaType, BinaryOp], JSONSchemaType]:
    """A utility decorator to unpack types of :class:`UnionType` when calling :meth:`JSONSchemaType.binary_op`.

    If :paramref:`~JSONSchemaType.binary_op.other` is a :class:`UnionType`, each type of the union
    will be recursively applied to the :meth:`~JSONSchemaType.binary_op` method.
    """

    def wrapper(self: JSONSchemaTypeT, other: JSONSchemaType, op: BinaryOp) -> JSONSchemaType:
        if not isinstance(other, UnionType):
            assert isinstance(other, JSONSchemaPrimitiveType)
            return func(self, other, op)

        result_types: list[JSONSchemaType] = []
        for typ in other.types:
            result_types.append(func(self, typ, op))

        return UnionType(*result_types)

    return wrapper


class JSONSchemaType(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """The verbose name of the type to be used in diagnostic messages."""

    @abstractmethod
    def binary_op(self, other: JSONSchemaType, op: BinaryOp, /) -> JSONSchemaType:
        """Get the resulting type of the binary operation with the other provided type.

        Args:
            other: The right hand operand of the operation.
            op: The string representation of the operator.
        Returns:
            The return type of the operation.
        Raises:
            UnsupportedOperation: The operator is unsupported for the operands
        """

    @abstractmethod
    def unary_op(self, op: UnaryOp) -> JSONSchemaType:
        """Get the resulting type of the unary operation.

        Args:
            op: The string representation of the operator.
        Returns:
            The return type of the operation.
        Raises:
            UnsupportedOperation: The operator is unsupported for the current type.
        """

    @overload
    def __or__(self, value: Self, /) -> Self: ...  # type: ignore

    @overload
    def __or__(self, value: JSONSchemaType, /) -> UnionType: ...

    def __or__(self, value, /):  # type: ignore
        return UnionType(self, value)


class UnionType(JSONSchemaType):
    types: set[JSONSchemaPrimitiveType]

    @overload
    def __new__(cls, type: JSONSchemaTypeT, /) -> JSONSchemaTypeT: ...

    # In reality, this won't account for unknown subtypes (see https://github.com/python/mypy/issues/6559#issuecomment-864411598)
    @overload
    def __new__(cls, type: JSONSchemaPrimitiveTypeT, *types: JSONSchemaPrimitiveTypeT) -> JSONSchemaPrimitiveTypeT: ...

    @overload
    def __new__(cls, type: JSONSchemaType, *types: JSONSchemaType) -> Self: ...

    def __new__(cls, type, *types):
        types = [type, *types]
        if any(isinstance(t, AnyType) for t in types):
            # TODO at some point we might allow
            # smarter unions, e.g. NumberType() | IntegerType() == NumberType()
            return AnyType()
        if all(t == types[0] for t in types):
            return types[0]

        self = super().__new__(cls)
        self.types = set()

        for typ in types:
            if isinstance(typ, UnionType):
                self.types.update(typ.types)
            else:
                self.types.add(typ)
        return self

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({', '.join(repr(t) for t in self.types)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UnionType):
            return NotImplemented
        return self.types == other.types

    @property
    def name(self) -> str:
        return f"union({', '.join(t.name for t in self.types)})"

    def binary_op(self, other: JSONSchemaType, op: BinaryOp) -> JSONSchemaType:
        result_types: list[JSONSchemaType] = []
        for typ in self.types:
            if isinstance(other, UnionType):
                result_types.extend(typ.binary_op(other_typ, op) for other_typ in other.types)
            else:
                result_types.append(typ.binary_op(other, op))

        return UnionType(*result_types)

    def unary_op(self, op: UnaryOp) -> JSONSchemaType:
        return UnionType(*(typ.unary_op(op) for typ in self.types))


class JSONSchemaPrimitiveType(JSONSchemaType, ABC):
    """A JSON Schema type other than :class:`UnionType`."""


@dataclass(frozen=True)
class ArrayType(JSONSchemaPrimitiveType, Generic[JSONSchemaTypeT]):
    elements_type: JSONSchemaTypeT
    """The type of the elements of the array."""

    @property
    def name(self) -> str:
        return f"array({self.elements_type.name})"

    def binary_op(self, other: JSONSchemaType, op: BinaryOp) -> NoReturn:
        raise UnsupportedOperation

    def unary_op(self, op: UnaryOp) -> JSONSchemaType:
        if op == "bool":
            return BooleanType()
        raise UnsupportedOperation


# Bound to JSONSchemaType:
TupleTs = TypeVarTuple("TupleTs")


@dataclass(frozen=True)
class TupleType(JSONSchemaPrimitiveType, Generic[Unpack[TupleTs]]):
    # Note: `*args` could be used for ease of use (TupleType(t1, t2, ...)).
    # However, it would require a hacky workaround (https://stackoverflow.com/a/58336722)
    # and type checkers complain about unpacked arguments matching a TypeVarTuple
    tuple_types: tuple[Unpack[TupleTs]]
    """The types of the tuple."""

    @property
    def name(self) -> str:
        return f"tuple({', '.join(t.name for t in self.tuple_types)})"  # type: ignore

    def binary_op(self, other: JSONSchemaType, op: BinaryOp) -> NoReturn:
        raise UnsupportedOperation

    def unary_op(self, op: UnaryOp) -> JSONSchemaType:
        if op == "bool":
            return BooleanType()
        raise UnsupportedOperation


@dataclass(frozen=True)
class AnyType(JSONSchemaPrimitiveType):
    @property
    def name(self) -> str:
        return "any"

    def binary_op(self, other: JSONSchemaType, op: BinaryOp) -> JSONSchemaType:
        return AnyType()

    def unary_op(self, op: UnaryOp) -> JSONSchemaType:
        return AnyType()


@dataclass(frozen=True)
class BooleanType(JSONSchemaPrimitiveType):
    @property
    def name(self) -> str:
        return "boolean"

    def binary_op(self, other: JSONSchemaType, op: BinaryOp) -> NoReturn:
        raise UnsupportedOperation

    def unary_op(self, op: UnaryOp) -> JSONSchemaType:
        if op == "bool":
            return BooleanType()
        raise UnsupportedOperation


@dataclass(frozen=True)
class NumberType(JSONSchemaPrimitiveType):
    @property
    def name(self) -> str:
        return "number"

    @unpack_union
    def binary_op(self, other: JSONSchemaPrimitiveType, op: BinaryOp) -> JSONSchemaType:
        if not isinstance(other, (NumberType, IntegerType)):
            raise UnsupportedOperation
        if op in {">", ">=", "<", "<="}:
            return BooleanType()
        if op in {"+", "-", "*", "/", "%"}:
            return NumberType()
        raise UnsupportedOperation

    def unary_op(self, op: UnaryOp) -> JSONSchemaType:
        if op == "-":
            return NumberType()
        if op == "bool":
            return BooleanType()
        raise UnsupportedOperation


@dataclass(frozen=True)
class IntegerType(JSONSchemaPrimitiveType):
    @property
    def name(self) -> str:
        return "integer"

    @unpack_union
    def binary_op(self, other: JSONSchemaPrimitiveType, op: BinaryOp) -> JSONSchemaType:
        if not isinstance(other, (NumberType, IntegerType)):
            raise UnsupportedOperation
        if op in {">", ">=", "<", "<="}:
            return BooleanType()
        if op in {"+", "-", "*", "%"}:
            return IntegerType() if isinstance(other, IntegerType) else NumberType()
        if op == "/":
            return NumberType()
        raise UnsupportedOperation

    def unary_op(self, op: UnaryOp) -> JSONSchemaType:
        if op == "-":
            return IntegerType()
        if op == "bool":
            return BooleanType()
        raise UnsupportedOperation


@dataclass(frozen=True)
class StringType(JSONSchemaPrimitiveType):
    @property
    def name(self) -> str:
        return "string"

    def binary_op(self, other: JSONSchemaType, op: BinaryOp) -> NoReturn:
        raise UnsupportedOperation

    def unary_op(self, op: UnaryOp) -> JSONSchemaType:
        if op == "bool":
            return BooleanType()
        raise UnsupportedOperation


@dataclass(frozen=True)
class DatetimeType(JSONSchemaPrimitiveType):
    @property
    def name(self) -> str:
        return "datetime"

    @unpack_union
    def binary_op(self, other: JSONSchemaPrimitiveType, op: BinaryOp) -> JSONSchemaType:
        if isinstance(other, DatetimeType):
            if op in {">", ">=", "<", "<="}:
                return BooleanType()
            if op == "-":
                return DurationType()
        elif isinstance(other, DurationType) and op in {"+", "-"}:
            return DatetimeType()
        raise UnsupportedOperation

    def unary_op(self, op: UnaryOp) -> NoReturn:
        raise UnsupportedOperation


@dataclass(frozen=True)
class DateType(JSONSchemaPrimitiveType):
    @property
    def name(self) -> str:
        return "date"

    @unpack_union
    def binary_op(self, other: JSONSchemaPrimitiveType, op: BinaryOp) -> JSONSchemaType:
        if isinstance(other, DateType):
            if op in {">", ">=", "<", "<="}:
                return BooleanType()
            if op == "-":
                return DurationType()
        elif isinstance(other, DurationType) and op in {"+", "-"}:
            return DateType()
        raise UnsupportedOperation

    def unary_op(self, op: UnaryOp) -> NoReturn:
        raise UnsupportedOperation


@dataclass(frozen=True)
class DurationType(JSONSchemaPrimitiveType):
    @property
    def name(self) -> str:
        return "duration"

    @unpack_union
    def binary_op(self, other: JSONSchemaPrimitiveType, op: BinaryOp) -> JSONSchemaType:
        if isinstance(other, DurationType):
            if op in {">", ">=", "<", "<="}:
                return BooleanType()
            if op in {"+", "-"}:
                return DurationType()
        elif isinstance(other, (DatetimeType, DateType)) and op == "+":
            return type(other)()
        raise UnsupportedOperation

    def unary_op(self, op: UnaryOp) -> JSONSchemaType:
        if op == "-":
            return DurationType()
        raise UnsupportedOperation


@dataclass(frozen=True)
class NullType(JSONSchemaPrimitiveType):
    @property
    def name(self) -> str:
        return "null"

    def binary_op(self, other: JSONSchemaType, op: BinaryOp) -> NoReturn:
        raise UnsupportedOperation

    def unary_op(self, op: UnaryOp) -> JSONSchemaType:
        if op == "bool":
            return BooleanType()
        raise UnsupportedOperation
