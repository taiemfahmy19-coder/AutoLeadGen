"""AutoLeadGen v2 - UI Views: Dedicated WhatsApp Login Screen."""
import os
import time
from datetime import datetime
import streamlit as st
from ui.components import page_header, empty_state

def render_login_screen():
    messenger = st.session_state.messenger
    wa_status = messenger.get_connection_status()
    qr_file = messenger.qr_path

    if wa_status == "CONNECTED":
        st.success("✅ تم تسجيل الدخول بنجاح! جاري الانتقال إلى لوحة التحكم...")
        time.sleep(1)
        st.session_state.authenticated = True
        st.rerun()

    _, col_main, _ = st.columns([1, 2.2, 1])

    with col_main:
        page_header("ربط حساب WhatsApp Web", "مرحباً بك في AutoLeadGen v2", "💬")

        with st.container(border=True):
            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                if wa_status in ["DISCONNECTED", "ERROR"]:
                    if st.button("🔗 توليد كود QR حي", type="primary", use_container_width=True):
                        messenger.start_qr_linking_worker(headless=True, timeout_sec=120)
                        st.info("جاري فتح WhatsApp Web واستخراج كود الـ QR الحقيقي...")
                        time.sleep(1)
                        st.rerun()
                else:
                    if st.button("🔄 فحص حالة المسح", type="primary", use_container_width=True):
                        st.rerun()

            with btn_c2:
                if wa_status in ["STARTING", "SCANNING"]:
                    if st.button("❌ إلغاء الربط", use_container_width=True):
                        messenger.cancel_worker()
                        st.rerun()
                else:
                    if st.button("🌐 فتح متصفح خارجي", use_container_width=True):
                        messenger.start_qr_linking_worker(headless=False, timeout_sec=120)
                        st.info("تم فتح متصفح للمسح المباشر...")
                        time.sleep(1)
                        st.rerun()

            if wa_status == "STARTING":
                st.write("")
                st.info("⏳ جاري الاتصال بسيرفرات WhatsApp Web وتوليد كود الـ QR الحي...")
                time.sleep(1.5)
                st.rerun()

            elif wa_status == "SCANNING":
                st.write("")
                st.success("🟢 الجلسة نشطة وكود الـ QR محدث مباشرة من سيرفرات واتساب!")
                if os.path.exists(qr_file) and os.path.getsize(qr_file) > 0:
                    try:
                        with open(qr_file, "rb") as f:
                            qr_bytes = f.read()
                        st.image(qr_bytes, width=310, caption=f"كود QR حي ({datetime.now().strftime('%H:%M:%S')})")
                    except Exception:
                        st.image(qr_file, width=310)
                else:
                    st.caption("جاري التقاط صورة كود الـ QR...")

                time.sleep(2.5)
                st.rerun()

            elif wa_status == "DISCONNECTED":
                st.write("")
                if st.button("🔍 التحقق من وجود جلسة سابقة محفوظة", use_container_width=True):
                    with st.spinner("جاري التحقق من ملفات الجلسة السابقة..."):
                        valid = messenger.verify_saved_session(timeout_sec=12)
                        if valid:
                            st.success("✅ الجلسة السابقة صالحة ومسجلة الدخول بنجاح! جاري الدخول...")
                            time.sleep(1)
                            st.session_state.authenticated = True
                            st.rerun()
                        else:
                            st.warning("⚠️ لا توجد جلسة سابقة صالحة. يرجى البدء بمسح كود جديد.")
