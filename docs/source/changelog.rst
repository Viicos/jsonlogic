=========
Changelog
=========

.. rtfc-unreleased::

   These changes are not yet released and are under active development.

.. rtfc-insert

0.2.0 (2026-08-30)
------------------

Changes
~~~~~~~

- Add support for Python 3.13 (:pr:`35`), 3.14 and 3.15, drop support for Python 3.8 and 3.9 (PR :pr:`37` by :user:`Viicos`).
- Rename the ``UnkownOperator`` exception to :class:`~jsonlogic.registry.UnknownOperator` (PR :pr:`38` by :user:`Viicos`).

Features
~~~~~~~~

- Add the ``*`` (multiply) operator, taking two or more arguments. (PR :pr:`30` by :user:`Viicos`).

  .. code-block:: python

      expr = JSONLogicExpression.from_json({"*": [2, {"var": "my_int"}, 3]})
      root_op = expr.as_operator_tree(operator_registry)

      assert evaluate(root_op, data={"my_int": 4}, data_schema=None) == 24

0.1.0 (2024-06-02)
------------------

- Initial working release. Check the docs for how to use the library.

0.0.1 (2024-03-12)
------------------

- Initial release.
