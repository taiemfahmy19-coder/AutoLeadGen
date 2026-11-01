"""AutoLeadGen v2 - UI Views: CRM Leads Table and Management (Apple iOS HIG Style)."""
from datetime import datetime
import pandas as pd
import streamlit as st
from config.constants import ALL_STATUSES, ALL_WA_STATUSES
from services.export_service import ExportService
from ui.components import render_ios_header, render_status_badge, escape


def render_crm():
    render_ios_header(
        title="إدارة العملاء (Leads CRM Table)",
        subtitle="تصفح، فلترة، تدقيق، وتأهيل قاعدة بيانات العملاء المحلية المعتمدة.",
        icon="📋",
        badge="Unified Database"
    )

    db = st.session_state.db
    leads = db.get_all_leads()

    if not leads:
        st.info("لا يوجد عملاء بعد في قاعدة البيانات. ابدأ بالبحث من شاشة Search Leads.")
        return

    # iOS Filter Bar
    with st.container(border=True):
        st.markdown("<p style='font-size: 0.82rem; font-weight: 700; color: var(--ios-subtext); text-transform: uppercase; margin-bottom: 8px;'>أدوات التصفية والفرز الذكي</p>", unsafe_allow_html=True)
        
        f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)
        with f_col1:
            sel_status = st.selectbox("الحالة (Status):", ["All"] + ALL_STATUSES)
        with f_col2:
            sel_wa = st.selectbox("حالة WhatsApp:", ["All"] + ALL_WA_STATUSES)
        with f_col3:
            all_cities = ["All"] + sorted(list(set(l[6] for l in leads if l[6])))
            sel_city = st.selectbox("المدينة:", all_cities)
        with f_col4:
            all_ind = ["All"] + sorted(list(set(l[5] for l in leads if l[5])))
            sel_ind = st.selectbox("المجال:", all_ind)
        with f_col5:
            min_score = st.slider("الحد الأدنى للـScore:", 0, 100, 0)

        search_q = st.text_input("🔎 بحث سريع (بالاسم، الهاتف، أو العنوان):", placeholder="اكتب للبحث الفوري...")

    # Apply filters
    filtered = leads
    if sel_status != "All":
        filtered = [l for l in filtered if l[9] == sel_status]
    if sel_wa != "All":
        filtered = [l for l in filtered if (l[13] if len(l) > 13 else "UNKNOWN") == sel_wa]
    if sel_city != "All":
        filtered = [l for l in filtered if l[6] == sel_city]
    if sel_ind != "All":
        filtered = [l for l in filtered if l[5] == sel_ind]
    if min_score > 0:
        filtered = [l for l in filtered if (l[8] or 0) >= min_score]
    if search_q:
        sq = search_q.lower()
        filtered = [l for l in filtered if sq in (l[1] or "").lower() or sq in (l[2] or "").lower() or sq in (l[3] or "").lower()]

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin: 12px 4px;">
        <span style="font-size: 0.9rem; color: var(--ios-subtext);">عرض <strong style="color: var(--ios-text);">{len(filtered)}</strong> من أصل <strong style="color: var(--ios-text);">{len(leads)}</strong> عميل</span>
        <span style="font-size: 0.78rem; font-weight: 600; color: var(--ios-blue);">● SQLite WAL Mode نشط ومفهرس</span>
    </div>
    """, unsafe_allow_html=True)

    if filtered:
        display_data = []
        for l in filtered:
            display_data.append({
                "ID": l[0],
                "اسم النشاط": l[1],
                "الهاتف": l[2],
                "WhatsApp": l[13] if len(l) > 13 else "UNKNOWN",
                "صحة الهاتف": l[14] if len(l) > 14 else "UNKNOWN",
                "المدينة": l[6],
                "المجال": l[5],
                "Score": l[8],
                "الحالة": l[9],
                "تاريخ الإضافة": l[11],
            })

        df_disp = pd.DataFrame(display_data)
        st.dataframe(df_disp, use_container_width=True, height=350)

        # Batch Management Section (iOS Inset Actions)
        st.write("")
        with st.container(border=True):
            st.markdown("<h3 style='margin: 0 0 12px 0; font-size: 1.15rem; font-weight: 700;'>⚡ إدارة ومراجعة العملاء المحددين</h3>", unsafe_allow_html=True)

            act_c1, act_c2 = st.columns([2, 2])
            with act_c1:
                selected_ids = st.multiselect(
                    "اختر العملاء لتطبيق إجراء جماعي عليهم:",
                    options=[l[0] for l in filtered],
                    format_func=lambda x: next((f"ID {l[0]} - {l[1]} ({l[6]})" for l in filtered if l[0] == x), str(x))
                )

            with act_c2:
                action = st.selectbox("الإجراء المطلوب:", [
                    "تأهيل العميل (Qualify)",
                    "جاهز للتواصل (Move to Ready Queue)",
                    "🔍 فحص وتحقق WhatsApp (Verify via Playwright)",
                    "تم التواصل (Mark Contacted)",
                    "تم الرد (Mark Replied)",
                    "مهتم بالخدمة (Mark Interested)",
                    "غير مهتم (Mark Not Interested)",
                    "حظر التواصل نهائياً (Mark DO NOT CONTACT)",
                    "بحاجة لمراجعة (Mark Needs Review)",
                    "بيانات غير صالحة (Mark Invalid)",
                    "تصدير المحدد إلى Excel",
                    "حذف العميل المحدد",
                ])

                if st.button("تطبيق الإجراء على المحددين", type="primary", use_container_width=True):
                    if not selected_ids:
                        st.warning("يرجى اختيار عميل واحد على الأقل.")
                    else:
                        for lid in selected_ids:
                            if action == "تأهيل العميل (Qualify)":
                                db.update_lead_status(lid, "QUALIFIED")
                            elif action == "جاهز للتواصل (Move to Ready Queue)":
                                db.promote_to_ready([lid])
                            elif action == "🔍 فحص وتحقق WhatsApp (Verify via Playwright)":
                                rec = db.get_lead_by_id(lid)
                                if rec and rec[2]:
                                    res_wa = st.session_state.messenger.verify_whatsapp_number(rec[2])
                                    db.update_lead_whatsapp_status(lid, res_wa)
                            elif action == "تم التواصل (Mark Contacted)":
                                db.update_lead_status(lid, "CONTACTED")
                            elif action == "تم الرد (Mark Replied)":
                                db.update_lead_status(lid, "REPLIED")
                            elif action == "مهتم بالخدمة (Mark Interested)":
                                db.update_lead_status(lid, "INTERESTED")
                            elif action == "غير مهتم (Mark Not Interested)":
                                db.update_lead_status(lid, "NOT_INTERESTED")
                            elif action == "حظر التواصل نهائياً (Mark DO NOT CONTACT)":
                                db.update_lead_status(lid, "DO_NOT_CONTACT")
                            elif action == "بحاجة لمراجعة (Mark Needs Review)":
                                db.update_lead_status(lid, "NEEDS_REVIEW")
                            elif action == "بيانات غير صالحة (Mark Invalid)":
                                db.update_lead_status(lid, "INVALID")
                            elif action == "حذف العميل المحدد":
                                db.delete_lead(lid)

                        if action == "تصدير المحدد إلى Excel":
                            selected_rows = [l for l in filtered if l[0] in selected_ids]
                            filename = f"selected_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                            ExportService.to_excel(selected_rows, filename)
                            st.success(f"تم تصدير {len(selected_rows)} عميل إلى {filename}")
                        else:
                            st.success(f"تم تنفيذ الإجراء '{action}' بنجاح!")
                        st.rerun()

        # Single Lead Detail Inspector
        st.write("")
        with st.container(border=True):
            st.markdown("<h3 style='margin: 0 0 8px 0; font-size: 1.15rem; font-weight: 700;'>🔍 بطاقة الفحص التفصيلي وسجل التفاعلات</h3>", unsafe_allow_html=True)
            
            lead_lookup = st.selectbox(
                "اختر عميلاً لعرض بطاقته الكاملة:",
                options=[l[0] for l in filtered],
                format_func=lambda x: next((f"{l[1]} | {l[2]} | Score: {l[8]}" for l in filtered if l[0] == x), str(x))
            )

            if lead_lookup:
                detail = db.get_lead_by_id(lead_lookup)
                if detail:
                    d_c1, d_c2, d_c3 = st.columns(3)
                    with d_c1:
                        st.write(f"**🏢 الاسم:** {detail[1]}")
                        st.write(f"**📞 الهاتف:** `{detail[2]}`")
                        st.write(f"**📶 صحة الهاتف:** `{detail[14] if len(detail) > 14 else 'UNKNOWN'}`")
                        st.write(f"**🟢 حالة WhatsApp:** `{detail[13] if len(detail) > 13 else 'UNKNOWN'}`")
                    with d_c2:
                        st.write(f"**🏷️ المجال:** {detail[5]}")
                        st.write(f"**📍 المدينة:** {detail[6]}")
                        st.write(f"**🗺️ العنوان:** {detail[3] or 'غير محدد'}")
                    with d_c3:
                        st.write(f"**★ الـScore:** `{detail[8]}/100`")
                        st.write(f"**📌 الحالة:** `{detail[9]}`")
                        st.write(f"**📅 تاريخ الإضافة:** {detail[11]}")

                    st.divider()
                    interactions = db.get_interactions_for_lead(lead_lookup)
                    st.markdown("<p style='font-size: 0.88rem; font-weight: 700; color: var(--ios-subtext); text-transform: uppercase;'>سجل التفاعلات (Timeline)</p>", unsafe_allow_html=True)
                    if interactions:
                        for inter in interactions:
                            st.caption(f"📅 {inter[2]} | قناة: {inter[3]} | حالة: {inter[5]} | ملاحظة: {inter[6]}")
                    else:
                        st.caption("لا توجد تفاعلات مسجلة لهذا العميل بعد.")
