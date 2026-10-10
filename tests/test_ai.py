"""Tests for the AI endpoints. A fake provider replaces the real AI, so no
API key or internet is needed and we can simulate failures on purpose."""
import json

from app.ai.exceptions import AINotConfiguredError, AIProviderError, AITimeoutError

GOOD_DESCRIPTION = json.dumps(
    {
        "description": "Build the login page with email and password fields and basic validation.",
        "checklist": ["Sketch the layout", "Build the form", "Connect it to the API"],
    }
)
GOOD_SUMMARY = json.dumps({"summary": "Create the login page for the app.", "key_points": ["Form", "Validation"]})


class FakeProvider:
    """Returns the given responses in order (the last one repeats). An Exception is raised instead."""

    name = "fake"
    model = "fake-1"

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = 0

    def complete(self, system_prompt, user_prompt):
        self.calls += 1
        item = self.responses[min(self.calls, len(self.responses)) - 1]
        if isinstance(item, Exception):
            raise item
        return item


def use_provider(monkeypatch, provider):
    monkeypatch.setattr("app.ai.service.get_provider", lambda: provider)
    return provider


def make_task(client, headers, title="Design the login page"):
    return client.post("/api/tasks", json={"title": title, "description": "Simple form"}, headers=headers).json()


# ---------- Option A: generate description ----------
def test_generate_description_works(client, user_headers):
    # Uses the built-in mock provider (AI_PROVIDER=mock in conftest).
    response = client.post("/api/tasks/generate-description", json={"title": "Plan the team offsite"}, headers=user_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Plan the team offsite"
    assert body["description"]
    assert len(body["checklist"]) >= 2
    assert body["provider"] == "mock"


def test_generate_description_requires_login(client):
    response = client.post("/api/tasks/generate-description", json={"title": "Plan the team offsite"})
    assert response.status_code == 401


def test_generate_description_validates_title(client, user_headers):
    response = client.post("/api/tasks/generate-description", json={"title": "ab"}, headers=user_headers)
    assert response.status_code == 422


def test_ai_answer_wrapped_in_code_fence_is_accepted(client, user_headers, monkeypatch):
    use_provider(monkeypatch, FakeProvider(f"```json\n{GOOD_DESCRIPTION}\n```"))
    response = client.post("/api/tasks/generate-description", json={"title": "Login page"}, headers=user_headers)
    assert response.status_code == 200


# ---------- Option B: summarize ----------
def test_summarize_own_task(client, user_headers, monkeypatch):
    use_provider(monkeypatch, FakeProvider(GOOD_SUMMARY))
    task = make_task(client, user_headers)
    response = client.post(f"/api/tasks/{task['id']}/summarize", headers=user_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == task["id"]
    assert body["summary"] == "Create the login page for the app."
    assert body["key_points"] == ["Form", "Validation"]


def test_summarize_works_with_mock_provider(client, user_headers):
    task = make_task(client, user_headers)
    response = client.post(f"/api/tasks/{task['id']}/summarize", headers=user_headers)
    assert response.status_code == 200
    assert response.json()["provider"] == "mock"


def test_user_cannot_summarize_another_users_task(client, user_headers, other_user_headers):
    task = make_task(client, other_user_headers)
    response = client.post(f"/api/tasks/{task['id']}/summarize", headers=user_headers)
    assert response.status_code == 403


def test_admin_can_summarize_any_task(client, user_headers, admin_headers):
    task = make_task(client, user_headers)
    response = client.post(f"/api/tasks/{task['id']}/summarize", headers=admin_headers)
    assert response.status_code == 200


def test_summarize_missing_task_returns_404(client, user_headers):
    assert client.post("/api/tasks/9999/summarize", headers=user_headers).status_code == 404


# ---------- AI failure handling ----------
def test_provider_error_returns_502(client, user_headers, monkeypatch):
    use_provider(monkeypatch, FakeProvider(AIProviderError("The AI service returned an error (HTTP 500).")))
    response = client.post("/api/tasks/generate-description", json={"title": "Login page"}, headers=user_headers)
    assert response.status_code == 502


def test_timeout_returns_504(client, user_headers, monkeypatch):
    use_provider(monkeypatch, FakeProvider(AITimeoutError()))
    response = client.post("/api/tasks/generate-description", json={"title": "Login page"}, headers=user_headers)
    assert response.status_code == 504


def test_missing_configuration_returns_503(client, user_headers, monkeypatch):
    def not_configured():
        raise AINotConfiguredError()

    monkeypatch.setattr("app.ai.service.get_provider", not_configured)
    response = client.post("/api/tasks/generate-description", json={"title": "Login page"}, headers=user_headers)
    assert response.status_code == 503


def test_invalid_json_from_ai_returns_502(client, user_headers, monkeypatch):
    provider = use_provider(monkeypatch, FakeProvider("Sorry, I cannot help with that."))
    response = client.post("/api/tasks/generate-description", json={"title": "Login page"}, headers=user_headers)
    assert response.status_code == 502
    assert provider.calls == 2  # first try + one retry


def test_json_with_wrong_shape_is_rejected(client, user_headers, monkeypatch):
    # Valid JSON, but the "checklist" key is missing -> fails Pydantic validation.
    use_provider(monkeypatch, FakeProvider(json.dumps({"description": "A long enough description text."})))
    response = client.post("/api/tasks/generate-description", json={"title": "Login page"}, headers=user_headers)
    assert response.status_code == 502


def test_retry_recovers_from_one_bad_answer(client, user_headers, monkeypatch):
    provider = use_provider(monkeypatch, FakeProvider("not json at all", GOOD_DESCRIPTION))
    response = client.post("/api/tasks/generate-description", json={"title": "Login page"}, headers=user_headers)
    assert response.status_code == 200
    assert provider.calls == 2
