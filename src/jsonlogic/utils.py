from __future__ import annotations

import enum
from contextlib import contextmanager
from typing import Generic, Iterator, Literal, TypeVar

from ._compat import TypeAlias


class _UnsetTypeEnum(enum.Enum):
    UNSET = enum.auto()

    def __repr__(self) -> str:
        return "UNSET"


UNSET = _UnsetTypeEnum.UNSET
"""A sentinel value representing an unset (or not provided) value."""

UnsetType: TypeAlias = Literal[UNSET]
"""The type of the :data:`UNSET` sentinel value."""


DataT = TypeVar("DataT")


class DataStack(Generic[DataT]):
    def __init__(self, root_data: DataT | UnsetType = UNSET) -> None:
        self._stack = []
        if root_data is not UNSET:
            self._stack.append(root_data)

    @property
    def tail(self) -> DataT:
        return self._stack[-1]

    def get(self, index: int, /) -> DataT:
        return self._stack[-index - 1]

    @contextmanager
    def push(self, data: DataT) -> Iterator[None]:
        self._stack.append(data)

        try:
            yield
        finally:
            self._stack.pop()
