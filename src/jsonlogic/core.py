"""Base structures of the library. The two classes defined, :class:`Operator` and :class:`JSONLogicExpression`,
can be extended to provide extra functionality.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ._compat import Self, TypeAlias
from .json_schema.types import AnyType, JSONSchemaType
from .typing import JSON, JSONLogicPrimitive, OperatorArgument

if TYPE_CHECKING:
    # This is a hack to make Pylance think `TypeAlias` comes from `typing`
    from typing import TypeAlias

    from .registry import OperatorRegistry
    from .typechecking import TypecheckContext


@dataclass
class Operator(ABC):
    """The base class for all operators."""

    operator: str = field(repr=False)
    """The string representation of the operator."""

    # metadata: Any | None = None
    # """Extra metadata for this operator.

    # For any exception encountered, this will be included.
    # """

    @classmethod
    @abstractmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        """Return an instance of the operator from the list of provided arguments.

        Args:
            operator: The ID of the operator, as provided by the :class:`~jsonlogic.registry.OperatorRegistry`.
            arguments: The list of the arguments for this operator. Subclasses are responsible
                for checking the correct number of arguments and optionally the types.
        """

    # @abstractmethod
    # def evaluate(self, context: EvaluationContext) -> Any:
    #     """Evaluate the operator with the provided data."""

    def typecheck(self, context: TypecheckContext) -> JSONSchemaType:
        """Typecheck the operator (and all children) given the data schema."""

        return AnyType()


class JSONLogicSyntaxError(Exception):
    """A syntax error when building an operator tree from a :class:`JSONLogicExpression`."""

    def __init__(self, message: str, /) -> None:
        self.message = message


NormalizedExpression: TypeAlias = "dict[str, list[JSONLogicExpression]]"


@dataclass
class JSONLogicExpression:
    """A parsed and normalized JSON Logic expression.

    A JSON Logic expression can be:

    - a single item dictionary, mapping the operator key to another :class:`JSONLogicExpression`,
    - a :data:`~jsonlogic.typing.JSONLogicPrimitive`.

    All JSON Logic expressions should be instantiated using the :meth:`from_json` constructor::

        expr = JSONLogicExpression.from_json(...)
    """

    expression: JSONLogicPrimitive | NormalizedExpression

    @classmethod
    def from_json(cls, json: JSON) -> Self:  # TODO disallow list? TODO fix type errors
        """Build a JSON Logic expression from JSON data.

        Operator arguments are recursively normalized to a :class:`list`::

            expr = JSONLogicExpression.from_json({"var": "varname"})
            assert expr.expression == {"var": ["varname"]}
        """
        if not isinstance(json, dict):
            return cls(expression=json)  # type: ignore

        operator, op_args = next(iter(json.items()))
        if not isinstance(op_args, list):
            op_args = [op_args]

        sub_expressions = [cls.from_json(op_arg) for op_arg in op_args]

        return cls({operator: sub_expressions})  # type: ignore

    def as_operator_tree(self, operator_registry: OperatorRegistry) -> JSONLogicPrimitive | Operator:
        """Return a recursive tree of operators, using the provided registry as a reference.

        Args:
            operator_registry: The registry to use to resolve operator IDs.

        Returns:
            The current expression if it is a :data:`~jsonlogic.typing.JSONLogicPrimitive`
            or an :class:`Operator` instance.
        """
        if not isinstance(self.expression, dict):
            return self.expression

        op_id, op_args = next(iter(self.expression.items()))
        OperatorCls = operator_registry.get(op_id)

        return OperatorCls.from_expression(op_id, [op_arg.as_operator_tree(operator_registry) for op_arg in op_args])
