"""AutoLeadGen v2 - Pipeline Cleaner: Phone Normalization, Validation, and Data Sanitization."""
import re
from urllib.parse import urlparse
from config.constants import (
    PHONE_VALID,
    PHONE_INVALID,
    PHONE_LANDLINE,
    PHONE_UNKNOWN,
    WA_STATUS_UNKNOWN,
)

# Mapping of Eastern Arabic (Arabic-Indic) digits to ASCII digits
ARABIC_DIGITS_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# Egyptian Landline Area Codes (without leading 0)
EGYPT_LANDLINE_PREFIXES = (
    "2",   # Cairo & Giza (02)
    "3",   # Alexandria (03)
    "13",  # Benha / Qalyubia (013)
    "40",  # Tanta / Gharbia (040)
    "45",  # Damanhour / Beheira (045)
    "46",  # Marsa Matruh (046)
    "47",  # Kafr El Sheikh (047)
    "48",  # Menoufia (048)
    "50",  # Mansoura / Dakahlia (050)
    "55",  # Zagazig / Sharqia (055)
    "57",  # Damietta (057)
    "62",  # Suez (062)
    "64",  # Ismailia (064)
    "65",  # Red Sea / Hurghada (065)
    "66",  # Port Said (066)
    "68",  # North Sinai (068)
    "69",  # South Sinai (069)
    "82",  # Beni Suef (082)
    "84",  # Fayoum (084)
    "86",  # Minya (086)
    "88",  # Assiut (088)
    "92",  # New Valley (092)
    "93",  # Sohag (093)
    "95",  # Luxor (095)
    "96",  # Qena (096)
    "97",  # Aswan (097)
)


def normalize_phone(phone, default_country_code="20") -> str:
    """
    Standardize phone numbers into E.164-like international format: +[country_code][national_number].

    KEY RULE: If the raw phone string starts with '+', it is already in international format
    (Google Maps always delivers numbers this way). Trust it completely — just strip formatting.

    Handles local/ambiguous numbers for Egypt, Saudi, UAE, and other Arab countries.
    Does NOT corrupt numbers from USA, UK, EU, or any country that provides a + prefix.
    """
    if not phone:
        return ""

    phone_str = str(phone).strip().translate(ARABIC_DIGITS_MAP)

    # ── FAST PATH: + prefix present → international format, trust it ──────────────
    # Google Maps button[data-item-id^='phone:tel:'] always provides numbers with +
    # in proper international E.164 format. Strip spaces/dashes/parens and return.
    if phone_str.startswith("+"):
        digits = re.sub(r"\D", "", phone_str)
        if len(digits) >= 7:
            # Edge case: Egypt mobile with redundant 0 after country code (+20 010xxxx → 13 digits)
            if digits.startswith("2001") and len(digits) == 13 and digits[4] in "0125":
                digits = "20" + digits[3:]
            return f"+{digits}"
        return ""

    # ── STANDARD PATH: no + prefix — local or ambiguous number ───────────────────
    digits = re.sub(r"\D", "", phone_str)
    if not digits:
        return ""

    # Remove international double-zero prefix (e.g. 00201012345678)
    if digits.startswith("00"):
        digits = digits[2:]

    # 1. Egypt with country code and redundant zero: 20010..., 20011..., 20012..., 20015... (13 digits)
    if digits.startswith("2001") and len(digits) == 13 and digits[4] in "0125":
        digits = "20" + digits[3:]
        return f"+{digits}"

    # 2. Egypt mobile with country code already: 2010..., 2011..., 2012..., 2015... (12 digits)
    if digits.startswith(("2010", "2011", "2012", "2015")) and len(digits) == 12:
        return f"+{digits}"

    # 3. Local Egyptian mobile with leading 0: 010..., 011..., 012..., 015... (11 digits)
    if digits.startswith(("010", "011", "012", "015")) and len(digits) == 11:
        return f"+20{digits[1:]}"

    # 4. Saudi mobile with explicit country code: 9665xxxxxxxx (12 digits)
    if digits.startswith("9665") and len(digits) == 12:
        return f"+{digits}"

    # 5. UAE mobile with explicit country code: 9715xxxxxxxx (12 digits)
    if digits.startswith("9715") and len(digits) == 12:
        return f"+{digits}"

    # 6. Ambiguous 050, 055, 057 (Egypt vs Saudi/UAE):
    if digits.startswith(("050", "055", "057")) and len(digits) == 10:
        if default_country_code == "966":
            return f"+966{digits[1:]}"
        elif default_country_code == "971":
            return f"+971{digits[1:]}"
        else:
            return f"+20{digits[1:]}"

    # 7. Distinct Saudi prefixes without country code: 051, 053, 054, 056, 058, 059 (10 digits)
    if digits.startswith(("051", "053", "054", "056", "058", "059")) and len(digits) == 10:
        if default_country_code == "971":
            return f"+971{digits[1:]}"
        return f"+966{digits[1:]}"

    # 8. Non-Egypt country: only add CC to genuinely SHORT local numbers.
    #    Long numbers (>=10 digits after stripping 00) already carry their CC.
    if default_country_code and default_country_code != "20":
        if digits.startswith(default_country_code):
            return f"+{digits}"
        if digits.startswith("0"):
            return f"+{default_country_code}{digits[1:]}"
        # Only prepend CC if number is short enough to be a local number
        # (i.e. missing the country code). Formula: local number ≈ 10 - len(CC) digits.
        cc_len = len(default_country_code)
        max_local_len = 10 - cc_len + 2  # +2 tolerance
        if 6 <= len(digits) <= max_local_len:
            return f"+{default_country_code}{digits}"

    # 9. Egyptian landlines with 0 prefix:
    if digits.startswith("0"):
        stripped = digits[1:]
        for pfx in EGYPT_LANDLINE_PREFIXES:
            if stripped.startswith(pfx):
                return f"+20{stripped}"
        if len(digits) in [9, 10, 11]:
            return f"+20{stripped}"

    # 10. Long number without recognizable prefix — treat as already containing CC
    if len(digits) >= 10:
        return f"+{digits}"

    return f"+{digits}" if len(digits) >= 7 else digits

def is_mobile_phone(phone: str) -> bool:
    """
    Check if a normalized or raw phone number belongs strictly to a mobile network
    capable of supporting WhatsApp.
    
    Uses an explicit carrier whitelist:
    - Egypt Mobile: +2010, +2011, +2012, +2015 (strictly 12 digits total)
    - Saudi Mobile: +9665 (strictly 12 digits total)
    - UAE Mobile: +9715 (strictly 12 digits total)
    - Kuwait: +965 (11 digits total)
    - Qatar: +974 (11 digits total)
    - Bahrain: +973 (11 digits total)
    - Oman: +968 (11 digits total)
    - Jordan: +9627 (12 digits total)
    - Iraq: +9647 (13 digits total)
    - Morocco: +2126, +2127 (12 digits total)
    - Algeria: +2135, +2136, +2137 (12 digits total)
    - Tunisia: +216 (11 digits total)
    - Libya: +2189 (12 digits total)
    - Lebanon: +961 (11 digits total)
    - Turkey: +905 (12 digits total)
    - USA/Canada: +1 (11 digits total)
    - UK: +447 (12 digits total)
    
    Rejects all Egyptian landlines (02, 03, 013, 040, 050, etc.).
    """
    if not phone:
        return False
    norm = normalize_phone(phone)
    if not norm:
        return False
    digits = norm.lstrip("+")

    # Reject Egyptian landlines immediately
    if digits.startswith("20"):
        for pfx in EGYPT_LANDLINE_PREFIXES:
            if digits[2:].startswith(pfx):
                return False

    # Reject Saudi landlines (+966 11, 12, 13, 14, 16, 17)
    if digits.startswith("966") and digits[3:5] in ["11", "12", "13", "14", "16", "17"]:
        return False

    # Reject UAE landlines (+971 2, 3, 4, 6, 7, 9)
    if digits.startswith("971") and len(digits) > 3 and digits[3] in ["2", "3", "4", "6", "7", "9"]:
        return False

    # Egypt Mobile: +20 10/11/12/15 xxxxxxxx (12 digits)
    if digits.startswith(("2010", "2011", "2012", "2015")) and len(digits) == 12:
        return True

    # Saudi Mobile: +966 5xxxxxxxx (12 digits)
    if digits.startswith("9665") and len(digits) == 12:
        return True

    # UAE Mobile: +971 5xxxxxxxx (12 digits)
    if digits.startswith("9715") and len(digits) == 12:
        return True

    # Kuwait Mobile: +965 (11 digits, usually starting with 5, 6, 9)
    if digits.startswith("965") and len(digits) == 11:
        return True

    # Qatar Mobile: +974 (11 digits, starting with 3, 5, 6, 7)
    if digits.startswith("974") and len(digits) == 11:
        return True

    # Bahrain Mobile: +973 (11 digits, starting with 3, 6)
    if digits.startswith("973") and len(digits) == 11:
        return True

    # Oman Mobile: +968 (11 digits, starting with 7, 9)
    if digits.startswith("968") and len(digits) == 11:
        return True

    # Jordan Mobile: +962 7 (12 digits)
    if digits.startswith("9627") and len(digits) == 12:
        return True

    # Iraq Mobile: +964 7 (13 digits)
    if digits.startswith("9647") and len(digits) == 13:
        return True

    # Syria Mobile: +963 9 (12 digits)
    if digits.startswith("9639") and len(digits) == 12:
        return True

    # Yemen Mobile: +967 7 (12 digits)
    if digits.startswith("9677") and len(digits) == 12:
        return True

    # Palestine Mobile: +970 59 / 56 (12 digits)
    if digits.startswith(("97059", "97056")) and len(digits) == 12:
        return True

    # Sudan Mobile: +249 9 / 1 (12 digits)
    if digits.startswith(("2499", "2491")) and len(digits) == 12:
        return True

    # Morocco Mobile: +212 6/7 (12 digits)
    if digits.startswith(("2126", "2127")) and len(digits) == 12:
        return True

    # Algeria Mobile: +213 5/6/7 (12 digits)
    if digits.startswith(("2135", "2136", "2137")) and len(digits) == 12:
        return True

    # Tunisia Mobile: +216 (11 digits, mobile 2, 4, 5, 9)
    if digits.startswith("216") and len(digits) == 11:
        return True

    # Libya Mobile: +218 9 (12 digits)
    if digits.startswith("2189") and len(digits) == 12:
        return True

    # Lebanon Mobile: +961 (11 digits, mobile 3, 70, 71, 76, 78, 79, 81)
    if digits.startswith("961") and len(digits) == 11:
        return True

    # Turkey Mobile: +90 5 (12 digits)
    if digits.startswith("905") and len(digits) == 12:
        return True

    # UK Mobile: +44 7 (12 digits)
    if digits.startswith("447") and len(digits) == 12:
        return True

    # Germany Mobile: +49 15/16/17 (12-13 digits)
    if digits.startswith(("4915", "4916", "4917")):
        return True

    # France Mobile: +33 6/7 (11 digits)
    if digits.startswith(("336", "337")) and len(digits) == 11:
        return True

    # Italy Mobile: +39 3 (12 digits)
    if digits.startswith("393") and len(digits) in [12, 13]:
        return True

    # Spain Mobile: +34 6/7 (11 digits)
    if digits.startswith(("346", "347")) and len(digits) == 11:
        return True

    # India Mobile: +91 6/7/8/9 (12 digits)
    if digits.startswith("91") and len(digits) == 12 and digits[2] in "6789":
        return True

    # Pakistan Mobile: +92 3 (12 digits)
    if digits.startswith("923") and len(digits) == 12:
        return True

    # USA / Canada Mobile: +1 (11 digits)
    if digits.startswith("1") and len(digits) == 11:
        return True

    # International valid mobile carrier fallback (must be 10-15 digits)
    if 10 <= len(digits) <= 15 and not digits.startswith("202") and not digits.startswith("203"):
        return True

    return False


def get_phone_validity(phone: str) -> str:
    """
    Determine the detailed validity status of a phone number:
    - VALID: Mobile phone passing carrier whitelist
    - LANDLINE: Detected landline phone
    - INVALID: Malformed or unparseable
    - UNKNOWN: Empty or unrecognized
    """
    if not phone:
        return PHONE_UNKNOWN

    norm = normalize_phone(phone)
    if not norm or len(norm) < 8:
        return PHONE_INVALID

    if is_mobile_phone(norm):
        return PHONE_VALID

    digits = norm.lstrip("+")
    if digits.startswith("20"):
        sub = digits[2:]
        for pfx in EGYPT_LANDLINE_PREFIXES:
            if sub.startswith(pfx):
                return PHONE_LANDLINE

    return PHONE_INVALID


def clean_business_name(name: str) -> str:
    """Sanitize business name by removing redundant whitespace, line breaks, and private icon glyphs."""
    if not name:
        return ""
    cleaned = re.sub(r"[\ue000-\uf8ff]", "", str(name))
    cleaned = re.sub(r"[\r\n\t]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def clean_address(address: str) -> str:
    """Sanitize address by formatting commas, stripping extra whitespace and icon glyphs."""
    if not address:
        return ""
    cleaned = re.sub(r"[\ue000-\uf8ff]", "", str(address))
    cleaned = re.sub(r"[\r\n\t]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"\s*,\s*", ", ", cleaned)
    cleaned = re.sub(r",\s*,+", ", ", cleaned)
    return cleaned.strip(", ")


def clean_website(website: str) -> str:
    """Clean and standardize website URL."""
    if not website:
        return ""

    url = str(website).strip()
    if url in ["", "http://", "https://", "www."]:
        return ""

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if not netloc:
            netloc = parsed.path.lower()
            path = ""
        else:
            path = parsed.path

        netloc = re.sub(r"^www\.", "", netloc)
        cleaned_url = f"https://{netloc}{path}".rstrip("/")
        return cleaned_url if len(netloc) >= 3 and "." in netloc else ""
    except Exception:
        return url.rstrip("/")


def detect_language(text: str = "", phone: str = "", city: str = "", country: str = "") -> str:
    """Detect whether the lead is Arabic, English, or other language based on country/region rules."""
    from config.constants import detect_country_and_language
    geo = detect_country_and_language(phone=phone, country_name=country, city=city)
    if country or (phone and any(c.isdigit() for c in phone)):
        return geo.get("language", "English")

    combined = f"{text} {city}"
    if re.search(r"[\u0600-\u06FF]", combined):
        return "Arabic"
    return "English"



def normalize_email(email: str) -> str:
    """Normalize and validate an email address according to RFC 5322 pattern."""
    if not email:
        return ""
    clean = str(email).strip().lower()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if re.match(pattern, clean):
        if not clean.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js")):
            return clean
    return ""


def extract_emails(text: str) -> list[str]:
    """Extract unique valid email addresses from unstructured text, snippet, or webpage HTML."""
    if not text:
        return []
    pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    matches = re.findall(pattern, str(text))
    valid = []
    for m in matches:
        norm = normalize_email(m)
        if norm and norm not in valid:
            valid.append(norm)
    return valid


def extract_instagram_handle(url_or_text: str) -> str:
    """Extract clean Instagram handle (@username) from URL or text."""
    if not url_or_text:
        return ""
    raw = str(url_or_text).strip()
    match = re.search(r"(?:(?:https?://)?(?:www\.)?instagram\.com/|@)([a-zA-Z0-9_.]+)", raw)
    if match:
        handle = match.group(1).rstrip("/")
        if handle.lower() not in ["p", "reel", "explore", "stories", "direct", "accounts", "about"]:
            return f"@{handle}"
    if raw.startswith("@") and len(raw) > 1:
        return raw
    return ""


def clean_data(
    business_name: str = "",
    phone: str = "",
    address: str = "",
    website: str = "",
    industry: str = "",
    city: str = "",
    whatsapp_status: str = WA_STATUS_UNKNOWN,
    email: str = "",
    instagram_handle: str = "",
    facebook_url: str = "",
    country: str = "",
    language: str = None,
) -> dict:
    """
    Clean all lead data fields into a standardized dictionary with strict validation.
    Never invents missing data.
    """
    cleaned_name = clean_business_name(business_name)
    normalized_phone = normalize_phone(phone)
    phone_val = get_phone_validity(normalized_phone)
    cleaned_address = clean_address(address)
    cleaned_website = clean_website(website)
    cleaned_industry = clean_business_name(industry)
    cleaned_city = clean_business_name(city)
    lang = language or detect_language(cleaned_name, normalized_phone, cleaned_city, country=country)
    cleaned_email = normalize_email(email)
    cleaned_ig = extract_instagram_handle(instagram_handle)
    cleaned_fb = str(facebook_url).strip() if facebook_url else ""

    return {
        "business_name": cleaned_name,
        "phone": normalized_phone,
        "phone_validity": phone_val,
        "address": cleaned_address,
        "website": cleaned_website,
        "industry": cleaned_industry,
        "city": cleaned_city,
        "language": lang,
        "whatsapp_status": whatsapp_status,
        "email": cleaned_email,
        "instagram_handle": cleaned_ig,
        "facebook_url": cleaned_fb,
        "country": country,
    }

