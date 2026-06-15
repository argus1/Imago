from imago.config.settings import Settings


def test_settings_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("IMAGO_APP_NAME", "imago-test")
    monkeypatch.setenv("IMAGO_API_PORT", "9001")
    monkeypatch.setenv("IMAGO_MONAI_CACHE_MODE", "persistent_dataset")
    monkeypatch.setenv("IMAGO_MONAI_TRANSFORM_VERSION", "tfm-v1")
    monkeypatch.setenv("IMAGO_MONAI_EMIT_LINEAGE_RECORDS", "false")

    settings = Settings()

    assert settings.app_name == "imago-test"
    assert settings.api_port == 9001
    assert settings.monai_cache_mode == "persistent_dataset"
    assert settings.monai_transform_version == "tfm-v1"
    assert settings.monai_emit_lineage_records is False
