import pytest


@pytest.fixture(autouse=True)
def no_real_llm(monkeypatch):
    """Tests never call a hosted model, even when .env holds a real LLM_API_KEY."""
    monkeypatch.setattr("backend.analysis.llm_configured", lambda: False)
