from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Literal, TypeAlias, TypeVar, overload

from jsonlogic._compat import Self

JSONSchemaPrimitiveType: TypeAlias = (
    "AnyType | BooleanType | NumberType | StringType | DatetimeType | DateType | NullType"
)

JSONSchemaPrimitiveTypeT = TypeVar(
    "JSONSchemaPrimitiveTypeT",
    "AnyType",
    "BooleanType",
    "NumberType",
    "IntegerType",
    "StringType",
    "DatetimeType",
    "DateType",
    "NullType",
)


class JSONSchemaType(ABC):
    name: ClassVar[str]
    """The verbose name of the type to be used in diagnostic messages."""

    @abstractmethod
    def comparable_with(self, other: JSONSchemaType) -> bool:
        """Whether the provided type is comparable with the current type."""

    @overload
    def __or__(self, value: Self, /) -> Self: ...  # type: ignore

    @overload
    def __or__(self, value: JSONSchemaType, /) -> UnionType: ...

    def __or__(self, value, /):  # type: ignore
        return UnionType(self, value)


class UnionType(JSONSchemaType):
    name: ClassVar[str] = "union"

    types: set[JSONSchemaPrimitiveType]

    @overload
    def __new__(cls, *types: JSONSchemaPrimitiveTypeT) -> JSONSchemaPrimitiveTypeT: ...

    @overload
    def __new__(cls, *types: JSONSchemaType) -> Self: ...

    def __new__(cls, *types):
        if all(isinstance(t, type(types[0])) for t in types):
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
        return f"{self.__class__.__qualname__}({', '.join(str(t) for t in self.types)})"

    def comparable_with(self, other: JSONSchemaType) -> bool:
        for typ in self.types:
            if isinstance(other, UnionType):
                comparable = all(other_typ.comparable_with(typ) for other_typ in other.types)
            else:
                comparable = other.comparable_with(typ)
            if not comparable:
                return False
        return True


@dataclass(frozen=True)
class AnyType(JSONSchemaType):
    name: ClassVar[str] = "any"

    def comparable_with(self, other: JSONSchemaType) -> Literal[False]:
        return False


@dataclass(frozen=True)
class BooleanType(JSONSchemaType):
    name: ClassVar[str] = "boolean"

    def comparable_with(self, other: JSONSchemaType) -> Literal[False]:
        return False


@dataclass(frozen=True)
class NumberType(JSONSchemaType):
    name: ClassVar[str] = "number"

    def comparable_with(self, other: JSONSchemaType) -> bool:
        if isinstance(other, UnionType):
            return other.comparable_with(self)
        return isinstance(other, (NumberType, IntegerType))


@dataclass(frozen=True)
class IntegerType(JSONSchemaType):
    name: ClassVar[str] = "integer"

    def comparable_with(self, other: JSONSchemaType) -> bool:
        if isinstance(other, UnionType):
            return other.comparable_with(self)
        return isinstance(other, (NumberType, IntegerType))


@dataclass(frozen=True)
class StringType(JSONSchemaType):
    name: ClassVar[str] = "string"

    def comparable_with(self, other: JSONSchemaType) -> Literal[False]:
        return False


@dataclass(frozen=True)
class DatetimeType(JSONSchemaType):
    name: ClassVar[str] = "datetime"

    def comparable_with(self, other: JSONSchemaType) -> bool:
        if isinstance(other, UnionType):
            return other.comparable_with(self)
        # Probably doesn't make sense with date?
        return isinstance(other, DatetimeType)


@dataclass(frozen=True)
class DateType(JSONSchemaType):
    name: ClassVar[str] = "date"

    def comparable_with(self, other: JSONSchemaType) -> bool:
        if isinstance(other, UnionType):
            return other.comparable_with(self)
        return isinstance(other, DateType)


@dataclass(frozen=True)
class NullType(JSONSchemaType):
    name: ClassVar[str] = "null"

    def comparable_with(self, other: JSONSchemaType) -> Literal[False]:
        return False
