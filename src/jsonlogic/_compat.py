import sys

if sys.version_info >= (3, 13):
    from types import NoneType
    from typing import Self, TypeAlias, TypeIs, TypeVarTuple, Unpack
else:
    from typing_extensions import Self, TypeAlias, TypeIs, TypeVarTuple, Unpack

    NoneType = type(None)


__all__ = ("NoneType", "Self", "TypeAlias", "TypeIs", "TypeVarTuple", "Unpack")
