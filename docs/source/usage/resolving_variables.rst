Resolving variables
===================

In the original `JsonLogic`_ format, operators `accessing data <https://jsonlogic.com/operations.html#accessing-data>`_
use a dot-like notation. With the following expression:

.. code-block:: json

    {"var": "some.var"}

and the following data:

.. code-block:: json

    {
        "some": {
            "var": 1
        }
    }

the expression will evaluate to :json:`1`. However, this dot-like notation can be ambiguous:

- As the empty string :json:`""` is special cased to refer to the entire data object, it is impossible
  to refer to :json:`1` with the following data:

  .. code-block:: json

      {
          "": 1
      }

  as the reference :json:`""` would evaluate to :json:`{"": 1}`, and :json:`"."` could be parsed as a reference to :json:`{"": {"": 1}}`.

- There is no way to escape dots if present in data keys. The reference :json:`"some.var"` could refer to both
  :json:`1` and :json:`2` with the following data:

  .. code-block:: json

      {
          "some": {
              "var": 1
          },
          "some.var": 2
      }

For this reason, an alternative format is proposed, based on the JSON Pointer standard (:rfc:`6901`).

With the following data:

.. code-block:: json

    {
        "path": 1,
        "": 2,
        "": {"": 3},
        "path.to": 4,
        "path/": 5
    }

this is how the references will evaluate:

.. code-block:: bash

    {"var": "/path"} -> 1
    {"var": ""} -> 2
    {"var": "/"} -> whole object
    {"var": "//"} -> 3
    {"var": "/path.to"} -> 4
    {"var": "/path~1"} -> 5

Variables scopes
----------------

The original `JsonLogic`_ format implicitly uses the notion of a scope in the implementation
of some operators such as `map <https://jsonlogic.com/operations.html#map-reduce-and-filter>`_:

.. code-block:: json

    {
        "map": [
            [1, 2],
            {"*": [{"var": ""}, 2]}
        ]
    }

In this case, the variable reference :json:`""` will refer to each element of the array :json:`[1, 2]`.
This means that there is no way to access data from the top level object (say for example you wanted
to multiply every element of the array with :json:`{"var": "some_const"}` instead of :json:`2`).

The notion of *scope* is thus introduced, so that it is still possible to access data from the parent scope.
This scope can be specified by appending ``@n`` at the end of the variable reference. The current scope starts at
0, so using :json:`"some_var@0"` is equivalent to :json:`"some_var"`.

Using our previous ``map`` example, with the following data:

.. code-block:: json

    {
        "some_const": 2
    }

the operator can be written as:

.. code-block:: json

    {
        "map": [
            [1, 2],
            {"*": [{"var": ""}, {"var": "some_const@1"}]}
        ]
    }

and would evaluate to :json:`[2, 4]`.

For more details on resolving variables, you can refer to the API documentation: :doc:`../api/evaluation`.

.. _`JsonLogic`: https://jsonlogic.com/
