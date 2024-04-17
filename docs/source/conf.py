import sys
from pathlib import Path

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

project = "python-jsonlogic"
copyright = "2024, Victorien"
author = "Victorien"
release = "0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.todo",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_paramlinks",
]

rst_prolog = """
.. role:: python(code)
    :language: python
    :class: highlight
"""

templates_path = ["_templates"]
exclude_patterns = []

todo_include_todos = True

autodoc_member_order = "bysource"
autodoc_type_aliases = {
    "OperatorArgument": "OperatorArgument",
    "DiagnosticCategory": "DiagnosticCategory",
    "DiagnosticType": "DiagnosticType",
    "BinaryOp": "BinaryOp",
    "UnaryOp": "UnaryOp",
    "JSONSchemaPrimitiveType": "JSONSchemaPrimitiveType",
}
autoclass_content = "both"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

linkcheck_retries = 3

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]

html_theme_options = {
    "source_repository": "https://github.com/Viicos/jsonlogic/",
    "source_branch": "main",
    "source_directory": "docs/source/",
}
