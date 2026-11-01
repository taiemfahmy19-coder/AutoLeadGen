"""AutoLeadGen & AI Advertising Outreach Suite - Master Configuration."""
import os

PROJECT_NAME = "AutoLeadGen & AI Advertising Outreach Suite"
VERSION = "1.0.0"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "leads.db")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
WHATSAPP_PROFILE_DIR = os.path.join(DATA_DIR, "whatsapp_profile")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Ensure required directories exist
for folder in [DATA_DIR, BACKUP_DIR, WHATSAPP_PROFILE_DIR, LOG_DIR]:
    os.makedirs(folder, exist_ok=True)

# CRM Statuses
STATUS_NEW = "NEW"
STATUS_QUALIFIED = "QUALIFIED"
STATUS_READY = "READY"
STATUS_CONTACTED = "CONTACTED"
STATUS_REPLIED = "REPLIED"
STATUS_INTERESTED = "INTERESTED"
STATUS_NOT_INTERESTED = "NOT_INTERESTED"
STATUS_DO_NOT_CONTACT = "DO_NOT_CONTACT"
STATUS_INVALID = "INVALID"

ALL_STATUSES = [
    STATUS_NEW,
    STATUS_QUALIFIED,
    STATUS_READY,
    STATUS_CONTACTED,
    STATUS_REPLIED,
    STATUS_INTERESTED,
    STATUS_NOT_INTERESTED,
    STATUS_DO_NOT_CONTACT,
    STATUS_INVALID,
]

# Supported Languages
LANGUAGES = ["Arabic", "English", "Manual"]

# WhatsApp Lead Verification Statuses
WA_STATUS_VERIFIED = "VERIFIED"
WA_STATUS_NOT_VERIFIED = "NOT_VERIFIED"
WA_STATUS_UNKNOWN = "UNKNOWN"
ALL_WA_STATUSES = [WA_STATUS_VERIFIED, WA_STATUS_NOT_VERIFIED, WA_STATUS_UNKNOWN]

# WhatsApp & Outreach settings
WHATSAPP_DELAY_MIN = 180
WHATSAPP_DELAY_MAX = 300
WHATSAPP_WEB_URL = "https://web.whatsapp.com"
WHATSAPP_DIRECT_URL_TEMPLATE = "https://wa.me/{phone}?text={message}"

# Export formats
EXPORT_FORMATS = ["Excel (.xlsx)", "CSV (.csv)"]

# Lead Scoring Weights (Total = 100)
SCORING_WEIGHTS = {
    "phone_valid": 25,
    "website": 15,
    "name_address_complete": 15,
    "industry_clarity": 15,
    "ai_advertising_fit": 25,
    "data_quality": 5,
}

# Score-to-CRM Promotion Thresholds
SCORE_QUALIFIED_THRESHOLD = 80  # Score >= 80 qualifies for the CRM outreach pipeline
SCORE_EXCELLENT_THRESHOLD = 90  # Score >= 90 top tier target

# Target Industries & AI Advertising Fit Categories
HIGH_FIT_AI_INDUSTRIES = {
    # 25 points - Product & visual businesses
    "عطور": 25, "برفانات": 25, "perfumes": 25, "perfume": 25, "fragrance": 25,
    "شوكولاتة": 25, "chocolate": 25, "chocolates": 25,
    "حلويات": 25, "sweets": 25, "desserts": 25, "bakery": 25, "مخابز": 25,
    "ملابس": 25, "clothing": 25, "fashion": 25, "أزياء": 25,
    "أحذية": 25, "shoes": 25, "footwear": 25,
    "شنط": 25, "حقائب": 25, "bags": 25,
    "مجوهرات": 25, "jewelry": 25, "ذهب": 25, "فضة": 25,
    "إكسسوارات": 25, "accessories": 25,
    "مستحضرات تجميل": 25, "cosmetics": 25, "makeup": 25, "تجميل": 25,
    "منتجات عناية": 25, "skincare": 25, "عناية بالبشرة": 25,
    "هدايا": 25, "gifts": 25, "gift shop": 25,
    "مطاعم": 25, "مطعم": 25, "restaurant": 25, "restaurants": 25,
    "كافيهات": 25, "كافيه": 25, "cafe": 25, "coffee": 25, "قهوة": 25,
    
    # 20 points - Services with high visual/promotional need
    "أثاث": 20, "furniture": 20, "ديكور": 20, "decor": 20, "إضاءة": 20, "lighting": 20,
    "إلكترونيات": 20, "electronics": 20, "إكسسوارات موبايلات": 20, "mobile accessories": 20,
    "متاجر إلكترونية": 20, "ecommerce": 20, "متجر إلكتروني": 20, "online store": 20,
    "مصورون": 20, "مصور": 20, "photographer": 20, "photography": 20,
    "تشطيبات": 20, "مقاولات": 20, "finishing": 20,
    
    # 15 points - Knowledge, Education, B2B services
    "مدرسون": 15, "مدرس": 15, "مدرس خصوصي": 15, "teacher": 15, "tutoring": 15, "tutor": 15,
    "مدربون": 15, "مدرب": 15, "trainer": 15, "coach": 15, "courses": 15, "كورسات": 15,
    "شركات برمجة": 15, "software": 15, "برمجة": 15, "web development": 15,
    "شركات تصميم": 15, "design": 15, "graphic design": 15,
    "شركات تسويق": 15, "marketing": 15,
    "طباعة ودعاية": 15, "printing": 15, "advertising": 15,
    "عقارات": 15, "real estate": 15,
    "صناع محتوى": 15, "content creator": 15, "freelancers": 15,
    
    # 10 points - Standard baseline services
    "شحن": 10, "توصيل": 10, "shipping": 10, "delivery": 10,
    "خدمات منزلية": 10, "home services": 10,
    "خدمات رقمية": 10, "digital services": 10
}

# Industry Selection Presets for the Search UI
INDUSTRY_PRESETS = [
    # Category A: Products & Retail
    "محلات عطور وبرفانات",
    "محلات شوكولاتة",
    "محلات حلويات ومخابز",
    "محلات ملابس وأزياء",
    "محلات أحذية وشنط",
    "مجوهرات وإكسسوارات",
    "مستحضرات تجميل ومنتجات عناية",
    "محلات هدايا",
    "أثاث وديكور وإضاءة",
    "إلكترونيات وإكسسوارات موبايل",
    "مطاعم صغيرة",
    "كافيهات ومقاهي",
    # Category B: Small Companies
    "شركات برمجة وتطوير",
    "شركات تصميم ودعاية",
    "شركات تسويق رقمي",
    "شركات طباعة وإعلان",
    "شركات عقارات وتشطيبات",
    "شركات شحن وتوصيل",
    "متاجر إلكترونية",
    # Category C: Service Providers
    "مدرسون خصوصيون وأصحاب كورسات",
    "مدربون وCoaches",
    "مصورون واستوديوهات",
    "Freelancers ومقدمو خدمات رقمية"
]

# Common Cities Presets
CITY_PRESETS = [
    "القاهرة", "الجيزة", "الإسكندرية", "المنصورة", "طنطا", "الزقازيق",
    "بورسعيد", "الإسماعيلية", "السويس", "أسيوط", "سوهاج", "قنا", "الأقصر", "أسوان",
    "الرياض", "جدة", "الدمام", "مكة", "المدينة المنورة", "الشارقة", "دبي", "أبوظبي"
]

# Default Arabic Template (Master Plan Section 24)
DEFAULT_ARABIC_TEMPLATE = """السلام عليكم 👋

أنا بقدم خدمات تصميم محتوى وإعلانات احترافية للبيزنسات، منها تصميمات السوشيال ميديا وفيديوهات إعلانية بالـAI بجودة عالية.

📦 الباقة الشهرية — 1500 جنيه
• 8 تصميمات إعلانية
• 2 فيديو Reels
• كتابة المحتوى والكابشن
• أفكار إعلانية مناسبة لنشاطك

🎬 فيديوهات إضافية:
• من 10 لـ90 ثانية: 500 جنيه
• أكثر من 90 ثانية: 900 جنيه

لو مهتم، أقدر أبعتلك نماذج من شغلي وتشوف الجودة بنفسك قبل أي اتفاق."""

# Default English Template (Master Plan Section 25)
DEFAULT_ENGLISH_TEMPLATE = """Hello 👋

I provide professional social media designs and high-quality AI advertising videos for small businesses.

📦 Monthly package — EGP 1,500
• 8 advertising designs
• 2 Reels videos
• Content and captions
• Advertising ideas tailored to your business

🎬 Additional videos:
• 10–90 seconds: EGP 500
• Over 90 seconds: EGP 900

If you're interested, I can send you some examples of my work so you can check the quality before making any decision."""

# UI settings
PAGE_TITLE = "AutoLeadGen"
PAGE_ICON = "🎯"