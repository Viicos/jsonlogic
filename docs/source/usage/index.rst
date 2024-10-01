.. _usage:

Usage
=====

``python-jsonlogic`` builds on top of the existing `JsonLogic`_ implementation
and provides useful features to make it sane and extensible. To describe the data object
used by JSON Logic expressions, the `JSON Schema`_ specification is used.

To work with a JSON Logic expression, it must be parsed as a :class:`~jsonlogic.core.JSONLogicExpression`:

.. code-block:: python

    from jsonlogic import JSONLogicExpression

    expr = JSONLogicExpression.from_json({">": [{"var": "my_int"}, 2]})

By using the :meth:`~jsonlogic.core.JSONLogicExpression.from_json` constructor, the JSON
expression will be recursively parsed, and operator arguments will be normalized to a list
if necessary. The underlying expression can be accessed:

.. code-block:: pycon

    >>> expr.expression
    {
        '>': [
            JSONLogicExpression(expression={'var': ['my_int']}),  # "my_int" argument as a list
            2
        ]
    }

At this stage, the parsed expression doesn't have any knowledge about the operators being used.
To do so, an :class:`~jsonlogic.registry.OperatorRegistry` can be used to then build an operator
tree from the constructed expression:

.. code-block:: python

    from jsonlogic import Operator
    from jsonlogic.registry import OperatorRegistry

    registry = OperatorRegistry()

    @registry.register("var")
    class Var(Operator):
        ...

    @registry.register(">")
    class GreaterThan(Operator):
        ...

    assert registry.get("var") is Var

This allows using any operator set you'd like when evaluating an expression. ``python-jsonlogic``
provides a default set of operators, but it *purposely differs* from the available operators
on the `JsonLogic`_ website. In the future, a matching implementation of these operators might
be provided to ease transition from the already existing implementations.

By making use of this default operator registry, we will construct our operator tree:

.. code-block:: pycon

    >>> from jsonlogic.operators import operator_registry
    >>> root_op = expr.as_operator_tree(operator_registry)
    >>> root_op
    GreaterThan(left=Var(variable_path='my_int', default_value=UNSET), right=2)

When calling :meth:`~jsonlogic.core.JSONLogicExpression.as_operator_tree`, operator instances
will be recursively created using :meth:`~jsonlogic.core.Operator.from_expression`. This method
receives two arguments:

- :paramref:`~jsonlogic.core.Operator.from_expression.operator`: The string representation of the operator.
- :paramref:`~jsonlogic.core.Operator.from_expression.arguments`: The list of arguments for this operator.
  This can either be another :class:`~jsonlogic.core.Operator` or a :data:`~jsonlogic.typing.JSONLogicPrimitive`.

.. warning::

    Each operator is responsible for checking the provided arguments. For example, the ``GreaterThan`` operator
    used in the code example above expects two arguments, and should raise
    a :exc:`~jsonlogic.core.JSONLogicSyntaxError` otherwise. It is thus recommended to catch any
    potential exceptions when calling :meth:`~jsonlogic.core.JSONLogicExpression.as_operator_tree`.

From there, you are guaranteed to work with a **syntactically valid** JSON Logic expression.
The next sections will go over typechecking and evaluating the expression.

.. toctree::
    :maxdepth: 2

    resolving_variables
    typechecking
    evaluation
    creating_operators

.. _`JsonLogic`: https://jsonlogic.com/
.. _`JSON Schema`: https://json-schema.org/
