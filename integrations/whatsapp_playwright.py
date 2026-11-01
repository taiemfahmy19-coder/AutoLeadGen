"""AutoLeadGen v2 - Integrations: WhatsApp Playwright Automation and Real Session Management."""
import os
import time
import json
import random
import shutil
import threading
import urllib.parse
from datetime import datetime
from pipeline.cleaner import normalize_phone, is_mobile_phone
from integrations.link_generator import generate_direct_link
from config.settings import WHATSAPP_PROFILE_DIR, DATA_DIR
from config.constants import (
    WHATSAPP_DELAY_MIN,
    WHATSAPP_DELAY_MAX,
    STATUS_DO_NOT_CONTACT,
    STATUS_CONTACTED,
    STATUS_INVALID,
    WA_STATUS_VERIFIED,
    WA_STATUS_NOT_VERIFIED,
    WA_STATUS_UNKNOWN,
    INTERACTION_SENT,
    INTERACTION_MANUALLY_MARKED,
)
from utils.logger import info, warning, error

try:
    from playwright_stealth import Stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

STATUS_FILE = os.path.join(DATA_DIR, "whatsapp_status.json")
QR_IMAGE_PATH = os.path.join(DATA_DIR, "whatsapp_qr.png")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

LOGIN_SUCCESS_SELECTORS = [
    "#side",
    "#pane-side",
    "[data-testid='chat-list']",
    "div[role='navigation']",
    "div[aria-label='Chat list']",
    "div[aria-label='قائمة الدردشات']",
    "div[contenteditable='true'][data-tab='3']",
    "header",
    "[data-testid='intro-title']"
]

QR_SELECTORS = [
    "canvas",
    "div[data-ref]",
    "div[data-testid='qrcode']",
    "div[role='dialog'] canvas"
]

QR_RELOAD_SELECTORS = [
    "button:has-text('Click to reload')",
    "button:has-text('إعادة التحميل')",
    "button:has-text('انقر لإعادة')",
    "button[role='button']:has-text('Reload')",
    "div[data-ref] button",
    "div[data-testid='qrcode'] button",
    "span[data-icon='refresh-large']",
    "span[data-icon='reload']",
]


def _apply_stealth(page):
    """Mask Playwright and Chromium automation flags."""
    if STEALTH_AVAILABLE:
        try:
            Stealth().apply_stealth_sync(page)
        except Exception:
            pass


def _bezier_point(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    """Cubic Bezier curve point calculation."""
    return (
        (1 - t)**3 * p0 +
        3 * (1 - t)**2 * t * p1 +
        3 * (1 - t) * t**2 * p2 +
        t**3 * p3
    )


def _human_mouse_move(page, target_x: float, target_y: float, steps: int = 16):
    """Move mouse along a natural human curve with subtle deviations."""
    try:
        start_x = getattr(page, "_human_mouse_x", random.uniform(150, 400))
        start_y = getattr(page, "_human_mouse_y", random.uniform(150, 400))

        dx = target_x - start_x
        dy = target_y - start_y

        ctrl1_x = start_x + dx * random.uniform(0.15, 0.45) + random.uniform(-25, 25)
        ctrl1_y = start_y + dy * random.uniform(0.15, 0.45) + random.uniform(-25, 25)
        ctrl2_x = start_x + dx * random.uniform(0.55, 0.85) + random.uniform(-25, 25)
        ctrl2_y = start_y + dy * random.uniform(0.55, 0.85) + random.uniform(-25, 25)

        for i in range(1, steps + 1):
            t = i / steps
            cx = _bezier_point(start_x, ctrl1_x, ctrl2_x, target_x, t) + random.uniform(-1.0, 1.0)
            cy = _bezier_point(start_y, ctrl1_y, ctrl2_y, target_y, t) + random.uniform(-1.0, 1.0)
            page.mouse.move(cx, cy)
            time.sleep(random.uniform(0.005, 0.012))

        page.mouse.move(target_x, target_y)
        page._human_mouse_x = target_x
        page._human_mouse_y = target_y
    except Exception:
        pass


def _human_click(page, locator) -> bool:
    """Move mouse naturally to locator's bounding box and click with realistic hold duration."""
    try:
        if locator.count() == 0 or not locator.first.is_visible():
            return False
        box = locator.first.bounding_box()
        if not box:
            locator.first.click()
            return True

        pad_x = min(12.0, max(2.0, box["width"] * 0.15))
        pad_y = min(12.0, max(2.0, box["height"] * 0.15))
        target_x = box["x"] + random.uniform(pad_x, max(pad_x + 1.0, box["width"] - pad_x))
        target_y = box["y"] + random.uniform(pad_y, max(pad_y + 1.0, box["height"] - pad_y))

        _human_mouse_move(page, target_x, target_y)
        time.sleep(random.uniform(0.08, 0.22))

        page.mouse.down()
        time.sleep(random.uniform(0.06, 0.13))
        page.mouse.up()
        time.sleep(random.uniform(0.1, 0.25))
        return True
    except Exception:
        try:
            locator.first.click()
            return True
        except Exception:
            return False


class WhatsAppMessenger:
    def __init__(self, db=None, profile_dir=WHATSAPP_PROFILE_DIR, status_file=None, qr_path=None):
        self.db = db
        self.profile_dir = profile_dir
        os.makedirs(self.profile_dir, exist_ok=True)
        self.status_file = status_file if status_file is not None else STATUS_FILE
        self.qr_path = qr_path if qr_path is not None else QR_IMAGE_PATH
        self._worker_thread = None
        self._stop_event = threading.Event()

    def get_connection_status(self) -> str:
        if not os.path.exists(self.profile_dir) or len(os.listdir(self.profile_dir)) == 0:
            if not os.path.exists(self.status_file):
                self._save_status("DISCONNECTED")
                return "DISCONNECTED"

        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("status", "DISCONNECTED")
            except Exception:
                pass
        return "DISCONNECTED"

    def get_status_details(self) -> dict:
        base = {
            "status": "DISCONNECTED",
            "connected": False,
            "message": "",
            "qr_available": False,
            "session_exists": False,
            "worker_running": False,
            "updated_at": "",
        }

        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    base.update(saved)
            except Exception:
                pass

        base["connected"] = base.get("status") == "CONNECTED"
        base["qr_available"] = os.path.exists(self.qr_path) and os.path.getsize(self.qr_path) > 0
        base["session_exists"] = (os.path.exists(self.profile_dir) and len(os.listdir(self.profile_dir)) > 0)
        base["worker_running"] = (self._worker_thread is not None and self._worker_thread.is_alive())

        if base["status"] in ("STARTING", "SCANNING") and not base["worker_running"]:
            if not base["connected"]:
                base["status"] = "DISCONNECTED"
                base["message"] = "انتهت عملية الربط بدون تسجيل دخول. يرجى المحاولة مرة أخرى."

        return base

    def _save_status(self, status: str, extra_info: dict = None):
        data = {
            "status": status,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if extra_info:
            data.update(extra_info)
        try:
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            error(f"Failed to save WhatsApp status: {e}")

    def check_session(self) -> bool:
        return self.get_connection_status() == "CONNECTED"

    def fast_session_check(self) -> bool:
        if not os.path.exists(self.profile_dir) or len(os.listdir(self.profile_dir)) == 0:
            return False
        return self.check_session()

    def _is_on_qr_page(self, page) -> bool:
        """Check if page is currently displaying WhatsApp Web QR login screen."""
        try:
            # If main chat list or navigation or conversation pane is present, NOT on QR page
            if page.locator("#pane-side, #side, [data-testid='chat-list'], #main").count() > 0:
                return False
            # Check known QR selectors
            for q_sel in ["canvas[aria-label*='Scan']", "div[data-ref]", "div[data-testid='qrcode']", "div[role='dialog'] canvas"]:
                loc = page.locator(q_sel)
                if loc.count() > 0 and loc.first.is_visible():
                    return True
            # If any canvas exists on the root without chat list
            canvases = page.locator("canvas")
            if canvases.count() > 0 and canvases.first.is_visible():
                return True
        except Exception:
            pass
        return False

    def _open_chat_via_search(self, page, digits: str) -> bool:
        """
        Open a chat with phone digits using WhatsApp Web's in-app search/new chat UI,
        simulating authentic human navigation and avoiding the telemetry of repeated URL visits.
        Returns True if chat was successfully loaded into #main, False otherwise.
        """
        SEARCH_SELECTORS = [
            "div[data-testid='chat-list-search'][contenteditable='true']",
            "#side div[contenteditable='true'][role='textbox']",
            "div[role='textbox'][data-tab='3']",
            "div[aria-label='Search or start new chat']",
            "div[aria-label='بحث أو بدء دردشة جديدة']",
            "div[aria-label='Search input']",
            "#side div[contenteditable='true']"
        ]

        NEW_CHAT_BTN_SELECTORS = [
            "button[aria-label='New chat']",
            "div[role='button'][title='New chat']",
            "div[role='button'][title='دردشة جديدة']",
            "span[data-icon='new-chat-outline']",
            "span[data-icon='chat']",
            "button[data-testid='chat-list-search-icon']"
        ]

        try:
            search_box = None
            for sel in SEARCH_SELECTORS:
                try:
                    loc = page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        search_box = loc.first
                        break
                except Exception:
                    pass

            if not search_box:
                for b_sel in NEW_CHAT_BTN_SELECTORS:
                    try:
                        b_loc = page.locator(b_sel)
                        if b_loc.count() > 0 and b_loc.first.is_visible():
                            _human_click(page, b_loc)
                            time.sleep(1.0)
                            break
                    except Exception:
                        pass

                for sel in SEARCH_SELECTORS:
                    try:
                        loc = page.locator(sel)
                        if loc.count() > 0 and loc.first.is_visible():
                            search_box = loc.first
                            break
                    except Exception:
                        pass

            if not search_box:
                return False

            _human_click(page, search_box)
            time.sleep(random.uniform(0.3, 0.6))

            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            time.sleep(0.2)

            # Type phone number with human cadence
            for ch in digits:
                page.keyboard.type(ch)
                time.sleep(random.uniform(0.04, 0.08))

            time.sleep(2.5)

            # Search results selectors
            tail_digits = digits[-7:] if len(digits) >= 7 else digits
            RESULT_SELECTORS = [
                f"#pane-side span[title*='{tail_digits}']",
                f"#side span[title*='{tail_digits}']",
                "#pane-side div[data-testid='cell-frame-container']",
                "#pane-side div[role='listitem']",
                "#side div[role='listitem']",
                "div[data-testid='chat-list'] div[role='gridcell']",
                "div[data-testid='contact-list-key']"
            ]

            chat_item = None
            start_srch = time.time()
            while time.time() - start_srch < 6:
                for r_sel in RESULT_SELECTORS:
                    try:
                        r_loc = page.locator(r_sel)
                        if r_loc.count() > 0 and r_loc.first.is_visible():
                            chat_item = r_loc.first
                            break
                    except Exception:
                        pass
                if chat_item:
                    break
                time.sleep(0.6)

            if chat_item:
                _human_click(page, chat_item)
                time.sleep(random.uniform(1.5, 2.5))
                if page.locator("#main").count() > 0 and page.locator("#main").first.is_visible():
                    return True

            page.keyboard.press("Enter")
            time.sleep(1.5)
            if page.locator("#main").count() > 0 and page.locator("#main").first.is_visible():
                return True

            return False
        except Exception as e:
            warning(f"In-app search navigation: {e}")
            return False

    def start_qr_linking_worker(self, headless=True, timeout_sec=120):
        if self._worker_thread and self._worker_thread.is_alive():
            info("WhatsApp: Worker thread is already active.")
            return True

        self._stop_event.clear()
        self._save_status("STARTING", {"message": "جاري فتح متصفح WhatsApp Web..."})

        self._worker_thread = threading.Thread(
            target=self._run_linking_worker,
            args=(headless, timeout_sec),
            daemon=True
        )
        self._worker_thread.start()
        return True

    def _run_linking_worker(self, headless, timeout_sec):
        from playwright.sync_api import sync_playwright

        info(f"WhatsApp Worker: Starting (headless={headless}, timeout={timeout_sec}s)...")
        context = None

        try:
            with sync_playwright() as p:
                launch_args = [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
                if not headless:
                    launch_args.extend(["--window-position=150,100", "--window-size=1100,850"])

                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.profile_dir,
                    headless=headless,
                    user_agent=USER_AGENT,
                    viewport={"width": 1100, "height": 850} if headless else None,
                    args=launch_args
                )
                page = context.new_page()
                page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)

                start_time = time.time()
                last_qr_ref = None
                last_capture_time = 0
                qr_captured = False

                while time.time() - start_time < timeout_sec:
                    if self._stop_event.is_set():
                        info("WhatsApp Worker: Stop event received. Terminating.")
                        break

                    # 1. Check if logged in
                    is_logged_in = False
                    for selector in LOGIN_SUCCESS_SELECTORS:
                        try:
                            if page.locator(selector).count() > 0:
                                is_logged_in = True
                                break
                        except Exception:
                            pass

                    if is_logged_in:
                        info("WhatsApp Worker: Chat list detected! Login successful.")
                        self._save_status("CONNECTED", {"message": "تم تسجيل الدخول بنجاح!"})
                        if os.path.exists(self.qr_path):
                            try:
                                os.remove(self.qr_path)
                            except Exception:
                                pass
                        time.sleep(3)
                        context.close()
                        return

                    # 2. Check for expired QR reload button
                    for r_sel in QR_RELOAD_SELECTORS:
                        try:
                            r_btn = page.locator(r_sel)
                            if r_btn.count() > 0 and r_btn.first.is_visible():
                                r_btn.first.click()
                                time.sleep(1.2)
                                break
                        except Exception:
                            pass

                    # 3. Screenshot QR canvas
                    now = time.time()
                    for qr_sel in QR_SELECTORS:
                        try:
                            loc = page.locator(qr_sel)
                            if loc.count() > 0 and loc.first.is_visible():
                                current_ref = loc.first.get_attribute("data-ref")
                                if (current_ref != last_qr_ref) or (not qr_captured) or (now - last_capture_time > 3.5):
                                    loc.first.screenshot(path=self.qr_path)
                                    last_qr_ref = current_ref
                                    last_capture_time = now
                                    qr_captured = True
                                    remaining = int(timeout_sec - (now - start_time))
                                    self._save_status("SCANNING", {
                                        "message": "كود الـ QR محدث وجاهز للمسح...",
                                        "remaining_sec": remaining,
                                        "refreshed_at": now
                                    })
                                    break
                        except Exception:
                            pass

                    time.sleep(1)

                info("WhatsApp Worker: Timeout reached without login.")
                if self.get_connection_status() != "CONNECTED":
                    self._save_status("DISCONNECTED", {"message": "انتهت مهلة مسح الـ QR Code."})
                if os.path.exists(self.qr_path):
                    try:
                        os.remove(self.qr_path)
                    except Exception:
                        pass
                if context:
                    context.close()

        except Exception as e:
            error(f"WhatsApp Worker Error: {e}")
            self._save_status("ERROR", {"message": f"خطأ أثناء تشغيل المتصفح: {e}"})
            if context:
                try:
                    context.close()
                except Exception:
                    pass

    def cancel_worker(self):
        self._stop_event.set()
        if os.path.exists(self.qr_path):
            try:
                os.remove(self.qr_path)
            except Exception:
                pass
        self._save_status("DISCONNECTED")

    def verify_saved_session(self, timeout_sec=20) -> bool:
        from playwright.sync_api import sync_playwright

        if not os.path.exists(self.profile_dir) or len(os.listdir(self.profile_dir)) == 0:
            self._save_status("DISCONNECTED")
            return False

        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.profile_dir,
                    headless=True,
                    user_agent=USER_AGENT,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                page = context.new_page()
                page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=45000)

                start = time.time()
                while time.time() - start < timeout_sec:
                    for sel in LOGIN_SUCCESS_SELECTORS:
                        try:
                            if page.locator(sel).count() > 0:
                                self._save_status("CONNECTED")
                                context.close()
                                return True
                        except Exception:
                            pass

                    for qsel in QR_SELECTORS:
                        try:
                            if page.locator(qsel).count() > 0:
                                self._save_status("DISCONNECTED", {"message": "انتهت صلاحية الجلسة."})
                                context.close()
                                return False
                        except Exception:
                            pass
                    time.sleep(1)

                context.close()
                return False
        except Exception as e:
            error(f"WhatsApp: Error during session verification: {e}")
            return False

    def disconnect(self) -> bool:
        self.cancel_worker()
        self._save_status("DISCONNECTED")
        if os.path.exists(self.qr_path):
            try:
                os.remove(self.qr_path)
            except Exception:
                pass
        try:
            if os.path.exists(self.profile_dir):
                shutil.rmtree(self.profile_dir, ignore_errors=True)
                os.makedirs(self.profile_dir, exist_ok=True)
            return True
        except Exception as e:
            error(f"WhatsApp: Error clearing session files: {e}")
            return False

    def can_contact(self, lead_id=None, status=None, whatsapp_status=None) -> tuple[bool, str]:
        if status == STATUS_DO_NOT_CONTACT:
            return False, "هذا العميل في قائمة الحظر (DO_NOT_CONTACT) وممنوع التواصل معه نهائياً."

        if whatsapp_status == WA_STATUS_NOT_VERIFIED:
            return False, "هذا الرقم تم التحقق منه وتأكد أنه غير موجود على WhatsApp."

        if lead_id is not None and self.db is not None:
            lead = self.db.get_lead_by_id(lead_id)
            if lead is not None:
                if len(lead) > 9 and lead[9] == STATUS_DO_NOT_CONTACT:
                    return False, "هذا العميل في قائمة الحظر (DO_NOT_CONTACT) وممنوع التواصل معه نهائياً."
                if len(lead) > 13 and lead[13] == WA_STATUS_NOT_VERIFIED:
                    return False, "هذا الرقم تم التحقق منه وتأكد أنه غير موجود على WhatsApp."

        return True, ""

    def verify_whatsapp_number(self, phone: str, timeout_sec: int = 8) -> str:
        """
        Verify if a given phone number has an active WhatsApp account using WhatsApp Web.
        Returns: WA_STATUS_VERIFIED, WA_STATUS_NOT_VERIFIED, or WA_STATUS_UNKNOWN.
        """
        if not self.check_session():
            return WA_STATUS_UNKNOWN

        norm_phone = normalize_phone(phone)
        if not norm_phone or len(norm_phone) < 10 or not is_mobile_phone(norm_phone):
            return WA_STATUS_NOT_VERIFIED

        digits = norm_phone.lstrip("+")
        url = f"https://web.whatsapp.com/send?phone={digits}"

        from playwright.sync_api import sync_playwright

        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.profile_dir,
                    headless=True,
                    user_agent=USER_AGENT,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=30000)

                start = time.time()
                while time.time() - start < timeout_sec:
                    # 1. Invalid number modal check
                    try:
                        popup = page.locator("div[data-testid='confirm-popup'], div[role='dialog']")
                        if popup.count() > 0 and popup.first.is_visible():
                            text = popup.first.inner_text().lower()
                            if any(msg in text for msg in ["invalid", "غير صالح", "not on whatsapp", "لا يستخدم", "url"]):
                                context.close()
                                return WA_STATUS_NOT_VERIFIED
                    except Exception:
                        pass

                    # 2. Composer loaded
                    try:
                        composer = page.locator("div[contenteditable='true'][data-tab='10'], #main, footer")
                        if composer.count() > 0:
                            context.close()
                            return WA_STATUS_VERIFIED
                    except Exception:
                        pass

                    time.sleep(1)

                context.close()
                return WA_STATUS_UNKNOWN
        except Exception as e:
            warning(f"WhatsApp verification error for {phone}: {e}")
            return WA_STATUS_UNKNOWN

    def send_supervised(self, lead_id: int, phone: str, message: str, delay: int = None) -> tuple[bool, str]:
        """
        Backward compatible method: Records manual outreach review.
        Reality-based: Records interaction status as 'MANUALLY_MARKED' (not fake 'SENT').
        """
        allowed, reason = self.can_contact(lead_id=lead_id)
        if not allowed:
            return False, reason

        norm_phone = normalize_phone(phone)
        if not norm_phone:
            return False, "رقم الهاتف غير صالح."

        if self.db and lead_id:
            self.db.update_lead_status(lead_id, STATUS_CONTACTED)
            self.db.insert_interaction(
                lead_id=lead_id,
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                channel="Manual WhatsApp Review",
                message=message,
                status=INTERACTION_MANUALLY_MARKED,
                notes="Manually recorded by user in outreach queue"
            )

        info(f"Outreach: Manually marked contact for {norm_phone}")
        return True, f"تم تسجيل المراجعة والتواصل يدوياً للرقم {norm_phone}"

    def send_via_playwright(self, lead_id: int, phone: str, message: str) -> tuple[bool, str]:
        """
        Send a REAL WhatsApp message using Playwright persistent context.
        Requires verified session and strictly respects DO_NOT_CONTACT.
        """
        allowed, reason = self.can_contact(lead_id=lead_id)
        if not allowed:
            return False, reason

        norm_phone = normalize_phone(phone)
        if not norm_phone:
            return False, "رقم هاتف غير صالح."

        digits = norm_phone.lstrip("+")
        encoded_text = urllib.parse.quote(message)
        send_url = f"https://web.whatsapp.com/send?phone={digits}&text={encoded_text}"

        from playwright.sync_api import sync_playwright

        COMPOSER_SELECTORS = [
            "footer div[contenteditable='true']",
            "div[contenteditable='true'][data-tab='10']",
            "div[data-testid='conversation-compose-box-input']",
            "div[role='textbox'][contenteditable='true']",
            "#main div[contenteditable='true']",
            "div[aria-label='Type a message']",
            "div[aria-label='اكتب رسالة']",
            "div[aria-label='رسالة']",
        ]

        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.profile_dir,
                    headless=True,
                    user_agent=USER_AGENT,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
                )
                page = context.new_page()
                _apply_stealth(page)
                page.goto(send_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(2.5)

                start_wait = time.time()
                chat_loaded = False
                invalid_number = False

                while time.time() - start_wait < 35:
                    # 1. Check if QR code is visible (session disconnected)
                    if self._is_on_qr_page(page):
                        self._save_status("DISCONNECTED", {"message": "جلسة WhatsApp غير متصلة."})
                        context.close()
                        return False, "⚠️ جلسة WhatsApp Web غير متصلة! يرجى مسح رمز الـ QR أولاً من شاشة تسجيل الدخول لربط حسابك عبر الهاتف."

                    # 2. Invalid number dialog check
                    try:
                        popup = page.locator("div[data-testid='confirm-popup'], div[role='dialog']")
                        if popup.count() > 0 and popup.first.is_visible():
                            text = popup.first.inner_text().lower()
                            if any(msg in text for msg in ["invalid", "غير صالح", "url", "not on whatsapp"]):
                                invalid_number = True
                                break
                    except Exception:
                        pass

                    # 3. Check composer
                    for c_sel in COMPOSER_SELECTORS:
                        try:
                            loc = page.locator(c_sel)
                            if loc.count() > 0 and loc.first.is_visible():
                                chat_loaded = True
                                break
                        except Exception:
                            pass
                    if chat_loaded:
                        break

                    time.sleep(1)

                if invalid_number:
                    if self.db and lead_id:
                        self.db.update_lead_whatsapp_status(lead_id, WA_STATUS_NOT_VERIFIED)
                        self.db.update_lead_status(lead_id, STATUS_INVALID)
                    context.close()
                    return False, f"⚠️ رقم الهاتف {phone} غير مسجل على WhatsApp."

                if not chat_loaded:
                    context.close()
                    return False, "❌ تعذر تحميل المحادثة. يمكنك استخدام الرابط المباشر (wa.me) كبديل."

                composer = None
                for c_sel in COMPOSER_SELECTORS:
                    try:
                        loc = page.locator(c_sel)
                        if loc.count() > 0 and loc.first.is_visible():
                            composer = loc.first
                            break
                    except Exception:
                        pass

                if composer is None:
                    context.close()
                    return False, "❌ تعذر تحديد مربع الكتابة."

                _human_click(page, composer)
                self._type_human_like(page, composer, message)

                sent = False
                send_selectors = [
                    "button[data-testid='compose-btn-send']",
                    "button[aria-label*='Send']",
                    "button[aria-label*='إرسال']",
                    "span[data-icon='send']",
                    "button:has(span[data-icon='send'])",
                ]

                for sel in send_selectors:
                    try:
                        btn = page.locator(sel)
                        if btn.count() > 0 and btn.first.is_visible():
                            _human_click(page, btn)
                            sent = True
                            break
                    except Exception:
                        pass

                if not sent:
                    if composer:
                        try:
                            composer.press("Enter")
                            sent = True
                        except Exception:
                            pass
                    try:
                        page.keyboard.press("Enter")
                        sent = True
                    except Exception:
                        pass

                time.sleep(3)
                context.close()

            if self.db and lead_id:
                self.db.update_lead_status(lead_id, STATUS_CONTACTED)
                self.db.insert_interaction(
                    lead_id=lead_id,
                    date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    channel="WhatsApp Web (Playwright)",
                    message=message,
                    status=INTERACTION_SENT,
                    notes="Sent via Playwright automated session"
                )

            self._save_status("CONNECTED")
            return True, "✅ تم إرسال الرسالة بنجاح عبر جلسة WhatsApp Web!"

        except Exception as e:
            error(f"WhatsApp Playwright send error: {e}")
            return False, f"تعذر الإرسال: {e}"

    def _type_human_like(self, page, composer, message: str, status_callback=None):
        """
        Simulate authentic human typing behavior on WhatsApp Web:
        - Clicks into the message composer to gain real keyboard focus.
        - Types character by character with realistic speed fluctuations (35ms - 85ms).
        - Spaces, newlines, and punctuation have slightly longer natural pauses (60ms - 150ms).
        - Introduces subtle human typos (1-2 typos on longer text) with backspace correction.
        - Inserts periodic 'thinking/drafting' pauses every few seconds (3s, 5s, or 10s)
          which naturally activates and reactivates WhatsApp's 'typing...' (يكتب الآن...) presence indicator.
        - Pauses for 1.2 to 2.5 seconds before hitting send (reviewing what was written).
        """
        import random
        import time

        TYPO_MAP = {
            'م': 'ن', 'ن': 'م', 'ا': 'ل', 'ل': 'ا', 'ي': 'ب', 'ب': 'ي',
            'ت': 'ن', 'ك': 'م', 'و': 'ر', 'ر': 'و', 'د': 'ج', 'ج': 'ح',
            'ف': 'ق', 'ق': 'ف', 'س': 'ش', 'ش': 'س', 'ص': 'ض',
        }

        try:
            _human_click(page, composer)
            time.sleep(random.uniform(0.5, 1.0))

            existing = composer.inner_text().strip()
            if existing:
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                time.sleep(0.3)

            # Pick 1 or 2 natural typo positions on longer messages
            typo_positions = set()
            if len(message) > 40:
                candidates = [i for i, c in enumerate(message[10:-10], 10) if c in TYPO_MAP and message[i - 1].isalnum()]
                if candidates:
                    num_typos = random.choice([1, min(2, len(candidates))])
                    typo_positions = set(random.sample(candidates, num_typos))

            chars_since_pause = 0
            next_pause_target = random.randint(16, 30)

            for idx, char in enumerate(message):
                # Simulate a natural human typo & correction
                if idx in typo_positions and char in TYPO_MAP:
                    wrong_char = TYPO_MAP[char]
                    page.keyboard.type(wrong_char)
                    time.sleep(random.uniform(0.18, 0.35))
                    page.keyboard.press("Backspace")
                    time.sleep(random.uniform(0.10, 0.20))

                if char == '\n':
                    page.keyboard.press("Shift+Enter")
                    time.sleep(random.uniform(0.08, 0.16))
                else:
                    page.keyboard.type(char)
                chars_since_pause += 1

                keystroke_delay = random.uniform(0.035, 0.085)
                if char in (' ', '\n', '،', '؟', '.', '!', '-'):
                    keystroke_delay += random.uniform(0.05, 0.12)
                time.sleep(keystroke_delay)

                if chars_since_pause >= next_pause_target and idx < len(message) - 8:
                    pause_type = random.choices(["short", "medium", "thoughtful"], weights=[50, 35, 15])[0]
                    if pause_type == "short":
                        pause_sec = random.uniform(2.5, 3.8)
                    elif pause_type == "medium":
                        pause_sec = random.uniform(4.5, 6.0)
                    else:
                        pause_sec = random.uniform(8.0, 10.5)

                    if status_callback:
                        status_callback(f"✍️ جاري الكتابة... (توقف طبيعي {pause_sec:.1f} ثوانٍ - مؤشر 'يكتب الآن...' نشط)")

                    time.sleep(pause_sec)
                    chars_since_pause = 0
                    next_pause_target = random.randint(16, 32)

            time.sleep(random.uniform(1.2, 2.2))

        except Exception as e:
            try:
                page.keyboard.insert_text(message)
                time.sleep(0.8)
            except Exception:
                try:
                    composer.fill(message)
                    time.sleep(0.8)
                except Exception:
                    pass

    def send_batch_automated(
        self,
        items: list[dict],
        min_delay: int = 90,
        max_delay: int = 180,
        enable_human_typing: bool = True,
        batch_size: int = 5,
        enable_cooldown: bool = True,
        cooldown_min: int = 900,
        cooldown_max: int = 1500,
        progress_callback = None
    ) -> dict:
        """
        Send WhatsApp messages in batch automatically with complete anti-ban stealth:
        - Uses Playwright Stealth injection to mask automation fingerprints.
        - Employs Bézier curve human mouse movements and realistic hold clicks.
        - Uses in-app search navigation to avoid repeated direct URL navigation telemetry.
        - Simulates human typing with authentic pauses and subtle typo corrections.
        - Enforces safe individual delays (90-180s) and batch cooldown pauses (15-25 mins).
        """
        import random
        from playwright.sync_api import sync_playwright

        results = {"total": len(items), "sent": 0, "failed": 0, "details": []}
        if not items:
            return results

        COMPOSER_SELECTORS = [
            "footer div[contenteditable='true']",
            "div[contenteditable='true'][data-tab='10']",
            "div[data-testid='conversation-compose-box-input']",
            "div[role='textbox'][contenteditable='true']",
            "#main div[contenteditable='true']",
            "div[aria-label='Type a message']",
            "div[aria-label='اكتب رسالة']",
            "div[aria-label='رسالة']",
        ]

        SEND_SELECTORS = [
            "button[data-testid='compose-btn-send']",
            "button[aria-label*='Send']",
            "button[aria-label*='إرسال']",
            "span[data-icon='send']",
            "button:has(span[data-icon='send'])",
        ]

        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.profile_dir,
                    headless=True,
                    user_agent=USER_AGENT,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
                )
                page = context.new_page()
                _apply_stealth(page)

                # Open WhatsApp Web once at the start of the batch session
                page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=45000)
                time.sleep(3)

                for idx, itm in enumerate(items):
                    lead_id = itm.get("id")
                    phone = itm.get("phone", "")
                    message = itm.get("message", "")
                    lead_name = itm.get("name", "عميل")

                    # Check contact permissions
                    if lead_id:
                        allowed, reason = self.can_contact(lead_id=lead_id)
                        if not allowed:
                            results["failed"] += 1
                            results["details"].append({"id": lead_id, "name": lead_name, "success": False, "error": reason})
                            if progress_callback:
                                progress_callback(idx + 1, len(items), lead_name, False, reason)
                            continue

                    norm_phone = normalize_phone(phone)
                    if not norm_phone:
                        results["failed"] += 1
                        results["details"].append({"id": lead_id, "name": lead_name, "success": False, "error": "رقم غير صالح"})
                        if progress_callback:
                            progress_callback(idx + 1, len(items), lead_name, False, "رقم غير صالح")
                        continue

                    digits = norm_phone.lstrip("+")
                    chat_loaded = False
                    invalid_number = False

                    # Check if QR code is visible (session disconnected)
                    if self._is_on_qr_page(page):
                        self._save_status("DISCONNECTED", {"message": "جلسة WhatsApp غير متصلة."})
                        context.close()
                        err_msg = "⚠️ جلسة WhatsApp Web غير متصلة! يرجى مسح رمز الـ QR أولاً لربط حسابك عبر الهاتف."
                        if progress_callback:
                            progress_callback(idx + 1, len(items), lead_name, False, err_msg)
                        return {
                            "total": len(items),
                            "sent": 0,
                            "failed": len(items),
                            "details": [{"id": lead_id, "name": lead_name, "success": False, "error": err_msg}]
                        }

                    # Step 1: Attempt in-app search navigation (100% human pattern)
                    try:
                        if self._open_chat_via_search(page, digits):
                            chat_loaded = True
                    except Exception as s_err:
                        warning(f"In-app search failed for {digits}: {s_err}")

                    # Step 2: Fallback to direct navigation if in-app search couldn't open chat
                    if not chat_loaded:
                        send_url = f"https://web.whatsapp.com/send?phone={digits}"
                        try:
                            page.goto(send_url, wait_until="domcontentloaded", timeout=45000)
                            time.sleep(2)
                        except Exception as nav_err:
                            warning(f"Fallback navigation error: {nav_err}")

                        start_wait = time.time()
                        while time.time() - start_wait < 35:
                            if self._is_on_qr_page(page):
                                self._save_status("DISCONNECTED", {"message": "جلسة WhatsApp غير متصلة."})
                                context.close()
                                err_msg = "⚠️ جلسة WhatsApp Web غير متصلة! يرجى مسح رمز الـ QR أولاً لربط حسابك عبر الهاتف."
                                if progress_callback:
                                    progress_callback(idx + 1, len(items), lead_name, False, err_msg)
                                return {
                                    "total": len(items),
                                    "sent": 0,
                                    "failed": len(items),
                                    "details": [{"id": lead_id, "name": lead_name, "success": False, "error": err_msg}]
                                }

                            try:
                                popup = page.locator("div[data-testid='confirm-popup'], div[role='dialog']")
                                if popup.count() > 0 and popup.first.is_visible():
                                    text = popup.first.inner_text().lower()
                                    if any(msg in text for msg in ["invalid", "غير صالح", "url", "not on whatsapp"]):
                                        invalid_number = True
                                        break
                            except Exception:
                                pass

                            for c_sel in COMPOSER_SELECTORS:
                                try:
                                    loc = page.locator(c_sel)
                                    if loc.count() > 0 and loc.first.is_visible():
                                        chat_loaded = True
                                        break
                                except Exception:
                                    pass
                            if chat_loaded:
                                break

                            time.sleep(1)

                    if invalid_number:
                        if self.db and lead_id:
                            self.db.update_lead_whatsapp_status(lead_id, WA_STATUS_NOT_VERIFIED)
                            self.db.update_lead_status(lead_id, STATUS_INVALID)
                        results["failed"] += 1
                        results["details"].append({"id": lead_id, "name": lead_name, "success": False, "error": "الرقم غير مسجل على واتساب"})
                        if progress_callback:
                            progress_callback(idx + 1, len(items), lead_name, False, "الرقم غير مسجل على واتساب")
                        continue

                    if not chat_loaded:
                        results["failed"] += 1
                        results["details"].append({"id": lead_id, "name": lead_name, "success": False, "error": "تعذر تحميل المحادثة"})
                        if progress_callback:
                            progress_callback(idx + 1, len(items), lead_name, False, "تعذر تحميل المحادثة")
                        continue

                    composer = None
                    for c_sel in COMPOSER_SELECTORS:
                        try:
                            loc = page.locator(c_sel)
                            if loc.count() > 0 and loc.first.is_visible():
                                composer = loc.first
                                break
                        except Exception:
                            pass

                    if composer:
                        _human_click(page, composer)
                        if enable_human_typing:
                            typing_cb = lambda note: progress_callback(idx + 1, len(items), lead_name, True, note) if progress_callback else None
                            self._type_human_like(page, composer, message, status_callback=typing_cb)
                        else:
                            time.sleep(0.4)
                            try:
                                page.keyboard.insert_text(message)
                            except Exception:
                                composer.fill(message)
                            time.sleep(0.5)

                    sent = False
                    for sel in SEND_SELECTORS:
                        try:
                            btn = page.locator(sel)
                            if btn.count() > 0 and btn.first.is_visible():
                                _human_click(page, btn)
                                sent = True
                                break
                        except Exception:
                            pass

                    if not sent:
                        if composer:
                            try:
                                composer.press("Enter")
                                sent = True
                            except Exception:
                                pass
                        try:
                            page.keyboard.press("Enter")
                            sent = True
                        except Exception:
                            pass

                    time.sleep(2.5)

                    if self.db and lead_id:
                        self.db.update_lead_status(lead_id, STATUS_CONTACTED)
                        self.db.insert_interaction(
                            lead_id=lead_id,
                            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            channel="WhatsApp Web (Playwright Automated)",
                            message=message,
                            status=INTERACTION_SENT,
                            notes="Sent via anti-detection batch pilot with human typing & in-app search"
                        )

                    results["sent"] += 1
                    results["details"].append({"id": lead_id, "name": lead_name, "success": True, "error": None})
                    if progress_callback:
                        progress_callback(idx + 1, len(items), lead_name, True, "تم الإرسال بنجاح ✅")

                    # Safety intervals & Batch cooling
                    if idx < len(items) - 1:
                        is_batch_end = enable_cooldown and ((idx + 1) % batch_size == 0)
                        if is_batch_end:
                            cooldown_wait = random.randint(int(cooldown_min), int(cooldown_max))
                            info(f"WhatsApp batch: Cooling down for {cooldown_wait}s after batch of {idx + 1} messages...")
                            for rem in range(cooldown_wait, 0, -1):
                                m, s = divmod(rem, 60)
                                if progress_callback:
                                    progress_callback(
                                        idx + 1,
                                        len(items),
                                        lead_name,
                                        True,
                                        f"🛑 استراحة أمان لحماية الحساب (اكتملت دفعة {idx + 1} عملاء): متبقي {m} دقيقة و {s:02d} ثانية..."
                                    )
                                if rem % 45 == 0:
                                    try:
                                        _human_mouse_move(page, random.uniform(200, 600), random.uniform(200, 500))
                                    except Exception:
                                        pass
                                time.sleep(1)
                        else:
                            random_wait = random.randint(int(min_delay), int(max_delay))
                            info(f"WhatsApp batch: waiting random anti-ban safety interval of {random_wait} seconds...")
                            for remaining in range(random_wait, 0, -1):
                                m, s = divmod(remaining, 60)
                                desc = f"{m} دقيقة و {s:02d} ثانية" if m > 0 else f"{s} ثانية"
                                if progress_callback:
                                    progress_callback(
                                        idx + 1,
                                        len(items),
                                        lead_name,
                                        True,
                                        f"⏳ فاصل أمان بشري عشوائي: متبقي {desc} لحماية رقمك..."
                                    )
                                time.sleep(1)

                context.close()

        except Exception as e:
            error(f"WhatsApp send_batch_automated error: {e}")

        return results

    def generate_direct_link(self, phone: str, message: str) -> str:
        return generate_direct_link(phone, message)
