"""AutoLeadGen v2 - Services: Outreach Queue Management and Message Personalization."""
from database.repository import LeadRepository
from config.constants import (
    STATUS_READY,
    STATUS_DO_NOT_CONTACT,
    STATUS_NEEDS_REVIEW,
    WA_STATUS_NOT_VERIFIED,
)


import re
import random

DEFAULT_SPINTAX_TEMPLATES = [
    (
        "{مساء الخير|أهلاً بحضرتك|السلام عليكم} يا فندم {👋|🌹}، "
        "{شفت شغلكم المحترم|تابعت نشاطكم المتميز|لفت انتباهنا تميزكم} في {business} بمجال {industry} في {city} 👌، "
        "{وحابين نقترح على حضرتك|وكنا حابين نشارككم} فكرة تسويقية بالذكاء الاصطناعي {هتضاعف|هتزود بشكل ملحوظ} عدد زباينكم ومبيعاتكم بإذن الله.\n\n"
        "💡 وفيه تجربة مجانية علشان تتأكد من الشغل، ولو عجبك هنكمل مع بعض بإذن الله 🤝. "
        "{تحب نبعت لحضرتك التفاصيل؟|هل يناسب حضرتك نوضحلك التفاصيل؟}"
    ),
    (
        "{أهلاً بك|مرحباً بحضرتك|تحياتي لحضرتك} يا فندم {✨|🤝}، "
        "{معجبين جداً بما تقدمونه|متابعين لنجاحكم وتطوركم} في {business} كأحد الأسماء المميزة في {industry} بـ {city}. "
        "{جهزنا لحضراتكم استراتيجية تسويق|أعددنا فكرة مبتكرة} بالذكاء الاصطناعي تساعدكم في {جذب عملاء جدد يومياً|زيادة الحجوزات والمبيعات}.\n\n"
        "🎁 وفيه تجربة مجانية علشان تتأكد من الشغل، ولو عجبك هنكمل مع بعض بإذن الله 🤝. "
        "{هل تحب نوضح لحضرتك الفكرة بنبذة سريعة؟|تحب نبعتلك التفاصيل؟}"
    ),
    (
        "{السلام عليكم ورحمة الله|مساء الورد يا فندم|أهلاً وسهلاً}، "
        "{سعداء بالتواصل مع إدارة|حابين نحيي القائمين على} {business} بمدينة {city} 🌟. "
        "بنساعد المشاريع الرائدة في قطاع {industry} إنها {تضاعف عوائدها|تكسب عملاء مستمرين وتزيد مبيعاتها} عبر حلول الأتمتة والذكاء الاصطناعي. "
        "{لو في فرصة، تحب نشاركك فكرتنا وتفاصيل الشغل؟|تحب نبعت لحضرتك ملخص بسيط عن الطريقة؟}"
    ),
    (
        "{تحياتنا الطيبة لحضرتك|مساء النور والسرور|أهلاً يا فندم} {💐|⭐}، "
        "{خطوة تواصل سريعة مع|رسالة تقدير لجهودكم في} {business} ({industry} - {city}). "
        "طبقنا مؤخراً نظام ذكاء اصطناعي تسويقي حقق نتائج ممتازة في نفس مجالكم، "
        "{وحابين نعرض التجربة على حضرتك|وحبينا نشارك التجربة دي معاكم للاستفادة}. "
        "{نقدر نبعتلك شرح مبسط في دقيقة؟|لو وقت حضرتك يسمح، تحب نبعتلك التفاصيل؟}"
    ),
    (
        "{مرحباً يا فندم|أهلاً بحضرتك|مساء الخير} 👋، "
        "{كل التوفيق لكم في|منبهرين بالمستوى الراقي لـ} {business} في {city} 👌. "
        "في فكرة تسويقية ذكية جداً في مجال {industry} بتعتمد على الذكاء الاصطناعي {لجلب عملاء مهتمين جاهزين للشراء|لرفع المبيعات والأرباح بشكل تلقائي}. "
        "{تحب نبعتلك نبذة سريعة ونماذج من النتائج؟|لو مهتم حضرتك، نقدر نبعتلك التفاصيل ونماذج الشغل؟}"
    ),
]


class OutreachService:
    def __init__(self, db: LeadRepository):
        self.db = db

    def get_queue_leads(self) -> list:
        """
        Fetch leads ready for outreach:
        - Must have status == READY
        - Excludes DO_NOT_CONTACT, NOT_VERIFIED, and NEEDS_REVIEW
        """
        all_leads = self.db.get_all_leads()
        queue = []
        for l in all_leads:
            st = l[9]
            wa_st = l[13] if len(l) > 13 else "UNKNOWN"
            if st == STATUS_READY and wa_st != WA_STATUS_NOT_VERIFIED and st != STATUS_DO_NOT_CONTACT and st != STATUS_NEEDS_REVIEW:
                queue.append(l)
        return queue

    @staticmethod
    def parse_spintax(text: str) -> str:
        """
        Recursively resolves Spintax patterns: {option1|option2|option3}.
        Handles nested Spintax gracefully.
        Leaves non-pipe braces (e.g. template variables) intact if not containing '|'.
        """
        if not text:
            return ""

        pattern = re.compile(r"\{([^{}]+)\}")

        # Limit iterations to avoid infinite loops on malformed input
        iterations = 0
        while iterations < 20:
            match = pattern.search(text)
            if not match:
                break
            content = match.group(1)
            # Only process if it actually contains the spintax pipe separator
            if "|" in content:
                choices = content.split("|")
                chosen = random.choice(choices).strip()
                text = text[:match.start()] + chosen + text[match.end():]
            else:
                # Replace with placeholder tokens if it has no pipe, to avoid re-matching
                # But here we just break if no pipe matches exist
                break
            iterations += 1

        # Also handle any remaining pipe groups
        def spintax_sub(m):
            opts = m.group(1).split("|")
            return random.choice(opts).strip()

        while "{" in text and "|" in text and iterations < 40:
            new_text = re.sub(r"\{([^{}]+?\|[^{}]+?)\}", spintax_sub, text)
            if new_text == text:
                break
            text = new_text
            iterations += 1

        return text

    @staticmethod
    def _is_english_template(template_str: str) -> bool:
        """Detect if the template is primarily English/non-Arabic."""
        if not template_str:
            return False
        # Count latin vs arabic chars
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', template_str))
        latin_chars = len(re.findall(r'[a-zA-Z]', template_str))
        return latin_chars > arabic_chars

    @staticmethod
    def _translate_arabic_to_english(text: str, category: str = "general") -> str:
        """Translate common Arabic terms (industry, city, or generic names) into clean English."""
        if not text:
            return ""
        from config.constants import INDUSTRY_TRANSLATIONS
        t_clean = text.strip()
        if t_clean in INDUSTRY_TRANSLATIONS:
            return INDUSTRY_TRANSLATIONS[t_clean]
        for ar_k, en_v in INDUSTRY_TRANSLATIONS.items():
            if ar_k in t_clean or t_clean in ar_k:
                return en_v
        return text

    @staticmethod
    def _clean_business_name_for_english(name: str) -> str:
        """
        If the place name contains Arabic, make sure it renders cleanly in English:
        1. If it has both English and Arabic (e.g. 'Zara زارا' or 'Starbucks (ستاربكس)'), keep the English part.
        2. If it is 100% Arabic characters, replace with 'your business' so the message remains 100% English.
        """
        if not name:
            return "your business"
        clean = name.strip()

        # If name has latin letters, extract the latin part (e.g., 'Chanel شانيل' -> 'Chanel')
        has_latin = bool(re.search(r'[a-zA-Z]', clean))
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', clean))

        if has_latin and has_arabic:
            # Extract latin words
            latin_parts = re.findall(r"[a-zA-Z0-9&'\-.]+", clean)
            if latin_parts:
                return " ".join(latin_parts).strip()

        # If it's purely Arabic characters and no English letters
        if has_arabic and not has_latin:
            # Check if it matches an industry to describe it as e.g. 'your shop' or 'your business'
            return "your business"

        return clean

    @classmethod
    def build_personalized_message(
        cls,
        name_or_template: str = "",
        industry: str = "",
        city: str = "",
        template: str = None,
        **kwargs
    ) -> str:
        """
        Build an authentic, varied outreach message tailored to the lead's business name, industry, and city.
        Applies full Spintax randomization so no two outgoing messages have the same text hash.
        Supports both positional and keyword invocations.
        Ensures 100% pure English when the template is in English (translates Arabic industries, cleans business names).
        """
        biz_arg = kwargs.get("business") or kwargs.get("name")
        ind_arg = kwargs.get("industry") or industry
        cty_arg = kwargs.get("city") or city

        # If name_or_template contains template braces and no explicit template provided
        if not template and "{" in name_or_template and ("business" in name_or_template or "industry" in name_or_template or "city" in name_or_template or "|" in name_or_template):
            raw_template = name_or_template
            b_name = (biz_arg or "").strip()
        else:
            raw_template = template if (template and template.strip()) else random.choice(DEFAULT_SPINTAX_TEMPLATES)
            b_name = (biz_arg or name_or_template or "").strip()

        ind = (ind_arg or "").strip()
        cty = (cty_arg or "").strip()

        is_en = cls._is_english_template(raw_template)

        if is_en:
            # Clean and normalize for 100% English output
            biz_display = cls._clean_business_name_for_english(b_name)
            ind_display = cls._translate_arabic_to_english(ind, "industry") if ind else "your industry"
            # Remove any Arabic from city if present (e.g. 'Miami، الولايات المتحدة' -> 'Miami')
            if "،" in cty or "," in cty:
                cty_parts = [p.strip() for p in re.split(r'[,،]', cty)]
                latin_cities = [p for p in cty_parts if re.search(r'[a-zA-Z]', p)]
                cty_display = latin_cities[0] if latin_cities else (cty_parts[0] if cty_parts else "your city")
            else:
                cty_display = cty if cty and not re.search(r'[\u0600-\u06FF]', cty) else "your area"

            first_name = biz_display.split()[0] if biz_display and biz_display != "your business" else "there"
        else:
            first_name = b_name.split()[0] if b_name else "يا فندم"
            biz_display = b_name if b_name else "مشروعكم"
            ind_display = ind if ind else "مجالكم"
            cty_display = cty if cty else "مدينتكم"

        # 1. Substitute lead variables
        try:
            populated = raw_template.format(
                name=first_name,
                business=biz_display,
                industry=ind_display,
                city=cty_display
            )
        except Exception:
            populated = raw_template
            populated = populated.replace("{name}", first_name)
            populated = populated.replace("{business}", biz_display)
            populated = populated.replace("{industry}", ind_display)
            populated = populated.replace("{city}", cty_display)

        # 2. Resolve Spintax alternatives
        final_msg = cls.parse_spintax(populated)
        return final_msg.strip()

