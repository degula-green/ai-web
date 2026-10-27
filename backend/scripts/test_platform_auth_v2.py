import asyncio
import sys
import os
from pathlib import Path

# Ensure project root is at the beginning of sys.path
backend_root = str(Path(__file__).resolve().parents[1])
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Clear global modules to avoid 'app' namespace conflict
if 'app' in sys.modules:
    for mod in list(sys.modules.keys()):
        if mod == 'app' or mod.startswith('app.'):
            del sys.modules[mod]

async def main():
    print("🚀 Starting V2.0 Controlled Browser Auth Test (Manual Login)...")
    
    # Import manager after path setup
    from app.adapters.platforms.manager import platform_auth_manager
    
    try:
        # 1. Start Task
        task_id = await platform_auth_manager.start_auth_task("douyin")
        print(f"✅ Auth Task Initiated! Task ID: {task_id}")
        print("🖥️  A browser window should pop up. Please log in manually (QR, Phone, etc.).")
        print("⌛ Monitoring session for 180 seconds...")
        
        # 2. Poll Status
        for i in range(90):
            await asyncio.sleep(2)
            task = await platform_auth_manager.get_task_status(task_id)
            if not task:
                print("❌ Task not found.")
                break
            
            # Print current progress on the same line
            print(f"[{i+1}/60] Current Status: {task.status}        ", end='\r')
            
            if task.status == "authorized":
                print("\n\n🎉 Login Successful!")
                print(f" - Captured Nickname: {task.account_info.get('nickname')}")
                print(f" - Captured Cookies count: {len(task.session_data['cookies'])}")
                print(f" - Session saved to memory and ready for persistence.")
                break
            elif task.status in ["failed", "timeout"]:
                print(f"\n❌ Task End State: {task.status}. Message: {task.message}")
                break
        else:
            print("\n⏰ Test timed out. Please try again.")
            
    except Exception as e:
        print(f"\n🔥 Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        await platform_auth_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
