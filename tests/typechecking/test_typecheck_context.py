from __future__ import annotations

from jsonlogic._compat import Self
from jsonlogic.core import Operator
from jsonlogic.evaluation.evaluation_context import EvaluationContext
from jsonlogic.typechecking import Diagnostic, TypecheckContext
from jsonlogic.typing import OperatorArgument


class DummyOp(Operator):
    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        return cls(operator)

    def evaluate(self, context: EvaluationContext) -> None:
        return None


def test_typecheck_context():
    context = TypecheckContext({"root": "schema"}, settings={"diagnostics": {"general": "warning"}})

    assert context.current_schema == {"root": "schema"}

    op = DummyOp("")

    context.add_diagnostic("General - warning", "general", op)
    context.add_diagnostic("General - information", "general", op, type="information")
    assert context.diagnostics == [
        Diagnostic(
            message="General - warning",
            category="general",
            operator=op,
            type="warning",
        ),
        Diagnostic(
            message="General - information",
            category="general",
            operator=op,
            type="information",
        ),
    ]
