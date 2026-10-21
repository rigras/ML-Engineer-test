import pytest
from pydantic import ValidationError

from app.infrastructure.settings import ConfigurationInvalid, Settings, load_settings


def test_defaults_load() -> None:
    settings = Settings(_env_file=None)

    assert settings.render_dpi == 300
    assert settings.fuzzy_threshold == 0.90
    assert settings.max_upload_bytes == 20 * 1024 * 1024
    assert settings.max_pages == 50
    assert settings.ner_model == "en_core_web_sm"
    assert settings.tesseract_cmd is None


def test_environment_overrides_a_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCINTEL_RENDER_DPI", "200")

    assert Settings(_env_file=None).render_dpi == 200


def test_invalid_value_fails_naming_the_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCINTEL_FUZZY_THRESHOLD", "1.7")

    with pytest.raises(ValidationError, match="fuzzy_threshold"):
        Settings(_env_file=None)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("DOCINTEL_RENDER_DPI", "0"),
        ("DOCINTEL_MAX_PAGES", "0"),
        ("DOCINTEL_LOG_LEVEL", "LOUD"),
        ("DOCINTEL_OCR_CONFIDENCE_FLOOR", "101"),
    ],
)
def test_out_of_range_values_are_rejected(
    monkeypatch: pytest.MonkeyPatch, key: str, value: str
) -> None:
    monkeypatch.setenv(key, value)

    with pytest.raises(ValidationError, match=key.removeprefix("DOCINTEL_").lower()):
        Settings(_env_file=None)


def test_load_settings_names_the_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCINTEL_FUZZY_THRESHOLD", "1.7")

    with pytest.raises(ConfigurationInvalid, match="DOCINTEL_FUZZY_THRESHOLD"):
        load_settings(env_file=None)
