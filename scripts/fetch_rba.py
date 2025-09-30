#!/usr/bin/env python3
import os, sys, json, datetime, urllib.request, xml.etree.ElementTree as ET

RBA_URL = os.environ.get(
    "RBA_XML_URL",
    "https://www.rba.gov.au/rss/rss-cb-exchange-rates.xml"
)
OUT_LATEST = os.environ.get("OUT_LATEST", "public/rates-latest.json")
OUT_HISTORY = os.environ.get("OUT_HISTORY", "public/history.json")

# Namespaces from the RBA feed
NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rba": "https://www.rba.gov.au/statistics/frequency/exchange-rates.html",
    "cb": "http://www.cbwiki.net/wiki/index.php/Specification_1.2/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "rss": "http://purl.org/rss/1.0/"
}

def fetch_xml(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read()

def parse_rates(xml_bytes: bytes):
    root = ET.fromstring(xml_bytes)
    items = root.findall("rss:item", NS)
    # Output structure
    out = {
        "source": "RBA 4pm",
        "source_url": RBA_URL,
        "as_at_aest": None,       # ISO timestamp from dc:date
        "date": None,             # YYYY-MM-DD from cb:period
        "base": "AUD",
        "rates": []               # list of {code, per_aud, aud_per_unit, decimals, title}
    }

    # capture feed-level timestamp if present
    ch = root.find("rss:channel", NS)
    if ch is not None:
        dcdate = ch.find("dc:date", NS)
        if dcdate is not None and dcdate.text:
            out["as_at_aest"] = dcdate.text

    for it in items:
        # currencies live in cb:statistics/cb:exchangeRate
        exch = it.find("cb:statistics/cb:exchangeRate", NS)
        if exch is None: 
            continue

        tgt = exch.find("cb:targetCurrency", NS)
        obs = exch.find("cb:observation", NS)
        period = exch.find("cb:observationPeriod/cb:period", NS)

        if not (tgt is not None and obs is not None):
            continue

        code = (tgt.text or "").strip()
        # Skip TWI pseudo currency marked XXX
        if code == "XXX":
            continue

        val_el = obs.find("cb:value", NS)
        dec_el = obs.find("cb:decimals", NS)
        if val_el is None or not val_el.text:
            continue

        try:
            per_aud = float(val_el.text)  # target per 1 AUD
        except ValueError:
            continue

        aud_per_unit = None
        if per_aud != 0:
            aud_per_unit = 1.0 / per_aud

        decimals = None
        if dec_el is not None and dec_el.text and dec_el.text.isdigit():
            decimals = int(dec_el.text)

        title = it.find("rss:title", NS)
        out["rates"].append({
            "code": code,
            "per_aud": per_aud,
            "aud_per_unit": aud_per_unit,
            "decimals": decimals,
            "title": title.text if title is not None else ""
        })

        if out["date"] is None and period is not None and period.text:
            out["date"] = period.text

    # sort by code for stability
    out["rates"].sort(key=lambda r: r["code"])
    return out

def load_history(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def main():
    xml = fetch_xml(RBA_URL)
    today = parse_rates(xml)
    if not today["rates"]:
        print("No rates parsed; abort.", file=sys.stderr)
        sys.exit(1)

    # Write latest
    save_json(OUT_LATEST, today)

    # Append/replace same-date entry in history
    hist = load_history(OUT_HISTORY)
    # Deduplicate by date
    hist = [h for h in hist if h.get("date") != today["date"]]
    hist.append(today)
    # sort history by date ascending
    hist.sort(key=lambda h: (h.get("date") or ""))
    save_json(OUT_HISTORY, hist)

    print(f"Wrote {OUT_LATEST} and {OUT_HISTORY} for date {today['date']} with {len(today['rates'])} currencies.")

if __name__ == "__main__":
    main()
