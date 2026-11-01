"""AutoLeadGen v2 — Entry Point."""
import sys
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import streamlit as st
from config.settings import PAGE_TITLE, PAGE_ICON, PROJECT_NAME, VERSION
from database.repository import LeadRepository
from database.backup_service import BackupService
from integrations.whatsapp_playwright import WhatsAppMessenger
from integrations.instagram_playwright import InstagramEngine
from integrations.maps_scraper import LeadScraper
from ui.theme import apply_theme
from ui.components import nav_logo
from ui.views import (
    render_dashboard,
    render_search,
    render_crm,
    render_message_center,
    render_outreach_queue,
    render_settings,
)

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="auto",
)

# Apply theme
apply_theme()

# Mobile viewport meta & touch enhancements
st.markdown('''
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
@media (max-width: 768px) {
    [data-testid="collapsedControl"] {
        display: flex !important;
        background: #1a1a1a !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 10px !important;
        top: 10px !important;
        right: 10px !important;
        left: auto !important;
        z-index: 99999 !important;
    }
}
</style>
''', unsafe_allow_html=True)

# Singletons
if "db"          not in st.session_state: st.session_state.db          = LeadRepository()
if "messenger"   not in st.session_state: st.session_state.messenger   = WhatsAppMessenger(db=st.session_state.db)
if "ig_engine"   not in st.session_state: st.session_state.ig_engine   = InstagramEngine()
if "scraper"     not in st.session_state: st.session_state.scraper     = LeadScraper()
if "backup_svc"  not in st.session_state: st.session_state.backup_svc  = BackupService()
if "current_page" not in st.session_state: st.session_state.current_page = "Dashboard"


def main():
    wa_status    = st.session_state.messenger.get_connection_status()
    is_connected = (wa_status == "CONNECTED")

    # ── Sidebar ────────────────────────────────────────────────────────────
    with st.sidebar:
        nav_logo()

        # WhatsApp status pill
        if is_connected:
            st.markdown("""
            <div style="margin:0 12px 12px;background:rgba(48,209,88,0.1);border:1px solid rgba(48,209,88,0.2);
                        border-radius:10px;padding:8px 12px;font-size:13px;font-weight:600;color:#30d158;
                        display:flex;align-items:center;gap:8px">
                <span style="width:7px;height:7px;border-radius:50%;background:#30d158;
                             box-shadow:0 0 6px #30d158;display:inline-block"></span>
                WhatsApp متصل
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="margin:0 12px 12px;background:rgba(255,159,10,0.1);border:1px solid rgba(255,159,10,0.2);
                        border-radius:10px;padding:8px 12px;font-size:13px;font-weight:600;color:#ff9f0a;
                        display:flex;align-items:center;gap:8px">
                <span style="width:7px;height:7px;border-radius:50%;background:#ff9f0a;display:inline-block"></span>
                WhatsApp غير متصل
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='padding:0 4px'>", unsafe_allow_html=True)

        # Nav items
        nav_items = [
            ("📊", "لوحة التحكم",   "Dashboard"),
            ("🔍", "استكشاف العملاء", "Search Leads"),
            ("👥", "إدارة العملاء",   "Leads CRM"),
            ("💬", "مركز الرسائل",    "Message Center"),
            ("📤", "طابور التواصل",   "Outreach Queue"),
            ("⚙️", "الإعدادات",       "Settings"),
        ]

        for icon, label, key in nav_items:
            active = st.session_state.current_page == key
            bg     = "#0a84ff" if active else "transparent"
            color  = "#fff"    if active else "#888"
            weight = "700"     if active else "500"
            st.markdown(f"""
            <div style="background:{bg};border-radius:10px;padding:10px 12px;margin-bottom:3px;
                        cursor:pointer;font-size:14px;font-weight:{weight};color:{color};
                        display:flex;align-items:center;gap:10px">
                <span>{icon}</span><span>{label}</span>
            </div>""", unsafe_allow_html=True)
            if st.button(label, key=f"nav_{key}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.current_page = key
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        st.divider()

        # Quick stats
        try:
            m = st.session_state.db.get_dashboard_metrics()
            st.markdown(f"""
            <div style="padding:0 8px;font-size:13px;color:#666">
                <div style="display:flex;justify-content:space-between;padding:5px 0;
                            border-bottom:1px solid rgba(255,255,255,0.06)">
                    <span>إجمالي العملاء</span>
                    <strong style="color:#f0f0f0">{m['total']}</strong>
                </div>
                <div style="display:flex;justify-content:space-between;padding:5px 0;
                            border-bottom:1px solid rgba(255,255,255,0.06)">
                    <span>✓ واتساب مؤكد</span>
                    <strong style="color:#30d158">{m['wa_verified']}</strong>
                </div>
                <div style="display:flex;justify-content:space-between;padding:5px 0;
                            border-bottom:1px solid rgba(255,255,255,0.06)">
                    <span>في الطابور</span>
                    <strong style="color:#0a84ff">{m['ready']}</strong>
                </div>
                <div style="display:flex;justify-content:space-between;padding:5px 0">
                    <span>تم التواصل</span>
                    <strong style="color:#ff9f0a">{m['contacted']}</strong>
                </div>
            </div>""", unsafe_allow_html=True)
        except Exception:
            pass

        st.write("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄", use_container_width=True, help="تحديث"):
                st.rerun()
        with col2:
            if st.button("🚪", use_container_width=True, help="خروج"):
                st.session_state.messenger.disconnect()
                st.session_state.authenticated = False
                st.rerun()

    # ── Page Routing ────────────────────────────────────────────────────────
    page = st.session_state.current_page
    if   page == "Dashboard":     render_dashboard()
    elif page == "Search Leads":  render_search()
    elif page == "Leads CRM":     render_crm()
    elif page == "Message Center": render_message_center()
    elif page == "Outreach Queue": render_outreach_queue()
    elif page == "Settings":       render_settings()


if __name__ == "__main__":
    main()
