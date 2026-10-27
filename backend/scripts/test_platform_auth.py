import asyncio
import os
import sys
import base64
from pathlib import Path

# Ensure the project root (backend/) is the very first entry in sys.path
# to avoid conflicts with global 'app' packages in site-packages
backend_root = str(Path(__file__).resolve().parents[1])
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Force reload 'app' if it was already imported from elsewhere
if 'app' in sys.modules:
    import app
    if not getattr(app, '__file__', '').startswith(backend_root):
        for mod in list(sys.modules.keys()):
            if mod == 'app' or mod.startswith('app.'):
                del sys.modules[mod]

async def main():
    print("🚀 Starting Douyin QR Code Capture Test...")
    
    # Import adapter here to ensure sys.path is set and local 'app' is loaded
    from app.adapters.douyin_auth_adapter import douyin_auth_adapter
    
    try:
        # 1. Create task
        task_id, qr_base64 = await douyin_auth_adapter.create_auth_task()
        print(f"✅ Auth Task Created! Task ID: {task_id}")
        
        # 2. Save QR code image for visual check
        if "," in qr_base64:
            header, encoded = qr_base64.split(",", 1)
        else:
            encoded = qr_base64
            
        img_path = backend_root / "douyin_qr_test.png"
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(encoded))
        
        print(f"📸 QR Code saved to: {img_path}")
        print("💡 Please open the image and scan it with your Douyin app.")
        print("⌛ Monitoring login status for 60 seconds...")
        
        # 3. Poll status
        for i in range(30):
            await asyncio.sleep(2)
            result = await douyin_auth_adapter.check_login_status(task_id)
            status = result.get("status")
            print(f"[{i+1}/30] Current Status: {status}")
            
            if status == "authorized":
                print("🎉 Login Successful!")
                session = result["session"]
                print(f" - Cookies captured: {len(session['cookies'])}")
                print(f" - User Agent: {session['user_agent'][:50]}...")
                # We won't save to DB here as we don't have a DB session in this simple script
                break
            elif status == "failed":
                print(f"❌ Login Failed: {result.get('message')}")
                break
        else:
            print("⏰ Test timed out.")
            
    except Exception as e:
        print(f"🔥 Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await douyin_auth_adapter.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
