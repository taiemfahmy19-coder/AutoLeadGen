"""AutoLeadGen v2 - System Constants, Statuses, and Templates."""

# CRM Lead Statuses
STATUS_NEW = "NEW"
STATUS_QUALIFIED = "QUALIFIED"
STATUS_READY = "READY"
STATUS_CONTACTED = "CONTACTED"
STATUS_REPLIED = "REPLIED"
STATUS_INTERESTED = "INTERESTED"
STATUS_NOT_INTERESTED = "NOT_INTERESTED"
STATUS_DO_NOT_CONTACT = "DO_NOT_CONTACT"
STATUS_INVALID = "INVALID"
STATUS_NEEDS_REVIEW = "NEEDS_REVIEW"

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
    STATUS_NEEDS_REVIEW,
]

# WhatsApp Verification Statuses (Strict Disambiguation)
WA_STATUS_VERIFIED = "VERIFIED"
WA_STATUS_NOT_VERIFIED = "NOT_VERIFIED"
WA_STATUS_UNKNOWN = "UNKNOWN"
ALL_WA_STATUSES = [WA_STATUS_VERIFIED, WA_STATUS_NOT_VERIFIED, WA_STATUS_UNKNOWN]

# Phone Validity Statuses
PHONE_VALID = "VALID"
PHONE_INVALID = "INVALID"
PHONE_LANDLINE = "LANDLINE"
PHONE_UNKNOWN = "UNKNOWN"

# Interaction Statuses (Reality-Based)
INTERACTION_QUEUED = "QUEUED"
INTERACTION_OPENED = "OPENED"
INTERACTION_SENT = "SENT"
INTERACTION_DELIVERED = "DELIVERED"
INTERACTION_REPLIED = "REPLIED"
INTERACTION_FAILED = "FAILED"
INTERACTION_MANUALLY_MARKED = "MANUALLY_MARKED"

# Scoring Weights (Objective, max 100 points)
SCORING_WEIGHTS = {
    "phone_valid": 20,
    "mobile_carrier": 15,
    "whatsapp_verified": 25,
    "business_name": 10,
    "address": 10,
    "industry_clarity": 10,
    "source_quality": 10,
}

SCORE_QUALIFIED_THRESHOLD = 70
SCORE_EXCELLENT_THRESHOLD = 85

# WhatsApp Anti-Ban Safety Settings (Human Behavior Protocol)
WHATSAPP_DELAY_MIN = 90               # 1.5 minutes minimum between individual cold chats
WHATSAPP_DELAY_MAX = 180              # 3.0 minutes maximum between individual cold chats
WHATSAPP_BATCH_SIZE = 5               # Maximum leads sent per burst before mandatory cooling
WHATSAPP_COOLDOWN_MIN = 900           # 15 minutes cooldown between batches
WHATSAPP_COOLDOWN_MAX = 1500          # 25 minutes cooldown between batches
WHATSAPP_DAILY_RECOMMENDED_MAX = 35   # Recommended safe maximum messages per day
WHATSAPP_WEB_URL = "https://web.whatsapp.com"
WHATSAPP_DIRECT_URL_TEMPLATE = "https://wa.me/{phone}?text={message}"

# Export Formats
EXPORT_FORMATS = ["Excel (.xlsx)", "CSV (.csv)"]

# Supported Languages
LANGUAGES = ["Arabic", "English", "Manual"]

# Industry Presets for Search UI
INDUSTRY_PRESETS = [
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
    "شركات برمجة وتطوير",
    "شركات تصميم ودعاية",
    "شركات تسويق رقمي",
    "شركات طباعة وإعلان",
    "شركات عقارات وتشطيبات",
    "شركات شحن وتوصيل",
    "متاجر إلكترونية",
    "مدرسون خصوصيون وأصحاب كورسات",
    "مدربون وCoaches",
    "مصورون واستوديوهات",
    "Freelancers ومقدمو خدمات رقمية",
]

# Common Cities Presets (Legacy compatibility)
CITY_PRESETS = [
    "القاهرة", "الجيزة", "الإسكندرية", "المنصورة", "طنطا", "الزقازيق",
    "بورسعيد", "الإسماعيلية", "السويس", "أسيوط", "سوهاج", "قنا", "الأقصر", "أسوان",
    "الرياض", "جدة", "الدمام", "مكة", "المدينة المنورة", "الشارقة", "دبي", "أبوظبي"
]

# Comprehensive World Countries & Provinces Dataset for Google Maps Discovery
# Each entry includes: code (dial), flag, lat/lon/zoom (for map), provinces list, city_coords
WORLD_COUNTRIES_DATA = {
    # ─── المنطقة العربية / Middle East & North Africa ───────────────────────
    "مصر": {
        "code": "20", "flag": "🇪🇬",
        "lat": 26.82, "lon": 30.8, "zoom": 6,
        "region": "MENA",
        "provinces": [
            "القاهرة", "الجيزة", "الإسكندرية", "الدقهلية (المنصورة)", "الغربية (طنطا)",
            "الشرقية (الزقازيق)", "القليوبية (بنها)", "المنوفية (شبين الكوم)", "البحيرة (دمنهور)",
            "كفر الشيخ", "دمياط", "بورسعيد", "الإسماعيلية", "السويس", "الفيوم", "بني سويف",
            "المنيا", "أسيوط", "سوهاج", "قنا", "الأقصر", "أسوان", "البحر الأحمر (الغردقة)",
            "جنوب سيناء (شرم الشيخ)", "شمال سيناء", "مطروح", "الوادي الجديد"
        ],
        "city_coords": {
            "القاهرة": (30.033, 31.233, 11), "الجيزة": (30.008, 31.204, 12),
            "الإسكندرية": (31.2, 29.92, 11), "الدقهلية (المنصورة)": (31.04, 31.38, 12),
            "بورسعيد": (31.25, 32.28, 12), "الأقصر": (25.7, 32.64, 12),
            "أسوان": (24.09, 32.9, 12), "البحر الأحمر (الغردقة)": (27.26, 33.81, 12),
            "جنوب سيناء (شرم الشيخ)": (27.91, 34.33, 12),
        }
    },
    "المملكة العربية السعودية": {
        "code": "966", "flag": "🇸🇦",
        "lat": 24.0, "lon": 45.0, "zoom": 5,
        "region": "MENA",
        "provinces": [
            "الرياض", "جدة", "مكة المكرمة", "المدينة المنورة", "الدمام", "الخبر", "الظهران",
            "الأحساء", "الطائف", "تبوك", "بريدة", "عنيزة", "حائل", "أبها", "خميس مشيط",
            "جازان", "نجران", "ينبع", "الجبيل", "حفر الباطن", "الخرج"
        ],
        "city_coords": {
            "الرياض": (24.69, 46.72, 11), "جدة": (21.49, 39.19, 11),
            "مكة المكرمة": (21.42, 39.83, 12), "المدينة المنورة": (24.47, 39.61, 12),
            "الدمام": (26.43, 50.1, 12), "الطائف": (21.27, 40.42, 12),
        }
    },
    "الإمارات العربية المتحدة": {
        "code": "971", "flag": "🇦🇪",
        "lat": 24.47, "lon": 54.37, "zoom": 8,
        "region": "MENA",
        "provinces": ["دبي", "أبوظبي", "الشارقة", "عجمان", "رأس الخيمة", "الفجيرة", "أم القيوين", "العين"],
        "city_coords": {
            "دبي": (25.2, 55.27, 11), "أبوظبي": (24.47, 54.37, 11),
            "الشارقة": (25.34, 55.39, 12), "رأس الخيمة": (25.79, 55.94, 12),
        }
    },
    "الكويت": {
        "code": "965", "flag": "🇰🇼",
        "lat": 29.37, "lon": 47.98, "zoom": 10,
        "region": "MENA",
        "provinces": ["العاصمة", "حولي", "الفروانية", "الأحمدي", "الجهراء", "مبارك الكبير"],
        "city_coords": {"العاصمة": (29.37, 47.98, 11)}
    },
    "قطر": {
        "code": "974", "flag": "🇶🇦",
        "lat": 25.3, "lon": 51.53, "zoom": 10,
        "region": "MENA",
        "provinces": ["الدوحة", "الريان", "الوكرة", "الخور", "لوسيل", "أم صلال"],
        "city_coords": {"الدوحة": (25.28, 51.53, 11), "لوسيل": (25.42, 51.49, 12)}
    },
    "البحرين": {
        "code": "973", "flag": "🇧🇭",
        "lat": 26.07, "lon": 50.55, "zoom": 11,
        "region": "MENA",
        "provinces": ["المنامة", "المحرق", "الرفاع", "سترة", "مدينة حمد", "مدينة عيسى"],
        "city_coords": {"المنامة": (26.22, 50.58, 12)}
    },
    "سلطنة عُمان": {
        "code": "968", "flag": "🇴🇲",
        "lat": 21.0, "lon": 57.0, "zoom": 6,
        "region": "MENA",
        "provinces": ["مسقط", "صلالة", "صحار", "نزوى", "السيب", "بوشر", "مطرح", "البريمي"],
        "city_coords": {"مسقط": (23.59, 58.38, 11), "صلالة": (17.02, 54.09, 12)}
    },
    "الأردن": {
        "code": "962", "flag": "🇯🇴",
        "lat": 31.24, "lon": 36.51, "zoom": 8,
        "region": "MENA",
        "provinces": ["عمان", "إربد", "الزرقاء", "العقبة", "السلط", "مادبا", "جرش", "المفرق"],
        "city_coords": {"عمان": (31.95, 35.93, 11), "العقبة": (29.53, 35.0, 12)}
    },
    "العراق": {
        "code": "964", "flag": "🇮🇶",
        "lat": 33.0, "lon": 44.0, "zoom": 6,
        "region": "MENA",
        "provinces": ["بغداد", "البصرة", "أربيل", "الموصل", "السليمانية", "النجف", "كربلاء", "كركوك", "بابل"],
        "city_coords": {
            "بغداد": (33.34, 44.4, 11), "البصرة": (30.51, 47.82, 11),
            "أربيل": (36.19, 44.01, 11), "الموصل": (36.34, 43.12, 11),
        }
    },
    "سوريا": {
        "code": "963", "flag": "🇸🇾",
        "lat": 34.8, "lon": 38.99, "zoom": 7,
        "region": "MENA",
        "provinces": ["دمشق", "حلب", "حمص", "حماه", "اللاذقية", "دير الزور", "الرقة", "درعا"],
        "city_coords": {"دمشق": (33.51, 36.29, 11), "حلب": (36.2, 37.16, 11)}
    },
    "اليمن": {
        "code": "967", "flag": "🇾🇪",
        "lat": 15.55, "lon": 48.5, "zoom": 6,
        "region": "MENA",
        "provinces": ["صنعاء", "عدن", "تعز", "الحديدة", "إب", "ذمار", "المكلا"],
        "city_coords": {"صنعاء": (15.35, 44.21, 11), "عدن": (12.78, 45.04, 11)}
    },
    "فلسطين": {
        "code": "970", "flag": "🇵🇸",
        "lat": 31.9, "lon": 35.2, "zoom": 9,
        "region": "MENA",
        "provinces": ["القدس", "رام الله", "نابلس", "الخليل", "غزة", "جنين", "بيت لحم"],
        "city_coords": {"غزة": (31.5, 34.47, 12), "رام الله": (31.9, 35.2, 12)}
    },
    "المغرب": {
        "code": "212", "flag": "🇲🇦",
        "lat": 31.79, "lon": -7.09, "zoom": 6,
        "region": "MENA",
        "provinces": ["الدار البيضاء", "الرباط", "مراكش", "طنجة", "فاس", "أكادير", "مكناس", "وجدة", "تطوان"],
        "city_coords": {
            "الدار البيضاء": (33.59, -7.62, 11), "الرباط": (33.99, -6.85, 11),
            "مراكش": (31.63, -8.0, 11), "طنجة": (35.77, -5.8, 12),
        }
    },
    "الجزائر": {
        "code": "213", "flag": "🇩🇿",
        "lat": 28.03, "lon": 1.66, "zoom": 5,
        "region": "MENA",
        "provinces": ["الجزائر العاصمة", "وهران", "قسنطينة", "عنابة", "سطيف", "باتنة", "تلمسان"],
        "city_coords": {
            "الجزائر العاصمة": (36.74, 3.06, 11), "وهران": (35.69, -0.64, 11),
        }
    },
    "تونس": {
        "code": "216", "flag": "🇹🇳",
        "lat": 33.89, "lon": 9.54, "zoom": 7,
        "region": "MENA",
        "provinces": ["تونس العاصمة", "صفاقس", "سوسة", "بنزرت", "القيروان", "المنستير", "نابل"],
        "city_coords": {"تونس العاصمة": (36.82, 10.17, 11), "صفاقس": (34.74, 10.76, 12)}
    },
    "ليبيا": {
        "code": "218", "flag": "🇱🇾",
        "lat": 26.34, "lon": 17.23, "zoom": 5,
        "region": "MENA",
        "provinces": ["طرابلس", "بنغازي", "مصراتة", "الزاوية", "طبرق", "البيضاء"],
        "city_coords": {"طرابلس": (32.9, 13.18, 11), "بنغازي": (32.12, 20.07, 11)}
    },
    "لبنان": {
        "code": "961", "flag": "🇱🇧",
        "lat": 33.85, "lon": 35.86, "zoom": 9,
        "region": "MENA",
        "provinces": ["بيروت", "طرابلس", "صيدا", "صور", "زحلة", "جونيه", "جبيل"],
        "city_coords": {"بيروت": (33.89, 35.5, 12), "طرابلس": (34.44, 35.83, 12)}
    },
    "السودان": {
        "code": "249", "flag": "🇸🇩",
        "lat": 12.86, "lon": 30.22, "zoom": 5,
        "region": "MENA",
        "provinces": ["الخرطوم", "أم درمان", "بورتسودان", "كسلا", "الأبيض", "واو"],
        "city_coords": {"الخرطوم": (15.55, 32.53, 11)}
    },
    "موريتانيا": {
        "code": "222", "flag": "🇲🇷",
        "lat": 20.25, "lon": -10.94, "zoom": 6,
        "region": "MENA",
        "provinces": ["نواكشوط", "نواذيبو", "روصو", "كيفة"],
        "city_coords": {"نواكشوط": (18.07, -15.97, 11)}
    },
    "الصومال": {
        "code": "252", "flag": "🇸🇴",
        "lat": 5.15, "lon": 46.2, "zoom": 6,
        "region": "MENA",
        "provinces": ["مقديشو", "هرجيسا", "بربرة", "كيسمايو", "بوصاصو"],
        "city_coords": {"مقديشو": (2.05, 45.34, 11)}
    },
    # ─── تركيا & إيران ───────────────────────────────────────────────────────
    "تركيا": {
        "code": "90", "flag": "🇹🇷",
        "lat": 39.0, "lon": 35.0, "zoom": 6,
        "region": "MENA",
        "provinces": ["إسطنبول", "أنقرة", "إزمير", "أنطاليا", "بورصة", "طرابزون", "غازي عنتاب"],
        "city_coords": {
            "إسطنبول": (41.01, 28.95, 10), "أنقرة": (39.93, 32.86, 11),
            "إزمير": (38.42, 27.14, 11), "أنطاليا": (36.9, 30.71, 11),
        }
    },
    "إيران": {
        "code": "98", "flag": "🇮🇷",
        "lat": 32.0, "lon": 53.0, "zoom": 5,
        "region": "Asia",
        "provinces": ["طهران", "أصفهان", "شيراز", "مشهد", "تبريز", "كرمان", "الأهواز"],
        "city_coords": {"طهران": (35.69, 51.39, 10), "أصفهان": (32.66, 51.68, 11)}
    },
    "أفغانستان": {
        "code": "93", "flag": "🇦🇫",
        "lat": 33.93, "lon": 67.71, "zoom": 6,
        "region": "Asia",
        "provinces": ["كابول", "قندهار", "هرات", "مزار شريف", "جلال آباد"],
        "city_coords": {"كابول": (34.53, 69.17, 11)}
    },
    "باكستان": {
        "code": "92", "flag": "🇵🇰",
        "lat": 30.38, "lon": 69.35, "zoom": 5,
        "region": "Asia",
        "provinces": ["كراتشي", "لاهور", "إسلام آباد", "فيصل آباد", "رواولبندي", "بيشاور"],
        "city_coords": {"كراتشي": (24.86, 67.01, 10), "لاهور": (31.55, 74.35, 10)}
    },
    "بنغلاديش": {
        "code": "880", "flag": "🇧🇩",
        "lat": 23.69, "lon": 90.35, "zoom": 7,
        "region": "Asia",
        "provinces": ["دكا", "شيتاغونغ", "سيلهيت", "راجشاهي", "خولنا"],
        "city_coords": {"دكا": (23.81, 90.41, 11)}
    },
    # ─── أوروبا / Europe ─────────────────────────────────────────────────────
    "الولايات المتحدة (USA)": {
        "code": "1", "flag": "🇺🇸",
        "lat": 37.09, "lon": -95.71, "zoom": 4,
        "region": "Americas",
        "provinces": [
            "New York", "Los Angeles", "Chicago", "Houston", "Miami", "Dallas",
            "San Francisco", "Austin", "Seattle", "Boston", "Atlanta", "Denver",
            "Las Vegas", "Phoenix", "Philadelphia", "Washington DC", "Detroit", "Nashville"
        ],
        "city_coords": {
            "New York": (40.71, -74.01, 11), "Los Angeles": (34.05, -118.24, 10),
            "Chicago": (41.88, -87.63, 11), "Houston": (29.76, -95.37, 10),
            "Miami": (25.77, -80.19, 11), "Dallas": (32.78, -96.8, 10),
            "San Francisco": (37.77, -122.42, 12), "Austin": (30.27, -97.74, 11),
            "Seattle": (47.61, -122.33, 11), "Boston": (42.36, -71.06, 11),
        }
    },
    "كندا": {
        "code": "1", "flag": "🇨🇦",
        "lat": 56.13, "lon": -106.35, "zoom": 4,
        "region": "Americas",
        "provinces": ["Toronto", "Montreal", "Vancouver", "Calgary", "Ottawa", "Edmonton"],
        "city_coords": {"Toronto": (43.65, -79.38, 11), "Montreal": (45.51, -73.55, 11)}
    },
    "المملكة المتحدة (UK)": {
        "code": "44", "flag": "🇬🇧",
        "lat": 55.37, "lon": -3.44, "zoom": 6,
        "region": "Europe",
        "provinces": ["London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Liverpool", "Edinburgh"],
        "city_coords": {
            "London": (51.51, -0.13, 11), "Manchester": (53.48, -2.24, 11),
            "Birmingham": (52.48, -1.9, 11), "Glasgow": (55.86, -4.25, 11),
        }
    },
    "ألمانيا": {
        "code": "49", "flag": "🇩🇪",
        "lat": 51.17, "lon": 10.45, "zoom": 6,
        "region": "Europe",
        "provinces": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne", "Stuttgart", "Düsseldorf"],
        "city_coords": {
            "Berlin": (52.52, 13.4, 11), "Munich": (48.14, 11.58, 11),
            "Hamburg": (53.55, 9.99, 11), "Frankfurt": (50.11, 8.68, 11),
        }
    },
    "فرنسا": {
        "code": "33", "flag": "🇫🇷",
        "lat": 46.23, "lon": 2.21, "zoom": 6,
        "region": "Europe",
        "provinces": ["Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Bordeaux", "Nantes"],
        "city_coords": {
            "Paris": (48.86, 2.35, 11), "Lyon": (45.75, 4.84, 11),
            "Marseille": (43.3, 5.37, 11), "Nice": (43.71, 7.26, 12),
        }
    },
    "إيطاليا": {
        "code": "39", "flag": "🇮🇹",
        "lat": 41.87, "lon": 12.57, "zoom": 6,
        "region": "Europe",
        "provinces": ["Rome", "Milan", "Naples", "Turin", "Florence", "Venice", "Bologna"],
        "city_coords": {
            "Rome": (41.9, 12.5, 11), "Milan": (45.46, 9.19, 11),
            "Naples": (40.84, 14.25, 11), "Florence": (43.77, 11.26, 12),
        }
    },
    "إسبانيا": {
        "code": "34", "flag": "🇪🇸",
        "lat": 40.46, "lon": -3.75, "zoom": 6,
        "region": "Europe",
        "provinces": ["Madrid", "Barcelona", "Seville", "Valencia", "Bilbao", "Malaga", "Zaragoza"],
        "city_coords": {
            "Madrid": (40.42, -3.7, 11), "Barcelona": (41.39, 2.15, 11),
            "Seville": (37.39, -5.98, 11),
        }
    },
    "هولندا": {
        "code": "31", "flag": "🇳🇱",
        "lat": 52.13, "lon": 5.29, "zoom": 7,
        "region": "Europe",
        "provinces": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven"],
        "city_coords": {"Amsterdam": (52.37, 4.9, 12), "Rotterdam": (51.92, 4.48, 11)}
    },
    "بلجيكا": {
        "code": "32", "flag": "🇧🇪",
        "lat": 50.5, "lon": 4.47, "zoom": 8,
        "region": "Europe",
        "provinces": ["Brussels", "Antwerp", "Ghent", "Bruges", "Liège"],
        "city_coords": {"Brussels": (50.85, 4.35, 11)}
    },
    "سويسرا": {
        "code": "41", "flag": "🇨🇭",
        "lat": 46.82, "lon": 8.23, "zoom": 8,
        "region": "Europe",
        "provinces": ["Zurich", "Geneva", "Basel", "Bern", "Lausanne"],
        "city_coords": {"Zurich": (47.38, 8.54, 12), "Geneva": (46.2, 6.14, 12)}
    },
    "النمسا": {
        "code": "43", "flag": "🇦🇹",
        "lat": 47.52, "lon": 14.55, "zoom": 7,
        "region": "Europe",
        "provinces": ["Vienna", "Graz", "Linz", "Salzburg", "Innsbruck"],
        "city_coords": {"Vienna": (48.21, 16.37, 11)}
    },
    "السويد": {
        "code": "46", "flag": "🇸🇪",
        "lat": 60.13, "lon": 18.64, "zoom": 5,
        "region": "Europe",
        "provinces": ["Stockholm", "Gothenburg", "Malmö", "Uppsala", "Linköping"],
        "city_coords": {"Stockholm": (59.33, 18.07, 11)}
    },
    "النرويج": {
        "code": "47", "flag": "🇳🇴",
        "lat": 60.47, "lon": 8.47, "zoom": 5,
        "region": "Europe",
        "provinces": ["Oslo", "Bergen", "Trondheim", "Stavanger"],
        "city_coords": {"Oslo": (59.91, 10.75, 11)}
    },
    "الدنمارك": {
        "code": "45", "flag": "🇩🇰",
        "lat": 56.26, "lon": 9.5, "zoom": 7,
        "region": "Europe",
        "provinces": ["Copenhagen", "Aarhus", "Odense", "Aalborg"],
        "city_coords": {"Copenhagen": (55.68, 12.57, 11)}
    },
    "بولندا": {
        "code": "48", "flag": "🇵🇱",
        "lat": 51.92, "lon": 19.15, "zoom": 6,
        "region": "Europe",
        "provinces": ["Warsaw", "Kraków", "Gdańsk", "Wrocław", "Poznań"],
        "city_coords": {"Warsaw": (52.23, 21.01, 11), "Kraków": (50.06, 19.94, 11)}
    },
    "روسيا": {
        "code": "7", "flag": "🇷🇺",
        "lat": 61.52, "lon": 105.32, "zoom": 3,
        "region": "Europe",
        "provinces": ["Moscow", "St. Petersburg", "Novosibirsk", "Ekaterinburg", "Kazan"],
        "city_coords": {"Moscow": (55.75, 37.62, 10), "St. Petersburg": (59.95, 30.32, 10)}
    },
    "البرتغال": {
        "code": "351", "flag": "🇵🇹",
        "lat": 39.4, "lon": -8.22, "zoom": 7,
        "region": "Europe",
        "provinces": ["Lisbon", "Porto", "Faro", "Braga", "Coimbra"],
        "city_coords": {"Lisbon": (38.72, -9.14, 11), "Porto": (41.16, -8.63, 11)}
    },
    "اليونان": {
        "code": "30", "flag": "🇬🇷",
        "lat": 39.07, "lon": 21.82, "zoom": 7,
        "region": "Europe",
        "provinces": ["Athens", "Thessaloniki", "Patras", "Heraklion"],
        "city_coords": {"Athens": (37.98, 23.73, 11), "Thessaloniki": (40.64, 22.94, 11)}
    },
    "رومانيا": {
        "code": "40", "flag": "🇷🇴",
        "lat": 45.94, "lon": 24.97, "zoom": 7,
        "region": "Europe",
        "provinces": ["Bucharest", "Cluj-Napoca", "Timișoara", "Iași", "Brașov"],
        "city_coords": {"Bucharest": (44.43, 26.1, 11)}
    },
    "أوكرانيا": {
        "code": "380", "flag": "🇺🇦",
        "lat": 48.38, "lon": 31.17, "zoom": 6,
        "region": "Europe",
        "provinces": ["Kyiv", "Kharkiv", "Odessa", "Lviv", "Dnipro"],
        "city_coords": {"Kyiv": (50.45, 30.52, 11)}
    },
    # ─── آسيا / Asia ─────────────────────────────────────────────────────────
    "الهند": {
        "code": "91", "flag": "🇮🇳",
        "lat": 20.59, "lon": 78.96, "zoom": 5,
        "region": "Asia",
        "provinces": [
            "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
            "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
            "Surat", "Chandigarh", "Bhopal", "Indore", "Nagpur"
        ],
        "city_coords": {
            "Mumbai": (19.08, 72.88, 10), "Delhi": (28.61, 77.23, 10),
            "Bangalore": (12.97, 77.59, 10), "Hyderabad": (17.39, 78.49, 10),
            "Chennai": (13.08, 80.27, 10),
        }
    },
    "الصين": {
        "code": "86", "flag": "🇨🇳",
        "lat": 35.86, "lon": 104.2, "zoom": 4,
        "region": "Asia",
        "provinces": [
            "Beijing", "Shanghai", "Shenzhen", "Guangzhou", "Chengdu",
            "Xi'an", "Hangzhou", "Nanjing", "Wuhan", "Tianjin",
            "Chongqing", "Dongguan", "Suzhou", "Qingdao"
        ],
        "city_coords": {
            "Beijing": (39.91, 116.4, 10), "Shanghai": (31.23, 121.47, 10),
            "Shenzhen": (22.54, 114.06, 10), "Guangzhou": (23.13, 113.26, 10),
        }
    },
    "اليابان": {
        "code": "81", "flag": "🇯🇵",
        "lat": 36.2, "lon": 138.25, "zoom": 5,
        "region": "Asia",
        "provinces": ["Tokyo", "Osaka", "Kyoto", "Nagoya", "Sapporo", "Fukuoka", "Hiroshima"],
        "city_coords": {
            "Tokyo": (35.69, 139.69, 10), "Osaka": (34.69, 135.5, 11),
            "Kyoto": (35.01, 135.77, 12),
        }
    },
    "كوريا الجنوبية": {
        "code": "82", "flag": "🇰🇷",
        "lat": 35.91, "lon": 127.77, "zoom": 7,
        "region": "Asia",
        "provinces": ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon"],
        "city_coords": {"Seoul": (37.57, 126.98, 10), "Busan": (35.18, 129.07, 10)}
    },
    "إندونيسيا": {
        "code": "62", "flag": "🇮🇩",
        "lat": -0.79, "lon": 113.92, "zoom": 5,
        "region": "Asia",
        "provinces": ["Jakarta", "Surabaya", "Bandung", "Medan", "Bekasi", "Tangerang", "Bali"],
        "city_coords": {"Jakarta": (-6.21, 106.85, 10), "Bali": (-8.34, 115.09, 11)}
    },
    "ماليزيا": {
        "code": "60", "flag": "🇲🇾",
        "lat": 4.21, "lon": 101.98, "zoom": 7,
        "region": "Asia",
        "provinces": ["Kuala Lumpur", "Penang", "Johor Bahru", "Ipoh", "Kota Kinabalu"],
        "city_coords": {"Kuala Lumpur": (3.14, 101.69, 11)}
    },
    "سنغافورة": {
        "code": "65", "flag": "🇸🇬",
        "lat": 1.35, "lon": 103.82, "zoom": 12,
        "region": "Asia",
        "provinces": ["Downtown Core", "Orchard", "Changi", "Jurong", "Woodlands"],
        "city_coords": {"Downtown Core": (1.28, 103.85, 13)}
    },
    "تايلاند": {
        "code": "66", "flag": "🇹🇭",
        "lat": 15.87, "lon": 100.99, "zoom": 6,
        "region": "Asia",
        "provinces": ["Bangkok", "Phuket", "Chiang Mai", "Pattaya", "Chonburi"],
        "city_coords": {"Bangkok": (13.75, 100.51, 10), "Phuket": (7.89, 98.4, 11)}
    },
    "الفلبين": {
        "code": "63", "flag": "🇵🇭",
        "lat": 12.88, "lon": 121.77, "zoom": 6,
        "region": "Asia",
        "provinces": ["Manila", "Quezon City", "Cebu", "Davao", "Makati"],
        "city_coords": {"Manila": (14.59, 120.98, 11), "Cebu": (10.32, 123.9, 11)}
    },
    "فيتنام": {
        "code": "84", "flag": "🇻🇳",
        "lat": 14.06, "lon": 108.28, "zoom": 6,
        "region": "Asia",
        "provinces": ["Ho Chi Minh City", "Hanoi", "Da Nang", "Hai Phong", "Nha Trang"],
        "city_coords": {"Ho Chi Minh City": (10.82, 106.63, 10), "Hanoi": (21.03, 105.85, 10)}
    },
    "أستراليا": {
        "code": "61", "flag": "🇦🇺",
        "lat": -25.27, "lon": 133.78, "zoom": 4,
        "region": "Oceania",
        "provinces": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast"],
        "city_coords": {
            "Sydney": (-33.87, 151.21, 10), "Melbourne": (-37.81, 144.96, 10),
            "Brisbane": (-27.47, 153.03, 10), "Perth": (-31.95, 115.86, 10),
        }
    },
    "نيوزيلندا": {
        "code": "64", "flag": "🇳🇿",
        "lat": -40.9, "lon": 174.89, "zoom": 5,
        "region": "Oceania",
        "provinces": ["Auckland", "Wellington", "Christchurch", "Hamilton"],
        "city_coords": {"Auckland": (-36.87, 174.77, 11), "Wellington": (-41.29, 174.78, 11)}
    },
    # ─── أفريقيا / Africa ────────────────────────────────────────────────────
    "نيجيريا": {
        "code": "234", "flag": "🇳🇬",
        "lat": 9.08, "lon": 8.68, "zoom": 6,
        "region": "Africa",
        "provinces": ["Lagos", "Abuja", "Kano", "Ibadan", "Port Harcourt", "Benin City"],
        "city_coords": {"Lagos": (6.52, 3.38, 10), "Abuja": (9.07, 7.4, 11)}
    },
    "غانا": {
        "code": "233", "flag": "🇬🇭",
        "lat": 7.95, "lon": -1.02, "zoom": 7,
        "region": "Africa",
        "provinces": ["Accra", "Kumasi", "Tamale", "Sekondi-Takoradi"],
        "city_coords": {"Accra": (5.56, -0.2, 11)}
    },
    "كينيا": {
        "code": "254", "flag": "🇰🇪",
        "lat": -0.02, "lon": 37.91, "zoom": 6,
        "region": "Africa",
        "provinces": ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret"],
        "city_coords": {"Nairobi": (-1.29, 36.82, 11)}
    },
    "إثيوبيا": {
        "code": "251", "flag": "🇪🇹",
        "lat": 9.15, "lon": 40.49, "zoom": 6,
        "region": "Africa",
        "provinces": ["Addis Ababa", "Dire Dawa", "Mekelle", "Gondar"],
        "city_coords": {"Addis Ababa": (9.03, 38.75, 11)}
    },
    "جنوب أفريقيا": {
        "code": "27", "flag": "🇿🇦",
        "lat": -30.56, "lon": 22.94, "zoom": 5,
        "region": "Africa",
        "provinces": ["Johannesburg", "Cape Town", "Durban", "Pretoria", "Port Elizabeth"],
        "city_coords": {"Johannesburg": (-26.2, 28.04, 10), "Cape Town": (-33.93, 18.42, 10)}
    },
    "تنزانيا": {
        "code": "255", "flag": "🇹🇿",
        "lat": -6.37, "lon": 34.89, "zoom": 6,
        "region": "Africa",
        "provinces": ["Dar es Salaam", "Dodoma", "Mwanza", "Arusha", "Zanzibar"],
        "city_coords": {"Dar es Salaam": (-6.79, 39.21, 11), "Zanzibar": (-6.16, 39.2, 12)}
    },
    # ─── أمريكا اللاتينية / Latin America ───────────────────────────────────
    "البرازيل": {
        "code": "55", "flag": "🇧🇷",
        "lat": -14.24, "lon": -51.93, "zoom": 4,
        "region": "Americas",
        "provinces": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza",
                       "Belo Horizonte", "Manaus", "Curitiba", "Recife", "Porto Alegre"],
        "city_coords": {
            "São Paulo": (-23.55, -46.63, 10), "Rio de Janeiro": (-22.91, -43.17, 10),
        }
    },
    "المكسيك": {
        "code": "52", "flag": "🇲🇽",
        "lat": 23.63, "lon": -102.55, "zoom": 5,
        "region": "Americas",
        "provinces": ["Mexico City", "Guadalajara", "Monterrey", "Tijuana", "Cancún", "Puebla"],
        "city_coords": {"Mexico City": (19.43, -99.13, 10), "Guadalajara": (20.66, -103.35, 10)}
    },
    "الأرجنتين": {
        "code": "54", "flag": "🇦🇷",
        "lat": -38.42, "lon": -63.62, "zoom": 4,
        "region": "Americas",
        "provinces": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza", "Tucumán"],
        "city_coords": {"Buenos Aires": (-34.62, -58.38, 10)}
    },
    "كولومبيا": {
        "code": "57", "flag": "🇨🇴",
        "lat": 4.57, "lon": -74.3, "zoom": 6,
        "region": "Americas",
        "provinces": ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena"],
        "city_coords": {"Bogotá": (4.71, -74.07, 10), "Medellín": (6.22, -75.57, 10)}
    },
    "تشيلي": {
        "code": "56", "flag": "🇨🇱",
        "lat": -35.68, "lon": -71.54, "zoom": 5,
        "region": "Americas",
        "provinces": ["Santiago", "Valparaíso", "Concepción", "Antofagasta"],
        "city_coords": {"Santiago": (-33.46, -70.65, 10)}
    },
    "بيرو": {
        "code": "51", "flag": "🇵🇪",
        "lat": -9.19, "lon": -75.02, "zoom": 5,
        "region": "Americas",
        "provinces": ["Lima", "Arequipa", "Trujillo", "Cusco"],
        "city_coords": {"Lima": (-12.05, -77.04, 10)}
    },
    "دولة أخرى (Custom / Worldwide)": {
        "code": "", "flag": "🌐",
        "lat": 20.0, "lon": 0.0, "zoom": 2,
        "region": "Global",
        "provinces": [],
        "city_coords": {}
    }
}

# High-Fit Visual & Advertising Keywords
HIGH_FIT_AI_INDUSTRIES = {
    # Visual & Product niches (10 points)
    "عطور": 10, "برفانات": 10, "perfumes": 10, "perfume": 10, "fragrance": 10,
    "شوكولاتة": 10, "chocolate": 10, "chocolates": 10,
    "حلويات": 10, "sweets": 10, "desserts": 10, "bakery": 10, "مخابز": 10,
    "ملابس": 10, "clothing": 10, "fashion": 10, "أزياء": 10,
    "أحذية": 10, "shoes": 10, "footwear": 10,
    "شنط": 10, "حقائب": 10, "bags": 10,
    "مجوهرات": 10, "jewelry": 10, "ذهب": 10, "فضة": 10,
    "إكسسوارات": 10, "accessories": 10,
    "مستحضرات تجميل": 10, "cosmetics": 10, "makeup": 10, "تجميل": 10,
    "منتجات عناية": 10, "skincare": 10, "عناية بالبشرة": 10,
    "هدايا": 10, "gifts": 10, "gift shop": 10,
    "مطاعم": 10, "مطعم": 10, "restaurant": 10, "restaurants": 10,
    "كافيهات": 10, "كافيه": 10, "cafe": 10, "coffee": 10, "قهوة": 10,
    "أثاث": 8, "furniture": 8, "ديكور": 8, "decor": 8,
    "متاجر إلكترونية": 8, "ecommerce": 8,
    "مصورون": 8, "photographer": 8, "photography": 8,
    "مدرسون": 6, "teacher": 6, "tutoring": 6, "courses": 6, "كورسات": 6,
    "برمجة": 6, "software": 6, "تصميم": 6, "design": 6, "تسويق": 6, "marketing": 6,
    "عقارات": 6, "real estate": 6,
}

DEFAULT_ARABIC_TEMPLATE = """مساء الخير يا فندم 👋، شفت شغلكم المحترم في {business} بمجال {industry} في {city} 👌، وحابين نقترح على حضرتك فكرة تسويقية بالذكاء الاصطناعي هتضاعف عدد زباينكم ومبيعاتكم بإذن الله. لو مهتم يا فندم تحب نبعتلك التفاصيل ونماذج الشغل؟"""

DEFAULT_ENGLISH_TEMPLATE = """Hello 👋, we noticed the great work at {business} in {city} 🌟. We provide high-converting AI advertising videos and smart digital marketing solutions tailored for {industry} businesses to attract more paying customers. Would you be open to seeing a quick demo or case study?"""

DEFAULT_FRENCH_TEMPLATE = """Bonjour 👋, nous avons découvert votre entreprise {business} dans le secteur {industry} à {city} 🌟. Nous proposons des vidéos publicitaires et des solutions marketing avec intelligence artificielle pour attirer de nouveaux clients et développer vos ventes. Seriez-vous intéressé par quelques exemples de notre travail ?"""

DEFAULT_SPANISH_TEMPLATE = """¡Hola! 👋 Vimos el excelente trabajo de {business} en el sector {industry} en {city} 🌟. Desarrollamos videos publicitarios y estrategias de marketing con Inteligencia Artificial para atraer más clientes a negocios locales. ¿Le gustaría conocer más detalles y ver algunos ejemplos?"""

DEFAULT_GERMAN_TEMPLATE = """Hallo 👋, wir haben {business} im Bereich {industry} in {city} entdeckt 🌟. Wir erstellen moderne KI-Werbevideos und Marketinglösungen, um mehr Neukunden und Umsatz für Ihr Unternehmen zu gewinnen. Dürfen wir Ihnen ein paar unverbindliche Beispiele zusenden?"""

DEFAULT_TURKISH_TEMPLATE = """Merhaba 👋, {city}'deki {business} işletmenizi gördük 🌟. {industry} sektöründeki işletmeler için yapay zeka destekli reklam videoları ve dijital pazarlama çözümleri üretiyoruz. Detayları ve örnek çalışmalarımızı incelemek ister misiniz?"""

DEFAULT_ITALIAN_TEMPLATE = """Buongiorno 👋, abbiamo notato l'eccellente attività di {business} a {city} 🌟. Creiamo video pubblicitari e soluzioni di marketing con Intelligenza Artificiale per aumentare clienti e vendite nel settore {industry}. Le farebbe piacere ricevere qualche esempio?"""

MULTILINGUAL_TEMPLATES = {
    "Arabic": DEFAULT_ARABIC_TEMPLATE,
    "English": DEFAULT_ENGLISH_TEMPLATE,
    "French": DEFAULT_FRENCH_TEMPLATE,
    "Spanish": DEFAULT_SPANISH_TEMPLATE,
    "German": DEFAULT_GERMAN_TEMPLATE,
    "Turkish": DEFAULT_TURKISH_TEMPLATE,
    "Italian": DEFAULT_ITALIAN_TEMPLATE,
}

# Country & Region classification sets
ARAB_COUNTRIES = {
    "مصر", "المملكة العربية السعودية", "الإمارات العربية المتحدة", "الكويت",
    "قطر", "البحرين", "سلطنة عُمان", "الأردن", "العراق", "سوريا", "اليمن",
    "فلسطين", "المغرب", "الجزائر", "تونس", "ليبيا", "لبنان", "السودان",
    "موريتانيا", "الصومال", "جيبوتي", "جزر القمر",
    "Egypt", "Saudi Arabia", "UAE", "United Arab Emirates", "Kuwait", "Qatar",
    "Bahrain", "Oman", "Jordan", "Iraq", "Syria", "Yemen", "Palestine",
    "Morocco", "Algeria", "Tunisia", "Libya", "Lebanon", "Sudan", "Mauritania"
}

ARAB_DIAL_CODES = {
    "20", "966", "971", "965", "974", "973", "968", "962", "964",
    "963", "967", "970", "212", "213", "216", "218", "961", "249", "222", "252"
}

AMERICAS_COUNTRIES = {
    "الولايات المتحدة (USA)", "الولايات المتحدة", "كندا", "المكسيك", "البرازيل",
    "الأرجنتين", "كولومبيا", "تشيلي", "بيرو", "فنزويلا", "الإكوادور", "بوليفيا",
    "أوروغواي", "باراغواي", "بنما", "كوستاريكا", "غواتيمالا", "كوبا",
    "USA", "United States", "Canada", "Mexico", "Brazil", "Argentina", "Colombia",
    "Chile", "Peru", "Venezuela", "Ecuador", "Bolivia", "Uruguay", "Paraguay"
}

AMERICAS_DIAL_CODES = {
    "1", "52", "55", "54", "57", "56", "51", "58", "593", "591", "598", "595", "507", "506", "502"
}

EUROPE_SPECIAL_LANGS = {
    "33": ("French", "🇫🇷", "فرنسا"),
    "49": ("German", "🇩🇪", "ألمانيا"),
    "43": ("German", "🇦🇹", "النمسا"),
    "41": ("German", "🇨🇭", "سويسرا"),
    "34": ("Spanish", "🇪🇸", "إسبانيا"),
    "39": ("Italian", "🇮🇹", "إيطاليا"),
    "90": ("Turkish", "🇹🇷", "تركيا"),
}

COUNTRY_TO_LANG = {
    "فرنسا": ("French", "🇫🇷"), "France": ("French", "🇫🇷"),
    "ألمانيا": ("German", "🇩🇪"), "Germany": ("German", "🇩🇪"),
    "النمسا": ("German", "🇦🇹"), "Austria": ("German", "🇦🇹"),
    "سويسرا": ("German", "🇨🇭"), "Switzerland": ("German", "🇨🇭"),
    "إسبانيا": ("Spanish", "🇪🇸"), "Spain": ("Spanish", "🇪🇸"),
    "إيطاليا": ("Italian", "🇮🇹"), "Italy": ("Italian", "🇮🇹"),
    "تركيا": ("Turkish", "🇹🇷"), "Turkey": ("Turkish", "🇹🇷"),
}


def detect_country_and_language(phone: str = "", country_name: str = "", city: str = "", country_code: str = "") -> dict:
    """
    Auto-detect the lead's country, region, flag, and target message language according to strict rules:
    1. Americas -> English
    2. Arab countries -> Arabic
    3. Other countries -> native language if available (French, German, Spanish, Turkish, Italian) or English.
    """
    clean_country = (country_name or "").strip()
    digits = "".join(filter(str.isdigit, str(phone or "")))
    if digits.startswith("00"):
        digits = digits[2:]

    # A. Check country name from WORLD_COUNTRIES_DATA or known sets
    if clean_country:
        for arab_c in ARAB_COUNTRIES:
            if arab_c.lower() in clean_country.lower():
                flag = WORLD_COUNTRIES_DATA.get(clean_country, {}).get("flag", "🇪🇬")
                return {
                    "country": clean_country,
                    "region": "MENA",
                    "flag": flag,
                    "language": "Arabic",
                    "template": DEFAULT_ARABIC_TEMPLATE,
                }

        for am_c in AMERICAS_COUNTRIES:
            if am_c.lower() in clean_country.lower():
                flag = WORLD_COUNTRIES_DATA.get(clean_country, {}).get("flag", "🇺🇸")
                return {
                    "country": clean_country,
                    "region": "Americas",
                    "flag": flag,
                    "language": "English",
                    "template": DEFAULT_ENGLISH_TEMPLATE,
                }

        for spec_c, (spec_lang, spec_flag) in COUNTRY_TO_LANG.items():
            if spec_c.lower() in clean_country.lower():
                return {
                    "country": clean_country,
                    "region": "Europe",
                    "flag": spec_flag,
                    "language": spec_lang,
                    "template": MULTILINGUAL_TEMPLATES.get(spec_lang, DEFAULT_ENGLISH_TEMPLATE),
                }

    # B. Check phone international dial code
    if digits:
        # Match longest prefix in dial code maps
        for length in (3, 2, 1):
            pfx = digits[:length]
            if pfx in ARAB_DIAL_CODES:
                # Find matching country
                c_name = "دولة عربية"
                flag = "🇸🇦"
                for c_k, c_v in WORLD_COUNTRIES_DATA.items():
                    if c_v.get("code") == pfx:
                        c_name = c_k
                        flag = c_v.get("flag", "🇸🇦")
                        break
                return {
                    "country": c_name,
                    "region": "MENA",
                    "flag": flag,
                    "language": "Arabic",
                    "template": DEFAULT_ARABIC_TEMPLATE,
                }

            if pfx in AMERICAS_DIAL_CODES:
                c_name = "USA / Americas"
                flag = "🇺🇸"
                for c_k, c_v in WORLD_COUNTRIES_DATA.items():
                    if c_v.get("code") == pfx:
                        c_name = c_k
                        flag = c_v.get("flag", "🇺🇸")
                        break
                return {
                    "country": c_name,
                    "region": "Americas",
                    "flag": flag,
                    "language": "English",
                    "template": DEFAULT_ENGLISH_TEMPLATE,
                }

            if pfx in EUROPE_SPECIAL_LANGS:
                spec_lang, spec_flag, spec_cname = EUROPE_SPECIAL_LANGS[pfx]
                return {
                    "country": spec_cname,
                    "region": "Europe",
                    "flag": spec_flag,
                    "language": spec_lang,
                    "template": MULTILINGUAL_TEMPLATES.get(spec_lang, DEFAULT_ENGLISH_TEMPLATE),
                }

    # C. Check country_code explicitly
    code_str = str(country_code or "").strip("+")
    if code_str in ARAB_DIAL_CODES:
        return {"country": clean_country or "دولة عربية", "region": "MENA", "flag": "🇪🇬", "language": "Arabic", "template": DEFAULT_ARABIC_TEMPLATE}
    if code_str in AMERICAS_DIAL_CODES:
        return {"country": clean_country or "Americas", "region": "Americas", "flag": "🇺🇸", "language": "English", "template": DEFAULT_ENGLISH_TEMPLATE}
    if code_str in EUROPE_SPECIAL_LANGS:
        l, f, n = EUROPE_SPECIAL_LANGS[code_str]
        return {"country": clean_country or n, "region": "Europe", "flag": f, "language": l, "template": MULTILINGUAL_TEMPLATES.get(l, DEFAULT_ENGLISH_TEMPLATE)}

    # D. Default fallback
    flag = WORLD_COUNTRIES_DATA.get(clean_country, {}).get("flag", "🌐")
    return {
        "country": clean_country or "دولي",
        "region": "Global",
        "flag": flag,
        "language": "English",
        "template": DEFAULT_ENGLISH_TEMPLATE,
    }

