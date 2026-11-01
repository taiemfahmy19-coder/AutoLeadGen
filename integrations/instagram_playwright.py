"""AutoLeadGen v2 - Integrations: Instagram Direct Message Automation via Playwright Stealth."""
import os
import time
import random
import threading
from datetime import datetime
from config.settings import DATA_DIR
from utils.logger import info, warning, error

try:
    from playwright_stealth import Stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

# ─── Profile & State Paths ────────────────────────────────────────────────────
INSTAGRAM_PROFILE_DIR = os.path.join(DATA_DIR, "instagram_profile")
os.makedirs(INSTAGRAM_PROFILE_DIR, exist_ok=True)

# ─── Safety Constants (Anti-Ban Human Protocol) ───────────────────────────────
IG_DELAY_MIN    = 180   # 3 min minimum between DMs
IG_DELAY_MAX    = 360   # 6 min maximum between DMs
IG_BATCH_SIZE   = 5     # DMs per burst before mandatory cooldown
IG_COOLDOWN_MIN = 1200  # 20 min cooldown between batches
IG_COOLDOWN_MAX = 2100  # 35 min cooldown between batches
IG_DAILY_MAX    = 15    # Absolute safe daily DM cap

# ─── Selectors ────────────────────────────────────────────────────────────────
IG_HOME_INDICATORS = [
    "svg[aria-label='Home']",
    "a[href='/']",
    "div[role='navigation']",
    "header",
]
IG_LOGIN_INDICATORS = [
    "input[name='username']",
    "input[name='password']",
]
IG_SEARCH_INPUT = [
    "input[placeholder='Search...']",
    "input[placeholder='بحث...']",
    "input[name='queryBox']",
    "input[aria-label='Search']",
]
IG_MSG_INPUT = [
    "div[aria-label='Message']",
    "div[role='textbox']",
    "p[data-lexical-editor='true']",
    "div[contenteditable='true']",
]

# ─── Arabic Typo Map ──────────────────────────────────────────────────────────
ARABIC_TYPO_MAP = {
    "ا": ["أ", "إ", "آ"],
    "ه": ["ة"],
    "ة": ["ه"],
    "ي": ["ى"],
    "ى": ["ي"],
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _apply_stealth(page):
    if STEALTH_AVAILABLE:
        try:
            Stealth().apply_stealth_sync(page)
        except Exception:
            pass


def _bezier_point(p0, p1, p2, p3, t):
    return (
        (1 - t) ** 3 * p0
        + 3 * (1 - t) ** 2 * t * p1
        + 3 * (1 - t) * t ** 2 * p2
        + t ** 3 * p3
    )


def _human_mouse_move(page, tx, ty, steps=18):
    try:
        sx = getattr(page, "_ig_mx", random.uniform(200, 500))
        sy = getattr(page, "_ig_my", random.uniform(200, 400))
        dx, dy = tx - sx, ty - sy
        c1x = sx + dx * random.uniform(0.15, 0.4) + random.uniform(-20, 20)
        c1y = sy + dy * random.uniform(0.15, 0.4) + random.uniform(-20, 20)
        c2x = sx + dx * random.uniform(0.6, 0.85) + random.uniform(-20, 20)
        c2y = sy + dy * random.uniform(0.6, 0.85) + random.uniform(-20, 20)
        for i in range(1, steps + 1):
            t = i / steps
            cx = _bezier_point(sx, c1x, c2x, tx, t) + random.uniform(-0.8, 0.8)
            cy = _bezier_point(sy, c1y, c2y, ty, t) + random.uniform(-0.8, 0.8)
            page.mouse.move(cx, cy)
            time.sleep(random.uniform(0.004, 0.011))
        page.mouse.move(tx, ty)
        page._ig_mx, page._ig_my = tx, ty
    except Exception:
        pass


def _human_click(page, locator):
    try:
        if locator.count() == 0 or not locator.first.is_visible():
            return False
        box = locator.first.bounding_box()
        if not box:
            return False
        cx = box["x"] + box["width"] * random.uniform(0.3, 0.7)
        cy = box["y"] + box["height"] * random.uniform(0.3, 0.7)
        _human_mouse_move(page, cx, cy)
        time.sleep(random.uniform(0.08, 0.22))
        page.mouse.down()
        time.sleep(random.uniform(0.06, 0.18))
        page.mouse.up()
        return True
    except Exception:
        return False


def _type_human_like(page, locator, text: str):
    """Type with realistic speed and occasional Arabic typos."""
    locator.first.click()
    time.sleep(random.uniform(0.3, 0.7))
    for char in text:
        if char in ARABIC_TYPO_MAP and random.random() < 0.03:
            wrong = random.choice(ARABIC_TYPO_MAP[char])
            locator.first.press_sequentially(wrong, delay=random.randint(60, 140))
            time.sleep(random.uniform(0.18, 0.35))
            locator.first.press("Backspace")
            time.sleep(random.uniform(0.12, 0.25))
        locator.first.press_sequentially(char, delay=random.randint(55, 160))
        if char in (" ", "\n"):
            time.sleep(random.uniform(0.08, 0.22))
    time.sleep(random.uniform(0.4, 0.9))


# ─── Main Engine ──────────────────────────────────────────────────────────────
class InstagramEngine:
    """
    Zero-cost Instagram DM engine using Playwright with persistent profile.
    Stealth + Bezier mouse + human typing + safe delays to avoid detection.
    """

    def __init__(self):
        self._context = None
        self._page = None
        self._lock = threading.Lock()
        self._status = "DISCONNECTED"
        self._status_detail = ""
        self._sent_today = 0
        self._last_reset_date = datetime.now().date()
        self._pw = None

    # ── Status ─────────────────────────────────────────────────────────────────
    def get_status(self):
        return self._status

    def get_status_detail(self):
        return self._status_detail

    def get_sent_today(self):
        today = datetime.now().date()
        if today != self._last_reset_date:
            self._sent_today = 0
            self._last_reset_date = today
        return self._sent_today

    def _set_status(self, status, detail=""):
        self._status = status
        self._status_detail = detail
        info(f"[Instagram] {status} | {detail}")

    # ── Launch ─────────────────────────────────────────────────────────────────
    def launch(self, headless: bool = False) -> bool:
        """Launch Chromium with persistent profile and stealth patches."""
        with self._lock:
            try:
                from playwright.sync_api import sync_playwright
                self._pw = sync_playwright().start()
                self._context = self._pw.chromium.launch_persistent_context(
                    user_data_dir=INSTAGRAM_PROFILE_DIR,
                    headless=headless,
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--disable-dev-shm-usage",
                        "--window-size=1366,768",
                    ],
                    viewport={"width": 1366, "height": 768},
                    user_agent=USER_AGENT,
                    locale="ar-EG",
                    timezone_id="Africa/Cairo",
                )
                self._page = (
                    self._context.pages[0]
                    if self._context.pages
                    else self._context.new_page()
                )
                _apply_stealth(self._page)
                self._page.add_init_script(
                    "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
                )
                self._set_status("LAUNCHED", "Browser started")
                return True
            except Exception as exc:
                self._set_status("ERROR", str(exc))
                error(f"[Instagram] Launch failed: {exc}")
                return False

    # ── Check Login ────────────────────────────────────────────────────────────
    def check_login(self, timeout: int = 20000) -> str:
        """Navigate to instagram.com and detect login state.
        Returns: 'LOGGED_IN' | 'NEED_LOGIN' | 'ERROR'
        """
        try:
            self._page.goto(
                "https://www.instagram.com/",
                wait_until="domcontentloaded",
                timeout=timeout,
            )
            time.sleep(random.uniform(2.5, 4.5))
            for sel in IG_HOME_INDICATORS:
                try:
                    self._page.wait_for_selector(sel, timeout=4000)
                    self._set_status("CONNECTED", "Logged in ✅")
                    return "LOGGED_IN"
                except Exception:
                    pass
            for sel in IG_LOGIN_INDICATORS:
                try:
                    self._page.wait_for_selector(sel, timeout=3000)
                    self._set_status("NEED_LOGIN", "Login page detected")
                    return "NEED_LOGIN"
                except Exception:
                    pass
            self._set_status("NEED_LOGIN", "Unknown state — login manually")
            return "NEED_LOGIN"
        except Exception as exc:
            self._set_status("ERROR", str(exc))
            return "ERROR"

    # ── Open DM Chat ───────────────────────────────────────────────────────────
    def _open_dm_chat(self, handle: str, timeout: int = 15000) -> bool:
        """Open DM composer and search for @handle. Returns True when ready."""
        clean = handle.lstrip("@").strip()
        try:
            self._page.goto(
                "https://www.instagram.com/direct/new/",
                wait_until="domcontentloaded",
                timeout=timeout,
            )
            time.sleep(random.uniform(2.0, 3.5))

            search_el = None
            for sel in IG_SEARCH_INPUT:
                try:
                    el = self._page.locator(sel).first
                    el.wait_for(state="visible", timeout=5000)
                    search_el = self._page.locator(sel)
                    break
                except Exception:
                    pass

            if not search_el:
                warning("[Instagram] Search box not found in DM composer")
                return False

            _human_click(self._page, search_el)
            time.sleep(random.uniform(0.5, 1.0))
            _type_human_like(self._page, search_el, clean)
            time.sleep(random.uniform(1.5, 2.5))

            # Click first autocomplete result
            result_sels = [
                f"div[role='option']:has-text('{clean}')",
                "div[role='option']",
                "button[role='option']",
            ]
            clicked = False
            for sel in result_sels:
                try:
                    res = self._page.locator(sel).first
                    res.wait_for(state="visible", timeout=6000)
                    _human_click(self._page, self._page.locator(sel))
                    clicked = True
                    break
                except Exception:
                    pass

            if not clicked:
                warning(f"[Instagram] No result for @{clean}")
                return False

            time.sleep(random.uniform(0.8, 1.5))

            # Click Next / Chat
            for sel in ["button:has-text('Next')", "button:has-text('التالي')", "button:has-text('Chat')"]:
                try:
                    btn = self._page.locator(sel).first
                    btn.wait_for(state="visible", timeout=4000)
                    _human_click(self._page, self._page.locator(sel))
                    break
                except Exception:
                    pass

            time.sleep(random.uniform(1.5, 2.5))

            # Verify message input visible
            for sel in IG_MSG_INPUT:
                try:
                    self._page.locator(sel).first.wait_for(state="visible", timeout=6000)
                    return True
                except Exception:
                    pass
            return False
        except Exception as exc:
            error(f"[Instagram] _open_dm_chat: {exc}")
            return False

    # ── Send Single DM ─────────────────────────────────────────────────────────
    def send_dm(self, handle: str, message: str):
        """Send a single DM. Returns (bool, str)."""
        if self._status != "CONNECTED":
            return False, "Instagram غير متصل. سجّل الدخول أولاً."
        if self.get_sent_today() >= IG_DAILY_MAX:
            return False, f"تم الوصول للحد اليومي ({IG_DAILY_MAX} رسالة)."

        with self._lock:
            try:
                if not self._open_dm_chat(handle):
                    return False, f"تعذّر فتح المحادثة مع @{handle}"

                msg_el = None
                for sel in IG_MSG_INPUT:
                    try:
                        el = self._page.locator(sel).first
                        el.wait_for(state="visible", timeout=5000)
                        msg_el = self._page.locator(sel)
                        break
                    except Exception:
                        pass

                if not msg_el:
                    return False, "تعذّر إيجاد خانة إدخال الرسالة"

                _type_human_like(self._page, msg_el, message)
                time.sleep(random.uniform(1.2, 2.8))
                msg_el.first.press("Enter")
                time.sleep(random.uniform(1.0, 2.0))

                # Fallback: click Send button if still has text
                try:
                    if msg_el.first.inner_text().strip():
                        for sel in ["button:has-text('Send')", "button:has-text('إرسال')"]:
                            try:
                                self._page.locator(sel).first.click()
                                break
                            except Exception:
                                pass
                except Exception:
                    pass

                self._sent_today += 1
                info(f"[Instagram] DM sent to @{handle}")
                return True, f"✅ تم إرسال الرسالة إلى @{handle}"
            except Exception as exc:
                error(f"[Instagram] send_dm: {exc}")
                return False, f"خطأ: {exc}"

    # ── Batch Send ─────────────────────────────────────────────────────────────
    def send_batch_dms(
        self,
        leads: list,
        message_template: str,
        delay_min: int = IG_DELAY_MIN,
        delay_max: int = IG_DELAY_MAX,
        batch_size: int = IG_BATCH_SIZE,
        enable_cooldown: bool = True,
        cooldown_min: int = IG_COOLDOWN_MIN,
        cooldown_max: int = IG_COOLDOWN_MAX,
        progress_callback=None,
        stop_event=None,
    ) -> list:
        """Send batch DMs. Each lead dict needs: id, business_name, instagram_handle, industry, city."""
        results = []
        batch_count = 0

        for idx, lead in enumerate(leads):
            if stop_event and stop_event.is_set():
                break
            if self.get_sent_today() >= IG_DAILY_MAX:
                warning("[Instagram] Daily cap reached. Stopping.")
                break

            handle = lead.get("instagram_handle", "").lstrip("@").strip()
            if not handle:
                results.append({"lead_id": lead.get("id"), "handle": "", "success": False, "message": "لا يوجد حساب Instagram"})
                continue

            try:
                from services.outreach_service import OutreachService
                msg = OutreachService.build_personalized_message(
                    message_template,
                    business=lead.get("business_name", ""),
                    industry=lead.get("industry", ""),
                    city=lead.get("city", ""),
                )
            except Exception:
                msg = message_template

            if progress_callback:
                progress_callback(idx, len(leads), handle, "جاري الإرسال…")

            ok, detail = self.send_dm(handle, msg)
            results.append({"lead_id": lead.get("id"), "handle": handle, "success": ok, "message": detail})
            batch_count += 1

            if progress_callback:
                progress_callback(idx, len(leads), handle, detail)

            if idx < len(leads) - 1:
                if enable_cooldown and batch_count >= batch_size:
                    secs = random.randint(cooldown_min, cooldown_max)
                    info(f"[Instagram] Cooldown {secs}s…")
                    if progress_callback:
                        progress_callback(idx, len(leads), handle, f"🛑 راحة: {secs // 60} دقيقة…")
                    for _ in range(secs):
                        if stop_event and stop_event.is_set():
                            break
                        time.sleep(1)
                    batch_count = 0
                else:
                    delay = random.randint(delay_min, delay_max)
                    for _ in range(delay):
                        if stop_event and stop_event.is_set():
                            break
                        time.sleep(1)

        return results

    # ── Close ──────────────────────────────────────────────────────────────────
    def close(self):
        try:
            if self._context:
                self._context.close()
            if self._pw:
                self._pw.stop()
        except Exception:
            pass
        self._set_status("DISCONNECTED", "Browser closed")
        self._context = None
        self._page = None
        self._pw = None
