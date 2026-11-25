"""AutoLeadGen V3 — Secure Streamlit Login & First-Run Admin Setup View."""
import streamlit as st
from core.user_manager import UserManager


def render_login_v3():
    st.markdown("""
    <style>
        .v3-login-card {
            max-width: 440px;
            margin: 48px auto;
            padding: 36px 32px;
            background: linear-gradient(145deg, #0b1120 0%, #111936 100%);
            border: 1px solid rgba(99, 102, 241, 0.35);
            border-radius: 18px;
            box-shadow: 0 18px 48px rgba(0, 0, 0, 0.55), 0 0 28px rgba(99, 102, 241, 0.14);
        }
        .v3-login-title {
            font-size: 26px;
            font-weight: 800;
            text-align: center;
            background: linear-gradient(90deg, #e0e7ff, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 6px;
        }
        .v3-login-sub {
            text-align: center;
            color: #94a3b8;
            font-size: 13px;
            margin-bottom: 24px;
        }
    </style>
    <div class="v3-login-card">
        <div class="v3-login-title">AutoLeadGen V3</div>
        <div class="v3-login-sub">Global AI Business Discovery &amp; Email Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    mgr = UserManager(repo=st.session_state.get("db"))
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        if not mgr.has_any_users():
            st.info("مرحباً بك في AutoLeadGen V3! أنشئ حساب المدير الأول للبدء:")
            with st.form("v3_setup_admin_form"):
                new_user = st.text_input("اسم المستخدم (Admin)", value="admin")
                new_email = st.text_input("البريد الإلكتروني", value="")
                new_pw = st.text_input("كلمة المرور", type="password")
                confirm_pw = st.text_input("تأكيد كلمة المرور", type="password")
                submitted = st.form_submit_button("إنشاء حساب المدير والدخول", use_container_width=True)
                if submitted:
                    if not new_pw or len(new_pw) < 4:
                        st.error("كلمة المرور يجب أن تكون 4 أحرف على الأقل.")
                    elif new_pw != confirm_pw:
                        st.error("كلمتا المرور غير متطابقتين.")
                    else:
                        try:
                            mgr.create_user(new_user, new_pw, role="admin", email=new_email)
                            auth = mgr.authenticate_user(new_user, new_pw)
                            st.session_state["v3_user"] = auth
                            st.session_state["v3_role"] = auth["role"]
                            st.success("تم إنشاء الحساب وتسجيل الدخول بنجاح!")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
        else:
            with st.form("v3_login_form"):
                username = st.text_input("اسم المستخدم", placeholder="admin")
                password = st.text_input("كلمة المرور", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("تسجيل الدخول", use_container_width=True)
                if submitted:
                    auth = mgr.authenticate_user(username, password)
                    if auth:
                        st.session_state["v3_user"] = auth
                        st.session_state["v3_role"] = auth["role"]
                        st.rerun()
                    else:
                        st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")
