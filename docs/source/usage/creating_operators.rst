Creating operators
==================

Every operator should be defined as an implementation of the
:class:`~jsonlogic.core.Operator` abstract base class. In this example,
we will implement the ``>`` operator.

As the base class is defined as a :func:`~dataclasses.dataclass`,
we will follow that path for our operator.

Implementing the :meth:`~jsonlogic.core.Operator.from_expression` constructor
-----------------------------------------------------------------------------

The ``>`` (*greater than*) operator should take two arguments (no more, no less).
No specific constraints have to be applied on these arguments [#f1]_.

.. code-block:: python

    from dataclasses import dataclass
    from tying import Self

    from jsonlogic import JSONLogicSyntaxError, Operator
    from jsonlogic.typing import OperatorArgument

    @dataclass
    class GreaterThan(Operator):
        # Attributes will be defined below

        @classmethod
        def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
            # Any syntax error should raise a `JSONLogicSyntaxError`:
            if len(arguments) != 2:
                raise JSONLogicSyntaxError(f"{operator!r} expects two arguments, got {len(arguments)}")

Once you have validated the provided arguments, an instance of the ``GreaterThan``
operator can be created:

.. code-block:: python

    @dataclass
    class GreaterThan(Operator):
        # Each operator defines its own attributes:
        left: OperatorArgument
        right: OperatorArgument

        @classmethod
        def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
            ...
            # We map the provided arguments to the operator's attributes:
            return cls(operator=operator, left=arguments[0], right=arguments[1])


Implementing the :meth:`~jsonlogic.core.Operator.typecheck` method
------------------------------------------------------------------

By default, the :meth:`~jsonlogic.core.Operator.typecheck` method of the base
:class:`~jsonlogic.core.Operator` class returns the type :class:`~jsonlogic.json_schema.types.AnyType`.

For more details on how JSON Schema types are represented, see :ref:`representing types`.

This method is responsible for

- typechecking the children::

    from jsonlogic.typechecking import TypecheckContext
    from jsonlogic.json_schema import from_value
    from jsonlogic.json_schema.types import BooleanType

    class GreaterThan(Operator):
        ...

        def typecheck(self, context: TypecheckContext) -> BooleanType:
            left_type = get_type(self.left, context)
            right_type = get_type(self.right, context)

  :func:`~jsonlogic.typechecking.get_type` is a utility function to typecheck
  the argument if it is an :class:`~jsonlogic.core.Operator`, or infer the type
  from the primitive value. For more details on how this inference works, see
  :ref:`converting types specifier`.

- typechecking the current operator::

    class GreaterThan(Operator):
        ...

        def typecheck(self, context: TypecheckContext) -> BooleanType:
            left_type = get_type(self.left, context)
            right_type = get_type(self.right, context)

            if not left_type.comparable_with(right_type):
                context.add_diagnostic(
                    f"Cannot compare {left_type.name} with {right_type.name}",
                    "not_comparable",
                    self
                )
            return BooleanType()

  The :class:`~jsonlogic.typechecking.TypecheckContext` object is used to emit diagnostics
  and access the JSON Schema of the data provided when using :func:`~jsonlogic.typechecking.typecheck`.

Implementing the :meth:`~jsonlogic.core.Operator.apply` method
--------------------------------------------------------------

The :meth:`~jsonlogic.core.Operator.apply` method is used to evaluate the
operator.

.. todo::

    Will need to be defined with a data stack.


.. rubric:: Footnotes

.. [#f1] You could implement some checks on the type of the provided argument,
   if it happens to be a :data:`~jsonlogic.typing.JSONLogicPrimitive` where the
   ``>`` argument doesn't make sense (arrays for instance). However, this is a
   task better suited for typechecking.
