import sys

if sys.version_info >= (3, 12):
    from typing import Self, TypeAlias, TypeAliasType
else:
    from typing_extensions import Self, TypeAlias, TypeAliasType

__all__ = ("Self", "TypeAlias", "TypeAliasType")
