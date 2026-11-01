"""AutoLeadGen v2 — Clean UI Components."""
import html
import streamlit as st


def escape(text: str) -> str:
    return html.escape(str(text or ""))


def page_header(title: str, subtitle: str = "", icon: str = "", badge: str = "", *args, **kwargs):
    badge_html = f' &nbsp;·&nbsp; <span style="background:rgba(10,132,255,0.15);color:#0a84ff;font-size:11px;font-weight:700;padding:2px 8px;border-radius:6px">{escape(badge)}</span>' if badge else ""
    st.markdown(f"""
    <div style="padding:8px 0 20px">
        <div style="font-size:11px;font-weight:700;color:#888;text-transform:uppercase;
                    letter-spacing:1px;margin-bottom:6px">{escape(icon)} {escape(subtitle)}{badge_html}</div>
        <h1 style="font-size:26px;font-weight:700;color:#f0f0f0;margin:0;letter-spacing:-0.5px">
            {escape(title)}
        </h1>
    </div>
    """, unsafe_allow_html=True)


def section_label(text: str):
    st.markdown(f"""
    <p style="font-size:11px;font-weight:700;color:#888;text-transform:uppercase;
              letter-spacing:0.8px;margin:0 0 10px">{escape(text)}</p>
    """, unsafe_allow_html=True)


def wa_badge(status: str) -> str:
    if status == "VERIFIED":
        return '<span style="background:#30d158;color:#000;font-size:11px;font-weight:700;padding:2px 8px;border-radius:6px">✓ واتساب</span>'
    if status == "NOT_VERIFIED":
        return '<span style="background:#ff453a;color:#fff;font-size:11px;font-weight:600;padding:2px 8px;border-radius:6px">✗ لا يوجد</span>'
    return '<span style="background:#333;color:#888;font-size:11px;padding:2px 8px;border-radius:6px">غير معروف</span>'


def lead_card(name: str, phone: str, industry: str, city: str, wa_status: str, score: int = 0, wa_url: str = ""):
    badge = wa_badge(wa_status)
    score_bar = min(100, max(0, score))
    score_color = "#30d158" if score >= 70 else "#ff9f0a" if score >= 40 else "#888"
    wa_btn = f'<a href="{wa_url}" target="_blank" style="background:#25d366;color:#000;font-size:12px;font-weight:700;padding:8px 14px;border-radius:8px;text-decoration:none;white-space:nowrap;display:inline-flex;align-items:center;justify-content:center;min-height:36px">📲 واتساب</a>' if wa_url else ""

    st.markdown(f"""
    <div style="background:#222;border:1px solid rgba(255,255,255,0.08);border-radius:14px;
                padding:14px 16px;margin-bottom:8px;display:flex;flex-wrap:wrap;align-items:center;
                justify-content:space-between;gap:12px">
        <div style="flex:1;min-width:200px">
            <div style="font-size:14px;font-weight:600;color:#f0f0f0;margin-bottom:4px;
                        word-break:break-word">
                {escape(name)}
            </div>
            <div style="font-size:12px;color:#888;margin-bottom:6px;word-break:break-word">
                {escape(phone)} &nbsp;·&nbsp; {escape(industry)} &nbsp;·&nbsp; {escape(city)}
            </div>
            <div style="display:flex;align-items:center;gap:8px">
                {badge}
                <div style="flex:1;height:4px;background:#333;border-radius:99px;max-width:80px">
                    <div style="width:{score_bar}%;height:100%;background:{score_color};border-radius:99px"></div>
                </div>
                <span style="font-size:11px;color:{score_color};font-weight:600">{score}</span>
            </div>
        </div>
        <div style="width:auto">{wa_btn}</div>
    </div>
    """, unsafe_allow_html=True)


def stat_card(label: str, value, icon: str = "", color: str = "#0a84ff"):
    st.markdown(f"""
    <div style="background:#1a1a1a;border:1px solid rgba(255,255,255,0.07);border-radius:14px;
                padding:16px 18px;text-align:center">
        <div style="font-size:24px;margin-bottom:6px">{icon}</div>
        <div style="font-size:26px;font-weight:700;color:{color};font-family:'Plus Jakarta Sans',sans-serif;
                    letter-spacing:-1px">{value}</div>
        <div style="font-size:11px;font-weight:600;color:#666;text-transform:uppercase;
                    letter-spacing:0.5px;margin-top:4px">{escape(label)}</div>
    </div>
    """, unsafe_allow_html=True)


def empty_state(title: str, subtitle: str = "", icon: str = "🔍"):
    st.markdown(f"""
    <div style="text-align:center;padding:48px 24px;color:#555">
        <div style="font-size:48px;margin-bottom:12px">{icon}</div>
        <div style="font-size:16px;font-weight:600;color:#888;margin-bottom:6px">{escape(title)}</div>
        <div style="font-size:13px;color:#555">{escape(subtitle)}</div>
    </div>
    """, unsafe_allow_html=True)


def nav_logo():
    st.markdown("""
    <div style="padding:20px 16px 12px;border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:8px">
        <div style="font-size:18px;font-weight:700;color:#f0f0f0;letter-spacing:-0.3px">
            AutoLeadGen
        </div>
        <div style="font-size:11px;color:#555;margin-top:2px">استخراج عملاء WhatsApp العالمي</div>
    </div>
    """, unsafe_allow_html=True)


# Backward compatibility aliases
render_status_badge = wa_badge
render_lead_summary_card = lead_card
render_ios_header = page_header
