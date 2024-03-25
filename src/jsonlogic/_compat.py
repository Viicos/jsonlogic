import sys

if sys.version_info >= (3, 11):
    from types import NoneType
    from typing import Self, TypeAlias, TypeVarTuple, Unpack
else:
    from typing_extensions import Self, TypeAlias, TypeVarTuple, Unpack

    NoneType = type(None)


__all__ = ("NoneType", "Self", "TypeAlias", "TypeVarTuple", "Unpack")
