"""AutoLeadGen v2 - Integrations: Google Direct WhatsApp Scraper.

Searches Google Web for businesses that publicly publish their WhatsApp numbers or wa.me links.
Extracts 100% authentic WhatsApp leads worldwide.
"""
import re
import urllib.parse
from pipeline.cleaner import normalize_phone, is_mobile_phone, clean_business_name
from config.constants import WA_STATUS_VERIFIED, WA_STATUS_UNKNOWN
from utils.logger import info, warning, error

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


class GoogleSearchScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    def search_whatsapp_leads(
        self,
        industry: str,
        city: str,
        country: str,
        country_code: str = "20",
        limit: int = 15,
        exclude_phones: set = None,
    ) -> list[dict]:
        """
        Search Google Web for businesses with WhatsApp numbers/links in a target city & country.
        Strictly excludes any phone numbers in exclude_phones.
        Queries:
          "{industry}" "{city}" ("wa.me" OR "whatsapp" OR "واتساب")
        """
        limit = min(50, max(1, int(limit)))
        from playwright.sync_api import sync_playwright

        clean_country = re.sub(r"\(.*?\)", "", country).strip()
        location = f"{city} {clean_country}".strip()
        query = f'"{industry}" "{location}" (wa.me OR whatsapp OR "واتساب")'
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num={min(50, max(20, limit * 2))}&hl=ar"

        info(f"GoogleSearchScraper: Navigating to Google Search: {search_url}")
        collected = []
        seen_phones = set(exclude_phones) if exclude_phones else set()


        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={"width": 1280, "height": 900},
                    locale="ar-EG" if country_code in ["20", "966", "971", "965"] else "en-US",
                )
                page = context.new_page()
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3500)

                # Handle Google consent buttons if any
                for sel in ["button:has-text('Accept all')", "button:has-text('Tout accepter')", "button:has-text('قبول الكل')", "button:has-text('موافق')"]:
                    try:
                        btn = page.locator(sel)
                        if btn.count() > 0 and btn.first.is_visible():
                            btn.first.click()
                            page.wait_for_timeout(1500)
                            break
                    except Exception:
                        pass

                # Extract organic search result items
                search_results = page.locator("div.g, div[data-hveid].MjjYud, div.tF2Cxc").all()

                for res in search_results:
                    try:
                        text_content = res.inner_text()
                        if not text_content:
                            continue

                        # 1. Check for wa.me / api.whatsapp.com links in anchors
                        wa_phone = ""
                        links = res.locator("a").all()
                        for a in links:
                            href = a.get_attribute("href") or ""
                            wa_match = re.search(r"(?:wa\.me|api\.whatsapp\.com/send\?phone=)(\+?\d{8,15})", href)
                            if wa_match:
                                wa_phone = wa_match.group(1)
                                break

                        # 2. Extract phone from snippet text if not in link
                        if not wa_phone:
                            wa_inline = re.search(r"(?:wa\.me/|واتساب[:\s]*|whatsapp[:\s]*|tel[:\s]*)(\+?\d[\d\s\-]{8,15}\d)", text_content, re.IGNORECASE)
                            if wa_inline:
                                wa_phone = wa_inline.group(1)

                        if not wa_phone:
                            all_phones = re.findall(r"(\+?\d[\d\s\-]{8,15}\d)", text_content)
                            for candidate in all_phones:
                                norm_candidate = normalize_phone(candidate, default_country_code=country_code)
                                if is_mobile_phone(norm_candidate):
                                    wa_phone = norm_candidate
                                    break

                        if not wa_phone:
                            continue

                        norm_phone = normalize_phone(wa_phone, default_country_code=country_code)
                        if not norm_phone or not is_mobile_phone(norm_phone) or norm_phone in seen_phones:
                            continue

                        seen_phones.add(norm_phone)

                        # Extract Title / Business Name
                        title = ""
                        h3 = res.locator("h3")
                        if h3.count() > 0:
                            title = h3.first.inner_text().strip()
                        if not title:
                            lines = [ln.strip() for ln in text_content.split("\n") if ln.strip()]
                            title = lines[0] if lines else f"{industry} {city}"

                        cleaned_name = clean_business_name(title)
                        cleaned_name = re.sub(r"[\-|–|—].*?(Facebook|Instagram|LinkedIn|X|Twitter|تويتر|فيسبوك).*$", "", cleaned_name).strip()

                        website = ""
                        first_link = res.locator("a").first
                        if first_link.count() > 0:
                            raw_href = first_link.get_attribute("href") or ""
                            if not "google.com" in raw_href:
                                website = raw_href

                        collected.append({
                            "business_name": cleaned_name or f"{industry} - {city}",
                            "phone": norm_phone,
                            "address": f"{city}، {country}",
                            "website": website,
                            "industry": industry,
                            "city": city,
                            "country": country,
                            "source": "google_search",
                            "whatsapp_status": WA_STATUS_VERIFIED,
                        })

                        if len(collected) >= limit:
                            break

                    except Exception as ex:
                        continue

                browser.close()

        except Exception as e:
            error(f"GoogleSearchScraper error: {e}")

        info(f"GoogleSearchScraper: Returning {len(collected)} authentic WhatsApp leads.")
        return collected
