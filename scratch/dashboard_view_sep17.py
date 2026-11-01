"""AutoLeadGen v2 - UI Views: Dashboard and Quick WhatsApp Outreach Hub (Apple iOS HIG Style)."""
import json
import urllib.parse
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from ui.components import escape, render_status_badge, render_ios_header
from services.outreach_service import OutreachService
from services.lead_service import LeadService


def render_dashboard_whatsapp_hub(leads, db):
    eligible = []
    for l in leads:
        lid, b_name, phone, addr, site, ind, city, src, score, st_val = l[:10]
        wa_val = l[13] if len(l) > 13 else "UNKNOWN"

        if not phone or str(phone).strip() == "":
            continue
        if st_val in ["DO_NOT_CONTACT", "INVALID", "NEEDS_REVIEW"]:
            continue
        if wa_val == "NOT_VERIFIED":
            continue

        eligible.append({
            "id": lid,
            "name": (b_name or "").strip(),
            "phone": (phone or "").strip(),
            "industry": (ind or "").strip(),
            "city": (city or "").strip(),
            "wa_status": wa_val,
            "status": st_val
        })

    if not eligible:
        return

    # Apple-style Frosted Action Banner
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(37, 211, 102, 0.12) 0%, rgba(18, 140, 126, 0.08) 100%);
        border: 1px solid rgba(37, 211, 102, 0.28);
        border-radius: 20px;
        padding: 20px 24px;
        margin-bottom: 18px;
        box-shadow: var(--ios-shadow-sm);
        display: flex;
        justify-content: space-between;
        align-items: center;
    ">
        <div>
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                <span style="font-size: 24px;">💬</span>
                <h3 style="margin:0; font-size: 1.35rem; font-weight: 700; color: var(--ios-text);">مركز التواصل السريع عبر WhatsApp</h3>
            </div>
            <p style="margin:0; color: var(--ios-subtext); font-size: 0.92rem;">
                إرسال رسائل مخصصة للعملاء المؤهلين مباشرة أو استعراضهم مع مؤقت 10 ثوانٍ التفاعلي.
            </p>
        </div>
        <span style="
            background: rgba(37, 211, 102, 0.16);
            color: #25D366;
            padding: 4px 14px;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 700;
        ">جاهز للإرسال</span>
    </div>
    """, unsafe_allow_html=True)

    if "dash_wa_view" not in st.session_state:
        st.session_state["dash_wa_view"] = "select_send"

    btn_c1, btn_c2 = st.columns(2)
    with btn_c1:
        if st.button("📲 تحديد العملاء والإرسال المباشر",
                     type="primary" if st.session_state["dash_wa_view"] == "select_send" else "secondary",
                     use_container_width=True):
            st.session_state["dash_wa_view"] = "select_send"
            st.rerun()
    with btn_c2:
        if st.button("⏱️ استعراض العملاء (مؤقت 10 ثوانٍ)",
                     type="primary" if st.session_state["dash_wa_view"] == "carousel_10s" else "secondary",
                     use_container_width=True):
            st.session_state["dash_wa_view"] = "carousel_10s"
            st.rerun()

    with st.expander("✍️ تخصيص نص الرسالة باللهجة المصرية (اختياري)", expanded=False):
        custom_tpl = st.text_area(
            "نص الرسالة المخصصة:",
            value=st.session_state.get("dash_custom_egy_tpl", ""),
            placeholder="مساء الخير يا فندم {name}، شفت شغلكم في {business} بمجال {industry}...",
            height=85,
            key="dash_custom_egy_tpl_input"
        )
        st.session_state["dash_custom_egy_tpl"] = custom_tpl

    current_tpl = st.session_state.get("dash_custom_egy_tpl", "")

    # Quick Text Importer
    with st.expander("📥 لصق أرقام خارجية واستيرادها لقاعدة البيانات", expanded=False):
        st.markdown("الصق أرقاماً (رقم في كل سطر مع الاسم والمجال مفصولين بفواصل):")
        raw_pasted = st.text_area("الأرقام:", height=85, key="dash_paste_importer_area", placeholder="01012345678, اسم المحل, القاهرة, عطور")
        if st.button("➕ حفظ واستيراد الأرقام", type="primary", use_container_width=True):
            lead_svc = LeadService(db)
            added = lead_svc.import_raw_pasted_lines(raw_pasted)
            st.success(f"تم بنجاح استيراد {added} رقم كـ UNKNOWN وجاري فحصها.")
            st.rerun()

    # Filter by WhatsApp Verified
    f_c1, f_c2 = st.columns([3, 2])
    with f_c1:
        only_wa = st.toggle("🟢 عرض أرقام WhatsApp المؤكدة فقط (VERIFIED)", value=False, key="dash_filter_verified_only")
    with f_c2:
        verified_cnt = sum(1 for e in eligible if e["wa_status"] == "VERIFIED")
        st.caption(f"📊 مؤكد واتساب: **{verified_cnt}** | الإجمالي المؤهل: **{len(eligible)}**")

    if only_wa:
        eligible = [e for e in eligible if e["wa_status"] == "VERIFIED"]

    if not eligible:
        st.info("لا توجد أرقام مؤكدة مطابقة للشروط حالياً.")
        st.divider()
        return

    # VIEW 1: Multi-Select & Batch Send
    if st.session_state["dash_wa_view"] == "select_send":
        st.markdown(f"#### 🎯 تحديد العملاء للإرسال ({len(eligible)} عميل متاح)")

        sel_c1, sel_c2, sel_c3, sel_c4 = st.columns(4)
        with sel_c1:
            if st.button("⚡ اختيار أول 5", use_container_width=True):
                for i in range(len(eligible)):
                    st.session_state[f"dash_lead_chk_{i}"] = (i < 5)
                st.rerun()
        with sel_c2:
            if st.button("⚡ اختيار أول 10", use_container_width=True):
                for i in range(len(eligible)):
                    st.session_state[f"dash_lead_chk_{i}"] = (i < 10)
                st.rerun()
        with sel_c3:
            if st.button("✅ اختيار الكل", use_container_width=True):
                for i in range(len(eligible)):
                    st.session_state[f"dash_lead_chk_{i}"] = True
                st.rerun()
        with sel_c4:
            if st.button("❌ إلغاء الاختيار", use_container_width=True):
                for i in range(len(eligible)):
                    st.session_state[f"dash_lead_chk_{i}"] = False
                st.rerun()

        selected_leads = []
        for i, lead in enumerate(eligible):
            b_name = lead["name"] or "بدون اسم"
            ind = lead["industry"] or "عام"
            cty = lead["city"] or "غير محدد"
            ph = lead["phone"]
            lead_msg = OutreachService.build_personalized_message(lead["name"], lead["industry"], lead["city"], current_tpl)
            clean_digits = ph.lstrip("+")
            wa_url = f"https://wa.me/{clean_digits}?text={urllib.parse.quote(lead_msg)}"

            default_val = st.session_state.get(f"dash_lead_chk_{i}", i < 5)
            chk_col, card_col = st.columns([0.6, 9.4])
            with chk_col:
                st.write("")
                checked = st.checkbox("", value=default_val, key=f"dash_lead_chk_{i}")
            with card_col:
                safe_name = escape(b_name)
                safe_ph = escape(ph)
                safe_ind = escape(ind)
                safe_cty = escape(cty)
                safe_msg = escape(lead_msg)
                badge_html = render_status_badge(lead["wa_status"])

                st.markdown(f"""
                <div style="
                    background: var(--ios-card, rgba(255, 255, 255, 0.85));
                    border: 1px solid var(--ios-border, rgba(0, 0, 0, 0.08));
                    border-radius: 16px;
                    padding: 12px 16px;
                    margin-bottom: 8px;
                    box-shadow: var(--ios-shadow-sm);
                ">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <strong style="font-size:15px; font-weight: 700; color: var(--ios-text);">🏢 {safe_name}</strong>
                        {badge_html}
                    </div>
                    <div style="font-size:13px; color: var(--ios-subtext); margin-bottom:8px;">
                        📞 <b>الهاتف:</b> <span class="ltr-text" style="color: #007AFF; font-weight: 600;">{safe_ph}</span> &nbsp;|&nbsp; 🏷️ <b>النشاط:</b> {safe_ind} &nbsp;|&nbsp; 📍 <b>المدينة:</b> {safe_cty}
                    </div>
                    <div style="
                        font-size: 13px;
                        background: var(--ios-fill-tertiary);
                        border-right: 3px solid #34C759;
                        padding: 8px 12px;
                        border-radius: 8px;
                        color: var(--ios-text);
                        line-height: 1.45;
                    ">
                        <span style="color: #34C759; font-weight: 600;">💬 الرسالة:</span> {safe_msg}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if checked:
                selected_leads.append({"name": b_name, "phone": ph, "url": wa_url})

        if selected_leads:
            st.divider()
            st.success(f"✅ تم اختيار **{len(selected_leads)}** عميل جاهزين للإرسال!")
            link_cols = st.columns(min(3, max(1, len(selected_leads))))
            for idx, item in enumerate(selected_leads):
                col_idx = idx % len(link_cols)
                with link_cols[col_idx]:
                    st.link_button(f"📲 {item['name'][:18]} ({item['phone']})", item["url"], use_container_width=True)

    # VIEW 2: 10s Carousel View (Apple Music/Fitness Widget Style)
    elif st.session_state["dash_wa_view"] == "carousel_10s":
        carousel_items = []
        for lead in eligible:
            lead_msg = OutreachService.build_personalized_message(lead["name"], lead["industry"], lead["city"], current_tpl)
            clean_digits = lead["phone"].lstrip("+")
            carousel_items.append({
                "id": lead["id"],
                "name": escape(lead["name"] or "بدون اسم"),
                "phone": escape(lead["phone"]),
                "industry": escape(lead["industry"] or "عام"),
                "city": escape(lead["city"] or "غير محدد"),
                "wa_status": lead["wa_status"],
                "message": escape(lead_msg),
                "url": f"https://wa.me/{clean_digits}?text={urllib.parse.quote(lead_msg)}"
            })

        carousel_json = json.dumps(carousel_items)
        carousel_html = f"""
        <div id="carouselContainer" style="
            font-family: 'Alexandria', -apple-system, BlinkMacSystemFont, sans-serif;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(37, 211, 102, 0.35);
            border-radius: 20px;
            padding: 22px 24px;
            direction: rtl;
            box-shadow: 0 10px 30px rgba(0,0,0,0.06);
        ">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(0,0,0,0.06); padding-bottom:12px; margin-bottom:14px;">
                <span style="background: rgba(37, 211, 102, 0.15); color: #25D366; padding:4px 14px; border-radius:9999px; font-weight:700; font-size:13px;" id="clientCounter">عميل 1 من {len(carousel_items)}</span>
                <span id="autoTimerStatus" style="font-size:13px; color:#8e8e93; font-weight:500;">⏱️ التبديل خلال <b id="countdownSec" style="color:#25D366; font-size:15px;">10</b> ثوانٍ</span>
                <button onclick="toggleTimer()" id="pausePlayBtn" style="
                    padding: 5px 14px;
                    border-radius: 10px;
                    border: 1px solid rgba(0,0,0,0.1);
                    background: white;
                    cursor: pointer;
                    font-size: 12px;
                    font-weight: 600;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                ">⏸️ إيقاف مؤقت</button>
            </div>
            <div style="background: rgba(0,0,0,0.05); height: 6px; border-radius: 9999px; overflow: hidden; margin-bottom: 16px;">
                <div id="pBar" style="background: linear-gradient(90deg, #25D366 0%, #128C7E 100%); height: 100%; width: 0%; transition: width 0.1s linear;"></div>
            </div>
            <div style="
                background: rgba(246, 246, 248, 0.8);
                border: 1px solid rgba(0,0,0,0.06);
                border-radius: 16px;
                padding: 16px 20px;
                margin-bottom: 16px;
            ">
                <h3 id="cardBusiness" style="margin:0 0 6px 0; color: #1c1c1e; font-size: 17px; font-weight: 700;">...</h3>
                <div style="font-size:13px; color: #8e8e93; margin-bottom:10px;">
                    📞 <b>الهاتف:</b> <span id="cardPhone" style="direction:ltr; font-weight:700; color: #007AFF;">...</span> |
                    🏢 <b>النشاط:</b> <span id="cardIndustry" style="color: #1c1c1e;">...</span> |
                    📍 <b>المدينة:</b> <span id="cardCity" style="color: #1c1c1e;">...</span>
                </div>
                <div style="
                    background: white;
                    border-right: 3px solid #25D366;
                    padding: 12px 14px;
                    border-radius: 10px;
                    font-size: 13.5px;
                    color: #1c1c1e;
                    line-height: 1.5;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
                " id="cardMessage">...</div>
            </div>
            <div style="display:flex; gap:12px;">
                <button onclick="prevClient()" style="
                    flex: 1;
                    padding: 10px 14px;
                    border-radius: 12px;
                    border: 1px solid rgba(0,0,0,0.1);
                    background: white;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 13px;
                ">⏮️ السابق</button>
                <a id="cardSendLink" href="#" target="_blank" style="
                    flex: 3;
                    text-align: center;
                    background: linear-gradient(180deg, #25D366 0%, #128C7E 100%);
                    color: white;
                    text-decoration: none;
                    padding: 10px 18px;
                    border-radius: 12px;
                    font-weight: 700;
                    font-size: 14px;
                    box-shadow: 0 4px 14px rgba(37, 211, 102, 0.35);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                ">📲 إرسال على واتساب</a>
                <button onclick="nextClient()" style="
                    flex: 1;
                    padding: 10px 14px;
                    border-radius: 12px;
                    border: 1px solid rgba(0,0,0,0.1);
                    background: white;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 13px;
                ">التالي ⏭️</button>
            </div>
        </div>
        <script>
        var items = {carousel_json};
        var currentIndex = 0;
        var isPaused = false;
        var secondsRemaining = 10;
        function renderCard(idx) {{
            if (!items || items.length === 0) return;
            var item = items[idx];
            document.getElementById('clientCounter').innerText = 'عميل ' + (idx + 1) + ' من ' + items.length;
            document.getElementById('cardBusiness').innerText = '🏢 ' + item.name;
            document.getElementById('cardPhone').innerText = item.phone;
            document.getElementById('cardIndustry').innerText = item.industry;
            document.getElementById('cardCity').innerText = item.city;
            document.getElementById('cardMessage').innerText = item.message;
            document.getElementById('cardSendLink').href = item.url;
        }}
        function nextClient() {{ currentIndex = (currentIndex + 1) % items.length; resetCountdown(); renderCard(currentIndex); }}
        function prevClient() {{ currentIndex = (currentIndex - 1 + items.length) % items.length; resetCountdown(); renderCard(currentIndex); }}
        function resetCountdown() {{ secondsRemaining = 10; document.getElementById('pBar').style.width = '0%'; }}
        function toggleTimer() {{ isPaused = !isPaused; document.getElementById('pausePlayBtn').innerText = isPaused ? '▶️ تشغيل' : '⏸️ إيقاف'; }}
        setInterval(function() {{
            if (isPaused) return;
            secondsRemaining -= 0.1;
            document.getElementById('pBar').style.width = (((10 - secondsRemaining) / 10) * 100) + '%';
            document.getElementById('countdownSec').innerText = Math.max(0, Math.ceil(secondsRemaining));
            if (secondsRemaining <= 0) nextClient();
        }}, 100);
        renderCard(0);
        </script>
        """
        components.html(carousel_html, height=360)

    st.divider()


def render_dashboard():
    render_ios_header(
        title="لوحة مؤشرات الأداء والعملاء",
        subtitle="نظرة شاملة ومحدثة على دورة حياة العملاء، خط الأنابيب، والتواصل الموثق.",
        icon="📊",
        badge="Direct CRM Pipeline"
    )

    db = st.session_state.db
    # Auto-qualify any new high scoring leads
    db.auto_qualify_new_leads(min_score=70)

    leads = db.get_all_leads()
    metrics = db.get_dashboard_metrics()

    if not leads:
        st.info("👋 مرحباً بك! لا توجد بيانات مسجلة بعد. توجه إلى **Search Leads** للبدء باكتشاف العملاء.")
        return

    render_dashboard_whatsapp_hub(leads, db)

    # Top KPI Row (iOS Metric Cards)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 إجمالي العملاء", metrics["total"])
    with col2:
        st.metric("🟢 مؤكد WhatsApp", metrics["wa_verified"])
    with col3:
        st.metric("⏱️ جاهز للتواصل (READY)", metrics["ready"])
    with col4:
        st.metric("📬 تم التواصل (CONTACTED)", metrics["contacted"])

    sub_c1, sub_c2, sub_c3, sub_c4 = st.columns(4)
    with sub_c1:
        st.caption(f"⭐ **مؤهل (Score >= 70):** `{metrics['qualified']}`")
    with sub_c2:
        st.caption(f"🆕 **جديد:** `{metrics['new']}`")
    with sub_c3:
        st.caption(f"🔍 **بحاجة لمراجعة:** `{metrics['needs_review']}`")
    with sub_c4:
        st.caption(f"📊 **متوسط التقييم:** `{metrics['avg_score']}/100`")

    st.divider()

    # Pipeline action buttons with iOS HIG styling
    p_btn1, p_btn2 = st.columns(2)
    with p_btn1:
        if st.button("⚡ تأهيل العملاء ذوي التقييم المرتفع (Score >= 70)", use_container_width=True):
            promoted = db.auto_qualify_new_leads(min_score=70)
            st.success(f"تم تأهيل {promoted} عميل ونقلهم إلى QUALIFIED.")
            st.rerun()

    with p_btn2:
        if st.button("🚀 نقل المؤهلين إلى طابور التواصل (Move to READY)", type="primary", use_container_width=True):
            promoted, rejected = db.promote_to_ready()
            st.success(f"تم اعتماد {len(promoted)} عميل في طابور التواصل.")
            if rejected:
                st.warning(f"تم استبعاد {len(rejected)} عميل لنقص الهاتف أو وجود حظر.")
            st.rerun()

    st.divider()

    # Visual Distribution Charts
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("توزيع الحالات (CRM Status)")
        st_counts = {}
        for l in leads:
            st_val = l[9]
            st_counts[st_val] = st_counts.get(st_val, 0) + 1
        df_st = pd.DataFrame(list(st_counts.items()), columns=["Status", "Count"]).set_index("Status")
        st.bar_chart(df_st)

    with c2:
        st.subheader("توزيع المجالات (Industries)")
        ind_counts = {}
        for l in leads:
            ind_val = l[5] or "غير محدد"
            ind_counts[ind_val] = ind_counts.get(ind_val, 0) + 1
        df_ind = pd.DataFrame(list(ind_counts.items()), columns=["Industry", "Count"]).set_index("Industry")
        st.bar_chart(df_ind)
