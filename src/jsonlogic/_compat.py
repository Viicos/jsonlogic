import sys

if sys.version_info >= (3, 13):
    from typing import Self, TypeAlias, TypeIs, TypeVarTuple, Unpack
else:
    from typing import TypeAlias

    from typing_extensions import Self, TypeIs, TypeVarTuple, Unpack


__all__ = ("Self", "TypeAlias", "TypeIs", "TypeVarTuple", "Unpack")
