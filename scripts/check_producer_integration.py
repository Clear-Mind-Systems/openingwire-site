#!/usr/bin/env python3
"""Render the real scraper into disposable copies of the real site.

Run with the scraper's test environment:
  python scripts/check_producer_integration.py --producer-root ../scraper-business

All records and clocks below are labelled synthetic fixtures. The producer uses
an in-memory database; sockets are blocked. Neither input checkout is written.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import hashlib
import importlib
import io
import json
from pathlib import Path
import shutil
import socket
import sqlite3
import sys
import tempfile
import unittest

from check_site import Document, START, END, FRESH_START, FRESH_END, sample
import check_site

NOW = datetime(2026, 10, 17, 20, tzinfo=timezone.utc)
STATES = (
    ("fresh", "2026-10-17T19:00:00Z"),
    ("stale", "2026-10-04T13:27:46Z"),
    ("missing", None),
    ("invalid", "2026-10-18T19:00:00Z"),
)


def shell(source):
    for start, end in ((START, END), (FRESH_START, FRESH_END)):
        before, rest = source.split(start)
        _, after = rest.split(end)
        source = before + start + end + after
    return source


def files(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*")
            if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts}


class ProducerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = Path(__file__).resolve().parents[1]
        cls.source_before = files(cls.site)
        cls.producer = importlib.import_module("pipeline.seo_pages")
        cls.schema = importlib.import_module("pipeline.db").SCHEMA
        cls.cfg = importlib.import_module("pipeline.config").load_config()
        cls.fingerprint = staticmethod(importlib.import_module("pipeline.normalize").fingerprint)

    @classmethod
    def tearDownClass(cls):
        if cls.source_before != files(cls.site):
            raise AssertionError("Integration tests modified the site checkout")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="openingwire-paired-")
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name) / "site"
        shutil.copytree(self.site, self.target,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(self.schema)
        self.addCleanup(self.conn.close)

    def seed(self, stamp):
        if stamp is not None:
            for job in ("pending_applications", "issued_licenses", "pending_refresh", "ingest"):
                self.conn.execute(
                    "INSERT INTO run_log(job,started_at,finished_at,status) VALUES(?,?,?, 'ok')",
                    (job, stamp, stamp))
        for metro in ("houston", "dfw", "austin", "san-antonio"):
            for stage in ("newly-licensed", "application-pending"):
                source_id = "synthetic-" + metro + "-" + stage
                licensed = stage == "newly-licensed"
                payload = {
                    "address": f"{len(metro)} {metro} {stage} Fixture St",
                    "city": "Fixture <City>", "owner": "SYNTHETIC Operator " + metro,
                    "state": "TX", "country": "United States",
                    "trade_name": "SYNTHETIC <Cafe> & Long Name " + metro,
                    "license_id" if licensed else "application_id": source_id,
                    "license_status" if licensed else "applicationstatus": "Active",
                }
                self.conn.execute(
                    "INSERT INTO venues(fingerprint,trade_name,category,stage,metro,city,"
                    "issue_date,submission_date,first_seen,needs_review,address,owner,license_id) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (self.fingerprint(payload["address"], payload["city"], payload["owner"]),
                     payload["trade_name"], "restaurant", stage, metro, payload["city"],
                     "2026-10-16" if licensed else None,
                     "2026-10-10", "2026-10-16T15:00:00Z", 0,
                     payload["address"], payload["owner"], source_id if licensed else None))
                self.conn.execute(
                    "INSERT INTO raw_records(source,source_id,payload,fetched_at) VALUES(?,?,?,?)",
                    ("issued_licenses" if licensed else "pending_applications", source_id,
                     json.dumps(payload), "2026-10-16T15:00:00Z"))

    def assert_state(self, state, stamp, *, later_failure=False, inventory_review=False):
        before = files(self.target)
        self.seed(stamp)
        if later_failure:
            self.conn.execute(
                "INSERT INTO run_log(job,started_at,finished_at,status) "
                "VALUES('pending_refresh', '2026-10-17T19:30:00Z', '2026-10-17T19:31:00Z', 'error')")
        if inventory_review:
            self.conn.execute("UPDATE venues SET stage='application-closed' "
                              "WHERE stage='application-pending' AND metro='houston'")
            self.conn.execute(
                "INSERT INTO source_observations(source,source_id,payload,observed_at) "
                "SELECT source,source_id,payload,? FROM raw_records "
                "WHERE source_id='synthetic-houston-application-pending'", (stamp,))
        self.assertTrue(self.producer.refresh_site(self.target, self.conn, self.cfg, now=NOW))
        metadata = json.loads((self.target / "data/sample-metadata.json").read_text())
        self.assertEqual(metadata["source_freshness"], state)
        self.assertEqual(metadata["generated_at"], "2026-10-17T20:00:00Z")
        self.assertEqual(metadata["source_ingest_succeeded_at"], stamp)
        self.assertIsNone(metadata["published_at"])
        self.assertEqual(metadata["contract_version"], 1)
        ready = state == "fresh" and not later_failure and not inventory_review
        self.assertEqual(metadata["source_readiness"]["ready"], ready)
        if inventory_review:
            self.assertEqual(metadata["source_readiness"]["quality_review"]["reappeared_closed_pending"]["count"], 1)
        self.assertEqual(metadata["freshness_thresholds_hours"],
                         {"source_ingest": 48, "generated_artifact": 192})
        self.assertEqual(len(self.producer.SAMPLE_PAGE_PATHS), 8)
        for path in self.producer.SAMPLE_PAGE_PATHS:
            with self.subTest(page=path, state=state):
                original = before[path].decode()
                result = (self.target / path).read_text()
                self.assertEqual(shell(result), shell(original))
                for marker in (START, END, FRESH_START, FRESH_END):
                    self.assertEqual(result.count(marker), 1)
                self.assertLess(result.index(FRESH_END), result.index("<table"))
                document = Document(result)
                cards = [n for n in document.nodes if n.has_class("sample-freshness")]
                self.assertEqual(len(cards), 1, "known evidence must replace the unknown card")
                card = cards[0]
                self.assertEqual(card.tag, "div")
                self.assertEqual(card.attrs.get("data-source-freshness"), state)
                self.assertEqual(card.attrs.get("aria-labelledby"), "sample-status-title")
                ids = [n.attrs["id"] for n in document.nodes if "id" in n.attrs]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertIn("sample-status-title", document.ids)
                self.assertIn("does not update between publications", card.text())
                self.assertIn("Publication: unverified", card.text())
                self.assertEqual("publication and delivery blocked" in card.text(), not ready)
                self.assertIn("Sample generated: 2026-10-17 20:00:00 UTC", card.text())
                self.assertTrue(any(n.tag == "a" and n.attrs.get("href", "").startswith(
                    "mailto:founders@openingwire.com?subject=") for n in card.nodes()))
                self.assertNotIn("Archive reference:", card.text())
                self.assertNotIn("for this table is unavailable", card.text())
                if state in {"fresh", "stale"}:
                    self.assertNotIn("unknown", card.text().lower())
                    self.assertIn(stamp, result)
                    self.assertIn("within 48 hours" if state == "fresh" else "Source data stale", card.text())
                else:
                    self.assertIn("Source freshness unknown", card.text())
                    self.assertNotIn("within 48 hours", card.text())
                self.assertIn("&lt;cafe&gt;", sample(result).lower())
                self.assertNotIn("<cafe>", sample(result).lower())
                self.assertIn("2026", sample(result))
                self.assertIn("https://data.texas.gov/resource/", sample(result))
                self.assertIn("Opening unresolved", sample(result))
                self.assertIn("First observed:", sample(result))
                self.assertIn("Application Filed" if metadata["pages"][path]["kind"] == "pending"
                              else "License Issued", sample(result))
                # Exclude the initial LF and final marker indentation only.
                rows = sample(result)[1:].rsplit("\n", 1)[0]
                self.assertEqual(hashlib.sha256(rows.encode()).hexdigest(),
                                 metadata["pages"][path]["rows_sha256"])
                venue_rows = [n for n in Document(sample(result)).nodes if n.tag == "tr"
                              and not n.has_class("seo-teaser")]
                self.assertEqual(len(venue_rows), metadata["pages"][path]["row_count"])
        after = files(self.target)
        allowed = set(self.producer.SAMPLE_PAGE_PATHS) | {"data/sample-metadata.json"}
        self.assertTrue({p for p in after if before.get(p) != after[p]} <= allowed)
        # A later frontend-only change can use this reviewed generated output as
        # its baseline without being forced back to an unknown/archive card.
        previous_git = check_site.git

        def generated_baseline(_root, *args):
            if args[0] == "ls-tree":
                return "\n".join(after).encode()
            if args[0] == "show":
                return after[args[1].split(":", 1)[1]]
            raise AssertionError(args)

        try:
            check_site.git = generated_baseline
            with redirect_stdout(io.StringIO()):
                self.assertTrue(check_site.check_site(self.target, "reviewed-generated-fixture"))
        finally:
            check_site.git = previous_git
        if state != "invalid":
            self.assertFalse(self.producer.refresh_site(
                self.target, self.conn, self.cfg, now=NOW + timedelta(minutes=1)))
            self.assertEqual(files(self.target), after)

    def test_fresh_actual_pair(self):
        self.assert_state(*STATES[0])

    def test_stale_actual_pair(self):
        self.assert_state(*STATES[1])

    def test_missing_actual_pair(self):
        self.assert_state(*STATES[2])

    def test_future_invalid_actual_pair(self):
        self.assert_state(*STATES[3])

    def test_newer_required_source_failure_cannot_hide_behind_fresh_ingest(self):
        self.assert_state(*STATES[0], later_failure=True)

    def test_fresh_sources_with_unresolved_closed_inventory_remain_blocked(self):
        self.assert_state(*STATES[0], inventory_review=True)

    def test_malformed_region_fails_before_any_write(self):
        path = self.target / self.producer.SAMPLE_PAGE_PATHS[-1]
        original = path.read_text()
        start = original.index(FRESH_START)
        end = original.index(FRESH_END) + len(FRESH_END)
        region = original[start:end]
        after_table = (original[:start] + original[end:]).replace("</table>", "</table>" + region, 1)
        for broken in (original.replace(FRESH_END, ""),
                       original + FRESH_START + FRESH_END,
                       original.replace(FRESH_START, "TEMP").replace(FRESH_END, FRESH_START).replace("TEMP", FRESH_END),
                       original.replace(FRESH_START, "").replace(FRESH_END, ""),
                       after_table):
            with self.subTest(broken=broken[:50]):
                path.write_text(broken)
                before = files(self.target)
                with self.assertRaises(ValueError):
                    self.producer.refresh_site(self.target, self.conn, self.cfg, now=NOW)
                self.assertEqual(files(self.target), before)
        path.write_text(original)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.producer_root.resolve()
    if not (root / "pipeline/seo_pages.py").is_file():
        parser.error("--producer-root must be the scraper checkout under review")
    sys.path.insert(0, str(root))
    sys.dont_write_bytecode = True

    def denied(*_args, **_kwargs):
        raise RuntimeError("Paired fixtures forbid network, SMTP and provider connections")

    socket.create_connection = denied
    socket.socket.connect = denied
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ProducerIntegration))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
