from imago.config.settings import Settings


def test_settings_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("IMAGO_APP_NAME", "imago-test")
    monkeypatch.setenv("IMAGO_API_PORT", "9001")

    settings = Settings()

    assert settings.app_name == "imago-test"
    assert settings.api_port == 9001
