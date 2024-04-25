from jsonlogic.json_schema.types import IntegerType
from jsonlogic.typechecking import DiagnosticsConfig, TypecheckSettings


def test_context_settings() -> None:
    settings = TypecheckSettings.from_dict(
        {
            "diagnostics": {
                "operator": "warning",
            },
            "variable_casts": {
                "date": IntegerType,
                "customfmt": IntegerType,
            },
        },
    )

    assert settings.diagnostics == DiagnosticsConfig(
        operator="warning",
    )
    assert settings.variable_casts == {
        "date": IntegerType,
        "customfmt": IntegerType,
    }
