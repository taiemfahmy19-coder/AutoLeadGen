"""AutoLeadGen v2 - Integrations: Zero-Cost Direct SMTP Email Outreach Engine."""
import os
import json
import time
import random
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import DATA_DIR
from services.outreach_service import OutreachService
from utils.logger import info, warning, error

EMAIL_CONFIG_PATH = os.path.join(DATA_DIR, "email_config.json")

# Standard provider presets
SMTP_PRESETS = {
    "Gmail (App Password)": {
        "host": "smtp.gmail.com",
        "port": 465,
        "use_ssl": True,
        "use_tls": False,
        "note": "يتطلب تفعيل التحقق بخطوتين في Google وإنشاء 'كلمة مرور للتطبيقات' (App Password)."
    },
    "Outlook / Office 365": {
        "host": "smtp.office365.com",
        "port": 587,
        "use_ssl": False,
        "use_tls": True,
        "note": "يستخدم منفذ 587 مع بروتوكول STARTTLS المشفر."
    },
    "Yahoo Mail": {
        "host": "smtp.mail.yahoo.com",
        "port": 465,
        "use_ssl": True,
        "use_tls": False,
        "note": "يتطلب كلمة مرور تطبيقات (App Password) من حساب ياهو."
    },
    "Custom SMTP / Webmail": {
        "host": "mail.yourdomain.com",
        "port": 465,
        "use_ssl": True,
        "use_tls": False,
        "note": "أدخل بيانات خادم البريد الخاص بدومين شركتك (cPanel / Webmail)."
    }
}

DEFAULT_EMAIL_SUBJECTS = [
    "{فكرة تسويقية مميزة|اقتراح للتعاون|استراتيجية نمو بالذكاء الاصطناعي} لـ {business} 🌟",
    "{تحية طيبة|مرحباً بحضرتك|السلام عليكم} - مقترح لتطوير مبيعات {business} في {city} 📈",
    "فكرة مبتكرة بمجال {industry} قد تضاعف عملاء {business} 👌",
]

DEFAULT_EMAIL_HTML_TEMPLATE = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f7f9fa; margin: 0; padding: 20px; color: #2d3748; }
  .email-container { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
  .header { background: linear-gradient(135deg, #0a84ff 0%, #0056b3 100%); padding: 28px 24px; text-align: center; color: #ffffff; }
  .header h2 { margin: 0; font-size: 22px; font-weight: 700; }
  .content { padding: 32px 28px; line-height: 1.8; font-size: 15px; }
  .badge { display: inline-block; background: #eef2ff; color: #4338ca; padding: 4px 12px; border-radius: 99px; font-size: 13px; font-weight: 600; margin-bottom: 16px; }
  .highlight-box { background: #f8fafc; border-right: 4px solid #0a84ff; padding: 16px; border-radius: 6px; margin: 20px 0; font-size: 14px; }
  .footer { background: #f8fafc; padding: 20px; text-align: center; font-size: 12px; color: #718096; border-top: 1px solid #edf2f7; }
  .btn { display: inline-block; background: #0a84ff; color: #ffffff !important; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 16px; }
</style>
</head>
<body>
<div class="email-container">
  <div class="header">
    <h2>مقترح شراكة وتطوير رقمي</h2>
  </div>
  <div class="content">
    <span class="badge">{industry} - {city}</span>
    <p>أهلاً بحضرتك يا فندم في <strong>{business}</strong> 👋،</p>
    <p>{intro}</p>
    <div class="highlight-box">
      <strong>💡 القيمة المضافة لمشروعكم:</strong><br>
      {value_prop}
    </div>
    <p>{cta}</p>
    <p style="margin-top: 24px;">مع خالص التقدير والاحترام،<br><strong>{sender_name}</strong></p>
  </div>
  <div class="footer">
    تم إرسال هذه الرسالة إلى إدارة {business}. إذا كنت لا ترغب في تلقي مقترحات أخرى، يسعدنا إبلاغنا بالرد على هذا الإيميل.
  </div>
</div>
</body>
</html>
"""


class EmailEngine:
    def __init__(self, config_path=EMAIL_CONFIG_PATH):
        self.config_path = config_path
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

    def load_config(self) -> dict:
        """Load saved SMTP configuration."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                warning(f"Failed to read email config: {e}")
        return {
            "provider": "Gmail (App Password)",
            "host": "smtp.gmail.com",
            "port": 465,
            "use_ssl": True,
            "use_tls": False,
            "sender_name": "فريق التطوير والتسويق",
            "sender_email": "",
            "password": "",
            "is_configured": False
        }

    def save_config(self, cfg: dict) -> bool:
        """Save SMTP configuration locally."""
        try:
            cfg["is_configured"] = bool(cfg.get("sender_email") and cfg.get("password") and cfg.get("host"))
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            info("Email configuration saved successfully.")
            return True
        except Exception as e:
            error(f"Failed to save email config: {e}")
            return False

    def test_connection(self, cfg: dict = None) -> tuple[bool, str]:
        """Test SMTP server connectivity and authentication."""
        config = cfg or self.load_config()
        host = config.get("host", "").strip()
        port = int(config.get("port", 465))
        sender_email = config.get("sender_email", "").strip()
        password = config.get("password", "").strip()
        use_ssl = config.get("use_ssl", True)
        use_tls = config.get("use_tls", False)

        if not host or not sender_email or not password:
            return False, "يرجى إدخال اسم الخادم، البريد الإلكتروني، وكلمة المرور/App Password."

        server = None
        try:
            if use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(host, port, context=context, timeout=12)
            else:
                server = smtplib.SMTP(host, port, timeout=12)
                if use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)

            server.login(sender_email, password)
            server.quit()
            return True, "✅ تم الاتصال بخادم البريد وتسجيل الدخول بنجاح تام!"
        except smtplib.SMTPAuthenticationError:
            return False, "❌ خطأ في المصادقة: البريد الإلكتروني أو كلمة المرور غير صحيحة. (إذا كنت تستخدم Gmail، تأكد من استخدام 'App Password' وليس كلمة مرور حسابك العادية)."
        except Exception as e:
            return False, f"❌ تعذر الاتصال بالخادم ({host}:{port}): {e}"
        finally:
            if server:
                try:
                    server.close()
                except Exception:
                    pass

    def send_single_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = "",
        cfg: dict = None
    ) -> tuple[bool, str]:
        """Send a single email via SMTP with dual HTML/text payload."""
        config = cfg or self.load_config()
        if not config.get("is_configured") and not (config.get("sender_email") and config.get("password")):
            return False, "إعدادات البريد غير مكتملة. يرجى ضبط خادم الـ SMTP أولاً في صفحة الإعدادات."

        host = config.get("host", "").strip()
        port = int(config.get("port", 465))
        sender_email = config.get("sender_email", "").strip()
        sender_name = config.get("sender_name", "").strip() or sender_email
        password = config.get("password", "").strip()
        use_ssl = config.get("use_ssl", True)
        use_tls = config.get("use_tls", False)

        if not to_email or "@" not in to_email:
            return False, f"البريد الإلكتروني للعميل غير صالح ({to_email})."

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = to_email

        # Attach Plain Text fallback first, then HTML
        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        if html_content:
            msg.attach(MIMEText(html_content, "html", "utf-8"))

        server = None
        try:
            if use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(host, port, context=context, timeout=15)
            else:
                server = smtplib.SMTP(host, port, timeout=15)
                if use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)

            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, msg.as_string())
            server.quit()
            return True, "تم إرسال الإيميل بنجاح ✅"
        except Exception as e:
            error(f"Failed to send email to {to_email}: {e}")
            return False, f"تعذر الإرسال: {e}"
        finally:
            if server:
                try:
                    server.close()
                except Exception:
                    pass

    def build_custom_email_payload(
        self,
        business_name: str,
        industry: str,
        city: str,
        custom_subject: str = None,
        custom_intro: str = None,
        custom_value: str = None,
        custom_cta: str = None,
    ) -> tuple[str, str]:
        """
        Construct dynamic Subject and HTML body applying full Spintax randomization.
        """
        b_name = business_name or "مشروعكم"
        ind = industry or "مجالكم"
        cty = city or "مدينتكم"
        cfg = self.load_config()
        sender = cfg.get("sender_name", "فريق العمل")

        # 1. Subject line with Spintax
        raw_subject = custom_subject or random.choice(DEFAULT_EMAIL_SUBJECTS)
        populated_subject = raw_subject.replace("{business}", b_name).replace("{industry}", ind).replace("{city}", cty)
        subject = OutreachService.parse_spintax(populated_subject)

        # 2. Body components with Spintax
        raw_intro = custom_intro or (
            "{شاهدنا تميزكم ونجاحكم اللافت|لفت انتباهنا المستوى الراقي لخدماتكم|نتابع باهتمام نشاطكم الريادي} "
            "في قطاع {industry} بمدينة {city}، وأحببنا مشاركتكم فكرة مبتكرة نطبقها حالياً مع شركائنا."
        )
        raw_value = custom_value or (
            "طورنا منظومة أتمتة تسويقية قائمة على الذكاء الاصطناعي قادرة على {استقطاب عملاء مهتمين جاهزين للشراء|مضاعفة عدد الاستفسارات والطلبات|خفض تكلفة الاستحواذ على العملاء بنسبة 40%} بشكل آلي ومنتظم."
        )
        raw_cta = custom_cta or (
            "{إذا كان وقت حضرتك يسمح، هل يناسبك أن نرسل لك دراسة حالة سريعة؟|يسعدنا جداً مشاركة نبذة تفصيلية ونماذج لنتائج سابقة إذا رغبت في الاطلاع عليها.|هل يناسبك تحديد موعد لمكالمة سريعة لمدة 5 دقائق لاستعراض الفكرة؟}"
        )

        intro = OutreachService.parse_spintax(raw_intro.replace("{business}", b_name).replace("{industry}", ind).replace("{city}", cty))
        value_prop = OutreachService.parse_spintax(raw_value.replace("{business}", b_name).replace("{industry}", ind).replace("{city}", cty))
        cta = OutreachService.parse_spintax(raw_cta.replace("{business}", b_name).replace("{industry}", ind).replace("{city}", cty))

        html = (
            DEFAULT_EMAIL_HTML_TEMPLATE
            .replace("{business}", b_name)
            .replace("{industry}", ind)
            .replace("{city}", cty)
            .replace("{intro}", intro)
            .replace("{value_prop}", value_prop)
            .replace("{cta}", cta)
            .replace("{sender_name}", sender)
        )

        plain_text = f"أهلاً بإدارة {b_name}،\n\n{intro}\n\nالقيمة المضافة:\n{value_prop}\n\n{cta}\n\nمع خالص التقدير،\n{sender}"
        return subject, html, plain_text

    def send_batch_emails(
        self,
        items: list[dict],
        min_delay: int = 5,
        max_delay: int = 15,
        progress_callback = None
    ) -> dict:
        """
        Send a batch of cold emails with realistic safety pauses between messages.
        """
        results = {"total": len(items), "sent": 0, "failed": 0, "details": []}
        cfg = self.load_config()

        ok, err = self.test_connection(cfg)
        if not ok:
            results["failed"] = len(items)
            results["details"].append({"email": "all", "success": False, "error": err})
            return results

        for idx, item in enumerate(items):
            lead_id = item.get("id")
            email_addr = item.get("email", "").strip()
            name = item.get("name", "العميل")
            subject = item.get("subject", "")
            html_body = item.get("html", "")
            text_body = item.get("text", "")

            if not email_addr or "@" not in email_addr:
                results["failed"] += 1
                results["details"].append({"id": lead_id, "name": name, "email": email_addr, "success": False, "error": "بريد غير صالح"})
                if progress_callback:
                    progress_callback(idx + 1, len(items), name, False, "بريد غير صالح")
                continue

            success, note = self.send_single_email(email_addr, subject, html_body, text_body, cfg=cfg)

            if success:
                results["sent"] += 1
                results["details"].append({"id": lead_id, "name": name, "email": email_addr, "success": True, "error": None})
                if progress_callback:
                    progress_callback(idx + 1, len(items), name, True, "تم الإرسال بنجاح ✅")
            else:
                results["failed"] += 1
                results["details"].append({"id": lead_id, "name": name, "email": email_addr, "success": False, "error": note})
                if progress_callback:
                    progress_callback(idx + 1, len(items), name, False, note)

            # Polite spacing between emails
            if idx < len(items) - 1:
                wait_sec = random.randint(min_delay, max_delay)
                time.sleep(wait_sec)

        return results
