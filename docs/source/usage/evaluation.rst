Evaluation
==========

Once our JSON Logic expression has been typechecked [#f1]_, it can be evaluated
using the utility :func:`~jsonlogic.evaluation.evaluate` function:

.. code-block:: python

    from jsonlogic import JSONLogicExpression, Operator
    from jsonlogic.evaluation import evaluate
    from jsonlogic.operators import operator_registry

    expr = JSONLogicExpression.from_json({">": [{"var": "my_int"}, 2]})

    root_op = expr.as_operator_tree(operator_registry)

    return_value = evaluate(
        root_op,
        data={"my_int": 1},
        data_schema=None,
        settings={  # Optional
            "variable_casts": {...},
        },
    )

    assert return_value is False

This function returns the evaluated expression result. Because the implementation
of the typechecking functionnality is based on the `JSON Schema`_ specification,
we assume the provided :paramref:`~jsonlogic.evaluation.evaluate.data` argument
is JSON data. When string variables are of a specific format, The
:paramref:`~jsonlogic.evaluation.evaluate.data_schema` argument is used to
know what is the corresponding format:

.. code-block:: python

    expr = JSONLogicExpression.from_json({
        ">": [
            {"var": "a_date_var"},
            "2020-01-01",
        ]
    })

    root_op = expr.as_operator_tree(operator_registry)

    return_value = evaluate(
        root_op,
        data={"a_date_var": "2024-01-01"},
        data_schema={  # Use the same schema used during typechecking.
            "type": "object",
            "properties": {
                "a_date_var": {"type": "string", "format": "date"},
            },
        },
        settings={
            "literal_casts": [date.fromisoformat],
        },
    )

    assert return_value is True

During evaluation, variables are resolved and casted to a specific type
(see :meth:`~jsonlogic.evaluation.EvaluationContext.resolve_variable`)
according to the provided JSON Schema.

.. note::

    If you are dealing with already converted data, you can pass :data:`None`
    to the :paramref:`~jsonlogic.evaluation.evaluate.data_schema` argument.
    This way, no variable cast will be performed during evaluation.

Evaluation settings
-------------------

Most of the available evaluation settings are analogous to the typechecking settings.
You can refer to the API documentation of the :class:`~jsonlogic.evaluation.EvaluationSettings`
class for more details.

.. _`JSON Schema`: https://json-schema.org/

.. rubric:: footnotes

.. [#f1] Of course you can skip this step and evaluate the expression directly.
   Do note that no runtime exception will be caught during evaluation of operators.


