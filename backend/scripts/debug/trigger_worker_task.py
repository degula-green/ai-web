import redis
import json
import time

def trigger_test_task():
    # 使用服务器 Redis 地址
    r = redis.Redis(
        host='47.115.216.167', 
        port=6379, 
        password='zhao991023.', 
        db=0, 
        decode_responses=True
    )
    queue_name = "mediacrawler:task_queue"
    
    task_id = f"test_kw_{int(time.time())}"
    
    payload = {
        "task_id": task_id,
        "platform": "dy",
        "task_type": "search",
        "config": {
            "keywords": "人工智能",
            "max_count": 10
        }
    }
    
    print(f"--- 正在向服务器 Redis (47.115.216.167) 发送测试任务 ---")
    print(f"队列名: {queue_name}")
    print(f"内容: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        r.lpush(queue_name, json.dumps(payload))
        print(f"\n[OK] Task successfully sent to server!")
        print(f"Please check the 'worker.py' console, it should have started processing.")
    except Exception as e:
        print(f"[ERROR] Failed to send: {e}")

if __name__ == "__main__":
    trigger_test_task()
