================
python-jsonlogic
================

|Pythons| |PyPI| |Ruff|

.. |Pythons| image:: https://img.shields.io/pypi/pyversions/python-jsonlogic.svg
  :alt: Supported Python versions
  :target: https://pypi.org/project/python-jsonlogic/

.. |PyPI| image:: https://img.shields.io/pypi/v/python-jsonlogic.svg
  :alt: PyPI - Version
  :target: https://pypi.org/project/python-jsonlogic/

.. |Ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
  :alt: PyPI - Version
  :target: https://github.com/astral-sh/ruff

``python-jsonlogic`` is an extensible and sane implementation of `JsonLogic`_, making use of the `JSON Schema`_ specification.

.. _`JSON Schema`: https://json-schema.org/

Motivation
----------

While the `JsonLogic`_ format can be great to serialize logic, it lacks a formal specification
and some aspects are unclear/unspecified:

* `operators <https://jsonlogic.com/operations.html>`_ arguments can take any value. For instance,
  `comparison operators <https://jsonlogic.com/operations.html#---and->`_ are said to work with "numeric" values,
  however the `JavaScript playground <https://jsonlogic.com/play.html>`_ doesn't validate inputs. It is
  also convenient to allow such comparison operators for date and datetime objects as well.
* Operators `accessing data <https://jsonlogic.com/operations.html#accessing-data>`_ use a dot-like notation,
  which is ambiguous when dealing with keys such as ``my.key``.
* Operators such as `map <https://jsonlogic.com/operations.html#map-reduce-and-filter>`_ provides their own data scope,
  making it impossible to access higher-level data inside the operator expression.

For these reasons, ``python-jsonlogic`` provides a way to typecheck your JSON Logic expressions at "compile" time,
before applying input data to them.

.. _`JsonLogic`: https://jsonlogic.com/

Installation
------------

From PyPI:

.. code:: bash

    pip install python-jsonlogic

The library can be imported from the ``jsonlogic`` module.

Usage
-----

.. code-block:: python

    # 1. Create or use an already existing operator registry:
    from jsonlogic.operators import operator_registry

    # 2. Parse the JSON Logic expression:
    from jsonlogic import JSONLogicExpression

    expr = JSONLogicExpression.from_json({">": [{"var": "my_int"}, 2]})

    # 3. Create an operator tree:
    root_op = expr.as_operator_tree(operator_registry)

    # 4. Typecheck the expression:
    from jsonlogic.typechecking import typecheck

    typ, diagnostics = typecheck(
        root_op,
        data_schema={
          "type": "object",
          "properties": {
                "my_int": {"type": "integer"}
            },
        }
    )
    print(typ)
    #> BooleanType()

    # 5. Evaluate with data:
    from jsonlogic.evaluation import evaluate
    value = evaluate(
        root_op,
        data={"my_int": 3},
        data_schema=None,
    )
    print(value)
    #> True
