from types import SimpleNamespace

import pytest

import app.observability.tracing as tracing_module
from app.observability.tracing import configure_langsmith

LANGSMITH_ENV_VARS = ("LANGSMITH_TRACING", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT")


@pytest.fixture(autouse=True)
def isolate_langsmith_state():
    saved_env = {key: tracing_module.os.environ.get(key) for key in LANGSMITH_ENV_VARS}
    for key in LANGSMITH_ENV_VARS:
        tracing_module.os.environ.pop(key, None)
    saved_flag = tracing_module._langsmith_configured
    tracing_module._langsmith_configured = False

    yield

    for key, value in saved_env.items():
        if value is None:
            tracing_module.os.environ.pop(key, None)
        else:
            tracing_module.os.environ[key] = value
    tracing_module._langsmith_configured = saved_flag


def test_configure_langsmith_sets_env_vars_when_enabled(monkeypatch):
    settings = SimpleNamespace(langsmith_tracing=True, langsmith_api_key="lsv2_test", langsmith_project="supportiq")
    monkeypatch.setattr(tracing_module, "get_settings", lambda: settings)

    configure_langsmith()

    assert tracing_module.os.environ["LANGSMITH_TRACING"] == "true"
    assert tracing_module.os.environ["LANGSMITH_API_KEY"] == "lsv2_test"
    assert tracing_module.os.environ["LANGSMITH_PROJECT"] == "supportiq"


def test_configure_langsmith_does_nothing_without_an_api_key(monkeypatch):
    settings = SimpleNamespace(langsmith_tracing=True, langsmith_api_key=None, langsmith_project="supportiq")
    monkeypatch.setattr(tracing_module, "get_settings", lambda: settings)

    configure_langsmith()

    assert "LANGSMITH_API_KEY" not in tracing_module.os.environ


def test_configure_langsmith_is_idempotent(monkeypatch):
    calls = []
    settings = SimpleNamespace(langsmith_tracing=True, langsmith_api_key="lsv2_test", langsmith_project="supportiq")

    def fake_get_settings():
        calls.append(1)
        return settings

    monkeypatch.setattr(tracing_module, "get_settings", fake_get_settings)

    configure_langsmith()
    configure_langsmith()

    assert len(calls) == 1
