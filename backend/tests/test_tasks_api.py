from fastapi.testclient import TestClient

from app.main import create_app


def test_create_and_get_task() -> None:
    with TestClient(create_app()) as client:
        create_response = client.post(
            "/api/v1/tasks",
            json={
                "task_type": "content_workflow",
                "platform": "douyin",
                "source_type": "link",
                "source_value": "https://example.com/demo",
            },
        )
        assert create_response.status_code == 200
        created = create_response.json()["data"]
        task_id = created["task_id"]

        get_response = client.get(f"/api/v1/tasks/{task_id}")
        assert get_response.status_code == 200
        fetched = get_response.json()["data"]
        assert fetched["task_id"] == task_id
        assert fetched["state"] == "created"
