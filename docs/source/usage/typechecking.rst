Typechecking
============

To avoid any runtime type errors when evaluating a JSON Logic expression,
``python-jsonlogic`` provides a *typechecking* mechanism, based on the `JSON Schema`_
specification.

This typechecking implementation is configurable to some extent, and was built
with editor integration in mind. Typechecking an operator tree will result in a list
of :class:`~jsonlogic.typechecking.Diagnostic`, emitted by the operators of the tree.

To typecheck an operator tree, the utility :func:`~jsonlogic.typechecking.typecheck` function
can be used:

.. code-block:: python

    from jsonlogic import JSONLogicExpression, Operator
    from jsonlogic.json_schema.types import BooleanType
    from jsonlogic.operators import operator_registry
    from jsonlogic.typechecking import typecheck

    expr = JSONLogicExpression.from_json({">": [{"var": "my_int"}, 2]})

    root_op = expr.as_operator_tree(operator_registry)
    assert isinstance(root_op, Operator)

    root_type, diagnostics = typecheck(
        root_op,
        data_schema={
            "type": "object",
            "properties": {
                "my_int": {"type": "integer"},
            },
        },
        settings={  # Optional
            "diagnostics": {"argument_type": "warning"},
        }
    )
    assert root_type == BooleanType()

This function returns a two-tuple, containing:

- The type returned by the operator (see :ref:`representing types`).
- The list of emitted diagnostics.

For more information on the structure of diagnostics and the related configuration,
refer to the :ref:`diagnostics` section.

.. _representing types:

Representing types
------------------

The :mod:`jsonlogic.json_schema.types` module defines a fixed representation of the possible
JSON Schema types. The primitive types are represented (e.g. :class:`~jsonlogic.json_schema.types.BooleanType`),
but the module extends on the different `formats <https://json-schema.org/understanding-json-schema/reference/string#format>`_
to allow operators to work with specific formats (e.g. ``"date"`` and ``"date-time"``).

Compound types
^^^^^^^^^^^^^^

Compound types are also supported to some extent. This includes:

- Union types::

    from jsonlogic.json_schema.types import BooleanType, NullType, UnionType

    bool_or_null = BooleanType() | NullType()

    assert UnionType(BooleanType(), NullType()) == bool_or_null

  with some heuristics implemented::

      assert UnionType(NullType(), NullType()) == NullType()

- Array types::

    from jsonlogic.json_schema.types import ArrayType, IntegerType

    array = ArrayType(IntegerType())

  `tuples <https://json-schema.org/understanding-json-schema/reference/array#tupleValidation>`_ are also supported::

      from jsonlogic.json_schema.types import BooleanType, IntegerType, TupleType

      tup = TupleType((BooleanType(), IntegerType()))

.. _converting types specifier:

Converting types from a ``"format"`` specifier
----------------------------------------------

The need for a ``"format"`` specifier in the `JSON Schema`_ specification comes
from the lack of these types in the JSON format.

When evaluating a JSON Logic expression, it might be beneficial to allow specific
operations on some formats:

.. code-block:: json

    {
        ">": [
            "2023-01-01",
            "2000-01-01"
        ]
    }

Without any type coercion to a :class:`~jsonlogic.json_schema.types.DatetimeType`,
this expression would fail to typecheck (and evaluate), as the ``">"`` operator
is not applicable on strings. To overcome this issue, we have two solutions:

- Define a ``"as_date"`` operator, that would convert the string to a :class:`datetime.date`
  object:

  .. code-block:: json

    {
        ">": [
            {"as_date": "2023-01-01"},
            {"as_date": "2023-01-01"}
        ]
    }

  While this makes sense for literals in the expression, it feels redundant for a variable
  already defined as ``"format": "date"`` in the data JSON Schema:

  .. code-block:: json

    {
        ">": [
            {"as_date": {"var": "a_date_var"}},
            {"as_date": "2023-01-01"}
        ]
    }

- Apply type inference on the format of the string. When using the
  :func:`~jsonlogic.typechecking.typecheck` function, inference can be configured
  for literals in the expression *and* data variables. The next sections will
  describe how this inference can be configured.


Inference for literals
^^^^^^^^^^^^^^^^^^^^^^

The :attr:`~jsonlogic.typechecking.TypecheckSettings.literal_casts` configuration value
can be used to express how inference should work when a string literal is encountered::

    from datetime import datetime, date

    from jsonlogic.json_schema.types import DatetimeType, DateType

    typecheck(
        root_op,
        data_schema={...},
        settings={
            "literal_casts": {
                datetime.fromisoformat: DatetimeType,
                date.fromisoformat: DateType,
            }
        }
    )

With this configuration, whenever a string literal will be encountered during typechecking,
every function defined in ``"literal_casts"`` will be called, until one of them doesn't raise
any exception (generally a :exc:`ValueError`).

The default value for :attr:`~jsonlogic.typechecking.TypecheckSettings.literal_casts` is an empty
:class:`dict`, meaning no literal cast will be attempted.

.. warning::

    Using this feature might lead to unwanted behavior, especially if the intent
    was to have the ISO formatted date treated as a string. For this reason, no
    default value is provided for this setting.

Inference for JSON Schema data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Similarly, any JSON Schema with a specific format can be inferred to a specific type.
The :attr:`~jsonlogic.typechecking.TypecheckSettings.variable_casts` controls this behavior::

    from jsonlogic.json_schema.types import DatetimeType, DateType

    typecheck(
        root_op,
        data_schema={...},
        settings={
            "variable_casts": {
                "date-time": DatetimeType,
                "date": DateType,
            }
        }
    )

Whenever a JSON Schema attribute with a format present in ``"variable_casts"`` is encountered,
the matching JSON Schema type will be returned (assuming this attribute is of type ``"string"``).

.. note::

    :attr:`~jsonlogic.typechecking.TypecheckSettings.literal_casts` is only relevant when
    encountering a literal value in a JSON Logic expression. For instance, when evaluating
    :json:`{">" ["2021-01-01", "2020-01-01"]}` with :attr:`~jsonlogic.typechecking.TypecheckSettings.literal_casts`
    set to :python:`{date.fromisoformat: DateType}`, the expression will successfully typecheck
    (and evaluate to :data:`True`).

    :attr:`~jsonlogic.typechecking.TypecheckSettings.variable_casts`, on the other hand, is only
    used when accessing data. For instance, when evaluating :json:`{"var": "/date_var"}` and
    ``date_var`` is described by the JSON Schema :json:`{"type": "string", "format": "date"}`,
    using :python:`{"date": DateType}` for :attr:`~jsonlogic.typechecking.TypecheckSettings.variable_casts`
    will typecheck to :python:`DateType`.

.. _diagnostics:

Diagnostics
-----------

A diagnostic is defined by four values:

- A :attr:`~jsonlogic.typechecking.Diagnostic.message`: a description of the diagnostic.
- A :attr:`~jsonlogic.typechecking.Diagnostic.category`, e.g. ``"argument_type"``
  when the provided argument(s) type(s) does not match what is expected.
- A :attr:`~jsonlogic.typechecking.Diagnostic.type`: the type of the diagnostic (i.e.
  ``"error"``, ``"warning"`` or ``"information"``).
- An :attr:`~jsonlogic.typechecking.Diagnostic.operator`: which operator emitted
  this diagnostic.

When using the :func:`~jsonlogic.typechecking.typecheck` function, the default
type for each category can be customized::

    typecheck(
        root_op,
        data_schema={...},
        settings={
            "diagnostics": {
                "argument_type": "warning",
                "not_comparable": None,
            }
        }
    )

.. _`JSON Schema`: https://json-schema.org/
