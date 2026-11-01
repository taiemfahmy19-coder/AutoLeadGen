"""AutoLeadGen v2 - UI Views: Message Center and Template Management."""
import streamlit as st
from config.constants import LANGUAGES
from ui.components import page_header, section_label, empty_state, escape

def render_message_center():
    page_header("مركز الرسائل والقوالب التسويقية", "Template Studio", "💬")

    db = st.session_state.db
    templates = db.get_all_templates()
    template_options = {t[0]: f"{t[1]} ({t[2]})" for t in templates}

    selected_t_id = st.selectbox(
        "اختر القالب لتعديله أو استعراضه:",
        options=list(template_options.keys()),
        format_func=lambda x: template_options[x]
    )

    current_t = next((t for t in templates if t[0] == selected_t_id), None)

    if current_t:
        t_id, t_name, t_lang, t_content, t_ind = current_t

        col_left, col_right = st.columns(2)
        
        with col_left:
            with st.container(border=True):
                section_label("بيانات وتفاصيل القالب")
                name_input = st.text_input("اسم القالب:", value=t_name)
                lang_input = st.selectbox("اللغة:", LANGUAGES, index=0 if t_lang == "Arabic" else 1)
                ind_input = st.text_input("المجال المخصص:", value=t_ind or "General")

                content_input = st.text_area("نص رسالة العرض التسويقي:", value=t_content, height=220)

                st.caption("المتغيرات المتاحة: {name}, {business}, {industry}, {city}")

                if st.button("💾 حفظ تعديلات القالب", type="primary", use_container_width=True):
                    db.update_template(t_id, name_input, lang_input, content_input, ind_input)
                    st.success("تم حفظ القالب بنجاح!")
                    st.rerun()

        with col_right:
            with st.container(border=True):
                section_label("👁️ معاينة حية (Preview)")
                all_leads = db.get_all_leads()
                if all_leads:
                    lead_choices = {l[0]: f"{l[1]} ({l[6]} - {l[5]})" for l in all_leads}
                    preview_lid = st.selectbox("اختر عميلاً للتجربة:", options=list(lead_choices.keys()), format_func=lambda x: lead_choices[x])
                    lead_item = db.get_lead_by_id(preview_lid)
                    if lead_item:
                        b_name = lead_item[1] or "صاحب العمل"
                        first_name = b_name.split()[0] if b_name else "صاحب العمل"
                        try:
                            preview_text = content_input.format(
                                name=first_name,
                                business=b_name,
                                industry=lead_item[5] or "نشاطك",
                                city=lead_item[6] or "مدينتك"
                            )
                        except Exception as ex:
                            preview_text = f"خطأ في تنسيق المتغيرات: {ex}\n\n{content_input}"

                        safe_preview = escape(preview_text).replace('\n', '<br>')
                        st.markdown(f"""
                        <div style="background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 16px;">
                            <div style="font-size: 11px; font-weight: 700; color: var(--green); margin-bottom: 8px;">
                                💬 AutoLeadGen
                            </div>
                            <div style="color: var(--text); font-size: 14px; line-height: 1.6;">{safe_preview}</div>
                        </div>
                        """, unsafe_allow_html=True)
