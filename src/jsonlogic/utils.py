from typing import Literal


class Unset:
    """A class representing an unset value."""

    def __bool__(self) -> Literal[False]:
        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}()"


UNSET: Unset = Unset()
