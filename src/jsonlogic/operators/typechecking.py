from typing import Any

from jsonlogic.core import Operator
from jsonlogic.json_schema import from_value
from jsonlogic.json_schema.types import JSONSchemaType
from jsonlogic.typing import OperatorArgument


def get_type(obj: OperatorArgument, data_schema: dict[str, Any]) -> JSONSchemaType:
    return obj.typecheck(data_schema) if isinstance(obj, Operator) else from_value(obj)


class TypecheckError(Exception):
    def __init__(self, message: str, operator: Operator, /) -> None:
        self.operator = operator
        self.message = message
