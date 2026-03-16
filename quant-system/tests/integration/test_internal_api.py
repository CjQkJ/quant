from fastapi.testclient import TestClient

from apps.agent_orchestrator.main import app


client = TestClient(app)


def test_internal_api_policy_and_live_guard():
    response = client.get("/risk/policy")
    assert response.status_code == 200
    assert response.json()["version"]

    live_response = client.post("/execution/live/submit")
    assert live_response.status_code == 403


def test_tool_catalog_endpoint():
    response = client.get("/tools/catalog/executor_agent")
    assert response.status_code == 200
    tool_names = {item["name"] for item in response.json()}
    assert "run_paper_cycle" in tool_names
