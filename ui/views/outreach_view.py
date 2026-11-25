"""AutoLeadGen v2 - UI Views: Omnichannel Supervised Outreach Queue (WhatsApp, Cold Email, Social)."""
import time
import streamlit as st
from config.constants import STATUS_DO_NOT_CONTACT, STATUS_CONTACTED, INTERACTION_SENT
from services.outreach_service import OutreachService
from integrations.email_engine import EmailEngine, DEFAULT_EMAIL_SUBJECTS
from ui.components import page_header, section_label, wa_badge, empty_state, escape


def render_outreach_queue():
    page_header("مركز التواصل متعدد القنوات (Omnichannel Outreach)", "Multi-Channel Outreach Hub", "📤")

    db = st.session_state.db
    messenger = st.session_state.messenger
    wa_status = messenger.get_connection_status()

    outreach_svc = OutreachService(db)
    ready_leads = outreach_svc.get_queue_leads()

    if not ready_leads:
        empty_state("طابور التواصل فارغ حالياً", "لا يوجد عملاء في حالة 'جاهز للتواصل' (READY). يمكنك استخراج عملاء جدد من صفحة البحث.", "📭")
        return

    from config.constants import DEFAULT_ARABIC_TEMPLATE, DEFAULT_ENGLISH_TEMPLATE, MULTILINGUAL_TEMPLATES
    templates = db.get_all_templates()
    ar_template = next((t[3] for t in templates if t[2] == "Arabic"), DEFAULT_ARABIC_TEMPLATE)
    if not ar_template or "{business}" not in ar_template:
        ar_template = DEFAULT_ARABIC_TEMPLATE

    en_template = next((t[3] for t in templates if t[2] == "English"), DEFAULT_ENGLISH_TEMPLATE)
    if not en_template or "{business}" not in en_template:
        en_template = DEFAULT_ENGLISH_TEMPLATE

    def get_template_for_lead(lead_row):
        # Index 10 is language in the leads schema
        lang = lead_row[10] if len(lead_row) > 10 and lead_row[10] else "Arabic"
        if lang == "English":
            return en_template
        return MULTILINGUAL_TEMPLATES.get(lang, ar_template)

    tab_wa, tab_email, tab_social = st.tabs([
        "🟢 حملات واتساب (WhatsApp Web)",
        "✉️ حملات البريد الإلكتروني (Cold Email)",
        "📸 منصات التواصل (Instagram & Social)"
    ])

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 1: WHATSAPP OUTREACH
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_wa:
        if wa_status == "CONNECTED":
            st.success("🟢 WhatsApp Web متصل وجاهز للإرسال الآلي المباشر")
        else:
            st.warning("🟠 WhatsApp Web غير متصل حالياً.")

        st.caption(f"إجمالي العملاء الجاهزين في الطابور: **{len(ready_leads)}** عميل")

        if wa_status == "CONNECTED":
            with st.container(border=True):
                section_label("🚀 الإرسال الآلي التلقائي لكافة عملاء الطابور (Auto-Pilot)")
                st.markdown(
                    f"<p style='font-size:13px;color:#888;margin-bottom:8px'>"
                    f"إرسال رسائل مخصصة باسم كل مكان ونشاطه تلقائياً لجميع العملاء الجاهزين ({len(ready_leads)} عميل) دون أي تدخل منك."
                    f"</p>",
                    unsafe_allow_html=True
                )
                col_q1, col_q2 = st.columns([3, 2])
                with col_q1:
                    q_delay_range = st.slider(
                        "الفاصل الزمني البشري العشوائي بين كل رسالة (ثوانٍ لحماية الرقم):",
                        min_value=60,
                        max_value=300,
                        value=(90, 180),
                        key="q_auto_delay",
                        help="الفاصل الزمني الآمن والموصى به دولياً هو 90 إلى 180 ثانية مع محاكاة سلوك بشري كامل لمنع حظر الحساب."
                    )
                    q_typing_mode = st.checkbox(
                        "✍️ تفعيل محاكاة الكتابة البشرية (مع أخطاء عفوية وتصحيحها ومؤشر 'يكتب الآن...')",
                        value=True,
                        key="q_auto_typing",
                        help="يقوم بكتابة الحروف بشكل واقعي، وتصحيح أخطاء عفوية طفيفة لمحاكاة أصابع الإنسان على الكيبورد، وتفعيل مؤشر الكتابة."
                    )
                    q_cooldown_mode = st.checkbox(
                        "🛑 تفعيل نظام الدفعات وفترات الراحة (استراحة 15 دقيقة بعد كل 5 رسائل)",
                        value=True,
                        key="q_auto_cooldown",
                        help="يقسم الإرسال لدفعات صغيرة مع فترات راحة حقيقية كما يفعل البشر، وهو الدرع الأقوى لمنع رصد الـ Bulk Messaging."
                    )
                with col_q2:
                    st.markdown(f"""
                    <div style="background:#1a1a1a;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:10px 14px;margin-top:8px">
                        <div style="font-size:12px;color:#888">🛡️ حماية الحساب والتخفي: <b>مفعلة (Stealth)</b></div>
                        <div style="font-size:12px;color:#30d158">⏱️ فاصل عشوائي: <b>{q_delay_range[0]} - {q_delay_range[1]} ثانية</b></div>
                        <div style="font-size:12px;color:#0a84ff">✍️ محاكي الكتابة: <b>{'بشري مع تصحيح' if q_typing_mode else 'سريع'}</b></div>
                        <div style="font-size:12px;color:#ff9f0a">🛑 استراحة الدفعات: <b>{'مفعلة (كل 5)' if q_cooldown_mode else 'معطلة'}</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.write("")
                    if st.button(f"🚀 بدء إرسال الطابور بالكامل ({len(ready_leads)} عميل)", type="primary", use_container_width=True, key="btn_start_wa_batch"):
                        batch_items = []
                        for lead in ready_leads:
                            lid, b_name, phone, address, website, industry, city = lead[:7]
                            lead_tpl = get_template_for_lead(lead)
                            msg = OutreachService.build_personalized_message(b_name, industry, city, lead_tpl)
                            batch_items.append({"id": lid, "phone": phone, "name": b_name, "message": msg})

                        progress_bar = st.progress(0.0)
                        status_text = st.empty()

                        def update_q_prog(curr, total, name, success, note):
                            progress_bar.progress(curr / total)
                            if "⏳" in str(note) or "✍️" in str(note) or "🛑" in str(note):
                                status_text.info(f"[{curr}/{total}] {note}")
                            elif success:
                                status_text.info(f"[{curr}/{total}] ✅ تم إرسال الرسالة إلى: **{name}**")
                            else:
                                status_text.warning(f"[{curr}/{total}] ⚠️ {name}: {note}")

                        res = messenger.send_batch_automated(
                            batch_items,
                            min_delay=q_delay_range[0],
                            max_delay=q_delay_range[1],
                            enable_human_typing=q_typing_mode,
                            enable_cooldown=q_cooldown_mode,
                            batch_size=5,
                            progress_callback=update_q_prog
                        )
                        if res["sent"] > 0 and res["failed"] == 0:
                            st.success(f"🎉 اكتمل إرسال الطابور بنجاح تام! تم إرسال {res['sent']} رسالة.")
                        elif res["sent"] > 0 and res["failed"] > 0:
                            st.warning(f"⚠️ تم إرسال {res['sent']} رسالة بنجاح، بينما تعذر إرسال {res['failed']} رسالة.")
                        else:
                            first_err = res["details"][0]["error"] if res.get("details") else "تعذر إرسال الرسائل."
                            st.error(f"❌ لم يتم إرسال أي رسالة: {first_err}")
                        time.sleep(1)
                        st.rerun()
        else:
            with st.container(border=True):
                st.warning("⚠️ WhatsApp Web غير متصل حالياً! لتفعيل الإرسال التلقائي دون تدخل، يجب ربط حسابك أولاً.")
                curr_st = messenger.get_connection_status()
                if curr_st in ["STARTING", "SCANNING"]:
                    st.info("⏳ جلسة الربط نشطة حالياً! إذا ظهرت نافذة المتصفح امسح رمز الـ QR من هاتفك (WhatsApp > الأجهزة المرتبطة).")
                    c_w1, c_w2 = st.columns(2)
                    with c_w1:
                        if st.button("🔄 فحص حالة الربط", use_container_width=True, key="q_chk_st"):
                            st.rerun()
                    with c_w2:
                        if st.button("❌ إلغاء الربط", use_container_width=True, key="q_cancel_st"):
                            messenger.cancel_worker()
                            st.rerun()
                else:
                    c_l1, c_l2 = st.columns(2)
                    with c_l1:
                        if st.button("🌐 فتح متصفح خارجي للمسح بالهاتف (موصى به)", type="primary", use_container_width=True, key="q_open_browser"):
                            messenger.start_qr_linking_worker(headless=False, timeout_sec=120)
                            st.info("تم فتح متصفح WhatsApp Web على جهازك! يرجى مسح رمز الـ QR بهاتفك الآن.")
                            time.sleep(1)
                            st.rerun()
                    with c_l2:
                        if st.button("📲 أو فتح شاشة الـ QR للربط", use_container_width=True, key="q_go_login"):
                            st.session_state.authenticated = False
                            st.rerun()

        # WhatsApp Individual Lead Cards
        for idx, lead in enumerate(ready_leads):
            lid, b_name, phone, address, website, industry, city, source, score, status = lead[:10]
            wa_st = lead[13] if len(lead) > 13 else "UNKNOWN"

            with st.container(border=True):
                cols = st.columns([0.5, 3, 2, 6])
                with cols[0]:
                    st.markdown(f"**#{idx+1}**")
                with cols[1]:
                    st.markdown(f"**{escape(b_name)}**")
                    st.caption(f"{escape(industry)} | {escape(city)}")
                with cols[2]:
                    st.markdown(f"**{escape(phone)}**")
                    st.markdown(wa_badge(wa_st), unsafe_allow_html=True)
                with cols[3]:
                    lead_tpl = get_template_for_lead(lead)
                    default_msg = OutreachService.build_personalized_message(b_name, industry, city, lead_tpl)
                    msg_edit = st.text_area("الرسالة:", value=default_msg, height=80, key=f"q_msg_{lid}", label_visibility="collapsed")
                    
                    btn_cols = st.columns(4)
                    with btn_cols[0]:
                        wa_link = messenger.generate_direct_link(phone, msg_edit)
                        st.link_button("🔗 wa.me", wa_link, use_container_width=True)
                    with btn_cols[1]:
                        if wa_status == "CONNECTED":
                            if st.button("🚀 إرسال Web", key=f"send_pw_{lid}", type="primary", use_container_width=True):
                                with st.spinner("جاري الإرسال..."):
                                    success, res_msg = messenger.send_via_playwright(lid, phone, msg_edit)
                                    if success:
                                        st.success(res_msg)
                                        st.rerun()
                                    else:
                                        st.error(res_msg)
                    with btn_cols[2]:
                        if st.button("✅ Contacted", key=f"mark_c_{lid}", use_container_width=True):
                            messenger.send_supervised(lid, phone, msg_edit)
                            st.success("تم التحديث إلى CONTACTED.")
                            st.rerun()
                    with btn_cols[3]:
                        if st.button("🛑 حظر", key=f"dnc_{lid}", use_container_width=True):
                            db.update_lead_status(lid, STATUS_DO_NOT_CONTACT)
                            st.error("تم حظر العميل.")
                            st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 2: COLD EMAIL OUTREACH
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_email:
        email_engine = EmailEngine()
        email_cfg = email_engine.load_config()

        if not email_cfg.get("is_configured"):
            st.warning("⚠️ لم يتم ضبط إعدادات خادم البريد (SMTP) بعد! يمكنك إعداد بريد Gmail أو خادم شركتك بسهولة من صفحة الإعدادات.")
            if st.button("⚙️ الانتقال إلى صفحة الإعدادات لضبط البريد", type="primary"):
                st.session_state.current_page = "Settings"
                st.rerun()

        # Email Campaign Composer
        with st.container(border=True):
            section_label("✉️ صانع حملات البريد الإلكتروني (Email Campaign Studio)")
            st.markdown(
                "<p style='font-size:13px;color:#888;margin-bottom:8px'>"
                "يدعم عنوان الإيميل ومحتواه محرك الـ <b>Spintax</b> المتطور لتوليد صيغ مختلفة لكل عميل وتفادي مجلد الـ Spam بالكامل."
                "</p>",
                unsafe_allow_html=True
            )

            em_c1, em_c2 = st.columns([2, 1])
            with em_c1:
                email_subject_template = st.text_input(
                    "عنوان الإيميل (مع دعم Spintax):",
                    value=DEFAULT_EMAIL_SUBJECTS[0],
                    help="يمكنك استخدام {business} و {industry} و {city} وخيارات {خيار1|خيار2}"
                )
            with em_c2:
                email_delay_range = st.slider("الفاصل بين كل إيميل (ثوانٍ):", min_value=3, max_value=30, value=(5, 12))

            with st.expander("👁️ معاينة قالب الإيميل التفاعلي (HTML Live Preview)", expanded=False):
                subj_demo, html_demo, text_demo = email_engine.build_custom_email_payload(
                    business_name="كلاس ون للحلويات",
                    industry="حلويات وشوكولاتة",
                    city="الرياض",
                    custom_subject=email_subject_template
                )
                st.caption(f"**نموذج لعنوان الإيميل المولد:** {subj_demo}")
                st.components.v1.html(html_demo, height=380, scrolling=True)

        # Leads Filtered for Email Outreach
        leads_with_email = []
        for lead in ready_leads:
            lid, b_name, phone, address, website, industry, city = lead[:7]
            em = lead[15] if len(lead) > 15 else ""
            if em and "@" in str(em):
                leads_with_email.append(lead)

        st.caption(f"عدد العملاء الذين يتوفر لديهم بريد إلكتروني مسجل: **{len(leads_with_email)}** من أصل {len(ready_leads)} عميل")

        if leads_with_email:
            if st.button(f"🚀 إرسال حملة البريد لكافة المؤهلين ({len(leads_with_email)} عميل)", type="primary", use_container_width=True, key="btn_send_all_emails"):
                em_prog = st.progress(0.0)
                em_stat = st.empty()

                email_items = []
                for lead in leads_with_email:
                    lid, b_name, phone, address, website, industry, city = lead[:7]
                    em = lead[15]
                    subj, html_body, txt_body = email_engine.build_custom_email_payload(
                        business_name=b_name,
                        industry=industry,
                        city=city,
                        custom_subject=email_subject_template
                    )
                    email_items.append({
                        "id": lid,
                        "email": em,
                        "name": b_name,
                        "subject": subj,
                        "html": html_body,
                        "text": txt_body
                    })

                def update_email_prog(curr, total, name, success, note):
                    em_prog.progress(curr / total)
                    if success:
                        em_stat.info(f"[{curr}/{total}] ✅ تم إرسال الإيميل إلى: **{name}**")
                    else:
                        em_stat.warning(f"[{curr}/{total}] ⚠️ {name}: {note}")

                res = email_engine.send_batch_emails(
                    email_items,
                    min_delay=email_delay_range[0],
                    max_delay=email_delay_range[1],
                    progress_callback=update_email_prog
                )
                if res["sent"] > 0:
                    st.success(f"🎉 تم إرسال {res['sent']} إيميل بنجاح تام!")
                if res["failed"] > 0:
                    st.warning(f"تعذر إرسال {res['failed']} إيميل.")
                time.sleep(1)
                st.rerun()

        # Individual Lead Email Cards
        for idx, lead in enumerate(ready_leads):
            lid, b_name, phone, address, website, industry, city = lead[:7]
            curr_email = lead[15] if len(lead) > 15 else ""
            em_st = lead[16] if len(lead) > 16 else "UNKNOWN"

            with st.container(border=True):
                ec1, ec2, ec3, ec4 = st.columns([0.5, 3, 3, 4.5])
                with ec1:
                    st.markdown(f"**#{idx+1}**")
                with ec2:
                    st.markdown(f"**{escape(b_name)}**")
                    st.caption(f"{escape(industry)} | {escape(city)}")
                with ec3:
                    new_em = st.text_input("البريد الإلكتروني:", value=curr_email, key=f"em_inp_{lid}", placeholder="name@business.com")
                    if new_em != curr_email:
                        db.update_lead_email(lid, new_em)
                with ec4:
                    subj, html_b, txt_b = email_engine.build_custom_email_payload(
                        business_name=b_name,
                        industry=industry,
                        city=city,
                        custom_subject=email_subject_template
                    )
                    st.caption(f"**العنوان:** {subj}")
                    b_col1, b_col2 = st.columns(2)
                    with b_col1:
                        if st.button("✉️ إرسال إيميل فردي", key=f"send_em_btn_{lid}", type="primary", use_container_width=True):
                            if not new_em:
                                st.error("يرجى إدخال بريد إلكتروني أولاً.")
                            else:
                                with st.spinner("جاري إرسال الإيميل عبر SMTP..."):
                                    ok, msg = email_engine.send_single_email(new_em, subj, html_b, txt_b)
                                    if ok:
                                        db.update_lead_email_status(lid, "SENT")
                                        st.success(msg)
                                    else:
                                        st.error(msg)
                    with b_col2:
                        if st.button("✅ تم التواصل", key=f"mark_em_c_{lid}", use_container_width=True):
                            db.update_lead_status(lid, STATUS_CONTACTED)
                            st.success("تم التحديث إلى CONTACTED.")
                            st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 3: INSTAGRAM DM OUTREACH
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_social:
        ig = st.session_state.get("ig_engine")
        ig_status = ig.get_status() if ig else "DISCONNECTED"
        ig_detail = ig.get_status_detail() if ig else ""
        ig_sent = ig.get_sent_today() if ig else 0

        section_label("📸 محرك Instagram DM (Auto-Pilot)")
        st.markdown(
            "<p style='font-size:13px;color:#888;margin-bottom:8px'>"
            "إرسال رسائل Direct Message آلية على Instagram بتقنية Playwright Stealth + Bézier Mouse + Human Typing. "
            "تُخزَّن الجلسة بصورة دائمة لتفادي تسجيل الدخول في كل مرة."
            "</p>",
            unsafe_allow_html=True
        )

        # ── Status Bar ──────────────────────────────────────────────────────
        status_color = {"CONNECTED": "#30d158", "LAUNCHED": "#ff9f0a", "NEED_LOGIN": "#ff9f0a",
                        "DISCONNECTED": "#636366", "ERROR": "#ff453a"}.get(ig_status, "#636366")
        status_icon  = {"CONNECTED": "🟢", "LAUNCHED": "🟡", "NEED_LOGIN": "🟠",
                        "DISCONNECTED": "⚫", "ERROR": "🔴"}.get(ig_status, "⚫")
        st.markdown(
            f"<div style='background:#1a1a1a;border:1px solid {status_color}33;"
            f"border-radius:10px;padding:10px 14px;margin-bottom:12px;display:flex;"
            f"align-items:center;gap:10px'>"
            f"<span style='font-size:16px'>{status_icon}</span>"
            f"<span style='color:{status_color};font-weight:700;font-size:14px'>{ig_status}</span>"
            f"<span style='color:#666;font-size:12px;margin-left:8px'>{ig_detail}</span>"
            f"<span style='margin-left:auto;color:#888;font-size:12px'>رسائل اليوم: "
            f"<strong style='color:#f0f0f0'>{ig_sent}</strong>/15</span>"
            f"</div>",
            unsafe_allow_html=True
        )

        # ── Session Controls ─────────────────────────────────────────────────
        with st.container(border=True):
            section_label("🔑 إدارة جلسة Instagram")
            ic1, ic2, ic3 = st.columns(3)
            with ic1:
                if st.button("🚀 تشغيل المتصفح (يدوي - للتسجيل)", use_container_width=True, key="ig_launch_headful"):
                    if ig:
                        ok = ig.launch(headless=False)
                        if ok:
                            state = ig.check_login()
                            st.rerun()
                    else:
                        st.error("Instagram engine غير موجود. أعد تشغيل التطبيق.")
            with ic2:
                if st.button("🔍 فحص حالة الجلسة", use_container_width=True, key="ig_check_login"):
                    if ig and ig_status in ("LAUNCHED", "CONNECTED", "NEED_LOGIN"):
                        state = ig.check_login()
                        st.rerun()
                    elif ig and ig_status == "DISCONNECTED":
                        ok = ig.launch(headless=True)
                        if ok:
                            ig.check_login()
                        st.rerun()
            with ic3:
                if st.button("⏹️ إغلاق المتصفح", use_container_width=True, key="ig_close"):
                    if ig:
                        ig.close()
                        st.rerun()

            if ig_status == "NEED_LOGIN":
                st.info("📌 المتصفح مفتوح — قم بتسجيل الدخول على Instagram يدوياً، ثم اضغط **'فحص حالة الجلسة'** للتأكيد.")

        # ── Instagram DM Template ────────────────────────────────────────────
        ig_leads_with_handle = [l for l in ready_leads if len(l) > 17 and l[17]]
        ig_leads_no_handle   = [l for l in ready_leads if not (len(l) > 17 and l[17])]

        with st.container(border=True):
            section_label("✍️ قالب رسالة Instagram DM")
            ig_template = st.text_area(
                "نص الرسالة (يدعم Spintax {خيار1|خيار2} ومتغيرات {business} {industry} {city}):",
                value=(
                    "مرحباً 👋 شفنا حسابكم {business} في مجال {industry} بـ{city} 🌟\n"
                    "لدينا {حلول تسويقية|أفكار إبداعية|استراتيجيات} بالذكاء الاصطناعي "
                    "{ستضاعف مبيعاتكم|ستعزز حضوركم الرقمي|ستجذب عملاء جدد} 🚀\n"
                    "هل تودّ التفاصيل؟ 😊"
                ),
                height=120,
                key="ig_dm_template",
            )
            st.caption(
                f"عملاء لديهم حساب Instagram جاهزون: **{len(ig_leads_with_handle)}** | "
                f"بدون حساب: **{len(ig_leads_no_handle)}**"
            )

        # ── Auto-Pilot Batch Sender ──────────────────────────────────────────
        if ig_status == "CONNECTED":
            with st.container(border=True):
                section_label("🤖 الإرسال الآلي التلقائي (Instagram Auto-Pilot)")
                ap_c1, ap_c2 = st.columns([3, 2])
                with ap_c1:
                    ig_delay_range = st.slider(
                        "الفاصل الزمني بين كل رسالة (ثوانٍ):",
                        min_value=120, max_value=600, value=(180, 360),
                        key="ig_delay_slider",
                        help="الحد الأدنى الآمن 3 دقائق — Instagram أكثر صرامة من واتساب."
                    )
                    ig_cooldown = st.checkbox(
                        "🛑 تفعيل استراحة إلزامية (20 دقيقة بعد كل 5 رسائل)",
                        value=True, key="ig_cooldown_chk"
                    )
                with ap_c2:
                    st.markdown(
                        f"<div style='background:#1a1a1a;border:1px solid rgba(255,255,255,0.08);"
                        f"border-radius:10px;padding:10px 14px;margin-top:8px'>"
                        f"<div style='font-size:12px;color:#666;margin-bottom:6px'>📊 إحصائيات الجلسة</div>"
                        f"<div style='font-size:13px;color:#f0f0f0'>رسائل اليوم: <strong style='color:#30d158'>{ig_sent}</strong>/15</div>"
                        f"<div style='font-size:13px;color:#f0f0f0'>جاهزون بـ IG: <strong style='color:#0a84ff'>{len(ig_leads_with_handle)}</strong></div>"
                        f"<div style='font-size:11px;color:#666;margin-top:6px'>الحد اليومي الآمن: 15 DM</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                if not ig_leads_with_handle:
                    st.warning("⚠️ لا يوجد عملاء لديهم حساب Instagram. أضف الحسابات في الجدول أدناه أولاً.")
                elif ig_sent >= 15:
                    st.error("🛑 تم الوصول للحد اليومي الآمن (15 رسالة). استمر غداً.")
                else:
                    remaining = 15 - ig_sent
                    sendable = [
                        {"id": l[0], "business_name": l[1], "instagram_handle": l[17],
                         "industry": l[5] or "", "city": l[6] or ""}
                        for l in ig_leads_with_handle[:remaining]
                    ]
                    if st.button(
                        f"🚀 بدء الإرسال الآلي ({len(sendable)} رسالة IG)",
                        type="primary", use_container_width=True, key="ig_autopilot_btn"
                    ):
                        progress_bar = st.progress(0, text="جاري التهيئة…")
                        result_placeholder = st.empty()
                        stop_ev = __import__("threading").Event()
                        results_store = []

                        def _ig_progress(idx, total, handle, detail):
                            pct = int((idx + 1) / total * 100)
                            progress_bar.progress(pct, text=f"@{handle} — {detail}")

                        results_store = ig.send_batch_dms(
                            leads=sendable,
                            message_template=ig_template,
                            delay_min=ig_delay_range[0],
                            delay_max=ig_delay_range[1],
                            batch_size=5,
                            enable_cooldown=ig_cooldown,
                            progress_callback=_ig_progress,
                        )

                        ok_count  = sum(1 for r in results_store if r["success"])
                        err_count = len(results_store) - ok_count
                        progress_bar.progress(100, text="✅ اكتمل الإرسال")
                        result_placeholder.success(
                            f"✅ تم إرسال **{ok_count}** رسالة بنجاح | ❌ فشل: **{err_count}**"
                        )
                        for r in results_store:
                            if r["success"]:
                                db.update_lead_status(r["lead_id"], STATUS_CONTACTED)
                        st.rerun()
        else:
            st.info("💡 شغّل المتصفح وسجّل الدخول أولاً لتفعيل الإرسال الآلي.")

        # ── Per-Lead Manual DM Table ─────────────────────────────────────────
        st.divider()
        section_label("📋 العملاء — إدارة حسابات Instagram وإرسال فردي")

        for idx, lead in enumerate(ready_leads):
            lid, b_name, phone, address, website, industry, city = lead[:7]
            ig_h = lead[17] if len(lead) > 17 else ""
            fb_u = lead[18] if len(lead) > 18 else ""

            with st.container(border=True):
                sc1, sc2, sc3, sc4 = st.columns([0.5, 2.5, 3, 5])
                with sc1:
                    st.markdown(f"**#{idx+1}**")
                with sc2:
                    st.markdown(f"**{escape(b_name)}**")
                    st.caption(f"{escape(industry)} | {escape(city)}")
                with sc3:
                    new_ig = st.text_input(
                        "حساب Instagram:", value=ig_h,
                        key=f"ig_inp_{lid}", placeholder="@business_handle"
                    )
                    if new_ig != ig_h:
                        db.update_lead_social(lid, instagram_handle=new_ig)
                with sc4:
                    btn_cols = st.columns(3)
                    with btn_cols[0]:
                        if ig_status == "CONNECTED" and new_ig:
                            if st.button("📩 إرسال DM", key=f"ig_send_{lid}",
                                         type="primary", use_container_width=True):
                                try:
                                    msg = OutreachService.build_personalized_message(
                                        ig_template,
                                        business=b_name, industry=industry or "", city=city or ""
                                    )
                                except Exception:
                                    msg = ig_template
                                with st.spinner(f"جاري إرسال DM لـ @{new_ig.lstrip('@')}…"):
                                    ok, detail = ig.send_dm(new_ig, msg)
                                if ok:
                                    db.update_lead_status(lid, STATUS_CONTACTED)
                                    st.success(detail)
                                else:
                                    st.error(detail)
                        else:
                            st.button("📩 DM", key=f"ig_send_{lid}",
                                      disabled=True, use_container_width=True,
                                      help="يتطلب اتصال Instagram وحساب IG للعميل")
                    with btn_cols[1]:
                        if new_ig:
                            clean_h = new_ig.lstrip("@").strip()
                            st.link_button("📸 Instagram", f"https://instagram.com/{clean_h}",
                                           use_container_width=True)
                        else:
                            search_url = f"https://www.google.com/search?q=site:instagram.com+{b_name}+{city}"
                            st.link_button("🔍 بحث", search_url, use_container_width=True)
                    with btn_cols[2]:
                        if website and str(website).startswith("http"):
                            st.link_button("🌐 الموقع", website, use_container_width=True)
                        else:
                            st.caption("لا يوجد موقع")


