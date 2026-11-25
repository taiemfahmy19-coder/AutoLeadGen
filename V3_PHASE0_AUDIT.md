# Phase 0 — Repository Audit (AutoLeadGen V2 → V3 Readiness)

**Date:** 2026-11-25  
**Workspace:** `D:\AI feed\AutoLeadGen`  
**Audit Scope:** Full codebase, SQLite database (`data/leads.db`), 17 test modules (118 tests), dependencies, runtime SDKs, integration seams, and V3 compatibility risks.

---

## 1. الوظائف الحالية (Current Working Functionality)

| Module / Component | Verified Capability | Evidence |
| :--- | :--- | :--- |
| **Entry & Navigation (`app.py`)** | Multi-page Streamlit UI (`Dashboard`, `Search Leads`, `Leads CRM`, `Message Center`, `Outreach Queue`, `Settings`), responsive mobile CSS (`ui/theme.py`, `ui/components.py`). | `app.py`, `ui/theme.py` |
| **Google Maps Scraper (`integrations/maps_scraper.py`)** | Playwright live browser scraping of Google Maps business cards (`phone`, `name`, `address`, `website`), image/font/media blocking for speed, real-number policy (`use_live_browser=False` returns `[]`). | `integrations/maps_scraper.py`, `tests/test_search_multilingual_dedup.py` |
| **Google Web Search Scraper (`integrations/google_search_scraper.py`)** | Organic Google Web discovery for public `wa.me` numbers. | `integrations/google_search_scraper.py`, `tests/test_google_search_scraper.py` |
| **Data Cleaner (`pipeline/cleaner.py`)** | E.164 normalization, Arabic-Indic digit mapping (`٠-٩`), Egyptian landline detection (`EGYPT_LANDLINE_PREFIXES`), mobile whitelisting. | `pipeline/cleaner.py`, `tests/test_cleaner.py` (10/10 pass) |
| **5-Level Deduplicator (`pipeline/deduplicator.py`)** | Phone E.164, website domain, name+address token/sequence similarity ($\ge 60\%$), place listing URL, cross-source atomic merging with `merge_history`. | `pipeline/deduplicator.py`, `tests/test_deduplicator.py`, `tests/test_deduplication_engine.py` |
| **Multi-Factor Scorer (`pipeline/scorer.py`)** | 0–100 objective scoring breakdown (`LeadScoreBreakdown`), industry fit, priority classification (`HIGH`, `MEDIUM`, `LOW`). | `pipeline/scorer.py`, `tests/test_scorer.py`, `tests/test_scoring_engine.py` |
| **Outbound Email (`integrations/email_engine.py`)** | Zero-cost SMTP (`SSL` 465 / `STARTTLS` 587) with Gmail/Outlook/Yahoo/Custom presets, Spintax subjects & HTML/text dual bodies, batch sending with safety delays. | `integrations/email_engine.py`, `tests/test_email_engine.py` (7/7 pass) |
| **Database & Backups (`database/`)** | SQLite 3 with WAL mode, `PRAGMA foreign_keys = ON`, `threading.Lock` transaction context manager, 6 indexes (`idx_leads_phone`, `idx_leads_status`, `idx_leads_score`, `idx_leads_wa`, `idx_interactions_lead_id`, `idx_contacts_lead_id`), SQLite Online Backup API (`BackupService`). Current DB (`data/leads.db`) holds 4 seeded templates, 3,480 merge history records, 3,906 audit logs, and 0 active leads. | `database/connection.py`, `database/repository.py`, `database/backup_service.py` |
| **Export (`services/export_service.py`)** | Streaming UTF-8-BOM CSV (`utf-8-sig`) and `.xlsx` export via `openpyxl`. | `services/export_service.py` |
| **Legacy WhatsApp/IG (`integrations/whatsapp_playwright.py`, `integrations/instagram_playwright.py`)** | Playwright Stealth automation with Bezier mouse curves and human typing delays. Note: Facebook & Instagram are explicitly removed from V3 development scope. | `integrations/whatsapp_playwright.py`, `integrations/instagram_playwright.py` |

---

## 2. الوظائف المكسورة أو الناقصة (Broken, Partial & Missing Functionality)

1. **3 اختبارات فاشلة (115 passed, 3 failed out of 118):**
   - `tests/test_phone_normalization.py::test_egyptian_mobile_with_erroneous_plus`: `normalize_phone("+01012345678")` returns `"+01012345678"` instead of `"+201012345678"` because the `+` fast-path in `pipeline/cleaner.py:64` bypasses local-zero detection for `+010`/`+011`/`+012`/`+015`.
   - `tests/test_search_multilingual_dedup.py::test_other_countries_language`: Test asserts `English` for France (`+33`), while `config/constants.py` was later expanded to return `"French"`, `"German"`, `"Spanish"`, `"Turkish"`.
   - `tests/test_whatsapp_verification.py::test_random_numbers_never_marked_as_verified`: Test expects `use_live_browser=False` to return synthetic leads with `WA_STATUS_UNKNOWN`, whereas `LeadScraper.search_leads()` strictly returns `[]` when `use_live_browser=False`.
2. **خريطة العالم التفاعلية (`ui/views/search_view.py:237-248`):**
   - تستخدم Leaflet 1.9.4 عبر CDN، لكنها **توزع العلامات عشوائياً** حول إحداثيات المدينة (`rng.uniform(-0.03, 0.03)` و`rng.uniform(-0.05, 0.05)`) ولا تحفظ إحداثيات `latitude`/`longitude` حقيقية في جدول `leads`.
   - لا يوجد `Marker Clustering`، ولا `Heatmap`، ولا تحميل تدريجي، ولا فلترة مباشرة على الخريطة.
3. **محرك الاكتشاف (`integrations/maps_scraper.py`):**
   - يعتمد فقط على Google Maps Playwright ومقيد بسقف صلب `limit = min(50, ...)`، بدون OpenStreetMap/Overpass API أو Wikidata أو Government Registries أو تقسيم جغرافي للشبكة أو حفظ نقطة استئناف (Checkpoint/Pagination).
4. **البريد الوارد وذكاء الردود:**
   - لا يوجد استماع IMAP، ولا ربط للردود بالشركات، ولا تصنيف آلي للردود، ولا نظام إدارة إلغاء الاشتراك (Unsubscribe / Consent).
5. **الذكاء الاصطناعي المحلي:**
   - لا يوجد تكامل مع Ollama / Qwen / Gemma ولا مصنف محلي باستخدام `scikit-learn`؛ مجرد مطابقة كلمات مفتاحية ثابتة في `pipeline/scorer.py`.
6. **الخلفية والمهام المجدولة (Background Jobs):**
   - كل العمليات الثقيلة (Scraping، Email Batching) تعمل بشكل متزامن (Synchronous) داخل خيط Streamlit، مما يجمّد الواجهة. لا يوجد `APScheduler` أو Task Queue حقيقي بـ Task ID / Cancel / Progress.
7. **Backend API وتطبيق Android:**
   - لا يوجد خادم FastAPI ولا WebSocket، ولا يوجد مجلد تطبيق Flutter/Android ولا أي بيئة بناء Android مثبتة حالياً على الجهاز.
8. **وثائق متضاربة مع الكود:**
   - `docs/ARCHITECTURE.md` يذكر `core/config_manager.py` و`core/system_controller.py` و`core/scheduler.py` غير الموجودة في `core/`.

---

## 3. المشاكل الأمنية (Security Findings)

1. **غياب المصادقة (High Severity):** `app.py` لا يفرض تسجيل دخول؛ أي مستخدم يصل للمنفذ `8501` يمكنه مسح قاعدة البيانات (`settings_view.py:391`) أو إرسال حملات بريد أو قراءة بيانات العملاء.
2. **تخزين كلمات مرور البريد كنص صريح (High Severity):** `integrations/email_engine.py:124` يحفظ `password` (App Password) داخل `data/email_config.json` بدون تشفير.
3. **غياب JWT / Argon2 / RBAC / Rate Limiting:** لا توجد طبقة مصادقة API أو صلاحيات أدوار أو تحديد معدل الطلبات.
4. **أمان قاعدة البيانات (`LeadRepository`):** الاستعلامات محمية بـ `?` parameterization و`ALLOWED_UPDATE_COLUMNS`، لكن لا يوجد عزل لبيانات الأسرار أو جلسات المستخدمين.

---

## 4. التبعيات وبيئة التشغيل (Dependencies & Toolchain Audit)

### المثبت حالياً (Installed):
- **Python:** `3.14.4` (`C:\Python314\python.exe`)
- **Web / API:** `streamlit 1.63.0`, `fastapi 0.141.1`, `uvicorn 0.52.0`, `starlette 1.3.1`, `pydantic 2.13.4`, `websockets 16.1.1`, `httpx 0.28.1`, `requests 2.34.2`, `aiohttp 3.14.3`
- **Crypto:** `cryptography 50.0.2`, `itsdangerous 2.2.0`
- **Automation & Data:** `playwright 1.61.0`, `playwright-stealth 2.0.3`, `pandas 3.0.5`, `openpyxl 3.1.5`, `numpy 2.5.2`, `pytest 9.1.1`, `qrcode 8.2`
- **System Tools:** `winget.exe` متاح، `curl.exe` متاح، `git 2.47.1`، `gh` CLI مسجل الدخول، ومساحة قرص `D:` الحرة **78.76 GB** (و`C:` **11.3 GB**).

### غير مثبت حالياً (Missing — يتطلب التثبيت أو البناء حسب المرحلة):
- **Python Libraries المطلوبة لـ V3:** `argon2-cffi`, `PyJWT`, `apscheduler`, `beautifulsoup4`, `scikit-learn` (متاح تثبيتها عبر `pip`).
- **Android / Flutter Toolchain (حرجة للمرحلة 7 و8):**
  - `flutter` غير مثبت (`where flutter` فارغ).
  - `dart` غير مثبت.
  - `JDK 17+` غير مثبت (الموجود فقط `C:\Program Files\Java\jre-1.8`).
  - `Android SDK` غير مثبت (`ANDROID_HOME` و`ANDROID_SDK_ROOT` فارغان).
- **Local LLM Runtime (اختيارية للذكاء الاصطناعي الثقيل):** `ollama` غير مثبت حالياً (لذلك سنبني طبقة AI تدعم Ollama عند توفره + طبقة تحليل محلية ذكية تعمل بدونه عبر `scikit-learn` / heuristics).
- **Remote Tunnel:** `tailscale` غير مثبت حالياً (سنوفر إعداد وتكامل آمن يكتشف Tailscale / WireGuard ويوفر التوجيه والتوثيق).

---

## 5. نقاط الربط المناسبة (Integration Seams)

1. **Repository Abstraction (`database/repository.py` + `database/connection.py`):** نقطة ربط مثالية لتوسيع جدول `leads` بأعمدة V3 (`latitude`, `longitude`, `coord_source`, `coord_verified`, `data_confidence`, `country`, `continent`, `collected_at`, `source_url`, `ai_summary`, `ai_category`, `unsubscribed`, `last_reply_at`, `reply_sentiment`) وإضافة جداول V3 الجديدة (`users`, `tasks`, `discovery_checkpoints`, `email_queue`, `email_messages`, `lead_sources`, `geo_saved_states`, `notifications`) مع واجهة abstract repository تسمح بالانتقال لـ PostgreSQL/PostGIS لاحقاً.
2. **`services/` Layer (`lead_service.py`, `outreach_service.py`, `export_service.py`):** تشترك فيه واجهة Streamlit وخادم FastAPI الجديد وجدولة الخلفية (Background Task Manager) لضمان عدم تكرار المنطق.
3. **`integrations/`:** يمكن إضافة `overpass_discovery.py`, `wikidata_discovery.py`, `website_crawler.py`, `imap_listener.py` بنفس نمط `maps_scraper.py` و`email_engine.py`.
4. **Leaflet Component (`ui/views/search_view.py`):** جاهز للترقية لاستخدام إحداثيات حقيقية + `Leaflet.markercluster` + `Leaflet.heat` + خرائط متعددة الطبقات (Dark/Light/OSM/Satellite).

---

## 6. مخاطر التوافق (Compatibility Risks)

1. **كسر قاعدة البيانات الحالية (`data/leads.db`):** يوجد بالفعل جداول `templates` (4 صفوف) و`audit_log` (3906 صفوف) و`merge_history` (3480 صفاً). أي ترقية Schema يجب أن تستخدم `ALTER TABLE ... ADD COLUMN` الآمنة مع نسخة احتياطية قبل التنفيذ (`BackupService`).
2. **تعارض Loop في Streamlit + Playwright + FastAPI:** استدعاء `playwright.sync_api` من داخل Event Loop يؤدي لخطأ `Sync API inside the asyncio loop`. يجب تشغيل المهام الثقيلة في ThreadPoolExecutor أو Worker منفصل.
3. **Python 3.14 Compatibility:** بعض المكتبات القديمة قد لا تملك wheels لـ Python 3.14 (مثلاً `sentence-transformers` أو `torch`). يجب التحقق من توفر wheels قبل التثبيت والاعتماد على `scikit-learn` / `httpx` / `argon2-cffi` الخفيفة المتوافقة مع 3.14.
4. **بناء APK الحقيقي (`app-release.apk`):** نظراً لعدم وجود Flutter وJDK 17 وAndroid SDK حالياً على الجهاز، يتطلب إتمام المرحلة 8 تنزيل وتثبيت هذه الأدوات على قرص `D:\tools` (أو وجود اتصال مستقر لتنزيل Gradle dependencies).
5. **الوظائف القديمة vs نطاق V3:** الطلب يأمر بحذف Facebook/Instagram من نطاق V3 مع الحفاظ على الوظائف العاملة. سنوقف أي عرض أو تطوير جديد لـ FB/IG في واجهات V3 مع عدم كسر الاختبارات القائمة، والتركيز حصرياً على Email + Global Map.
