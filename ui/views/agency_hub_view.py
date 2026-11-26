"""AutoLeadGen v2 — Agency & Hiring Hub View."""
from ui.views.search_view import render_search

AGENCY_TEMPLATE = """مساؤكم خير يا فندم 👋 تحياتي لفريق {business} المبدع في مجال {industry}،

أنا تيم فهمي، مصمم جرافيك وإعلانات. بقدم دعماً إبداعياً مرناً لتخفيف ضغط تسليمات الحملات بتسليم سريع وجودة ممتازة.

وعلشان تشوفوا مستوى الشغل على أرض الواقع بنفسكم:
✨ أنا جاهز أنفذ لحضراتكم أول تصميم أو ريلز لعميل عندكم 'مجاناً تماماً وبدون أي مقابل' 🤝.

لو حابين نجرب، شرفني بالبريف وهجهزه لحضرتك في نفس اليوم:
📱 واتساب / اتصال: 01147018367
✉️ إيميل: taiemfahmy19@gmail.com

مع كامل التقدير،
تيم فهمي"""

AGENCY_PRESETS = [
    "شركات دعاية وإعلان وتسويق",
    "شركات توظيف وموارد بشرية",
    "شركات تصميم ودعاية",
    "شركات تسويق رقمي",
    "شركات طباعة وإعلان",
]


def render_agency_hub():
    """Render dedicated view for advertising & recruitment agencies with custom design pitch."""
    render_search(
        is_agency_hub=True,
        custom_title="قسم شركات الإعلانات والتوظيف (Agency & Hiring Hub)",
        custom_subtitle="استكشاف وتواصل مخصص لوكالات الدعاية والإعلان والتوظيف بالصيغة المعتمدة",
        custom_icon="🎯",
        industry_presets=AGENCY_PRESETS,
        default_ar_template=AGENCY_TEMPLATE,
        key_prefix="agency_",
    )
