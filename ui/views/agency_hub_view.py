"""AutoLeadGen v2 — UI View: Dedicated Agency & Recruitment Hub (باند شركات الإعلانات والتوظيف)."""
import urllib.parse
import streamlit as st
from config.constants import (
    WORLD_COUNTRIES_DATA,
    STATUS_READY,
    STATUS_CONTACTED,
    INTERACTION_SENT,
)
from database.repository import LeadRepository
from integrations.maps_scraper import MapsScraper
from pipeline.cleaner import DataCleaner
from pipeline.scorer import calculate_ai_fit
from services.outreach_service import OutreachService
from integrations.email_engine import EmailEngine
from ui.components import page_header, section_label, wa_badge, empty_state, escape


def render_agency_hub():
    page_header(
        "مركز شركات الإعلانات والتوظيف (Agency & Hiring Hub)",
        "Dedicated Hub for Creative Agencies & Recruitment",
        "🎯",
        "مخصص لتيم فهمي"
    )

    db: LeadRepository = st.session_state.db
    messenger = st.session_state.messenger
    wa_status = messenger.get_connection_status()

    # ═══════════════════════════════════════════════════════════════════════════
    # TABS: 1. استخراج واكتشاف | 2. الحملات والإرسال | 3. إدارة الشركات المستهدفة
    # ═══════════════════════════════════════════════════════════════════════════
    tab_search, tab_outreach, tab_crm = st.tabs([
        "🚀 استخراج شركات الإعلان والتوظيف",
        "📤 إرسال العروض والعينات المجانية",
        "📋 قائمة الشركات المستهدفة"
    ])

    # ── TAB 1: SEARCH & DISCOVERY ─────────────────────────────────────────────
    with tab_search:
        st.markdown("""
        <div style="background:rgba(10,132,255,0.08);border:1px solid rgba(10,132,255,0.25);
                    border-radius:12px;padding:12px 16px;margin-bottom:16px">
            <div style="font-size:14px;font-weight:700;color:#0a84ff;margin-bottom:4px">
                ⚡ رادار استكشاف وكالات الدعاية وشركات التوظيف (Turbo Scraping)
            </div>
            <div style="font-size:12px;color:#bbb">
                استخرج مئات وكالات الإعلان والتسويق ومكاتب التوظيف بدقة فائقة مع أرقام الواتساب والإيميلات ومواقعهم الرسمية فوراً.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_target, col_geo = st.columns([1, 1])

        with col_target:
            target_sector = st.selectbox(
                "النشاط المستهدف بدقة:",
                [
                    "شركات دعاية وإعلان وتسويق",
                    "شركات توظيف وموارد بشرية",
                    "شركات تصميم ودعاية",
                    "شركات تسويق رقمي",
                    "استوديوهات ميديا وموشن جرافيك",
                    "مكاتب استقدام وتوظيف بالخارج"
                ],
                index=0,
                key="agency_hub_target_sector"
            )

            limit_count = st.slider(
                "العدد المطلوب استخراجه:",
                min_value=5,
                max_value=150,
                value=25,
                step=5,
                key="agency_hub_limit"
            )

        with col_geo:
            country_choice = st.selectbox(
                "الدولة:",
                ["مصر 🇪🇬", "السعودية 🇸🇦", "الإمارات 🇦🇪", "الكويت 🇰🇼", "قطر 🇶🇦", "دولة أخرى"],
                index=0,
                key="agency_hub_country"
            )

            city_presets = {
                "مصر 🇪🇬": ["القاهرة", "الجيزة", "الإسكندرية", "التجمع الخامس", "الشيخ زايد", "المعادي", "مدينة نصر", "المهندسين", "مصر الجديدة", "الدقي"],
                "السعودية 🇸🇦": ["الرياض", "جدة", "الدمام", "الخبر", "مكة المكرمة", "المدينة المنورة"],
                "الإمارات 🇦🇪": ["دبي", "أبوظبي", "الشارقة", "عجمان"],
                "الكويت 🇰🇼": ["مدينة الكويت", "حولي", "السالمية", "الفروانية"],
                "قطر 🇶🇦": ["الدوحة", "الريان", "الوكرة"],
            }

            if country_choice in city_presets:
                city = st.selectbox("المدينة / المنطقة:", city_presets[country_choice], key="agency_hub_city")
            else:
                city = st.text_input("المدينة / الدولة يدوياً:", value="القاهرة", key="agency_hub_city_custom")

        st.write("")
        if st.button(f"🚀 بدء استخراج {limit_count} من {target_sector} في {city}", type="primary", use_container_width=True, key="agency_hub_btn_start"):
            status_box = st.empty()
            progress_bar = st.progress(0.0)

            clean_country = country_choice.split()[0] if " " in country_choice else country_choice
            query = f"{target_sector} في {city} {clean_country}"

            status_box.info(f"🔍 جاري البحث المباشر عن: **{query}**...")

            try:
                scraper = MapsScraper()
                raw_results = scraper.scrape_leads(
                    query=query,
                    limit=limit_count,
                    progress_callback=lambda curr, total: progress_bar.progress(min(1.0, curr / max(1, total)))
                )

                if not raw_results:
                    status_box.warning("⚠️ لم يتم العثور على نتائج جديدة لهذه المنطقة. جرب تغيير المدينة أو البحث عن نشاط مكمل.")
                else:
                    cleaner = DataCleaner()
                    added_count = 0

                    for item in raw_results:
                        cleaned = cleaner.clean_lead_data(
                            name=item.get("name", ""),
                            phone=item.get("phone", ""),
                            address=item.get("address", ""),
                            website=item.get("website", ""),
                            industry=target_sector,
                            city=city,
                            country=clean_country
                        )

                        if cleaned and cleaned.get("phone"):
                            fit_score = calculate_ai_fit(target_sector) + 15
                            lat = item.get("latitude")
                            lon = item.get("longitude")

                            db.insert_lead(
                                business_name=cleaned["business_name"],
                                phone=cleaned["phone"],
                                address=cleaned.get("address", ""),
                                website=cleaned.get("website", ""),
                                industry=target_sector,
                                city=city,
                                source="Google Maps Turbo",
                                language="Arabic",
                                score=fit_score,
                                status=STATUS_READY,
                                latitude=lat,
                                longitude=lon
                            )
                            added_count += 1

                    progress_bar.progress(1.0)
                    status_box.success(f"🎉 تم بنجاح استخراج وإضافة **{added_count}** شركة جديدة من {target_sector} إلى قاعدة البيانات!")
                    st.rerun()

            except Exception as e:
                status_box.error(f"❌ حدث خطأ أثناء الاستخراج: {e}")

    # ── TAB 2: OUTREACH & CAMPAIGNS ───────────────────────────────────────────
    with tab_outreach:
        st.markdown("""
        <div style="background:rgba(48,209,88,0.08);border:1px solid rgba(48,209,88,0.25);
                    border-radius:12px;padding:12px 16px;margin-bottom:16px">
            <div style="font-size:14px;font-weight:700;color:#30d158;margin-bottom:4px">
                💼 حملات التواصل والعينات المجانية لتيم فهمي
            </div>
            <div style="font-size:12px;color:#bbb">
                جميع الرسائل مجهزة بعرض التصميم والعينة المجانية مع أرقام التواصل (01147018367) والإيميل الرسمي (taiemfahmy19@gmail.com).
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Get all agency/recruitment leads
        all_leads = db.get_all_leads()
        agency_keywords = ["دعاية", "إعلان", "اعلان", "تسويق", "تصميم", "توظيف", "موارد بشرية", "recruitment", "hr", "agency", "marketing"]
        agency_leads = [
            l for l in all_leads
            if any(k in (l[5] or "").lower() for k in agency_keywords)
        ]
        ready_agency_leads = [l for l in agency_leads if l[9] == STATUS_READY]

        stat1, stat2, stat3 = st.columns(3)
        stat1.metric("إجمالي شركات الإعلان والتوظيف", len(agency_leads))
        stat2.metric("جاهز للتواصل الآن", len(ready_agency_leads))
        stat3.metric("تم التواصل معهم سابقاً", len([l for l in agency_leads if l[9] == STATUS_CONTACTED]))

        st.divider()

        # Template Selection
        templates = db.get_all_templates()
        agency_templates = [t for t in templates if t[0] in [5, 6, 7] or any(k in t[1] for k in ["إعلانات", "دعاية", "توظيف"])]

        if not agency_templates:
            agency_templates = templates

        tpl_names = [f"[{t[0]}] {t[1]}" for t in agency_templates]
        selected_tpl_idx = st.selectbox(
            "اختر صيغة الرسالة المراد استخدامها في الحملة:",
            range(len(tpl_names)),
            format_func=lambda i: tpl_names[i],
            index=0 if len(tpl_names) > 0 else 0,
            key="agency_hub_selected_tpl"
        )
        current_active_tpl = agency_templates[selected_tpl_idx][3]

        with st.expander("👁️ معاينة نص الصيغة المختارة (قابلة للتعديل والنسخ)", expanded=True):
            st.text_area("نص الصيغة الحالية:", value=current_active_tpl, height=180, disabled=True)

        st.write("")
        section_label(f"📋 الشركات الجاهزة للإرسال ({len(ready_agency_leads)} شركة)")

        if not ready_agency_leads:
            st.info("لا توجد شركات إعلانات أو توظيف في حالة 'جاهز للتواصل' حالياً. انتقل لتبويب 'استخراج شركات الإعلان والتوظيف' لإضافة المزيد.")
        else:
            # Batch Action Bar
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                if st.button(f"🚀 إرسال واتساب آلي للكل ({len(ready_agency_leads)} شركة)", type="primary", use_container_width=True, key="agency_hub_batch_wa"):
                    if wa_status != "CONNECTED":
                        st.error("⚠️ WhatsApp Web غير متصل. يرجى مسح رمز QR من لوحة التحكم أو صفحة الإعدادات أولاً.")
                    else:
                        batch_items = []
                        for lead in ready_agency_leads:
                            lid, b_name, phone, address, website, industry, city = lead[:7]
                            msg = OutreachService.build_personalized_message(b_name, industry, city, current_active_tpl)
                            batch_items.append({"id": lid, "phone": phone, "name": b_name, "message": msg})

                        p_bar = st.progress(0.0)
                        s_text = st.empty()

                        def update_prog(curr, total, name, success, note):
                            p_bar.progress(curr / total)
                            if success:
                                s_text.info(f"[{curr}/{total}] ✅ تم الإرسال إلى: **{name}**")
                            else:
                                s_text.warning(f"[{curr}/{total}] ⚠️ {name}: {note}")

                        res = messenger.send_batch_automated(
                            batch_items,
                            min_delay=60,
                            max_delay=120,
                            enable_human_typing=True,
                            enable_cooldown=True,
                            batch_size=5,
                            progress_callback=update_prog
                        )
                        s_text.success(f"🎉 اكتمل الإرسال! تم بنجاح إرسال {res['sent']} رسالة.")
                        st.rerun()

            with btn_col2:
                if st.button(f"✉️ إرسال بريد إلكتروني للشركات التي تملك إيميل", use_container_width=True, key="agency_hub_batch_email"):
                    leads_with_email = [l for l in ready_agency_leads if l[4] and "@" in str(l[4])]
                    if not leads_with_email:
                        st.warning("لم يتم العثور على إيميلات مسجلة لهذه الشركات في القائمة. (معظم الشركات يتم التواصل معها عبر الواتساب).")
                    else:
                        email_engine = EmailEngine(db)
                        sent_cnt = 0
                        for l in leads_with_email:
                            lid, b_name, phone, address, email_addr, industry, city = l[:7]
                            msg = OutreachService.build_personalized_message(b_name, industry, city, current_active_tpl)
                            subj = f"فرصة تعاون إبداعي لدعم وكالة {b_name} — عينة تصميم مجانية"
                            res = email_engine.send_email(email_addr, subj, msg, lead_id=lid)
                            if res.get("status") == "SENT":
                                sent_cnt += 1
                        st.success(f"🎉 تم إرسال {sent_cnt} إيميل بنجاح عبر حسابك taiemfahmy19@gmail.com!")
                        st.rerun()

            # Render individual lead cards
            for lead in ready_agency_leads[:30]:
                lid, b_name, phone, address, website, industry, city = lead[:7]
                lead_msg = OutreachService.build_personalized_message(b_name, industry, city, current_active_tpl)
                clean_digits = phone.lstrip("+")
                wa_url = f"https://wa.me/{clean_digits}?text={urllib.parse.quote(lead_msg)}"

                card_c1, card_c2 = st.columns([4, 1])
                with card_c1:
                    st.markdown(f"""
                    <div style="background:#1e1e1e;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:12px;margin-bottom:6px">
                        <div style="font-size:14px;font-weight:700;color:#fff">{escape(b_name)}</div>
                        <div style="font-size:12px;color:#aaa">📍 {escape(city)} &nbsp;|&nbsp; 🏷️ {escape(industry)} &nbsp;|&nbsp; 📞 {escape(phone)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with card_c2:
                    st.markdown(f"""
                    <a href="{wa_url}" target="_blank" style="background:#25d366;color:#000;font-size:12px;font-weight:700;
                               padding:10px 14px;border-radius:8px;text-decoration:none;display:block;text-align:center;margin-top:8px">
                        📲 فتح واتساب
                    </a>
                    """, unsafe_allow_html=True)

    # ── TAB 3: LEADS CRM TABLE ────────────────────────────────────────────────
    with tab_crm:
        section_label("قاعدة بيانات شركات الإعلانات والتوظيف")

        all_leads = db.get_all_leads()
        agency_keywords = ["دعاية", "إعلان", "اعلان", "تسويق", "تصميم", "توظيف", "موارد بشرية", "recruitment", "hr", "agency", "marketing"]
        agency_leads = [
            l for l in all_leads
            if any(k in (l[5] or "").lower() for k in agency_keywords)
        ]

        if not agency_leads:
            empty_state("لا توجد شركات مسجلة حتى الآن", "استخدم تبويب 'استخراج شركات الإعلان والتوظيف' للبدء في تجميع الشركات فوراً.", "🏢")
        else:
            filter_subsector = st.radio(
                "تصفية حسب القطاع:",
                ["الكل", "شركات دعاية وإعلان وتسويق", "شركات توظيف وموارد بشرية"],
                horizontal=True,
                key="agency_hub_crm_filter"
            )

            filtered = agency_leads
            if filter_subsector == "شركات دعاية وإعلان وتسويق":
                filtered = [l for l in agency_leads if any(k in (l[5] or "") for k in ["دعاية", "إعلان", "اعلان", "تسويق", "تصميم"])]
            elif filter_subsector == "شركات توظيف وموارد بشرية":
                filtered = [l for l in agency_leads if any(k in (l[5] or "") for k in ["توظيف", "موارد بشرية", "recruitment", "hr"])]

            st.caption(f"عدد الشركات المعروضة: **{len(filtered)}** شركة")

            import pandas as pd
            table_data = []
            for l in filtered:
                table_data.append({
                    "م": l[0],
                    "اسم الشركة": l[1],
                    "الهاتف": l[2],
                    "النشاط": l[5],
                    "المدينة": l[6],
                    "الموقع": l[4] or "—",
                    "الحالة": l[9],
                    "التقييم": f"{l[8]}%" if l[8] else "85%"
                })

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, height=450)
