"""AutoLeadGen v2 - UI Views: Settings, Connections, Backups, and Logs."""
import os
import time
import streamlit as st
from services.export_service import ExportService
from database.backup_service import BackupService
from database.migrations import run_migrations
from utils.logger import read_recent_logs
from ui.components import page_header, section_label
from config.settings import DATA_DIR


def render_settings():
    page_header("الإعدادات والاتصالات والنسخ الاحتياطي", "Settings & Connections", "⚙️")

    db = st.session_state.db
    backup_svc = BackupService()
    messenger = st.session_state.messenger

    # ══════════════════════════════════════════════════════════════════════════
    # 1. WHATSAPP CONNECTION
    # ══════════════════════════════════════════════════════════════════════════
    with st.container(border=True):
        section_label("📱 ربط حساب WhatsApp Web")

        wa_details = messenger.get_status_details()
        wa_status = wa_details.get("status", "DISCONNECTED")
        wa_msg = wa_details.get("message", "")
        qr_available = wa_details.get("qr_available", False)
        worker_running = wa_details.get("worker_running", False)

        # Status bar
        status_color = {
            "CONNECTED": "#30d158", "SCANNING": "#ff9f0a",
            "STARTING": "#ff9f0a", "DISCONNECTED": "#636366", "ERROR": "#ff453a"
        }.get(wa_status, "#636366")
        status_icon = {
            "CONNECTED": "🟢", "SCANNING": "🟡", "STARTING": "🟡",
            "DISCONNECTED": "⚫", "ERROR": "🔴"
        }.get(wa_status, "⚫")

        st.markdown(
            f"<div style=\'background:#1a1a1a;border:1px solid {status_color}33;"
            f"border-radius:10px;padding:10px 14px;margin-bottom:14px;"
            f"display:flex;align-items:center;gap:10px\'>"
            f"<span style=\'font-size:18px\'>{status_icon}</span>"
            f"<span style=\'color:{status_color};font-weight:700;font-size:15px\'>"
            f"{'متصل ✅' if wa_status == 'CONNECTED' else wa_status}</span>"
            f"<span style=\'color:#666;font-size:12px;margin-right:8px\'>{wa_msg}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

        if wa_status == "CONNECTED":
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔍 فحص صلاحية الجلسة", use_container_width=True, key="wa_verify"):
                    with st.spinner("جاري التحقق من الجلسة..."):
                        messenger.verify_saved_session(timeout_sec=20)
                    st.rerun()
            with c2:
                if st.button("🛑 قطع الاتصال وحذف الجلسة", use_container_width=True,
                             key="wa_disconnect", type="secondary"):
                    messenger.disconnect()
                    st.success("تم قطع الاتصال وحذف الجلسة.")
                    st.rerun()
        else:
            # QR Display area
            qr_placeholder = st.empty()
            info_placeholder = st.empty()

            # Show QR if available
            qr_path = os.path.join(DATA_DIR, "whatsapp_qr.png")
            if qr_available and os.path.exists(qr_path) and os.path.getsize(qr_path) > 0:
                with qr_placeholder.container():
                    st.markdown(
                        "<p style=\'text-align:center;color:#30d158;font-weight:700;"
                        "margin-bottom:8px\'>📱 امسح الـ QR Code بكاميرا هاتفك عبر واتساب</p>",
                        unsafe_allow_html=True
                    )
                    col_l, col_c, col_r = st.columns([1, 2, 1])
                    with col_c:
                        try:
                            st.image(qr_path, width=260, caption="WhatsApp Web QR Code")
                        except Exception:
                            st.warning("تعذر عرض صورة QR. جرب زر التحديث.")

                info_placeholder.info(
                    "⏳ QR Code نشط — افتح واتساب على هاتفك ← الثلاث نقاط ← الأجهزة المرتبطة ← ربط جهاز ← امسح الكود"
                )

                # Auto-refresh while scanning
                if worker_running:
                    time.sleep(2)
                    st.rerun()

            elif wa_status in ("SCANNING", "STARTING") and worker_running:
                with qr_placeholder.container():
                    st.markdown(
                        "<div style=\'text-align:center;padding:40px;color:#ff9f0a\'>"
                        "<p style=\'font-size:32px\'>⏳</p>"
                        "<p>جاري تحميل QR Code... انتظر لحظة</p>"
                        "</div>",
                        unsafe_allow_html=True
                    )
                time.sleep(2)
                st.rerun()
            else:
                with qr_placeholder.container():
                    st.markdown(
                        "<div style=\'text-align:center;padding:30px;background:#1a1a1a;"
                        "border-radius:12px;border:1px dashed #333\'>"
                        "<p style=\'font-size:40px;margin:0\'>📲</p>"
                        "<p style=\'color:#666;margin:8px 0\'>اضغط على أحد الأزرار أدناه لبدء الربط</p>"
                        "</div>",
                        unsafe_allow_html=True
                    )

            st.markdown("---")
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("📲 ربط عبر QR Code (مخفي)", type="primary",
                             use_container_width=True, key="wa_qr_headless"):
                    messenger.cancel_worker()
                    time.sleep(0.5)
                    messenger.start_qr_linking_worker(headless=True, timeout_sec=120)
                    time.sleep(2)
                    st.rerun()
            with b2:
                if st.button("🖥️ ربط عبر متصفح مرئي", use_container_width=True, key="wa_qr_headed"):
                    messenger.cancel_worker()
                    time.sleep(0.5)
                    messenger.start_qr_linking_worker(headless=False, timeout_sec=180)
                    time.sleep(1)
                    st.rerun()
            with b3:
                if st.button("🔄 تحديث الحالة", use_container_width=True, key="wa_refresh"):
                    st.rerun()

            if worker_running:
                remaining = wa_details.get("remaining_sec", "?")
                st.caption(f"⏱️ العملية نشطة — المهلة المتبقية: {remaining} ثانية")

    # ══════════════════════════════════════════════════════════════════════════
    # 2. EMAIL SMTP SETTINGS
    # ══════════════════════════════════════════════════════════════════════════
    from integrations.email_engine import EmailEngine, SMTP_PRESETS
    email_engine = EmailEngine()
    current_cfg = email_engine.load_config()

    with st.container(border=True):
        section_label("✉️ إعدادات البريد الإلكتروني (Cold Email SMTP)")
        st.markdown(
            "<p style=\'font-size:13px;color:#888;margin-bottom:12px\'>"
            "إرسال إيميلات تسويقية مجاناً 100% عبر SMTP المباشر (Gmail App Password، Outlook، بريد شركتك). "
            "البيانات محفوظة محلياً على جهازك فقط — لا يتم إرسالها لأي خادم."
            "</p>",
            unsafe_allow_html=True
        )

        # Status pill
        is_email_configured = current_cfg.get("is_configured", False)
        email_status_color = "#30d158" if is_email_configured else "#636366"
        email_status_txt = f"✅ مُفعَّل ({current_cfg.get('sender_email','')})" if is_email_configured else "⚫ غير مُفعَّل"
        st.markdown(
            f"<div style=\'display:inline-block;background:{email_status_color}22;"
            f"border:1px solid {email_status_color}55;border-radius:99px;"
            f"padding:4px 14px;font-size:13px;font-weight:600;color:{email_status_color};"
            f"margin-bottom:12px\'>{email_status_txt}</div>",
            unsafe_allow_html=True
        )

        provider_names = list(SMTP_PRESETS.keys())
        curr_provider = current_cfg.get("provider", provider_names[0])
        default_idx = provider_names.index(curr_provider) if curr_provider in provider_names else 0

        p_col1, p_col2 = st.columns(2)
        with p_col1:
            selected_provider = st.selectbox("مزود الخدمة:", provider_names, index=default_idx, key="em_provider")
            preset = SMTP_PRESETS[selected_provider]
            st.caption(f"💡 {preset['note']}")
        with p_col2:
            sender_name = st.text_input("اسم المرسل الظاهر للعميل:",
                                        value=current_cfg.get("sender_name", "فريق العمل"))

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            sender_email = st.text_input("بريدك الإلكتروني:",
                                         value=current_cfg.get("sender_email", ""),
                                         placeholder="example@gmail.com")
        with f_col2:
            password = st.text_input(
                "كلمة مرور التطبيقات (App Password):",
                value=current_cfg.get("password", ""),
                type="password",
                help="Gmail: Google Account → Security → 2-Step Verification → App Passwords → نشئ كلمة مرور جديدة (16 حرف)"
            )

        show_advanced = (selected_provider == "Custom SMTP / Webmail")
        with st.expander("⚙️ إعدادات الخادم المتقدمة", expanded=show_advanced):
            h_col1, h_col2, h_col3 = st.columns([2, 1, 1])
            with h_col1:
                host_val = st.text_input("خادم SMTP:", value=current_cfg.get("host", preset["host"]))
            with h_col2:
                port_val = st.number_input("المنفذ:", min_value=1, max_value=65535,
                                           value=int(current_cfg.get("port", preset["port"])))
            with h_col3:
                ssl_option = st.selectbox("التشفير:",
                                          ["SSL (Port 465)", "STARTTLS (Port 587)", "None"],
                                          index=0 if preset["use_ssl"] else 1)

        cfg_to_save = {
            "provider": selected_provider,
            "host": host_val if selected_provider == "Custom SMTP / Webmail" else preset["host"],
            "port": port_val if selected_provider == "Custom SMTP / Webmail" else preset["port"],
            "use_ssl": (ssl_option == "SSL (Port 465)") if selected_provider == "Custom SMTP / Webmail" else preset["use_ssl"],
            "use_tls": (ssl_option == "STARTTLS (Port 587)") if selected_provider == "Custom SMTP / Webmail" else preset["use_tls"],
            "sender_name": sender_name.strip(),
            "sender_email": sender_email.strip(),
            "password": password.strip(),
        }

        em_b1, em_b2 = st.columns(2)
        with em_b1:
            if st.button("💾 حفظ إعدادات البريد", type="primary", use_container_width=True, key="em_save"):
                if not sender_email.strip() or "@" not in sender_email:
                    st.error("يرجى إدخال بريد إلكتروني صحيح.")
                elif not password.strip():
                    st.error("يرجى إدخال App Password.")
                elif email_engine.save_config(cfg_to_save):
                    st.success("✅ تم حفظ إعدادات البريد بنجاح!")
                    time.sleep(0.4)
                    st.rerun()
                else:
                    st.error("❌ تعذر الحفظ.")
        with em_b2:
            if st.button("⚡ اختبار الاتصال الآن", use_container_width=True, key="em_test"):
                if not sender_email.strip() or not password.strip():
                    st.error("أدخل البريد وكلمة المرور أولاً.")
                else:
                    with st.spinner("جاري الاتصال بخادم البريد..."):
                        test_ok, test_msg = email_engine.test_connection(cfg_to_save)
                    if test_ok:
                        st.success(test_msg)
                    else:
                        st.error(test_msg)

        with st.expander("📖 كيفية إنشاء App Password لـ Gmail"):
            st.markdown("""
1. افتح [myaccount.google.com](https://myaccount.google.com)
2. اختر **الأمان (Security)**
3. فعّل **التحقق بخطوتين (2-Step Verification)**
4. اختر **كلمات مرور التطبيقات (App Passwords)**
5. اختر تطبيق: **Mail** وجهاز: **Windows Computer**
6. انسخ الـ 16 حرف المولّدة واستخدمها بدلاً من كلمة مرورك العادية
""")

    # ══════════════════════════════════════════════════════════════════════════
    # 3. INSTAGRAM CONNECTION
    # ══════════════════════════════════════════════════════════════════════════
    ig = st.session_state.get("ig_engine")
    ig_status = ig.get_status() if ig else "DISCONNECTED"
    ig_sent = ig.get_sent_today() if ig else 0

    with st.container(border=True):
        section_label("📸 ربط حساب Instagram (DM Automation)")
        st.markdown(
            "<p style=\'font-size:13px;color:#888;margin-bottom:10px\'>"
            "يتم حفظ جلسة Instagram تلقائياً في <code>data/instagram_profile/</code> — "
            "لن تحتاج لتسجيل الدخول مرة أخرى بعد أول مرة."
            "</p>",
            unsafe_allow_html=True
        )

        ig_color = {"CONNECTED": "#30d158", "NEED_LOGIN": "#ff9f0a",
                    "LAUNCHED": "#ff9f0a", "DISCONNECTED": "#636366", "ERROR": "#ff453a"}.get(ig_status, "#636366")
        ig_icon = {"CONNECTED": "🟢", "NEED_LOGIN": "🟠", "LAUNCHED": "🟡",
                   "DISCONNECTED": "⚫", "ERROR": "🔴"}.get(ig_status, "⚫")

        ig_m1, ig_m2, ig_m3 = st.columns(3)
        with ig_m1:
            st.metric("الحالة", f"{ig_icon} {ig_status}")
        with ig_m2:
            st.metric("DMs اليوم", f"{ig_sent} / 15")
        with ig_m3:
            profile_path = os.path.join(DATA_DIR, "instagram_profile")
            profile_exists = os.path.exists(profile_path) and len(os.listdir(profile_path)) > 0
            st.metric("جلسة محفوظة", "✅ موجودة" if profile_exists else "❌ لا توجد")

        ig_s1, ig_s2, ig_s3 = st.columns(3)
        with ig_s1:
            if st.button("🖥️ تسجيل دخول (متصفح مرئي)", use_container_width=True, key="cfg_ig_launch"):
                if ig:
                    with st.spinner("جاري تشغيل المتصفح..."):
                        ok = ig.launch(headless=False)
                        if ok:
                            ig.check_login()
                    st.rerun()
                else:
                    st.error("Instagram engine غير جاهز — أعد تشغيل التطبيق.")
        with ig_s2:
            if st.button("🔍 فحص الجلسة المحفوظة", use_container_width=True, key="cfg_ig_check"):
                if ig:
                    with st.spinner("جاري التحقق..."):
                        if ig_status == "DISCONNECTED":
                            ig.launch(headless=True)
                        ig.check_login()
                    st.rerun()
        with ig_s3:
            if st.button("⏹️ إغلاق المتصفح", use_container_width=True, key="cfg_ig_close"):
                if ig:
                    ig.close()
                    st.rerun()

        if ig_status == "NEED_LOGIN":
            st.info("📌 المتصفح مفتوح — سجّل الدخول يدوياً على instagram.com، ثم اضغط **'فحص الجلسة المحفوظة'**.")
        elif ig_status == "CONNECTED":
            st.success("🟢 Instagram متصل وجاهز للإرسال الآلي من صفحة 'طابور التواصل'.")
        else:
            st.caption("💡 اضغط 'تسجيل دخول (متصفح مرئي)' لفتح المتصفح وتسجيل الدخول لأول مرة.")

    # ══════════════════════════════════════════════════════════════════════════
    # 4. EXPORT
    # ══════════════════════════════════════════════════════════════════════════
    with st.container(border=True):
        section_label("📊 تصدير البيانات (Export)")
        leads = db.get_all_leads()
        if leads:
            st.caption(f"إجمالي العملاء المتاحين للتصدير: **{len(leads)}** عميل")
            exp_c1, exp_c2 = st.columns(2)
            with exp_c1:
                if st.button("📊 تصدير إلى Excel (.xlsx)", use_container_width=True, key="exp_xl"):
                    path = ExportService.to_excel(leads)
                    if path:
                        st.success(f"تم التصدير: `{path}`")
            with exp_c2:
                if st.button("📄 تصدير إلى CSV", use_container_width=True, key="exp_csv"):
                    path = ExportService.to_csv(leads)
                    if path:
                        st.success(f"تم التصدير: `{path}`")
        else:
            st.info("لا توجد بيانات متاحة للتصدير.")

    # ══════════════════════════════════════════════════════════════════════════
    # 5. BACKUPS
    # ══════════════════════════════════════════════════════════════════════════
    with st.container(border=True):
        section_label("💾 النسخ الاحتياطي (Backups)")
        b_c1, b_c2 = st.columns(2)
        with b_c1:
            if st.button("💾 إنشاء نسخة احتياطية الآن", type="primary",
                         use_container_width=True, key="backup_now"):
                path = backup_svc.create_backup()
                st.success(f"تم إنشاء النسخة الاحتياطية: `{path}`")
                st.rerun()
        with b_c2:
            backups = backup_svc.list_backups()
            if backups:
                b_names = [b["name"] for b in backups]
                selected_b = st.selectbox("اختر النسخة للاسترجاع:", b_names, key="backup_sel")
                if st.button("⚠️ استرجاع النسخة المحددة", type="secondary",
                             use_container_width=True, key="backup_restore"):
                    backup_svc.restore_backup(selected_b)
                    st.success(f"تم استرجاع '{selected_b}' بنجاح!")
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # 6. MIGRATIONS & RESET
    # ══════════════════════════════════════════════════════════════════════════
    with st.container(border=True):
        section_label("🔄 ترحيل قاعدة البيانات")
        if st.button("🚀 تشغيل Migration الآن", type="primary",
                     use_container_width=True, key="run_migration"):
            res = run_migrations()
            if res.get("status") == "success":
                st.success("تمت ترقية قاعدة البيانات بنجاح!")
            else:
                st.error(f"فشلت: {res.get('error')}")
            st.rerun()

    with st.container(border=True):
        section_label("🗑️ إعادة ضبط الداشبورد")
        all_leads_count = len(db.get_all_leads())
        st.warning(f"⚠️ يوجد حالياً **{all_leads_count}** عميل مسجل.")
        auto_backup = st.checkbox("💾 نسخة احتياطية تلقائية قبل المسح (موصى به)", value=True, key="reset_backup")
        confirm_wipe = st.checkbox("🔴 أؤكد رغبتي في مسح كافة البيانات نهائياً", value=False, key="reset_confirm")
        if st.button("🗑️ مسح كل البيانات الآن", type="primary",
                     use_container_width=True, disabled=not confirm_wipe, key="reset_btn"):
            if auto_backup:
                backup_svc.create_backup()
            deleted_count = db.clear_all_leads(reset_searches=True)
            for key in ["last_search_results", "last_search_industry", "last_search_city",
                        "last_search_city_name", "last_search_country_info"]:
                st.session_state.pop(key, None)
            st.success(f"🎉 تم مسح {deleted_count} عميل وإعادة ضبط الداشبورد!")
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # 7. LOGS
    # ══════════════════════════════════════════════════════════════════════════
    with st.container(border=True):
        section_label("📜 سجلات التشغيل (Logs)")
        log_content = read_recent_logs(max_bytes=25000)
        st.text_area("أحدث السجلات:", value=log_content, height=200, disabled=True)
