from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from tree_sitter import Language, Node, Parser

from jsonlogic._compat import Self, TypeAlias
from jsonlogic.core import JSONLogicExpression
from jsonlogic.typing import JSON

JSON_LANGUAGE = Language(str(Path(__file__).parent / "json.so"), "json")

json_parser = Parser()
json_parser.set_language(JSON_LANGUAGE)


@dataclass
class NodeType:
    type: str


ObjectNode: TypeAlias = Annotated[Node, NodeType("object")]


@dataclass
class ASTJSONLogicExpression(JSONLogicExpression):
    node: ObjectNode | None = None

    @classmethod
    def from_json_source(cls, s: str | bytes) -> Self:
        tree = json_parser.parse(s.encode("utf-8") if isinstance(s, str) else s)
        json_data = json.loads(s)
        return cls._from_json_and_nodes(json_data, tree.root_node.children[0])

    @classmethod
    def _from_json_and_nodes(cls, json: JSON, node: ObjectNode) -> Self:
        if not isinstance(json, dict):
            return cls(expression=json)

        operator, op_args = next(iter(json.items()))
        if not isinstance(op_args, list):
            op_args = [op_args]

        # children[1] is pair, children[2] is pair value:
        op_args_node = node.children[1].children[2]

        if op_args_node.type != "array":
            # operation argument was normalized to a list, so len(op_args) == 1:
            sub_expressions = [cls._from_json_and_nodes(op_args[0], op_args_node)]
        else:
            sub_expressions_args = zip(op_args, op_args_node.children[1::2])
            sub_expressions = [
                cls._from_json_and_nodes(op_arg, op_arg_node) for op_arg, op_arg_node in sub_expressions_args
            ]

        return cls({operator: sub_expressions}, node)

    def as_operator_tree(self, operator_registry):
        """Return a recursive tree of operators, using from the provided registry.

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

        return OperatorCls.from_expression(
            op_id, [op_arg.as_operator_tree(operator_registry) for op_arg in op_args], metadata=self.node
        )
