"""AutoLeadGen v2 — Clean iOS Design System with Full Mobile Responsiveness."""


def get_ios_theme_css() -> str:
    return """
<style>
/* ── Google Fonts ────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Alexandria:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

/* ── CSS Variables ───────────────────────────────────────────────── */
:root {
    --bg:       #0f0f0f;
    --surface:  #1a1a1a;
    --card:     #222222;
    --border:   rgba(255,255,255,0.08);
    --text:     #f0f0f0;
    --subtext:  #888888;
    --blue:     #0a84ff;
    --green:    #30d158;
    --orange:   #ff9f0a;
    --red:      #ff453a;
    --r:        14px;
    --font-ar:  'Alexandria', sans-serif;
    --font-en:  'Plus Jakarta Sans', sans-serif;
}

/* ── Base ────────────────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    font-family: var(--font-ar);
    color: var(--text);
    direction: rtl;
}
[data-testid="stApp"] { background: var(--bg) !important; }

/* ── Scrollbars ──────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 99px; }

/* ── Sidebar ─────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #111111 !important;
    border-right: 1px solid var(--border) !important;
    border-left: none !important;
    min-width: 220px !important;
}
[data-testid="stSidebar"] > div { padding: 0 !important; }

/* ── Main content ────────────────────────────────────────────────── */
.main .block-container {
    max-width: 1100px;
    padding: 24px 28px !important;
    margin: 0 auto;
}

/* ── Typography ──────────────────────────────────────────────────── */
h1, h2, h3, h4 {
    font-family: var(--font-ar);
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.3px;
    margin-bottom: 4px !important;
}
p, li, label, span {
    font-family: var(--font-ar);
    color: var(--text);
}

/* ── Cards ───────────────────────────────────────────────────────── */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    padding: 20px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
}

/* ── Primary Button ──────────────────────────────────────────────── */
[data-testid="stButton"] button[kind="primary"] {
    background: var(--blue) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: var(--font-ar) !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
    transition: opacity 0.15s;
    box-shadow: 0 4px 14px rgba(10,132,255,0.3);
    min-height: 44px !important;
}
[data-testid="stButton"] button[kind="primary"]:hover { opacity: 0.88; }

/* ── Secondary Button ────────────────────────────────────────────── */
[data-testid="stButton"] button[kind="secondary"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: var(--font-ar) !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    min-height: 44px !important;
}

/* ── Link Button ─────────────────────────────────────────────────── */
[data-testid="stLinkButton"] a {
    background: var(--green) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: var(--font-ar) !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    text-decoration: none !important;
    min-height: 44px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* ── Inputs ──────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] select,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: var(--font-ar) !important;
    font-size: 14px !important;
    min-height: 44px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--blue) !important;
    box-shadow: 0 0 0 3px rgba(10,132,255,0.15) !important;
}

/* ── Selectbox ───────────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: var(--font-ar) !important;
    min-height: 44px !important;
}

/* ── Radio ───────────────────────────────────────────────────────── */
[data-testid="stRadio"] label {
    font-family: var(--font-ar) !important;
    font-size: 14px !important;
    color: var(--subtext) !important;
}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    color: var(--subtext) !important;
}

/* ── Checkbox ────────────────────────────────────────────────────── */
[data-testid="stCheckbox"] label {
    font-family: var(--font-ar) !important;
    font-size: 14px !important;
    color: var(--text) !important;
}

/* ── Dataframe ───────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    overflow: auto !important;
    max-width: 100% !important;
}

/* ── Metric ──────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 16px 20px !important;
}
[data-testid="stMetricLabel"] {
    font-family: var(--font-ar) !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    color: var(--subtext) !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-en) !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    letter-spacing: -1px;
}

/* ── Alerts ──────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: var(--r) !important;
    border: 1px solid var(--border) !important;
    font-family: var(--font-ar) !important;
}

/* ── Tabs ────────────────────────────────────────────────────────── */
[data-testid="stTabs"] {
    gap: 6px;
    margin-bottom: 20px;
    flex-wrap: wrap !important;
}
[data-testid="stTabs"] [data-testid="stTab"] {
    font-family: var(--font-ar) !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 10px 16px !important;
    border-radius: 12px !important;
    background: #141414 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    color: var(--subtext) !important;
    transition: all 0.2s ease-in-out;
    white-space: nowrap;
}
[data-testid="stTabs"] [data-testid="stTab"]:hover {
    color: var(--text) !important;
    border-color: rgba(255,255,255,0.15) !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #1c1c1e !important;
    color: #ffffff !important;
    border-color: var(--blue) !important;
    box-shadow: 0 4px 16px rgba(10,132,255,0.25) !important;
}

/* ── Spinner ─────────────────────────────────────────────────────── */
[data-testid="stSpinner"] p {
    font-family: var(--font-ar) !important;
    color: var(--subtext) !important;
}

/* ── Divider ─────────────────────────────────────────────────────── */
hr { border-color: var(--border) !important; margin: 20px 0 !important; }

/* ── Hide Streamlit UI ───────────────────────────────────────────── */
#MainMenu, footer, [data-testid="stDeployButton"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }

/* ════════════════════════════════════════════════════════════════
   MOBILE RESPONSIVENESS — Tablet (≤ 1024px) & Phone (≤ 768px)
   ════════════════════════════════════════════════════════════════ */

/* ── Tablet (iPad, small laptops) ───────────────────────────────── */
@media (max-width: 1024px) {
    .main .block-container {
        padding: 16px 16px !important;
        max-width: 100% !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 22px !important;
    }

    [data-testid="stTabs"] [data-testid="stTab"] {
        font-size: 13px !important;
        padding: 8px 12px !important;
    }
}

/* ── Mobile Phone (≤ 768px) ─────────────────────────────────────── */
@media (max-width: 768px) {

    /* Content padding */
    .main .block-container {
        padding: 12px 10px !important;
        max-width: 100% !important;
    }

    /* Sidebar: collapse to overlay on small screens */
    [data-testid="stSidebar"] {
        min-width: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNavItems"] {
        padding: 8px 0 !important;
    }

    /* Page headers scale down */
    h1 { font-size: 20px !important; }
    h2 { font-size: 18px !important; }
    h3 { font-size: 16px !important; }
    h4 { font-size: 14px !important; }

    /* Metrics — 2 per row on mobile */
    [data-testid="stMetricValue"] {
        font-size: 20px !important;
        letter-spacing: -0.5px;
    }
    [data-testid="stMetricLabel"] {
        font-size: 10px !important;
    }
    [data-testid="stMetric"] {
        padding: 12px 10px !important;
    }

    /* Buttons — full width, touch-friendly */
    [data-testid="stButton"] button {
        font-size: 13px !important;
        padding: 10px 12px !important;
        min-height: 44px !important;
        width: 100% !important;
    }
    [data-testid="stLinkButton"] a {
        font-size: 13px !important;
        padding: 10px 12px !important;
        min-height: 44px !important;
    }

    /* Inputs — bigger touch targets */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {
        font-size: 16px !important; /* Prevents iOS zoom on focus */
        padding: 10px 12px !important;
    }
    [data-testid="stSelectbox"] > div > div {
        font-size: 16px !important;
    }

    /* Cards — less padding */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
        padding: 14px 12px !important;
        border-radius: 12px !important;
    }

    /* Tabs — scroll horizontally */
    [data-testid="stTabs"] {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        gap: 4px;
        padding-bottom: 4px;
    }
    [data-testid="stTabs"]::-webkit-scrollbar { display: none; }
    [data-testid="stTabs"] [data-testid="stTab"] {
        font-size: 12px !important;
        padding: 8px 10px !important;
        white-space: nowrap !important;
        border-radius: 10px !important;
        flex-shrink: 0;
    }

    /* Columns — stack vertically on mobile */
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 8px !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"] {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        flex: 1 1 100% !important;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] summary {
        font-size: 13px !important;
        padding: 10px 12px !important;
    }

    /* Progress bar */
    [data-testid="stProgressBar"] {
        height: 6px !important;
        border-radius: 3px !important;
    }

    /* Checkbox touch area */
    [data-testid="stCheckbox"] label {
        font-size: 13px !important;
        min-height: 40px !important;
        display: flex !important;
        align-items: center !important;
    }

    /* Caption / small text */
    [data-testid="stCaptionContainer"] {
        font-size: 11px !important;
    }

    /* Number input */
    [data-testid="stNumberInput"] input {
        font-size: 16px !important;
    }

    /* Slider */
    [data-testid="stSlider"] {
        padding: 8px 0 !important;
    }
    [data-testid="stSlider"] [data-testid="stThumbValue"] {
        font-size: 12px !important;
    }

    /* Dataframe horizontal scroll */
    [data-testid="stDataFrame"] {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch;
    }
    [data-testid="stDataFrame"] > div {
        min-width: 600px;
    }

    /* Alert messages */
    [data-testid="stAlert"] {
        font-size: 13px !important;
        padding: 10px 12px !important;
    }

    /* Divider margin */
    hr { margin: 14px 0 !important; }

    /* Hide sidebar button label if too long */
    [data-testid="stSidebar"] button {
        font-size: 13px !important;
    }
}

/* ── Very small phones (≤ 400px, Galaxy A series etc.) ──────────── */
@media (max-width: 400px) {
    .main .block-container {
        padding: 8px 8px !important;
    }

    h1 { font-size: 18px !important; }
    h3 { font-size: 14px !important; }

    [data-testid="stButton"] button {
        font-size: 12px !important;
    }

    [data-testid="stTabs"] [data-testid="stTab"] {
        font-size: 11px !important;
        padding: 7px 8px !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 18px !important;
    }
}

/* ── Lead card mobile fix — stacked layout ───────────────────────── */
@media (max-width: 768px) {
    /* Lead cards in search: stack checkbox + info + message + actions */
    .lead-card-mobile-stack [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
    }

    /* Make map fill width */
    iframe {
        width: 100% !important;
        max-width: 100% !important;
    }
}

/* ── Sidebar nav items touch-friendly ───────────────────────────── */
[data-testid="stSidebar"] [data-testid="stButton"] button {
    min-height: 44px !important;
    border-radius: 10px !important;
    font-size: 14px !important;
}

/* ── Progress text ───────────────────────────────────────────────── */
[data-testid="stProgressBar"] + div {
    font-size: 13px !important;
    font-family: var(--font-ar) !important;
}

/* ── Multiselect ─────────────────────────────────────────────────── */
[data-testid="stMultiSelect"] > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: var(--font-ar) !important;
    font-size: 14px !important;
}

/* ── Toggle ──────────────────────────────────────────────────────── */
[data-testid="stToggle"] label {
    font-family: var(--font-ar) !important;
    font-size: 14px !important;
    color: var(--text) !important;
}

/* ── Number input arrows larger on touch ────────────────────────── */
[data-testid="stNumberInput"] button {
    min-width: 32px !important;
    min-height: 32px !important;
}

/* ── RTL fix for sidebar on mobile ──────────────────────────────── */
@media (max-width: 768px) {
    [data-testid="stSidebar"] {
        border-right: none !important;
        border-bottom: 1px solid var(--border) !important;
    }
}
</style>
"""


def apply_theme():
    import streamlit as st
    st.markdown(get_ios_theme_css(), unsafe_allow_html=True)
