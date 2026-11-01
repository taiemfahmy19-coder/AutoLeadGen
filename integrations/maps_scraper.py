"""AutoLeadGen v2 - Integrations: Google Maps Live Lead Discovery (REAL NUMBERS ONLY — NO FAKES)."""
import re
import time
import urllib.parse
from pipeline.cleaner import normalize_phone, is_mobile_phone, clean_business_name, clean_address
from config.constants import WA_STATUS_UNKNOWN, WA_STATUS_VERIFIED, WA_STATUS_NOT_VERIFIED, INDUSTRY_TRANSLATIONS, ARAB_COUNTRIES
from utils.logger import info, warning, error


class LeadScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    def search_leads(
        self,
        industry: str,
        city: str,
        country: str = "مصر",
        country_code: str = "20",
        limit: int = 10,
        use_live_browser: bool = True,
        whatsapp_only: bool = True,
        search_engine: str = "maps",   # ignored — always Google Maps
        messenger=None,
        exclude_phones: set = None,
        progress_cb=None,
    ) -> list[dict]:
        """
        Search for REAL business leads via Google Maps live browser scraping ONLY.
        STRICT POLICY:
          - Never fabricates or randomizes phone numbers.
          - Only returns numbers extracted directly from Google Maps business cards.
          - Filters for mobile/WhatsApp-capable numbers when whatsapp_only=True.
          - Hard cap of 50 leads per search.
          - Excludes any phone already in exclude_phones.
        """
        limit = min(50, max(1, int(limit)))
        info(f"LeadScraper: Searching '{industry}' in '{city}, {country}' (target={limit}, wa_only={whatsapp_only})...")

        seen_phones = set(exclude_phones) if exclude_phones else set()

        if not use_live_browser:
            warning("LeadScraper: use_live_browser=False — Google Maps requires a live browser. Returning empty.")
            return []

        # Google Maps live scraping — the ONLY real source
        raw_leads = []
        try:
            maps_leads = self._scrape_with_playwright(
                industry=industry,
                city=city,
                country=country,
                country_code=country_code,
                limit=limit,
                whatsapp_only=whatsapp_only,
                messenger=messenger,
                progress_cb=progress_cb,
            )
            for lead in maps_leads:
                p = lead.get("phone", "")
                if p and p not in seen_phones:
                    seen_phones.add(p)
                    raw_leads.append(lead)
        except Exception as e:
            error(f"LeadScraper: Google Maps scraping error: {e}")

        # Final validation — phone normalization + mobile filter
        validated = []
        for item in raw_leads:
            phone = item.get("phone", "")
            norm = normalize_phone(phone, default_country_code=country_code)
            if not norm:
                continue

            item["phone"] = norm

            if whatsapp_only and not is_mobile_phone(norm):
                continue

            wa_st = item.get("whatsapp_status") or (WA_STATUS_VERIFIED if is_mobile_phone(norm) else WA_STATUS_UNKNOWN)
            item["whatsapp_status"] = wa_st

            validated.append(item)
            if len(validated) >= limit:
                break

        info(f"LeadScraper: Returning {len(validated)} validated real leads from Google Maps.")
        return validated

    def _scrape_with_playwright(
        self,
        industry: str,
        city: str,
        country: str,
        country_code: str,
        limit: int,
        whatsapp_only: bool = True,
        messenger=None,
        progress_cb=None,
    ) -> list[dict]:
        """
        Playwright-based Google Maps scraper.
        Extracts authentic phone numbers directly from official Google Maps business cards.
        Continuously scrolls until reaching the target number of leads or end of results.
        """
        from playwright.sync_api import sync_playwright
        collected = []
        seen_phones = set()

        clean_country = re.sub(r"\(.*?\)", "", country).strip()

        # Check if targeting an Arab country or non-Arab
        is_arab_country = any(ac.lower() in clean_country.lower() for ac in ARAB_COUNTRIES)
        
        # Build smart bilingual query for international countries
        search_industry = industry.strip()
        if not is_arab_country:
            en_ind = INDUSTRY_TRANSLATIONS.get(search_industry)
            if not en_ind:
                for ar_k, en_v in INDUSTRY_TRANSLATIONS.items():
                    if ar_k in search_industry:
                        en_ind = en_v
                        break
            if en_ind:
                search_industry = en_ind

        location_part = f"{city} {clean_country}".strip()
        search_query = f"{search_industry} in {location_part}".strip()
        maps_url = f"https://www.google.com/maps/search/{urllib.parse.quote(search_query)}"

        info(f"LeadScraper: Navigating → {maps_url} (Target={limit})")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--blink-settings=imagesEnabled=false",
                    "--disable-remote-fonts",
                    "--disable-background-networking",
                    "--disable-default-apps",
                    "--disable-extensions",
                    "--disable-sync",
                    "--disable-translate",
                    "--metrics-recording-only",
                    "--no-first-run",
                ]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                locale="ar-EG" if is_arab_country else "en-US",
            )
            context.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())
            page = context.new_page()

            try:
                page.goto(maps_url, timeout=35000)
                page.wait_for_timeout(1500)

                # Dismiss consent popups
                for c_sel in [
                    "button:has-text('Accept all')",
                    "button:has-text('قبول الكل')",
                    "button:has-text('موافق')",
                    "button:has-text('Tout accepter')",
                    "button:has-text('I agree')",
                ]:
                    try:
                        c_btn = page.locator(c_sel)
                        if c_btn.count() > 0 and c_btn.first.is_visible():
                            c_btn.first.click()
                            page.wait_for_timeout(500)
                            break
                    except Exception:
                        pass

                # Dynamic continuous scrolling loop to accumulate enough business cards
                # Needs roughly limit * 2.5 cards to guarantee target leads with mobile numbers
                target_cards_count = min(150, max(25, int(limit * 2.5)))
                feed = page.locator("div[role='feed']")

                info(f"LeadScraper: Scrolling Google Maps feed to collect at least {target_cards_count} cards...")

                prev_card_count = 0
                no_growth_ticks = 0
                max_scroll_attempts = 25

                for s_i in range(max_scroll_attempts):
                    # Find all visible card anchors
                    current_cards = page.locator("a.hfpxzc").count()
                    if current_cards == 0:
                        current_cards = page.locator("div.Nv2PK, div[role='article']").count()

                    if current_cards >= target_cards_count:
                        info(f"LeadScraper: Reached target card volume ({current_cards} cards) after {s_i+1} scrolls.")
                        break

                    if current_cards == prev_card_count:
                        no_growth_ticks += 1
                        if no_growth_ticks >= 3:
                            # Reached bottom of Google Maps results
                            info(f"LeadScraper: Reached end of Google Maps feed ({current_cards} total cards).")
                            break
                    else:
                        no_growth_ticks = 0

                    prev_card_count = current_cards

                    # Perform deep scroll in the feed container
                    try:
                        if feed.count() > 0:
                            feed.first.evaluate("el => el.scrollTop += 2200")
                        else:
                            page.keyboard.press("PageDown")
                    except Exception:
                        page.keyboard.press("PageDown")

                    page.wait_for_timeout(600)

                # Collect all unique card links
                card_locators = page.locator("a.hfpxzc").all()
                if not card_locators:
                    card_locators = page.locator("div.Nv2PK, div[role='article']").all()

                info(f"LeadScraper: Total cards discovered on Google Maps: {len(card_locators)}")

                places_to_visit = []
                for card in card_locators:
                    try:
                        name = card.get_attribute("aria-label") or ""
                        href = card.get_attribute("href") or ""
                        if not name:
                            inner_h = card.locator("div.qBF1Pd, div.fontHeadlineSmall").all()
                            if inner_h:
                                name = inner_h[0].inner_text().strip()
                        if name and href and "google.com/maps/place" in href:
                            places_to_visit.append({"name": name, "href": href})
                    except Exception:
                        continue

                info(f"LeadScraper: Inspecting business cards (Target: {limit} real leads)...")

                for p_idx, p_info in enumerate(places_to_visit):
                    if len(collected) >= limit:
                        break

                    try:
                        page.goto(p_info["href"], timeout=18000)
                        page.wait_for_timeout(400)

                        phone = ""
                        website = ""
                        address = f"{city}، {country}"

                        # Method 1: Official phone button attribute (most reliable)
                        phone_btn = page.locator("button[data-item-id^='phone:tel:']")
                        if phone_btn.count() > 0:
                            data_item = phone_btn.first.get_attribute("data-item-id") or ""
                            phone = data_item.replace("phone:tel:", "").strip()

                        # Method 2: tel: href link
                        if not phone:
                            tel_link = page.locator("a[href^='tel:']")
                            if tel_link.count() > 0:
                                phone = tel_link.first.get_attribute("href").replace("tel:", "").strip()

                        # Method 3: Extract from aria-label on phone buttons
                        if not phone:
                            aria_phone = page.locator("button[aria-label*='Phone'], button[aria-label*='هاتف']")
                            if aria_phone.count() > 0:
                                label_text = aria_phone.first.get_attribute("aria-label") or ""
                                p_match = re.search(r"(\+?\d[\d\s\-().]{7,18}\d)", label_text)
                                if p_match:
                                    phone = p_match.group(1).strip()

                        # Method 4: Extract from panel text (regex — fallback)
                        if not phone:
                            panel = page.locator("div[role='main']")
                            if panel.count() > 0:
                                panel_text = panel.first.inner_text()
                                p_match = re.search(r"(\+?\d[\d\s\-().]{8,18}\d)", panel_text)
                                if p_match:
                                    phone = p_match.group(1).strip()

                        # Skip if no phone — we NEVER invent fake numbers
                        if not phone:
                            continue

                        norm_phone = normalize_phone(phone, default_country_code=country_code)
                        if not norm_phone or norm_phone in seen_phones:
                            continue

                        if whatsapp_only and not is_mobile_phone(norm_phone):
                            continue

                        seen_phones.add(norm_phone)

                        # Extract website
                        web_btn = page.locator("a[data-item-id='authority']")
                        if web_btn.count() > 0:
                            website = web_btn.first.get_attribute("href") or ""

                        # Extract address
                        addr_btn = page.locator("button[data-item-id='address']")
                        if addr_btn.count() > 0:
                            addr_text = addr_btn.first.inner_text().strip()
                            if addr_text:
                                address = clean_address(addr_text)

                        wa_status = WA_STATUS_VERIFIED if is_mobile_phone(norm_phone) else WA_STATUS_UNKNOWN

                        info(f"LeadScraper: [{len(collected)+1}/{limit}] ✓ {p_info['name']} → {norm_phone}")
                        if progress_cb:
                            progress_cb(len(collected)+1, limit, p_info['name'])
                        collected.append({
                            "business_name": clean_business_name(p_info["name"]),
                            "phone": norm_phone,
                            "address": address,
                            "website": website,
                            "industry": industry,
                            "city": city,
                            "country": country,
                            "source": "google_maps",
                            "whatsapp_status": wa_status,
                        })

                    except Exception as item_err:
                        continue

            except Exception as e:
                error(f"LeadScraper: Navigation error: {e}")
            finally:
                browser.close()

        info(f"LeadScraper: Finished scraping. Collected {len(collected)} authentic leads from Google Maps.")
        return collected
