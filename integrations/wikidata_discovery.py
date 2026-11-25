"""AutoLeadGen V3 — Wikidata SPARQL Business Discovery Engine.

Endpoint: https://query.wikidata.org/sparql
Uses Wikidata property:
- P131: located in administrative entity
- P625: coordinate location (real GPS)
- P856: website
- P18: image (optional)
"""
import time
import logging
from typing import Generator, Optional, Callable

import requests

logger = logging.getLogger("AutoLeadGen")

SPARQL_URL = "https://query.wikidata.org/sparql"
USER_AGENT = "AutoLeadGen/3.0 (open-source)"

# Wikidata QIDs for countries — extend as needed
COUNTRY_QIDS: dict = {
    "Egypt": "Q79",
    "Saudi Arabia": "Q851",
    "UAE": "Q878",
    "Jordan": "Q810",
    "Kuwait": "Q817",
    "Qatar": "Q846",
    "Bahrain": "Q398",
    "Oman": "Q842",
    "Lebanon": "Q822",
    "Iraq": "Q796",
    "Syria": "Q858",
    "Libya": "Q1016",
    "Tunisia": "Q948",
    "Algeria": "Q262",
    "Morocco": "Q1028",
    "USA": "Q30",
    "United Kingdom": "Q145",
    "Germany": "Q183",
    "France": "Q142",
    "Italy": "Q38",
    "Spain": "Q29",
    "Turkey": "Q43",
    "India": "Q668",
    "China": "Q148",
    "Japan": "Q17",
    "Brazil": "Q155",
    "Canada": "Q16",
    "Australia": "Q408",
    "Russia": "Q159",
    "South Africa": "Q258",
    "Nigeria": "Q1033",
    "Kenya": "Q114",
}

SPARQL_TEMPLATE = """
SELECT DISTINCT ?item ?name ?website ?lat ?lon WHERE {{
  ?item wdt:P131 wd:{country_qid} .
  ?item wdt:P856 ?website .
  ?item wdt:P625 ?coord .
  ?item rdfs:label ?name FILTER (lang(?name) IN ("en", "ar", "fr", "de")) .
  BIND(geof:latitude(?coord) AS ?lat) .
  BIND(geof:longitude(?coord) AS ?lon) .
}}
LIMIT {limit}
OFFSET {offset}
"""


def search_businesses(
    country: str,
    limit: int = 500,
    cancel_check: Optional[Callable[[], bool]] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None,
) -> Generator[dict, None, None]:
    """
    Generator that yields normalized lead dicts from Wikidata SPARQL.
    Real GPS from P625 — only businesses with website + coordinates.
    Paginated: runs multiple queries with OFFSET until no more results.
    """
    qid = COUNTRY_QIDS.get(country)
    if not qid:
        logger.warning(f"Wikidata: No QID for country '{country}'. Skipping.")
        return

    offset = 0
    total_yielded = 0
    while True:
        if cancel_check and cancel_check():
            return

        sparql = SPARQL_TEMPLATE.format(country_qid=qid, limit=limit, offset=offset)
        try:
            resp = requests.get(
                SPARQL_URL,
                params={"query": sparql, "format": "json"},
                headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"},
                timeout=45,
            )
            if resp.status_code == 429:
                logger.warning("Wikidata rate-limited (429). Sleeping 60s…")
                if progress_cb:
                    progress_cb(0.0, "⏳ Wikidata rate limited, waiting 60s…")
                time.sleep(60)
                continue
            resp.raise_for_status()
            data = resp.json()
            bindings = data.get("results", {}).get("bindings", [])
            if not bindings:
                break

            for b in bindings:
                if cancel_check and cancel_check():
                    return
                name = b.get("name", {}).get("value", "").strip()
                if not name:
                    continue
                lat_raw = b.get("lat", {}).get("value", "")
                lon_raw = b.get("lon", {}).get("value", "")
                try:
                    lat = float(lat_raw) if lat_raw else None
                    lon = float(lon_raw) if lon_raw else None
                except ValueError:
                    lat, lon = None, None

                website = b.get("website", {}).get("value", "").strip()
                item_url = b.get("item", {}).get("value", "")

                yield {
                    "business_name": name,
                    "phone": "",
                    "email": "",
                    "website": website,
                    "address": country,
                    "city": "",
                    "country": country,
                    "industry": "Business",
                    "latitude": lat,
                    "longitude": lon,
                    "coord_source": "wikidata" if lat else "",
                    "coord_verified": 1 if lat else 0,
                    "source": "wikidata",
                    "source_url": item_url,
                    "data_confidence": "high" if (lat and website) else "medium",
                    "collected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                total_yielded += 1

            if len(bindings) < limit:
                break
            offset += limit
            time.sleep(2)  # Wikidata polite delay
            if progress_cb:
                progress_cb(0.5, f"🌐 Wikidata {country}: {total_yielded} businesses so far…")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Wikidata request error: {e}")
            time.sleep(5)
            break

    logger.info(f"Wikidata: {country} → {total_yielded} total businesses yielded")
