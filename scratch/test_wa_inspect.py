import sys
import os
import time

sys.path.insert(0, "d:/AI feed/AutoLeadGen")

from playwright.sync_api import sync_playwright
from config.settings import WHATSAPP_PROFILE_DIR
from integrations.whatsapp_playwright import USER_AGENT

digits = "201012345678"
send_url = f"https://web.whatsapp.com/send?phone={digits}"

print(f"Profile: {WHATSAPP_PROFILE_DIR}")
print(f"Opening: {send_url}")

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=WHATSAPP_PROFILE_DIR,
        headless=True,
        user_agent=USER_AGENT,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
    )
    page = context.new_page()
    page.goto(send_url, wait_until="domcontentloaded", timeout=45000)
    
    print("Waiting 10 seconds to see what renders...")
    time.sleep(10)
    
    print(f"Current Page URL: {page.url}")
    print(f"Page Title: {page.title()}")
    
    page.screenshot(path="d:/AI feed/AutoLeadGen/scratch/wa_debug.png")
    print("Screenshot saved to scratch/wa_debug.png")
    
    # Check if QR code is shown or main screen
    has_qr = page.locator("canvas[aria-label*='Scan'], div[data-ref]").count() > 0
    print(f"Has QR canvas: {has_qr}")
    
    # Check dialogs or popups
    popups = page.locator("div[role='dialog'], div[data-testid='confirm-popup']")
    print(f"Popups found: {popups.count()}")
    if popups.count() > 0:
        print(f"Popup text: {popups.first.inner_text()}")
        
    # Check side pane / main pane
    side = page.locator("#side, #pane-side").count()
    main = page.locator("#main").count()
    print(f"Side count: {side}, Main count: {main}")
    
    context.close()
