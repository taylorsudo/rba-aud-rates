#!/usr/bin/env python3
"""Fetch the RBA exchange rate feed and update the latest/history JSON files."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Optional

RBA_URL = os.environ.get(
    "RBA_XML_URL",
    "https://www.rba.gov.au/rss/rss-cb-exchange-rates.xml"
)
OUT_LATEST = os.environ.get("OUT_LATEST", "public/rates-latest.json")
OUT_HISTORY = os.environ.get("OUT_HISTORY", "public/history.json")
REQUEST_TIMEOUT = 30

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
    request = urllib.request.Request(url, headers={"User-Agent": "rba-aud-rates/1.0"})
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return response.read()


def _parse_rate_item(item: ET.Element) -> Optional[dict[str, Any]]:
    """Parse a single <item> into a rate dict, or None if it isn't a usable rate."""
    exch = item.find("cb:statistics/cb:exchangeRate", NS)
    if exch is None:
        return None

    target = exch.find("cb:targetCurrency", NS)
    observation = exch.find("cb:observation", NS)
    if target is None or observation is None:
        return None

    code = (target.text or "").strip()
    if code == "XXX":  # RBA's TWI pseudo-currency, not a real exchange rate
        return None

    value_el = observation.find("cb:value", NS)
    if value_el is None or not value_el.text:
        return None

    try:
        per_aud = float(value_el.text)  # target currency units per 1 AUD
    except ValueError:
        return None

    decimals_el = observation.find("cb:decimals", NS)
    decimals = (
        int(decimals_el.text)
        if decimals_el is not None and decimals_el.text and decimals_el.text.isdigit()
        else None
    )

    title = item.find("rss:title", NS)
    period = exch.find("cb:observationPeriod/cb:period", NS)

    return {
        "code": code,
        "per_aud": per_aud,
        "aud_per_unit": (1.0 / per_aud) if per_aud else None,
        "decimals": decimals,
        "title": title.text if title is not None else "",
        "period": period.text if period is not None and period.text else None,
    }


def parse_rates(xml_bytes: bytes) -> dict[str, Any]:
    root = ET.fromstring(xml_bytes)

    out: dict[str, Any] = {
        "source": "RBA 4pm",
        "source_url": RBA_URL,
        "as_at_aest": None,       # ISO timestamp from dc:date
        "date": None,             # YYYY-MM-DD from cb:period
        "base": "AUD",
        "rates": []               # list of {code, per_aud, aud_per_unit, decimals, title}
    }

    # capture feed-level timestamp if present
    channel = root.find("rss:channel", NS)
    if channel is not None:
        dc_date = channel.find("dc:date", NS)
        if dc_date is not None and dc_date.text:
            out["as_at_aest"] = dc_date.text

    for item in root.findall("rss:item", NS):
        parsed = _parse_rate_item(item)
        if parsed is None:
            continue

        period = parsed.pop("period")
        out["rates"].append(parsed)
        if out["date"] is None and period:
            out["date"] = period

    # sort by code for stability
    out["rates"].sort(key=lambda r: r["code"])
    return out


def load_history(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def update_history(history: list[dict[str, Any]], today: dict[str, Any]) -> list[dict[str, Any]]:
    """Return history with any existing entry for today's date replaced, sorted by date."""
    history = [h for h in history if h.get("date") != today["date"]]
    history.append(today)
    history.sort(key=lambda h: h.get("date") or "")
    return history


def main() -> None:
    try:
        xml_bytes = fetch_xml(RBA_URL)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"Failed to fetch RBA feed: {exc}", file=sys.stderr)
        sys.exit(1)

    today = parse_rates(xml_bytes)
    if not today["rates"]:
        print("No rates parsed; abort.", file=sys.stderr)
        sys.exit(1)

    save_json(OUT_LATEST, today)

    history = update_history(load_history(OUT_HISTORY), today)
    save_json(OUT_HISTORY, history)

    print(f"Wrote {OUT_LATEST} and {OUT_HISTORY} for date {today['date']} with {len(today['rates'])} currencies.")


if __name__ == "__main__":
    main()
