"""AutoLeadGen v2 — Global Google Maps Lead Discovery with WhatsApp-First Outreach & Auto-Language Detection."""
import json
import urllib.parse
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from config.constants import (
    INDUSTRY_PRESETS,
    WORLD_COUNTRIES_DATA,
    detect_country_and_language,
    MULTILINGUAL_TEMPLATES,
    STATUS_CONTACTED,
    INTERACTION_SENT,
)
from services.lead_service import LeadService
from services.outreach_service import OutreachService
from pipeline.cleaner import normalize_phone
from ui.components import page_header, section_label, escape, wa_badge


# ─── Leaflet HTML map component ─────────────────────────────────────────────

def _build_leaflet_html(
    center_lat: float,
    center_lon: float,
    zoom: int,
    markers: list,
    height_px: int = 440,
) -> str:
    """Return a self-contained Leaflet map HTML string."""
    markers_js = json.dumps(markers, ensure_ascii=False)
    marker_count = len(markers)
    show_badge = "block" if marker_count > 0 else "none"
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    html, body {{ width:100%; height:{height_px}px; background:#0d1117; }}
    #map {{ width:100%; height:{height_px}px; border-radius:16px; overflow:hidden; }}
    #layer-toggle {{
      position:absolute; top:12px; right:12px; z-index:1000;
      display:flex; gap:6px;
    }}
    #layer-toggle button {{
      background:rgba(28,28,30,0.88); backdrop-filter:blur(10px);
      color:#fff; border:1px solid rgba(255,255,255,0.2);
      border-radius:10px; padding:5px 12px; font-size:12px; cursor:pointer;
      font-family:-apple-system,'SF Pro Text','Segoe UI',sans-serif;
      transition: all 0.2s;
    }}
    #layer-toggle button:hover, #layer-toggle button.active {{
      background:rgba(10,132,255,0.85); border-color:transparent;
    }}
    #lead-badge {{
      position:absolute; bottom:14px; left:14px; z-index:1000;
      background:rgba(30,215,96,0.15); backdrop-filter:blur(10px);
      border:1px solid rgba(30,215,96,0.45); border-radius:12px;
      color:#1ed760; font-size:13px; font-weight:600; padding:6px 14px;
      font-family:-apple-system,'SF Pro Text','Segoe UI',sans-serif;
      display:{show_badge};
    }}
  </style>
</head>
<body>
<div id="map"></div>
<div id="layer-toggle">
  <button class="active" onclick="setLayer('osm',this)">🗺 خريطة</button>
  <button onclick="setLayer('sat',this)">🛰 قمر صناعي</button>
  <button onclick="setLayer('dark',this)">🌑 داكن</button>
</div>
<div id="lead-badge">🟢 {marker_count} عميل فريد على الخريطة</div>

<script>
  var map = L.map('map', {{
    center: [{center_lat}, {center_lon}],
    zoom: {zoom},
    zoomControl: true,
    attributionControl: false
  }});

  var layers = {{
    osm:  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom:19}}),
    sat:  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{maxZoom:19}}),
    dark: L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{maxZoom:19}})
  }};
  var currentLayer = layers.dark.addTo(map);

  function setLayer(name, btn) {{
    map.removeLayer(currentLayer);
    currentLayer = layers[name].addTo(map);
    document.querySelectorAll('#layer-toggle button').forEach(function(b){{b.classList.remove('active');}});
    btn.classList.add('active');
  }}

  var waIcon = L.divIcon({{
    html: '<div style="font-size:24px;line-height:1;filter:drop-shadow(0 2px 8px rgba(0,0,0,.6))">📲</div>',
    iconSize:[28,28], iconAnchor:[14,28], popupAnchor:[0,-30], className:''
  }});
  var pinIcon = L.divIcon({{
    html: '<div style="font-size:24px;line-height:1;filter:drop-shadow(0 2px 8px rgba(0,0,0,.6))">📍</div>',
    iconSize:[28,28], iconAnchor:[14,28], popupAnchor:[0,-30], className:''
  }});

  var markersData = {markers_js};
  markersData.forEach(function(m) {{
    var icon = (m.wa_status === 'VERIFIED') ? waIcon : pinIcon;
    var waLink = m.phone
      ? '<br><a href="https://wa.me/' + m.phone.replace(/[^0-9]/g,'') + '" target="_blank" '
        + 'style="color:#1ed760;font-weight:700;text-decoration:none;">📲 فتح WhatsApp</a>'
      : '';
    var badge = m.wa_status === 'VERIFIED'
      ? '<span style="background:#1ed760;color:#000;padding:1px 8px;border-radius:6px;font-size:11px;font-weight:700;">✅ مؤكد</span>'
      : '<span style="background:#636366;color:#fff;padding:1px 8px;border-radius:6px;font-size:11px;">واتساب</span>';
    var popup = '<div style="font-family:-apple-system,sans-serif;min-width:170px;'
      + 'direction:rtl;text-align:right;padding:4px 0;">'
      + '<b style="font-size:14px;display:block;margin-bottom:4px;">' + (m.name||'—') + '</b>'
      + '<span style="color:#8e8e93;font-size:12px;">' + (m.phone||'') + '</span><br/>'
      + badge + waLink
      + '</div>';
    L.marker([m.lat, m.lon], {{icon:icon}})
      .bindPopup(popup, {{maxWidth:240, closeButton:false}})
      .addTo(map);
  }});
</script>
</body>
</html>"""


# ─── Main View ───────────────────────────────────────────────────────────────

def render_search():
    page_header(
        title="استكشاف العملاء والتواصل عبر WhatsApp",
        subtitle="بحث واستخراج عملاء جدد بدون أي تكرار مع التعرف التلقائي على الدولة ولغة الرسالة.",
        icon="🌍",
        badge="WhatsApp Dedicated Engine"
    )

    db = st.session_state.db
    messenger = st.session_state.messenger
    wa_connected = (messenger.get_connection_status() == "CONNECTED")

    # ── Section 1: Geographic selection ──────────────────────────────────────
    with st.container(border=True):
        st.markdown(
            "<p style='font-size:0.82rem;font-weight:700;color:var(--ios-subtext);"
            "text-transform:uppercase;margin-bottom:12px;'>1. التحديد الجغرافي — الدولة والمحافظة</p>",
            unsafe_allow_html=True
        )

        geo_col1, geo_col2 = st.columns(2)

        with geo_col1:
            country_names = list(WORLD_COUNTRIES_DATA.keys())
            selected_country_label = st.selectbox(
                "اختر الدولة المستهدفة:",
                options=country_names,
                format_func=lambda c: f"{WORLD_COUNTRIES_DATA[c]['flag']} {c}"
            )
            country_info = WORLD_COUNTRIES_DATA[selected_country_label]
            country_code = country_info["code"]
            country_name = selected_country_label
            map_lat = country_info.get("lat", 20.0)
            map_lon = country_info.get("lon", 0.0)
            map_zoom = country_info.get("zoom", 4)

            if selected_country_label == "دولة أخرى (Custom / Worldwide)":
                cust_c1, cust_c2 = st.columns(2)
                with cust_c1:
                    country_name = st.text_input(
                        "اسم الدولة بالإنجليزية أو العربية:",
                        placeholder="مثال: United States"
                    )
                with cust_c2:
                    country_code = st.text_input(
                        "كود الاتصال الدولي (بدون +):",
                        placeholder="مثال: 1"
                    ).strip("+")

        with geo_col2:
            provinces = country_info.get("provinces", [])
            city_coords = country_info.get("city_coords", {})

            if provinces:
                city_mode = st.radio(
                    "اختيار المحافظة / المدينة:",
                    ["من قائمة المحافظات", "إدخال يدوي"],
                    horizontal=True
                )
                if city_mode == "من قائمة المحافظات":
                    city = st.selectbox("المحافظة / المدينة:", provinces)
                else:
                    city = st.text_input(
                        "اسم المدينة أو الحي يدوياً:",
                        placeholder="مثال: التجمع، المعادي، الرياض، Miami..."
                    )
            else:
                city = st.text_input(
                    "اسم المحافظة أو المدينة:",
                    placeholder="اكتب اسم المدينة أو المنطقة..."
                )

            if city and city in city_coords:
                city_lat, city_lon, city_zoom = city_coords[city]
                map_lat, map_lon, map_zoom = city_lat, city_lon, city_zoom

        # ── Leaflet Interactive Map ──────────────────────────────────────────
        st.divider()
        st.markdown(
            "<p style='font-size:0.82rem;font-weight:700;color:var(--ios-subtext);"
            "text-transform:uppercase;margin-bottom:6px;'>🗺 خريطة العالم التفاعلية</p>",
            unsafe_allow_html=True
        )

        last_results = st.session_state.get("last_search_results", [])
        last_country_info = st.session_state.get("last_search_country_info", {})

        map_markers = []
        if last_results and last_country_info:
            base_lat = last_country_info.get("lat", map_lat)
            base_lon = last_country_info.get("lon", map_lon)
            base_city_coords = last_country_info.get("city_coords", {})
            last_city = st.session_state.get("last_search_city_name", "")

            if last_city and last_city in base_city_coords:
                c = base_city_coords[last_city]
                m_lat, m_lon = c[0], c[1]
            else:
                m_lat, m_lon = base_lat, base_lon

            import random
            rng = random.Random(42)
            for item in last_results:
                scatter_lat = m_lat + rng.uniform(-0.03, 0.03)
                scatter_lon = m_lon + rng.uniform(-0.05, 0.05)
                map_markers.append({
                    "lat": scatter_lat,
                    "lon": scatter_lon,
                    "name": item.get("business_name") or item.get("اسم النشاط", "نشاط تجاري"),
                    "phone": item.get("phone") or item.get("الهاتف", ""),
                    "wa_status": item.get("whatsapp_status") or item.get("حالة WhatsApp", "UNKNOWN"),
                })

        leaflet_html = _build_leaflet_html(
            center_lat=map_lat,
            center_lon=map_lon,
            zoom=map_zoom,
            markers=map_markers,
            height_px=420,
        )
        components.html(leaflet_html, height=430, scrolling=False)

        # ── Section 2: Industry & quantity (Max 50 strictly) ─────────────────
        st.divider()
        st.markdown(
            "<p style='font-size:0.82rem;font-weight:700;color:var(--ios-subtext);"
            "text-transform:uppercase;margin-bottom:12px;'>2. النشاط التجاري والكمية المطلوبة (الحد الأقصى 50 شخص مختلف)</p>",
            unsafe_allow_html=True
        )

        niche_col1, niche_col2 = st.columns([3, 1])
        with niche_col1:
            ind_mode = st.radio(
                "طريقة إدخال المجال:",
                ["قائمة المجالات المقترحة", "إدخال يدوي مخصص"],
                horizontal=True
            )
            if ind_mode == "قائمة المجالات المقترحة":
                industry = st.selectbox("المجال / النشاط التجاري:", INDUSTRY_PRESETS)
            else:
                industry = st.text_input(
                    "النشاط يدوياً:",
                    placeholder="مثال: عطور ومستحضرات تجميل، كافيهات ومطاعم..."
                )

        with niche_col2:
            st.write("")
            st.write("")
            limit = st.number_input(
                "العدد المطلوب (أقصى حد 50):",
                min_value=1,
                max_value=50,
                value=20,
                help="الحد الأقصى الصارم هو 50 شخص مختلف تماماً. يضمن النظام استبعاد أي شخص ظهر في أي بحث سابق."
            )
            # Enforce hard cap
            limit = min(50, max(1, int(limit)))

        # ── Section 3: WhatsApp Filter ────────────────────────────────────────
        st.divider()
        st.markdown(
            "<p style='font-size:0.82rem;font-weight:700;color:var(--ios-subtext);"
            "text-transform:uppercase;margin-bottom:12px;'>3. إعدادات البحث المباشر عبر Google Maps</p>",
            unsafe_allow_html=True
        )

        st.info("🗺️ يعمل هذا النظام عبر **Google Maps الحي** فقط — يفتح كل بطاقة تجارية ويجلب الرقم الحقيقي المسجل فيها.")

        # Always live, always Maps — only let user control WA filter
        use_live = True
        chosen_engine = "maps"

        wa_only = st.checkbox(
            "🟢 أرقام هواتف محمولة فقط (صالحة للواتساب — استبعاد الأرقام الأرضية 100%)",
            value=True,
            help="يستبعد الأرقام الثابتة/الأرضية ويُرجع فقط أرقام الموبايل القادرة على استقبال واتساب.",
        )


        # ── Message Template Preview Accordion ───────────────────────────────
        with st.expander("📝 قوالب رسائل WhatsApp حسب الدولة واللغة التلقائية", expanded=False):
            st.markdown(
                "<p style='font-size:12px;color:#888;'>"
                "النظام يتعرف تلقائياً على الدولة ويختار اللغة المناسبة لكل شخص:<br>"
                "• <b>الأمريكتين:</b> إنجليزية (English)<br>"
                "• <b>الدول العربية:</b> عربية (Arabic)<br>"
                "• <b>دول أخرى:</b> الفرنسية/الألمانية/الإسبانية/التركية إن توفرت أو الإنجليزية."
                "</p>",
                unsafe_allow_html=True
            )
            tpl_tabs = st.tabs(["🇸🇦 العربية", "🇺🇸 الإنجليزية", "🇫🇷 الفرنسية", "🇪🇸 الإسبانية", "🇩🇪 الألمانية", "🇹🇷 التركية"])
            with tpl_tabs[0]:
                custom_ar = st.text_area("قالب الرسالة العربية:", value=MULTILINGUAL_TEMPLATES["Arabic"], height=85, key="tpl_input_Arabic")
            with tpl_tabs[1]:
                custom_en = st.text_area("قالب الرسالة الإنجليزية (للأمريكتين ودولي):", value=MULTILINGUAL_TEMPLATES["English"], height=85, key="tpl_input_English")
            with tpl_tabs[2]:
                custom_fr = st.text_area("قالب الرسالة الفرنسية:", value=MULTILINGUAL_TEMPLATES["French"], height=85, key="tpl_input_French")
            with tpl_tabs[3]:
                custom_es = st.text_area("قالب الرسالة الإسبانية:", value=MULTILINGUAL_TEMPLATES["Spanish"], height=85, key="tpl_input_Spanish")
            with tpl_tabs[4]:
                custom_de = st.text_area("قالب الرسالة الألمانية:", value=MULTILINGUAL_TEMPLATES["German"], height=85, key="tpl_input_German")
            with tpl_tabs[5]:
                custom_tr = st.text_area("قالب الرسالة التركية:", value=MULTILINGUAL_TEMPLATES["Turkish"], height=85, key="tpl_input_Turkish")

            active_templates = {
                "Arabic": custom_ar,
                "English": custom_en,
                "French": custom_fr,
                "Spanish": custom_es,
                "German": custom_de,
                "Turkish": custom_tr,
            }

        st.write("")
        if st.button(
            f"🚀 بدء استخراج حتى {limit} عميل جديد مختلف تماماً",
            type="primary",
            use_container_width=True
        ):
            if not industry or not city or not country_name:
                st.error("يرجى تحديد الدولة والمدينة والنشاط التجاري للمتابعة.")
                return

            # Fetch all known phones from previous searches to guarantee ZERO duplicates
            existing_phones = db.get_all_known_phones()
            info_msg = f"قاعدة البيانات تحتوي على {len(existing_phones)} رقم سابق — سيتم استبعاد أي تشابه بالكامل."

            # ── Live Progress & ETA Timer ────────────────────────────────────
            import time as _t
            _start_time = _t.time()

            _prog_container = st.container()
            with _prog_container:
                _prog_bar = st.progress(0, text="⏳ جاري فتح خرائط Google بالسرعة الفائقة وبدء الفحص...")
                _timer_box = st.empty()

            def _on_lead_found(found: int, target: int, business_name: str = ""):
                now = _t.time()
                elapsed = now - _start_time
                pct = min(int((found / max(target, 1)) * 100), 99)
                rate = elapsed / found if found > 0 else 0
                remaining = (target - found) * rate if found > 0 else 0
                
                el_min, el_sec = divmod(int(elapsed), 60)
                rem_min, rem_sec = divmod(int(remaining), 60)
                
                el_text = f"{el_min}د {el_sec}ث" if el_min else f"{el_sec}ث"
                rem_text = f"{rem_min}د {rem_sec}ث" if rem_min else f"{rem_sec}ث"
                
                _prog_bar.progress(pct, text=f"⚡ تم استخراج: {found}/{target} عميل | جارٍ فحص: {business_name}")
                _timer_box.markdown(
                    f'''<div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 10px 16px; margin: 10px 0; display: flex; justify-content: space-between; align-items: center; font-family: sans-serif;">
                        <span style="font-size: 13px; color: #8e8e93;">⏱ الوقت المستغرق: <b style="color: #ffffff;">{el_text}</b></span>
                        <span style="font-size: 13px; color: #8e8e93;">⏳ متبقي تقريباً: <b style="color: #ffd60a;">{rem_text}</b></span>
                        <span style="font-size: 13px; color: #8e8e93;">⚡ السرعة: <b style="color: #30d158;">{rate:.1f} ث/عميل</b></span>
                    </div>''',
                    unsafe_allow_html=True
                )

            raw_leads = st.session_state.scraper.search_leads(
                industry=industry,
                city=city,
                country=country_name,
                country_code=country_code or "20",
                limit=limit,
                use_live_browser=use_live,
                whatsapp_only=wa_only,
                search_engine=chosen_engine,
                messenger=messenger,
                exclude_phones=existing_phones,
                progress_cb=_on_lead_found,
            )

            _total_time = _t.time() - _start_time
            _tot_min, _tot_sec = divmod(int(_total_time), 60)
            _tot_text = f"{_tot_min}د {_tot_sec}ث" if _tot_min else f"{_tot_sec}ث"
            # Show completion briefly then clear — don't keep progress bar visible
            _prog_bar.progress(100, text=f"✅ اكتمل الاستخراج بنجاح في غضون {_tot_text}!")
            _timer_box.markdown(
                f'<div style="background:rgba(48,209,88,0.1);border:1px solid rgba(48,209,88,0.3);'
                f'border-radius:12px;padding:10px 16px;margin:10px 0;text-align:center;font-family:sans-serif;">'
                f'<span style="color:#30d158;font-size:14px;font-weight:700;">✅ انتهى البحث في {_tot_text} — شوف النتائج تحت 👇</span>'
                f'</div>',
                unsafe_allow_html=True
            )

            if not raw_leads:
                _prog_bar.empty()
                _timer_box.empty()
                st.warning(
                    "لم يتم العثور على أرقام جديدة غير مكررة في هذا البحث. "
                    "يرجى تجربة مدينة أخرى أو نشاط آخر، أو اختيار 'البحث المشترك المزدوج'."
                )
                return

            lead_svc = LeadService(db)
            processed = []
            new_count = 0
            merged_count = 0

            for item in raw_leads:
                raw_p = item.get("phone", "")
                norm_p = normalize_phone(raw_p, default_country_code=country_code or "20")

                # Double-check against existing phones set
                if norm_p in existing_phones or raw_p in existing_phones:
                    merged_count += 1
                    continue

                # Auto-detect country, region, and target language
                geo = detect_country_and_language(
                    phone=norm_p,
                    country_name=country_name,
                    city=city,
                    country_code=country_code or "20"
                )
                target_lang = geo["language"]

                # Save to DB
                res = lead_svc.process_and_save_lead(
                    business_name=item.get("business_name", ""),
                    phone=norm_p,
                    address=item.get("address", f"{city}، {country_name}"),
                    website=item.get("website", ""),
                    industry=item.get("industry", industry),
                    city=item.get("city", city),
                    source=item.get("source", "google_maps"),
                    whatsapp_status=item.get("whatsapp_status", "UNKNOWN"),
                    country=country_name,
                    language=target_lang,
                )

                # STRICT DEDUPLICATION: If merged into a previous record, exclude completely!
                if res["was_merged"]:
                    merged_count += 1
                    continue

                new_count += 1
                existing_phones.add(norm_p)
                existing_phones.add(norm_p.lstrip("+"))

                # Generate personalized message in the detected language
                tpl_text = active_templates.get(target_lang, MULTILINGUAL_TEMPLATES.get(target_lang, MULTILINGUAL_TEMPLATES["English"]))
                pers_msg = OutreachService.build_personalized_message(
                    tpl_text,
                    business=res["cleaned"]["business_name"],
                    industry=industry,
                    city=city
                )

                processed.append({
                    "id": res["lead_id"],
                    "business_name": res["cleaned"]["business_name"],
                    "phone": res["cleaned"]["phone"],
                    "phone_validity": res["cleaned"]["phone_validity"],
                    "whatsapp_status": res["cleaned"]["whatsapp_status"],
                    "address": res["cleaned"]["address"],
                    "city": res["cleaned"]["city"],
                    "country": geo["country"],
                    "region": geo["region"],
                    "flag": geo["flag"],
                    "language": target_lang,
                    "score": res["score"],
                    "message": pers_msg,
                    "اسم النشاط": res["cleaned"]["business_name"],
                    "الهاتف": res["cleaned"]["phone"],
                    "حالة WhatsApp": res["cleaned"]["whatsapp_status"],
                    "الدولة": f"{geo['flag']} {geo['country']}",
                    "اللغة": target_lang,
                })

                if len(processed) >= limit:
                    break

            db.insert_search(f"{industry} ({country_name})", city, len(processed))
            st.session_state["last_search_results"] = processed
            st.session_state["last_search_industry"] = industry
            st.session_state["last_search_city"] = f"{city}، {country_name}"
            st.session_state["last_search_city_name"] = city
            st.session_state["last_search_country_info"] = country_info

            if processed:
                st.session_state["show_extracted_leads"] = True
                _prog_bar.empty()
                _timer_box.empty()
                st.session_state["search_success_msg"] = (
                    f"🎉 تم استخراج **{len(processed)}** شخص جديد ومختلف تماماً بنجاح! "
                    f"(تم استبعاد وتخطي {merged_count} مكرر من عمليات البحث السابقة). "
                    f"حد البحث: أقصى حد {limit} شخص."
                )
                st.rerun()
            else:
                _prog_bar.empty()
                _timer_box.empty()
                st.warning("كافة النتائج التي وُجدت كانت مكررة من عمليات بحث سابقة. جرب مدينة أخرى.")

    # ══════════════════════════════════════════════════════════════════════════
    # ── Section 4: WhatsApp Selection & Outreach Hub ─────────────────────────
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.get("search_success_msg"):
        st.success(st.session_state.pop("search_success_msg"))

    last_res = st.session_state.get("last_search_results", [])
    
    # If no results in session, try to load latest leads from database as fallback
    if not last_res:
        recent_db_leads = db.get_all_leads()
        if recent_db_leads:
            # Take last 50 leads
            recent_db_leads = recent_db_leads[:50]
            recovered = []
            for r in recent_db_leads:
                lead_id = r[0]
                b_name = r[1] or ""
                phone = r[2] or ""
                addr = r[3] or ""
                site = r[4] or ""
                ind = r[5] or ""
                cty = r[6] or ""
                score = r[8] or 0
                lang = r[10] or "Arabic"
                wa_st = r[13] if len(r) > 13 else "UNKNOWN"
                ph_val = r[14] if len(r) > 14 else "VALID"
                geo = detect_country_and_language(phone=phone, city=cty)
                
                tpl_txt = MULTILINGUAL_TEMPLATES.get(lang, MULTILINGUAL_TEMPLATES.get("Arabic"))
                msg = OutreachService.build_personalized_message(
                    tpl_txt,
                    business=b_name,
                    industry=ind,
                    city=cty
                )
                recovered.append({
                    "id": lead_id,
                    "business_name": b_name,
                    "phone": phone,
                    "phone_validity": ph_val,
                    "whatsapp_status": wa_st,
                    "address": addr,
                    "city": cty,
                    "country": geo.get("country", ""),
                    "region": geo.get("region", ""),
                    "flag": geo.get("flag", "🌐"),
                    "language": lang,
                    "score": score,
                    "message": msg,
                    "اسم النشاط": b_name,
                    "الهاتف": phone,
                    "حالة WhatsApp": wa_st,
                    "الدولة": f"{geo.get('flag','🌐')} {geo.get('country','')}",
                    "اللغة": lang,
                })
            last_res = recovered
            st.session_state["last_search_results"] = recovered

    if last_res:
        st.divider()
        # Toggle / Show button for results
        show_leads = st.session_state.get("show_extracted_leads", True)
        
        btn_col1, btn_col2 = st.columns([3, 1])
        with btn_col1:
            btn_label = f"👥 إخفاء العملاء المستخرجين ({len(last_res)})" if show_leads else f"👥 إظهار العملاء المستخرجين ({len(last_res)} عميل)"
            if st.button(btn_label, type="primary" if not show_leads else "secondary", use_container_width=True, key="btn_toggle_show_leads"):
                st.session_state["show_extracted_leads"] = not show_leads
                st.rerun()
        with btn_col2:
            st.caption(f"إجمالي المتاح: {len(last_res)} عميل")

    if last_res and st.session_state.get("show_extracted_leads", True):
        st.divider()
        section_label(f"📲 نتائج البحث والتواصل المباشر عبر WhatsApp ({len(last_res)} شخص مختلف)")

        st.markdown(
            "<p style='font-size:13px;color:#888;margin-bottom:14px'>"
            "تم تحديد لغة كل شخص ودولته تلقائياً، وتجهيز رسالة مخصصة باسم مشروعه ومدينته. "
            "اختر الشخص وتواصل معه مباشرة عبر WhatsApp."
            "</p>",
            unsafe_allow_html=True
        )

        # Language distribution pills
        lang_counts = {}
        for r in last_res:
            l = r.get("language", "English")
            lang_counts[l] = lang_counts.get(l, 0) + 1

        lang_badges_html = " ".join([
            f"<span style='background:#1c1c1e;border:1px solid rgba(255,255,255,0.12);padding:4px 12px;border-radius:99px;font-size:12px;color:#f0f0f0;margin-left:6px;'>"
            f"{l}: <b>{cnt}</b></span>"
            for l, cnt in lang_counts.items()
        ])
        st.markdown(f"<div style='margin-bottom:14px;'>{lang_badges_html}</div>", unsafe_allow_html=True)

        # ── Bulk selection controls ──────────────────────────────────────────
        sel_col1, sel_col2, sel_col3 = st.columns([1.5, 2, 2])
        with sel_col1:
            select_all = st.checkbox("تحديد الكل", value=True, key="select_all_leads")

        selected_leads = []
        for idx, item in enumerate(last_res):
            default_val = select_all
            lead_chk_key = f"chk_lead_{item['id']}_{idx}"
            if lead_chk_key not in st.session_state:
                st.session_state[lead_chk_key] = default_val
            elif select_all != st.session_state.get("_prev_select_all", True):
                st.session_state[lead_chk_key] = select_all

        st.session_state["_prev_select_all"] = select_all

        with sel_col2:
            current_selected = [item for idx, item in enumerate(last_res) if st.session_state.get(f"chk_lead_{item['id']}_{idx}", True)]
            st.markdown(f"<p style='font-size:13px;padding-top:6px;color:#30d158;font-weight:600;'>المحدد للتواصل: {len(current_selected)} من {len(last_res)}</p>", unsafe_allow_html=True)

        with sel_col3:
            if wa_connected:
                st.caption("🟢 WhatsApp Web متصل — يمكنك الإرسال الآلي المباشر")
            else:
                st.caption("📱 يمكنك فتح الروابط مباشرة (wa.me) أو ربط WhatsApp في الإعدادات")

        # Bulk automated sender
        if current_selected and wa_connected:
            with st.expander(f"🚀 إرسال WhatsApp آلي بالمتصفح للعملاء المحددين ({len(current_selected)} عميل)", expanded=False):
                st.write("سيقوم النظام بإرسال الرسائل المخصصة عبر WhatsApp Web مع فواصل زمنية بشرية لحماية الحساب.")
                if st.button("بدء الإرسال الآلي الآن", type="primary", key="btn_bulk_wa"):
                    prog_bar = st.progress(0, text="جاري بدء الإرسال...")
                    sent_ok = 0
                    sent_fail = 0
                    for s_idx, s_lead in enumerate(current_selected):
                        pct = int((s_idx + 1) / len(current_selected) * 100)
                        prog_bar.progress(pct, text=f"جاري الإرسال لـ {s_lead['business_name']} ({s_lead['phone']})...")
                        ok, detail = messenger.send_via_playwright(
                            lead_id=s_lead["id"],
                            phone=s_lead["phone"],
                            message=s_lead["message"]
                        )
                        if ok:
                            sent_ok += 1
                            db.update_lead_status(s_lead["id"], STATUS_CONTACTED)
                        else:
                            sent_fail += 1
                        import time
                        time.sleep(2)
                    prog_bar.progress(100, text=f"اكتمل الإرسال: {sent_ok} بنجاح، {sent_fail} تعذر")
                    st.success(f"✅ تم الانتهاء: تم إرسال {sent_ok} رسالة بنجاح.")
                    st.rerun()

        # ── Individual Lead Cards ─────────────────────────────────────────────
        st.write("")
        for idx, item in enumerate(last_res):
            lid = item["id"]
            phone = item["phone"]
            b_name = item["business_name"]
            flag = item.get("flag", "🌐")
            country_lbl = item.get("country", "")
            lang_lbl = item.get("language", "English")
            msg = item.get("message", "")

            with st.container(border=True):
                c_chk, c_info, c_msg, c_act = st.columns([0.4, 2.8, 4.2, 2.6])

                with c_chk:
                    st.write("")
                    st.checkbox(
                        "",
                        key=f"chk_lead_{lid}_{idx}",
                        label_visibility="collapsed"
                    )

                with c_info:
                    st.markdown(f"**#{idx+1} {escape(b_name)}**")
                    st.caption(f"{flag} {country_lbl} • {escape(item.get('city', ''))}")
                    st.markdown(f"`{phone}`")
                    # Language pill
                    lang_color = "#30d158" if lang_lbl == "Arabic" else "#0a84ff"
                    st.markdown(
                        f"<span style='font-size:11px;font-weight:700;color:{lang_color};"
                        f"background:{lang_color}22;padding:2px 8px;border-radius:6px;'>"
                        f"لغة الرسالة: {lang_lbl}</span>",
                        unsafe_allow_html=True
                    )

                with c_msg:
                    edited_msg = st.text_area(
                        "نص الرسالة المجهزة:",
                        value=msg,
                        height=90,
                        key=f"msg_area_{lid}_{idx}",
                        label_visibility="collapsed"
                    )

                with c_act:
                    st.write("")
                    raw_digits = phone.replace("+", "").strip()
                    encoded_msg = urllib.parse.quote(edited_msg)
                    wa_url = f"https://wa.me/{raw_digits}?text={encoded_msg}"

                    # 1. Direct WhatsApp Link
                    st.link_button(
                        "📲 فتح WhatsApp",
                        wa_url,
                        use_container_width=True,
                        type="primary"
                    )

                    # 2. Automated Send via Playwright
                    if wa_connected:
                        if st.button("🤖 إرسال آلي", key=f"auto_btn_{lid}_{idx}", use_container_width=True):
                            with st.spinner("جاري الإرسال عبر المتصفح..."):
                                ok, detail = messenger.send_via_playwright(
                                    lead_id=lid,
                                    phone=phone,
                                    message=edited_msg
                                )
                            if ok:
                                db.update_lead_status(lid, STATUS_CONTACTED)
                                st.success("تم الإرسال بنجاح ✅")
                                st.rerun()
                            else:
                                st.error(detail)

                    # 3. Mark contacted button
                    if st.button("✅ تم التواصل", key=f"mark_c_{lid}_{idx}", use_container_width=True):
                        db.update_lead_status(lid, STATUS_CONTACTED)
                        st.success("تم تحديث الحالة إلى CONTACTED.")
                        st.rerun()
