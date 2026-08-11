import pytest

from aic.settings import AppSettings


def test_app_settings_loads_with_openai_api_key_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AIC_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = AppSettings(_env_file=None)

    assert settings.openai_api_key is None
