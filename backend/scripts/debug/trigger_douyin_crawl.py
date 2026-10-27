import sys
import os
import json
from pathlib import Path

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.lifecycle import build_container
from app.schemas.task import TaskCreateRequest
from app.core.task_state_machine import TaskState

def test_douyin_crawl():
    # 1. Build the container to get all services
    container = build_container()
    
    # 2. Prepare the task payload
    # Note: TaskService.create_task now requires a user_id
    payload = TaskCreateRequest(
        task_type="mediacrawler_collect",
        platform="douyin",
        source_type="search",
        source_value="open",
        title="Douyin Search for 'open'",
        config={
            "platform": "douyin",
            "keywords": "open",
            "max_count": 5,
            "collector": "mediacrawler",
            "crawler_type": "search"
        },
        start_async=True
    )
    
    # Use a dummy user_id (e.g., 1)
    user_id = 1
    
    print(f"Creating task for keyword 'open' on Douyin...")
    task_read = container.task_service.create_task(payload, user_id=user_id)
    
    task_id = task_read.task_id
    print(f"Task created! ID: {task_id}")
    print(f"Check Redis queue length: {container.media_crawler_orchestrator.status()}")
    
    # 3. Poll for status update (optional)
    print("Waiting for worker to pick up the task and update status...")
    import time
    for i in range(30): # Wait up to 60 seconds
        time.sleep(2)
        record = container.task_repository.get(task_id)
        print(f"[{i*2}s] Task State: {record.state}, Result Count: {record.result_count}")
        if record.error_message:
            print(f"Error: {record.error_message}")
        if record.state in [TaskState.PARSING, TaskState.FAILED]:
            break

if __name__ == "__main__":
    test_douyin_crawl()
