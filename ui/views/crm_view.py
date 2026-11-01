"""AutoLeadGen v2 - UI Views: Enterprise CRM Leads Hub & Lifecycle Manager."""
from datetime import datetime
import pandas as pd
import streamlit as st
from config.constants import ALL_STATUSES, ALL_WA_STATUSES, ALL_PRIORITIES
from services.export_service import ExportService
from ui.components import page_header, section_label, empty_state, wa_badge, escape


def render_crm():
    page_header("إدارة العملاء والمتابعات (Leads CRM Hub)", "Unified Database & Lifecycle", "📋")

    db = st.session_state.db
    leads = db.get_all_leads()

    if not leads:
        empty_state("لا يوجد عملاء بعد في قاعدة البيانات. ابدأ بالبحث من شاشة Search Leads أو شغّل دورة اليوم من Dashboard.")
        return

    # ── Advanced Filters ──────────────────────────────────────────────────────
    with st.container(border=True):
        section_label("أدوات التصفية والفرز الذكي")
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

        search_q = st.text_input("🔎 بحث فوري (بالاسم، الهاتف، المدينة، أو الملاحظات):", placeholder="اكتب للبحث الفوري...")

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
        filtered = [
            l for l in filtered
            if sq in (l[1] or "").lower()
            or sq in (l[2] or "").lower()
            or sq in (l[3] or "").lower()
            or sq in (l[6] or "").lower()
            or (len(l) > 22 and sq in (l[22] or "").lower())  # notes field
        ]

    st.caption(f"عرض {len(filtered)} من أصل {len(leads)} عميل")

    # ── Tabs: Detailed Profiles vs Data Table ────────────────────────────────
    tab_profiles, tab_table = st.tabs(["👤 بطاقات العملاء والمتابعة (Lead Profiles)", "📊 جدول البيانات والإجراءات الجماعية"])

    with tab_profiles:
        if not filtered:
            empty_state("لا توجد نتائج مطابقة للبحث أو التصفية الحالية.")
        else:
            # Paginate 15 per page
            page_size = 12
            total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
            page_num = st.number_input("الصفحة:", min_value=1, max_value=total_pages, value=1)
            start_idx = (page_num - 1) * page_size
            page_leads = filtered[start_idx:start_idx + page_size]

            for l in page_leads:
                lid = l[0]
                b_name = l[1] or "بدون اسم"
                phone = l[2] or ""
                addr = l[3] or ""
                website = l[4] or ""
                industry = l[5] or "عام"
                city = l[6] or ""
                source = l[7] or "search"
                score = l[8] or 0
                status = l[9] or "NEW"
                wa_st = l[13] if len(l) > 13 else "UNKNOWN"
                first_contact = l[19] if len(l) > 19 else ""
                last_contact = l[20] if len(l) > 20 else ""
                next_followup = l[21] if len(l) > 21 else ""
                notes = l[22] if len(l) > 22 else ""
                priority = l[23] if len(l) > 23 and l[23] else ("HIGH" if score >= 80 else ("MEDIUM" if score >= 50 else "LOW"))

                with st.container(border=True):
                    head_c1, head_c2, head_c3 = st.columns([3, 2, 2])
                    with head_c1:
                        st.markdown(f"### {escape(b_name)}")
                        st.caption(f"📍 {escape(city)} • 🏢 {escape(industry)} • 🏷️ المصدر: `{escape(source)}`")
                    with head_c2:
                        p_color = "#30d158" if priority == "HIGH" else ("#ff9f0a" if priority == "MEDIUM" else "#8e8e93")
                        st.markdown(
                            f"<span style='background:{p_color}22;color:{p_color};padding:3px 10px;border-radius:8px;font-weight:700;font-size:12px;'>"
                            f"أولوية: {priority} (Score: {score})</span>",
                            unsafe_allow_html=True
                        )
                        st.write(f"📞 `{phone}`")
                    with head_c3:
                        clean_digits = phone.replace("+", "").strip()
                        wa_url = f"https://wa.me/{clean_digits}"
                        st.link_button("📲 محادثة WhatsApp مباشرة", wa_url, use_container_width=True, type="primary")

                    st.divider()

                    # Lifecycle status editor & Follow-up notes
                    e_col1, e_col2, e_col3 = st.columns([2, 2, 3])
                    with e_col1:
                        new_st = st.selectbox(
                            "حالة العميل (Lifecycle Status):",
                            ALL_STATUSES,
                            index=ALL_STATUSES.index(status) if status in ALL_STATUSES else 0,
                            key=f"status_sel_{lid}"
                        )
                    with e_col2:
                        new_follow = st.text_input(
                            "المتابعة القادمة (Next Follow-up):",
                            value=next_followup or "",
                            placeholder="YYYY-MM-DD",
                            key=f"follow_in_{lid}"
                        )
                    with e_col3:
                        new_notes = st.text_area(
                            "ملاحظات المتابعة والعميل (Notes):",
                            value=notes or "",
                            height=65,
                            key=f"notes_in_{lid}"
                        )

                    save_col1, save_col2 = st.columns([2, 5])
                    with save_col1:
                        if st.button("💾 حفظ تعديلات العميل", key=f"btn_save_{lid}", use_container_width=True):
                            db.update_lead_crm(
                                lead_id=lid,
                                status=new_st,
                                notes=new_notes,
                                next_follow_up=new_follow
                            )
                            st.success("تم الحفظ بنجاح ✅")
                            st.rerun()
                    with save_col2:
                        if first_contact or last_contact:
                            st.caption(f"🕒 أول تواصل: `{first_contact or '—'}` | آخر تواصل: `{last_contact or '—'}`")

    with tab_table:
        display_data = []
        for l in filtered:
            display_data.append({
                "ID": l[0],
                "اسم النشاط": l[1],
                "الهاتف": l[2],
                "WhatsApp": l[13] if len(l) > 13 else "UNKNOWN",
                "المدينة": l[6],
                "المجال": l[5],
                "Score": l[8],
                "الحالة": l[9],
                "المتابعة القادمة": l[21] if len(l) > 21 else "",
                "الملاحظات": l[22] if len(l) > 22 else "",
            })
        df_disp = pd.DataFrame(display_data)
        st.dataframe(df_disp, use_container_width=True, height=350)

        st.write("")
        with st.container(border=True):
            section_label("إجراءات جماعية وتصدير البيانات")
            act_c1, act_c2 = st.columns([2, 2])
            with act_c1:
                selected_ids = st.multiselect(
                    "اختر العملاء لتطبيق إجراء جماعي:",
                    options=[l[0] for l in filtered],
                    format_func=lambda x: next((f"ID {l[0]} - {l[1]} ({l[6]})" for l in filtered if l[0] == x), str(x))
                )
            with act_c2:
                action = st.selectbox("الإجراء المطلوب:", [
                    "تأهيل العميل (Move to QUALIFIED)",
                    "جاهز للتواصل (Move to READY)",
                    "تم التواصل (Mark CONTACTED)",
                    "تم الرد (Mark REPLIED)",
                    "مهتم (Mark INTERESTED)",
                    "متابعة (Mark FOLLOW_UP)",
                    "تم التحويل بنجاح (Mark CONVERTED)",
                    "غير مهتم / مرفوض (Mark REJECTED)",
                    "حظر التواصل نهائياً (DO NOT CONTACT)",
                    "حذف المحدد نهائياً",
                ])
                if st.button("تطبيق الإجراء على المحددين", type="primary", use_container_width=True):
                    if not selected_ids:
                        st.warning("يرجى اختيار عميل واحد على الأقل.")
                    else:
                        for s_id in selected_ids:
                            if "QUALIFIED" in action:
                                db.update_lead_status(s_id, "QUALIFIED")
                            elif "READY" in action:
                                db.update_lead_status(s_id, "READY")
                            elif "CONTACTED" in action:
                                db.update_lead_status(s_id, "CONTACTED")
                            elif "REPLIED" in action:
                                db.update_lead_status(s_id, "REPLIED")
                            elif "INTERESTED" in action:
                                db.update_lead_status(s_id, "INTERESTED")
                            elif "FOLLOW_UP" in action:
                                db.update_lead_status(s_id, "FOLLOW_UP")
                            elif "CONVERTED" in action:
                                db.update_lead_status(s_id, "CONVERTED")
                            elif "REJECTED" in action:
                                db.update_lead_status(s_id, "REJECTED")
                            elif "DO NOT CONTACT" in action:
                                db.update_lead_status(s_id, "DO_NOT_CONTACT")
                            elif "حذف" in action:
                                db.delete_lead(s_id)
                        st.success(f"تم تطبيق الإجراء على {len(selected_ids)} عميل بنجاح.")
                        st.rerun()
