import asyncio
import base64
import uuid
import time
from typing import Dict, Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import playwright_stealth

def get_stealth_func():
    """动态获取 stealth 插件的可执行函数"""
    # 尝试常见的函数名
    for name in ["stealth_async", "stealth_page", "stealth"]:
        func = getattr(playwright_stealth, name, None)
        if callable(func):
            return func
    # 适配部分版本中 stealth_async 是一个模块的情况
    sa = getattr(playwright_stealth, "stealth_async", None)
    if sa and hasattr(sa, "stealth_async") and callable(sa.stealth_async):
        return sa.stealth_async
    return None

_stealth_func = get_stealth_func()

class DouyinAuthAdapter:
    """
    抖音授权适配器：负责通过 Playwright 捕获二维码并提取 Session
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        # 用于存储活动的授权任务: {task_id: {"context": context, "page": page, "created_at": timestamp}}
        self.active_tasks: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def _ensure_browser(self):
        async with self._lock:
            if not self.playwright:
                self.playwright = await async_playwright().start()
            if not self.browser:
                self.browser = await self.playwright.chromium.launch(headless=True)

    async def create_auth_task(self) -> Tuple[str, str]:
        """
        创建授权任务，获取二维码
        Returns: (task_id, qrcode_base64)
        """
        await self._ensure_browser()
        
        task_id = str(uuid.uuid4())
        # 创建独立上下文，模拟真实浏览器指纹
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        if _stealth_func:
            import inspect
            if inspect.iscoroutinefunction(_stealth_func):
                await _stealth_func(page)
            else:
                _stealth_func(page)

        try:
            # 前往抖音登录页，等待网络相对空闲
            await page.goto("https://www.douyin.com/passport/web/login/", wait_until="networkidle", timeout=60000)
            
            # 可能的选择器列表 (根据抖音最新版本和历史版本整理)
            qr_selectors = [
                "xpath=//div[@id='animate_qrcode_container']//img",
                "xpath=//div[contains(@class, 'qrcode-image')]//img",
                "xpath=//img[contains(@src, 'passport/web/qrcode')]",
                ".login-guide-container img",
                "#login-panel-new img"
            ]
            
            target_element = None
            for selector in qr_selectors:
                try:
                    # 尝试等待每个选择器，缩短单个等待时间
                    target_element = await page.wait_for_selector(selector, timeout=5000, state="visible")
                    if target_element:
                        print(f"DEBUG: Found QR code using selector: {selector}")
                        break
                except:
                    continue
            
            if not target_element:
                # 如果都没找到，保存截图以便排查
                error_img = "login_error_snapshot.png"
                await page.screenshot(path=error_img)
                raise RuntimeError(f"未找到二维码元素。当前页面截图已保存至: {error_img}")
            
            # 确保元素已加载完成（可能有位移动画）
            await asyncio.sleep(1)
            
            # 截取二维码元素
            qr_bytes = await target_element.screenshot()
            qr_base64 = base64.b64encode(qr_bytes).decode('utf-8')
            full_base64 = f"data:image/png;base64,{qr_base64}"
            
            # 存入活动任务表
            self.active_tasks[task_id] = {
                "context": context,
                "page": page,
                "created_at": time.time(),
                "status": "wait_scan"
            }
            
            # 自动清理任务 (2分钟后)
            asyncio.create_task(self._auto_cleanup(task_id, 120))
            
            return task_id, full_base64
            
        except Exception as e:
            await context.close()
            raise RuntimeError(f"获取抖音二维码失败: {str(e)}")

    async def check_login_status(self, task_id: str) -> dict:
        """
        检查登录状态并提取 Session
        """
        if task_id not in self.active_tasks:
            return {"status": "expired"}
            
        task = self.active_tasks[task_id]
        page = task["page"]
        context = task["context"]
        
        try:
            # 检查登录成功的标志 (从 legacy 代码中借鉴)
            # 1. 检查 Cookie 中是否有 LOGIN_STATUS=1
            cookies = await context.cookies()
            cookie_dict = {c['name']: c['value'] for c in cookies}
            
            # 2. 检查 LocalStorage
            has_login = await page.evaluate("() => window.localStorage.getItem('HasUserLogin')")
            
            if cookie_dict.get("LOGIN_STATUS") == "1" or has_login == "1":
                # 登录成功，提取完整数据
                local_storage = await page.evaluate("() => JSON.stringify(window.localStorage)")
                
                session_data = {
                    "cookies": cookies,
                    "local_storage": local_storage,
                    "user_agent": await page.evaluate("() => navigator.userAgent")
                }
                
                # 释放资源
                await self.cleanup_task(task_id)
                
                return {
                    "status": "authorized",
                    "session": session_data
                }
            
            # 检查是否还在登录页，判断是否扫码
            # 如果 URL 发生了变化，说明可能正在跳转或已成功
            current_url = page.url
            if "passport/web/login" not in current_url:
                # 可能是待手机确认或处理验证码
                return {"status": "wait_confirm"}
            
            return {"status": "wait_scan"}
            
        except Exception as e:
            await self.cleanup_task(task_id)
            return {"status": "failed", "message": str(e)}

    async def cleanup_task(self, task_id: str):
        if task_id in self.active_tasks:
            task = self.active_tasks.pop(task_id)
            try:
                await task["context"].close()
            except:
                pass

    async def _auto_cleanup(self, task_id: str, delay: int):
        await asyncio.sleep(delay)
        if task_id in self.active_tasks:
            await self.cleanup_task(task_id)

    async def shutdown(self):
        async with self._lock:
            for task_id in list(self.active_tasks.keys()):
                await self.cleanup_task(task_id)
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

# 单例模式
douyin_auth_adapter = DouyinAuthAdapter()
