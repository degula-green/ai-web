import asyncio
import uuid
import base64
import json
import threading
from datetime import datetime
from typing import Dict, Optional, Tuple, Any

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Try to import stealth with fallback as implemented before
import playwright_stealth

def get_stealth_func():
    for name in ["stealth_async", "stealth_page", "stealth"]:
        func = getattr(playwright_stealth, name, None)
        if callable(func):
            return func
    sa = getattr(playwright_stealth, "stealth_async", None)
    if sa and hasattr(sa, "stealth_async") and callable(sa.stealth_async):
        return sa.stealth_async
    return None

_stealth_func = get_stealth_func()

class AuthTaskInfo:
    def __init__(self, task_id: str, platform_code: str):
        self.task_id = task_id
        self.platform_code = platform_code
        self.status = "idle"  # idle, navigating, interacting, authorized, failed, timeout
        self.message: Optional[str] = None
        self.session_data: Optional[Dict[str, Any]] = None
        self.account_info: Optional[Dict[str, Any]] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

class PlatformAuthManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PlatformAuthManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.active_tasks: Dict[str, AuthTaskInfo] = {}
        self._initialized = True

    async def start_auth_task(self, platform_code: str) -> str:
        task_id = str(uuid.uuid4())
        task = AuthTaskInfo(task_id, platform_code)
        self.active_tasks[task_id] = task
        
        # Windows 涓?Uvicorn 榛樿浼氳缃?SelectorEventLoop 瀵艰嚧寮傛 Playwright subprocess 鎶ラ敊 NotImplementedError銆?
        # 鎴戜滑浣跨敤鐙珛绾跨▼鍜?asyncio.run 锛堜細鍚姩鍏ㄦ柊鐨勯粯璁?ProactorEventLoop锛夋潵杩愯娴忚鍣ㄤ换鍔°€?
        def run_in_thread(t: AuthTaskInfo):
            # 灏嗗紓姝ュ嚱鏁版斁杩涙柊鐨?event loop 鎵ц
            try:
                import sys
                if sys.platform == 'win32':
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                asyncio.run(self._run_auth_session_isolated(t))
            except Exception as e:
                t.status = "failed"
                t.message = str(e)
                t.updated_at = datetime.now()

        thread = threading.Thread(target=run_in_thread, args=(task,), daemon=True)
        thread.start()
        
        return task_id

    async def get_task_status(self, task_id: str) -> Optional[AuthTaskInfo]:
        return self.active_tasks.get(task_id)

    async def _run_auth_session_isolated(self, task: AuthTaskInfo):
        async with async_playwright() as p:
            browser = None
            context = None
            try:
                task.status = "navigating"
                task.updated_at = datetime.now()
                
                browser = await p.chromium.launch(
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                
                # 鍒涘缓鐙珛涓婁笅鏂囷紝妯℃嫙鐪熷疄娴忚鍣?
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                # 娉ㄥ叆闅愯韩鑴氭湰
                if _stealth_func:
                    import inspect
                    if inspect.iscoroutinefunction(_stealth_func):
                        await _stealth_func(page)
                    else:
                        _stealth_func(page)
                
                # 鍏堝幓棣栭〉寤虹珛鐜
                await page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=60000)
                
                # 濡傛灉娌¤嚜鍔ㄨ烦杞紝鍐嶅墠寰€鐧诲綍椤?
                await asyncio.sleep(2)
                if "login" not in page.url:
                    url_map = {
                        "xiaohongshu": "https://www.xiaohongshu.com/explore",
                        "bilibili": "https://passport.bilibili.com/login"
                    }
                    target_url = url_map.get(task.platform_code)
                    if target_url:
                        await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                
                task.status = "interacting"
                task.updated_at = datetime.now()
                
                # 杞鐩戝惉 Cookie
                start_time = asyncio.get_event_loop().time()
                while asyncio.get_event_loop().time() - start_time < 180:
                    # 绾跨▼瀹夊叏妫€鏌?
                    if task.status in ["canceled", "failed"]:
                        break
                    
                    try:
                        if page.is_closed():
                            task.status = "failed"
                            task.message = "用户关闭了浏览器窗口"
                            break
                            
                        cookies = await context.cookies()
                        if await self._is_logged_in(task.platform_code, cookies, page):
                            task.status = "interacting"
                            task.session_data = await self._collect_session_data(page, cookies)
                            task.account_info = await self._extract_basic_info(task.platform_code, page)
                            task.status = "authorized"
                            task.message = "授权成功"
                            task.updated_at = datetime.now()
                            # 鎺堟潈鎴愬姛鍚庡绛変竴浼氬効锛岀粰鐢ㄦ埛鐐瑰嚮鈥滀繚瀛樷€濇垨鏌ョ湅缁撴灉鐨勬椂闂?
                            await asyncio.sleep(8)
                            break
                    except Exception as e:
                        if self._is_transient_navigation_error(e):
                            task.status = "interacting"
                            task.message = "页面跳转中，继续等待授权完成"
                            task.updated_at = datetime.now()
                            await asyncio.sleep(1)
                            continue
                        if "Target closed" in str(e) or "context closed" in str(e).lower():
                            task.status = "failed"
                            task.message = "浏览器窗口已关闭"
                        else:
                            task.status = "failed"
                            task.message = f"浏览器交互异常: {str(e)}"
                        break
                    
                    await asyncio.sleep(2)
                else:
                    if task.status != "authorized":
                        task.status = "timeout"
                        task.message = "等待登录超时"
                
            except Exception as e:
                task.status = "failed"
                task.message = str(e)
            finally:
                if context:
                    await asyncio.sleep(2)
                    await context.close()
                if browser:
                    await browser.close()
                task.updated_at = datetime.now()

    async def _is_logged_in(self, platform: str, cookies: list, page: Page) -> bool:
        if platform == "douyin":
            return any(c['name'] == 'login_ticket' or c['name'] == 'passport_csrf_token_default' for c in cookies) and \
                   any(c['name'] == 'sid_guard' for c in cookies)
        return False

    async def _extract_basic_info(self, platform: str, page: Page) -> Dict[str, Any]:
        if platform != "douyin":
            return {}

        merged: Dict[str, Any] = {}

        try:
            dom_info = await page.evaluate(
                """
                () => {
                  const getText = (selectors) => {
                    for (const s of selectors) {
                      const el = document.querySelector(s);
                      const t = (el?.textContent || '').trim();
                      if (t) return t;
                    }
                    return '';
                  };
                  const getImage = (selectors) => {
                    for (const s of selectors) {
                      const el = document.querySelector(s);
                      const src = el?.getAttribute?.('src') || '';
                      if (src) return src;
                    }
                    return '';
                  };
                  const getAlt = (selectors) => {
                    for (const s of selectors) {
                      const el = document.querySelector(s);
                      const alt = (el?.getAttribute?.('alt') || el?.getAttribute?.('aria-label') || '').trim();
                      if (alt) return alt;
                    }
                    return '';
                  };
                  const links = Array.from(document.querySelectorAll('a[href*="/user/"]'));
                  let userHref = '';
                  for (const a of links) {
                    const href = a.getAttribute('href') || '';
                    if (href.includes('/user/')) {
                      userHref = href;
                      break;
                    }
                  }
                  const m = userHref.match(/\\/user\\/([^/?#]+)/);
                  const secUidFromHref = m ? decodeURIComponent(m[1]) : '';
                  const ls = {};
                  try {
                    for (let i = 0; i < localStorage.length; i++) {
                      const k = localStorage.key(i);
                      if (!k) continue;
                      ls[k] = localStorage.getItem(k);
                    }
                  } catch (_) {}
                  const fromLs = (keys) => {
                    for (const k of keys) {
                      const v = ls[k];
                      if (typeof v === 'string' && v.trim()) return v.trim();
                    }
                    return '';
                  };
                  return {
                    nickname: getText(['.nickname', '[data-e2e=\"user-name\"]', 'h1', '.author-name']),
                    nickname_alt: getAlt(['img[data-e2e=\"user-avatar\"]', 'img[class*=\"avatar\"]', 'a[href*=\"/user/\"] img']),
                    avatar_url: getImage(['img[data-e2e=\"user-avatar\"]', 'img[class*=\"avatar\"]', 'a[href*=\"/user/\"] img']),
                    sec_uid: secUidFromHref || fromLs(['sec_uid', 'secUid', 'sec_user_id', 'secUserId']),
                    uid: fromLs(['uid', 'user_id', 'userId']),
                    unique_id: fromLs(['unique_id', 'uniqueId']),
                    short_id: fromLs(['short_id', 'shortId']),
                  };
                }
                """
            )
            if isinstance(dom_info, dict):
                merged.update(self._normalize_account_info(dom_info))
        except Exception:
            pass

        try:
            # Try open profile page explicitly; URL and page script often contain stable sec_uid/昵称.
            profile_url = "https://www.douyin.com/user/self"
            await page.goto(profile_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(1200)
            profile_dom = await page.evaluate(
                """
                () => {
                  const getText = (selectors) => {
                    for (const s of selectors) {
                      const el = document.querySelector(s);
                      const t = (el?.textContent || '').trim();
                      if (t) return t;
                    }
                    return '';
                  };
                  const getImage = (selectors) => {
                    for (const s of selectors) {
                      const el = document.querySelector(s);
                      const src = el?.getAttribute?.('src') || '';
                      if (src) return src;
                    }
                    return '';
                  };
                  const getAlt = (selectors) => {
                    for (const s of selectors) {
                      const el = document.querySelector(s);
                      const alt = (el?.getAttribute?.('alt') || el?.getAttribute?.('aria-label') || '').trim();
                      if (alt) return alt;
                    }
                    return '';
                  };
                  const m = location.href.match(/\\/user\\/([^/?#]+)/);
                  const sec_uid = m ? decodeURIComponent(m[1]) : '';
                  const ogTitle = document.querySelector('meta[property=\"og:title\"]')?.getAttribute('content') || '';
                  const scriptText = Array.from(document.querySelectorAll('script[type=\"application/json\"]')).map(s => s.textContent || '').join('\\n');
                  return {
                    sec_uid,
                    nickname:
                      getText([
                        'h1',
                        '[data-e2e=\"user-title\"]',
                        '[data-e2e=\"user-name\"]',
                        '.nickname',
                        '.author-name',
                      ]) || getAlt(['img[data-e2e=\"user-avatar\"]', 'img[class*=\"avatar\"]']) || ogTitle,
                    avatar_url: getImage([
                      'img[data-e2e=\"user-avatar\"]',
                      'img[class*=\"avatar\"]',
                    ]),
                    scriptText,
                  };
                }
                """
            )
            if isinstance(profile_dom, dict):
                merged.update(self._normalize_account_info(profile_dom))
                script_text = str(profile_dom.get("scriptText") or "")
                if script_text:
                    regex_candidates = [
                        (r'"unique_id"\s*:\s*"([^"]+)"', "unique_id"),
                        (r'"short_id"\s*:\s*"([^"]+)"', "short_id"),
                        (r'"sec_uid"\s*:\s*"([^"]+)"', "sec_uid"),
                        (r'"nickname"\s*:\s*"([^"]+)"', "nickname"),
                        (r'"avatar(?:_thumb|_medium|_larger|_url)?"\s*:\s*"([^"]+https?[^"]+)"', "avatar_url"),
                    ]
                    extracted: dict[str, Any] = {}
                    for pattern, key in regex_candidates:
                        import re
                        m = re.search(pattern, script_text)
                        if m:
                            extracted[key] = m.group(1)
                    if extracted:
                        merged = {**merged, **self._normalize_account_info(extracted)}
        except Exception:
            pass

        try:
            profile_payload = await page.evaluate(
                """
                async () => {
                  const endpoints = [
                    '/aweme/v1/web/user/profile/self/',
                    '/aweme/v1/web/user/profile/other/?sec_user_id=self',
                  ];
                  for (const endpoint of endpoints) {
                    try {
                      const resp = await fetch(endpoint, { method: 'GET', credentials: 'include' });
                      if (!resp.ok) continue;
                      const data = await resp.json();
                      if (data && typeof data === 'object') {
                        return data;
                      }
                    } catch (_) {}
                  }
                  return null;
                }
                """
            )
            api_info = self._parse_douyin_profile_payload(profile_payload)
            if api_info:
                merged = {**merged, **api_info}
        except Exception:
            pass

        return merged

    @staticmethod
    def _pick_first_non_empty(*values: Any) -> str:
        invalid_values = {"self", "null", "undefined", "none", "nan", "{}", "[]"}
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text and text.lower() not in invalid_values:
                return text
        return ""

    @staticmethod
    def _extract_avatar_url(value: Any) -> str:
        if isinstance(value, str):
            text = value.strip()
            return text
        if isinstance(value, dict):
            url_list = value.get("url_list")
            if isinstance(url_list, list):
                for item in url_list:
                    text = str(item or "").strip()
                    if text:
                        return text
            return PlatformAuthManager._pick_first_non_empty(value.get("url"), value.get("uri"))
        return ""

    @classmethod
    def _normalize_account_info(cls, info: Dict[str, Any]) -> Dict[str, Any]:
        sec_uid = cls._pick_first_non_empty(info.get("sec_uid"), info.get("secUid"), info.get("sec_user_id"), info.get("secUserId"))
        uid = cls._pick_first_non_empty(info.get("uid"), info.get("user_id"), info.get("userId"))
        unique_id = cls._pick_first_non_empty(info.get("unique_id"), info.get("uniqueId"))
        short_id = cls._pick_first_non_empty(info.get("short_id"), info.get("shortId"))
        nickname = cls._pick_first_non_empty(
            info.get("nickname"),
            info.get("nickname_alt"),
            info.get("nick_name"),
            info.get("display_name"),
        )
        avatar_url = cls._pick_first_non_empty(
            cls._extract_avatar_url(info.get("avatar_url")),
            cls._extract_avatar_url(info.get("avatar_larger")),
            cls._extract_avatar_url(info.get("avatar_medium")),
            cls._extract_avatar_url(info.get("avatar_thumb")),
            cls._extract_avatar_url(info.get("avatar_168x168")),
        )
        platform_uid = cls._pick_first_non_empty(sec_uid, uid)
        account_name = cls._pick_first_non_empty(unique_id, short_id, platform_uid, nickname)
        return {
            "account_name": account_name,
            "nickname": nickname,
            "avatar_url": avatar_url,
            "platform_uid": platform_uid,
            "sec_uid": sec_uid,
            "uid": uid,
            "unique_id": unique_id,
            "short_id": short_id,
        }

    @classmethod
    def _parse_douyin_profile_payload(cls, payload: Any) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        candidates: list[dict[str, Any]] = [payload]
        for key in ("data", "user", "user_info", "profile", "owner"):
            value = payload.get(key)
            if isinstance(value, dict):
                candidates.append(value)
                for nested in ("user", "user_info", "profile", "owner"):
                    nested_value = value.get(nested)
                    if isinstance(nested_value, dict):
                        candidates.append(nested_value)

        for candidate in candidates:
            normalized = cls._normalize_account_info(candidate)
            if normalized.get("account_name") or normalized.get("nickname") or normalized.get("platform_uid"):
                return normalized
        return {}

    async def _collect_session_data(self, page: Page, cookies: list) -> Dict[str, Any]:
        return {
            "cookies": cookies,
            "local_storage": await page.evaluate("() => JSON.stringify(localStorage)"),
            "user_agent": await page.evaluate("() => navigator.userAgent"),
        }

    def _is_transient_navigation_error(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return (
            "execution context was destroyed" in text
            or "most likely because of a navigation" in text
            or "cannot find context with specified id" in text
        )

    async def shutdown(self):
        pass

# 鍏ㄥ眬鍗曚緥
platform_auth_manager = PlatformAuthManager()
