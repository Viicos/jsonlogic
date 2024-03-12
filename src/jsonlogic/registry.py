from typing import Callable, overload

from ._compat import Self, TypeAlias
from .core import Operator


class AlreadyRegistered(Exception):
    """The provided ID is already registered."""

    def __init__(self, operator_id: str, /) -> None:
        self.operator_id = operator_id


class UnkownOperator(Exception):
    """The provided ID does not exist in the registry."""

    def __init__(self, operator_id: str, /) -> None:
        self.operator_id = operator_id


OperatorType: TypeAlias = type[Operator]


class OperatorRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, OperatorType] = {}

    @overload
    def register(self, operator_id: str, *, force: bool = ...) -> Callable[[OperatorType], OperatorType]: ...

    @overload
    def register(self, operator_id: str, operator_type: OperatorType, *, force: bool = ...) -> OperatorType: ...

    def register(
        self, operator_id: str, operator_type: OperatorType | None = None, *, force: bool = False
    ) -> Callable[[OperatorType], OperatorType] | OperatorType:
        """Register an operator type under the provided ID.

        Args:
            operator_id: The ID to be used to register the operator.
            operator_type: Type class of the operator. If not provided,
                will return a callable to be applied on an operator class.
            force: Whether to override any existing operator under the provided ID.

        Raises:
            AlreadyRegistered: If ``force`` wasn't set and the ID already exist.

        Note:
            The method is usable as a decorator:

            .. code-block:: python
                :emphasize-lines: 5,6

                reg = OperatorRegistry()
                reg.register("==", EqualOperator)

                # Or:
                @reg.register("==")
                class EqualOperator(Operator): ...
        """

        if operator_type is None:

            def dec(operator_type: OperatorType, /) -> OperatorType:
                return self.register(operator_id, operator_type)

            return dec

        if operator_id in self._registry and not force:
            raise AlreadyRegistered(operator_id)

        self._registry[operator_id] = operator_type
        return operator_type

    def get(self, operator_id: str, /) -> OperatorType:
        """Get the operator class corresponding to the ID.

        Args:
            operator_id: The registered ID of the operator.

        Raises:
            UnkownOperator: If the provided ID does not exist.
        """
        try:
            return self._registry[operator_id]
        except KeyError:
            raise UnkownOperator(operator_id)  # noqa: B904

    def copy(self) -> Self:
        """Create a new instance of the registry."""

        new = self.__class__()
        new._registry = self._registry.copy()
        return new
