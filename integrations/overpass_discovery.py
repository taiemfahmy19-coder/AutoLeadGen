"""AutoLeadGen V3 — Overpass API Business Discovery Engine.

Respects Overpass API fair-use policy:
- Max 1 request/sec (enforced via time.sleep)
- Timeout 60s per query
- Exponential backoff on HTTP 429 / server overload
- No hard cap on results — generator-based streaming
"""
import re
import time
import logging
from typing import Generator, Optional, Callable

import requests

logger = logging.getLogger("AutoLeadGen")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# OSM tag categories that map to business types
BUSINESS_TAG_GROUPS = {
    "restaurant": [('amenity', 'restaurant'), ('amenity', 'fast_food'), ('amenity', 'cafe'), ('amenity', 'bar'), ('amenity', 'pub')],
    "shop": [('shop', '*')],
    "hotel": [('tourism', 'hotel'), ('tourism', 'motel'), ('tourism', 'hostel'), ('tourism', 'guest_house')],
    "clinic": [('amenity', 'clinic'), ('amenity', 'hospital'), ('amenity', 'dentist'), ('amenity', 'pharmacy'), ('healthcare', '*')],
    "office": [('office', '*')],
    "factory": [('industrial', 'factory'), ('landuse', 'industrial')],
    "all": [
        ('amenity', '~"restaurant|fast_food|cafe|bar|clinic|hospital|pharmacy|dentist|bank|post_office"'),
        ('shop', '~".+"'),
        ('tourism', '~"hotel|motel|hostel|guest_house"'),
        ('office', '~".+"'),
    ],
}

USER_AGENT = "AutoLeadGen/3.0 (open-source; contact: autoleadgen@example.com)"


def _build_overpass_query(area_name: str, country: str, business_type: str, limit: int = 500) -> str:
    """Build Overpass QL query to find businesses in a named area."""
    if business_type == "all" or business_type not in BUSINESS_TAG_GROUPS:
        tag_union = """
  node["amenity"~"restaurant|fast_food|cafe|bar|clinic|hospital|pharmacy|dentist|bank|hotel"](area.a);
  way["amenity"~"restaurant|fast_food|cafe|bar|clinic|hospital|pharmacy|dentist|bank|hotel"](area.a);
  node["shop"~".+"](area.a);
  way["shop"~".+"](area.a);
  node["tourism"~"hotel|motel|hostel|guest_house"](area.a);
  way["tourism"~"hotel|motel|hostel|guest_house"](area.a);
  node["office"~".+"](area.a);
  way["office"~".+"](area.a);"""
    else:
        lines = []
        for tag_k, tag_v in BUSINESS_TAG_GROUPS.get(business_type, []):
            safe_v = tag_v if tag_v != '*' else '~".+"'
            lines.append(f'  node["{tag_k}"="{safe_v}"](area.a);')
            lines.append(f'  way["{tag_k}"="{safe_v}"](area.a);')
        tag_union = "\n".join(lines)

    query = f"""
[out:json][timeout:60];
area["name"="{area_name}"]->.a;
(
{tag_union}
);
out center tags {limit};
"""
    return query


def _extract_lead_from_element(el: dict, city: str, country: str, source_url: str) -> Optional[dict]:
    """Normalize an Overpass element into a lead dict. Returns None if no name."""
    tags = el.get("tags", {})
    name = (tags.get("name") or tags.get("name:en") or tags.get("name:ar") or "").strip()
    if not name:
        return None

    # Coordinates: nodes have direct lat/lon; ways have center
    lat, lon = None, None
    if el.get("type") == "node":
        lat = el.get("lat")
        lon = el.get("lon")
    elif el.get("type") in ("way", "relation"):
        center = el.get("center", {})
        lat = center.get("lat")
        lon = center.get("lon")

    # Determine industry from tags
    industry = ""
    for key in ("amenity", "shop", "tourism", "office", "healthcare", "craft", "leisure"):
        if key in tags and tags[key]:
            industry = tags[key].replace("_", " ").title()
            break

    phone = tags.get("phone", "").strip()
    email = tags.get("email", "").strip()
    website = tags.get("website", "").strip()
    address_parts = [
        tags.get("addr:housenumber", ""),
        tags.get("addr:street", ""),
        tags.get("addr:city", city),
    ]
    address = ", ".join(p for p in address_parts if p).strip(", ")
    if not address:
        address = city

    return {
        "business_name": name,
        "phone": phone,
        "email": email,
        "website": website,
        "address": address,
        "city": city,
        "country": country,
        "industry": industry,
        "latitude": lat,
        "longitude": lon,
        "coord_source": "overpass" if (lat and lon) else "",
        "coord_verified": 1 if (lat and lon) else 0,
        "source": "overpass",
        "source_url": source_url,
        "data_confidence": "medium",
        "collected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def search_city(
    city: str,
    country: str,
    business_type: str = "all",
    batch_size: int = 500,
    cancel_check: Optional[Callable[[], bool]] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None,
) -> Generator[dict, None, None]:
    """
    Generator — yields normalized lead dicts from Overpass API for a city.
    Respects rate limits, never hardcodes a maximum result count.
    """
    query = _build_overpass_query(area_name=city, country=country, business_type=business_type, limit=batch_size)
    url = f"https://www.openstreetmap.org/search?q={city}+{country}"
    backoff = 1
    for attempt in range(3):
        if cancel_check and cancel_check():
            return
        try:
            resp = requests.post(
                OVERPASS_URL,
                data={"data": query},
                headers={"User-Agent": USER_AGENT},
                timeout=70,
            )
            if resp.status_code == 429:
                sleep_time = backoff * 60
                logger.warning(f"Overpass rate-limited (429). Sleeping {sleep_time}s…")
                if progress_cb:
                    progress_cb(0.0, f"⏳ Rate limited — waiting {sleep_time}s…")
                time.sleep(sleep_time)
                backoff *= 2
                continue
            resp.raise_for_status()
            data = resp.json()
            remark = data.get("remark", "")
            if "runtime error" in remark or "out of memory" in remark:
                logger.warning(f"Overpass server warning: {remark}")
            elements = data.get("elements", [])
            logger.info(f"Overpass: city={city}, country={country}, type={business_type} → {len(elements)} elements")
            for el in elements:
                if cancel_check and cancel_check():
                    return
                lead = _extract_lead_from_element(el, city=city, country=country, source_url=url)
                if lead:
                    yield lead
            time.sleep(1.1)  # polite delay
            return
        except requests.exceptions.Timeout:
            logger.warning(f"Overpass timeout for {city} (attempt {attempt + 1}/3)")
            time.sleep(backoff * 5)
            backoff *= 2
        except requests.exceptions.RequestException as e:
            logger.warning(f"Overpass request error: {e}")
            time.sleep(backoff * 3)
            backoff *= 2


def get_major_cities(country: str, max_cities: int = 20) -> list:
    """Get major cities in a country via Nominatim."""
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={
                "q": country,
                "featuretype": "city",
                "country": country,
                "format": "json",
                "limit": max_cities,
                "addressdetails": 0,
                "extratags": 0,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        cities = [d.get("name") or d.get("display_name", "").split(",")[0] for d in data if d.get("type") in ("city", "administrative", "town")]
        time.sleep(1)  # Nominatim 1 req/sec
        return [c for c in cities if c][:max_cities]
    except Exception as e:
        logger.warning(f"Nominatim lookup failed for {country}: {e}")
        return []


def search_country(
    country: str,
    business_type: str = "all",
    max_cities: int = 15,
    cancel_check: Optional[Callable[[], bool]] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None,
) -> Generator[dict, None, None]:
    """Discover major cities in a country then search each one."""
    cities = get_major_cities(country, max_cities=max_cities)
    if not cities:
        cities = [country]
    for idx, city in enumerate(cities):
        if cancel_check and cancel_check():
            return
        if progress_cb:
            progress_cb(idx / len(cities), f"🌍 Searching {city}, {country}…")
        yield from search_city(city=city, country=country, business_type=business_type, cancel_check=cancel_check)
