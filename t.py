from jsonlogic.core import JSONLogicExpression
from jsonlogic.registry import OperatorRegistry
from jsonlogic.operators.typechecked import typechecked_registry
from jsonlogic.operators.typechecked.base import TypecheckedOperator



# j = JSONLogicExpression.from_json({">": [{"var": "/a"}, {"var": "/b"}]})

# root_op = j.as_operator_tree(typechecked_registry)
# assert isinstance(root_op, TypecheckedOperator)

# root_type = root_op.typecheck(data_schema={
#     "type": "object",
#     "properties": {
#         "a": {"type": "integer"},
#         "b": {"type": "number"}
#     }
# })

# print(root_type)



j = JSONLogicExpression.from_json({"if": [
    {">": [{"var": "/a"}, {"var": "/b"}]}, {"var": "/a"},
    "3",
]})
root_op = j.as_operator_tree(typechecked_registry)
assert isinstance(root_op, TypecheckedOperator)

root_type = root_op.typecheck(data_schema={
    "type": "object",
    "properties": {
        "a": {"type": "integer"},
        "b": {"type": "number"}
    }
})

print(root_type)

#> BooleanType()

# root_type = root_op.typecheck(data_schema={
#     "type": "object",
#     "properties": {
#         "a": {"type": "integer"},
#         "b": {"type": "string", "format": "date-time"}
#     }
# })

#> Exception: Cannot compare integer and datetime