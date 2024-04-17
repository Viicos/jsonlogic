from jsonlogic.json_schema.types import DatetimeType, DateType, IntegerType
from jsonlogic.typechecking import DiagnosticsConfig, TypecheckContext, TypecheckSettings


def test_typecheck_context_settings() -> None:
    context = TypecheckContext({})
    assert context.settings == TypecheckSettings()


def test_context_settings():
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

    assert settings == TypecheckSettings(
        diagnostics=DiagnosticsConfig(
            operator="warning",
        ),
        variable_casts={
            "date": IntegerType,
            "customfmt": IntegerType,
        },
    )

    extend_settings = TypecheckSettings.from_dict(
        {
            "extend_variable_casts": {
                "customfmt": IntegerType,
            }
        },
    )

    assert extend_settings == TypecheckSettings(
        variable_casts={
            "date": DateType,
            "date-time": DatetimeType,
            "customfmt": IntegerType,
        }
    )
