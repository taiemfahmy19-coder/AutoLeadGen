"""AutoLeadGen v2 - WhatsApp Direct Link Generator."""
import urllib.parse
from pipeline.cleaner import normalize_phone
from config.constants import WHATSAPP_DIRECT_URL_TEMPLATE


def generate_direct_link(phone: str, message: str) -> str:
    """
    Generate a standard WhatsApp direct click-to-chat URL (wa.me)
    with safely encoded message text.
    """
    norm_phone = normalize_phone(phone)
    digits = norm_phone.lstrip("+")
    encoded_message = urllib.parse.quote(message)
    return WHATSAPP_DIRECT_URL_TEMPLATE.format(phone=digits, message=encoded_message)
