from jsonlogic import JSONLogicExpression


def test_from_json() -> None:
    expr = JSONLogicExpression.from_json({"op": [1, {"op": 2}, [3, [4, 5]], [6, [{"op": 7}]]]})

    assert expr == JSONLogicExpression(
        {"op": [1, JSONLogicExpression({"op": [2]}), [3, [4, 5]], [6, [JSONLogicExpression({"op": [7]})]]]}
    )
