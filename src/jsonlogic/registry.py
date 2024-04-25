"""The main operator registry class and related exceptions."""

from __future__ import annotations

from typing import Callable, Type, TypeVar, overload

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


OperatorType: TypeAlias = Type[Operator]

OperatorTypeT = TypeVar("OperatorTypeT", bound=Type[Operator])


class OperatorRegistry:
    """A collection of :class:`~jsonlogic.core.Operator` classes.

    Acts as a wrapper over a mapping of operator IDs to the actual class.

    .. code-block:: pycon

        >>> reg = OperatorRegistry()
        >>> reg.register("var", MyVarOperator)
        >>> reg.get("var")
        <class 'MyVarOperator'>
        >>> reg.get("unknown")
        Traceback (most recent call last):
        ...
        UnkownOperator: "unknown"
    """

    def __init__(self) -> None:
        self._registry: dict[str, OperatorType] = {}

    @overload
    def register(self, operator_id: str, *, force: bool = ...) -> Callable[[OperatorTypeT], OperatorTypeT]: ...

    @overload
    def register(self, operator_id: str, operator_type: OperatorTypeT, *, force: bool = ...) -> OperatorTypeT: ...

    def register(
        self, operator_id: str, operator_type: OperatorTypeT | None = None, *, force: bool = False
    ) -> Callable[[OperatorTypeT], OperatorTypeT] | OperatorTypeT:
        """Register an operator type under the provided ID.

        Args:
            operator_id: The ID to be used to register the operator.
            operator_type: The class object of the operator. If not provided,
                will return a callable to be applied on an operator class.
            force: Whether to override any existing operator under the provided ID.

        Raises:
            AlreadyRegistered: If :paramref:`force` wasn't set and the ID already exists.

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

            def dec(operator_type: OperatorTypeT, /) -> OperatorTypeT:
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

    def remove(self, operator_id: str, /) -> None:
        """Remove the operator from the registry.

        Args:
            operator_id: The registered ID of the operator to be removed.
        """

        self._registry.pop(operator_id, None)

    def copy(self, *, extend: OperatorRegistry | dict[str, OperatorType] | None = None, force: bool = False) -> Self:
        """Create a new instance of the registry.

        Args:
            extend: A registry or a mapping to use to register new operators
                while doing the copy.
            force: Whether to override any existing operator under the provided ID.

        Returns:
            A new instance of the registry.
        """

        new = self.__class__()
        new._registry = self._registry.copy()
        overrides = extend._registry if isinstance(extend, OperatorRegistry) else extend
        if overrides is not None:
            for id, operator in overrides.items():
                new.register(operator_id=id, operator_type=operator, force=force)
        return new
