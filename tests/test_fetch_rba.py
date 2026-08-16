import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import fetch_rba  # noqa: E402

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:rss="http://purl.org/rss/1.0/"
         xmlns:dc="http://purl.org/dc/elements/1.1/"
         xmlns:cb="http://www.cbwiki.net/wiki/index.php/Specification_1.2/">
  <rss:channel>
    <dc:date>2026-08-14T16:00:00+10:00</dc:date>
  </rss:channel>
  <rss:item>
    <rss:title>United States dollar</rss:title>
    <cb:statistics>
      <cb:exchangeRate>
        <cb:targetCurrency>USD</cb:targetCurrency>
        <cb:observationPeriod>
          <cb:period>2026-08-14</cb:period>
        </cb:observationPeriod>
        <cb:observation>
          <cb:value>0.6500</cb:value>
          <cb:decimals>4</cb:decimals>
        </cb:observation>
      </cb:exchangeRate>
    </cb:statistics>
  </rss:item>
  <rss:item>
    <rss:title>Trade Weighted Index</rss:title>
    <cb:statistics>
      <cb:exchangeRate>
        <cb:targetCurrency>XXX</cb:targetCurrency>
        <cb:observationPeriod>
          <cb:period>2026-08-14</cb:period>
        </cb:observationPeriod>
        <cb:observation>
          <cb:value>60.0</cb:value>
          <cb:decimals>1</cb:decimals>
        </cb:observation>
      </cb:exchangeRate>
    </cb:statistics>
  </rss:item>
  <rss:item>
    <rss:title>Japanese yen</rss:title>
    <cb:statistics>
      <cb:exchangeRate>
        <cb:targetCurrency>JPY</cb:targetCurrency>
        <cb:observationPeriod>
          <cb:period>2026-08-14</cb:period>
        </cb:observationPeriod>
        <cb:observation>
          <cb:value>96.50</cb:value>
          <cb:decimals>2</cb:decimals>
        </cb:observation>
      </cb:exchangeRate>
    </cb:statistics>
  </rss:item>
</rdf:RDF>
"""


class ParseRatesTests(unittest.TestCase):
    def test_parses_rates_skips_twi_and_sorts_by_code(self):
        out = fetch_rba.parse_rates(SAMPLE_XML.encode("utf-8"))

        self.assertEqual(out["date"], "2026-08-14")
        self.assertEqual(out["as_at_aest"], "2026-08-14T16:00:00+10:00")
        self.assertEqual([r["code"] for r in out["rates"]], ["JPY", "USD"])

    def test_computes_aud_per_unit_as_inverse_of_per_aud(self):
        out = fetch_rba.parse_rates(SAMPLE_XML.encode("utf-8"))
        usd = next(r for r in out["rates"] if r["code"] == "USD")

        self.assertAlmostEqual(usd["per_aud"], 0.65)
        self.assertAlmostEqual(usd["aud_per_unit"], 1 / 0.65)
        self.assertEqual(usd["decimals"], 4)
        self.assertEqual(usd["title"], "United States dollar")

    def test_skips_zero_rate_without_dividing_by_zero(self):
        xml = SAMPLE_XML.replace("<cb:value>0.6500</cb:value>", "<cb:value>0</cb:value>")
        out = fetch_rba.parse_rates(xml.encode("utf-8"))
        usd = next(r for r in out["rates"] if r["code"] == "USD")

        self.assertEqual(usd["per_aud"], 0.0)
        self.assertIsNone(usd["aud_per_unit"])


class UpdateHistoryTests(unittest.TestCase):
    def test_appends_new_date(self):
        history = [{"date": "2026-08-13", "rates": []}]
        today = {"date": "2026-08-14", "rates": []}

        result = fetch_rba.update_history(history, today)

        self.assertEqual([h["date"] for h in result], ["2026-08-13", "2026-08-14"])

    def test_replaces_existing_entry_for_same_date(self):
        history = [{"date": "2026-08-14", "rates": [{"code": "OLD"}]}]
        today = {"date": "2026-08-14", "rates": [{"code": "NEW"}]}

        result = fetch_rba.update_history(history, today)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["rates"][0]["code"], "NEW")

    def test_sorts_by_date_ascending(self):
        history = [{"date": "2026-08-15", "rates": []}, {"date": "2026-08-13", "rates": []}]
        today = {"date": "2026-08-14", "rates": []}

        result = fetch_rba.update_history(history, today)

        self.assertEqual([h["date"] for h in result], ["2026-08-13", "2026-08-14", "2026-08-15"])


if __name__ == "__main__":
    unittest.main()
