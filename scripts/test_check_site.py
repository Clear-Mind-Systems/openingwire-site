#!/usr/bin/env python3
"""Secret-free checks for incomplete, corrupted and blocked generated bundles."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from check_site import END, START, REQUIRED_SOURCES, provenance_errors


class ProvenanceBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="openingwire-consumer-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "data").mkdir()
        self.marketing = {"index.html"} | {f"fixture-{i}/index.html" for i in range(7)}
        self.rows = '<tr><td>SYNTHETIC licensing record</td></tr>'
        self.sources = {p: self.page() for p in self.marketing}
        self.metadata = {
            "published_at": None,
            "generated_at": "2026-10-21T21:00:00Z",
            "freshness_thresholds_hours": {"source_ingest": 48},
            "pages": {p: self.row_evidence() for p in self.marketing},
            "source_readiness": {
                "ready": True, "status": "ready", "reasons": [],
                "latest_ingest_status": "ok",
                "sources": {name: {"status": "fresh", "latest_status": "ok",
                                   "last_successful_at": "2026-10-21T20:00:00Z",
                                   "latest_attempt_at": "2026-10-21T20:00:00Z"}
                            for name in REQUIRED_SOURCES},
            },
        }

    def page(self, notice="", *, rows=None):
        return ('<div id="sample-freshness" data-source-freshness="fresh">'
                + notice + '</div>' + START + '\n'
                + (self.rows if rows is None else rows) + '\n    ' + END)

    def row_evidence(self, rows=None, count=1):
        return {"rows_sha256": hashlib.sha256(
            (self.rows if rows is None else rows).encode()).hexdigest(), "row_count": count}

    def errors(self):
        (self.root / "data/sample-metadata.json").write_text(json.dumps(self.metadata))
        return provenance_errors(self.root, self.sources, self.marketing)

    def test_complete_consistent_bundle(self):
        self.assertEqual(self.errors(), [])

    def test_empty_rows_are_valid_and_counted_as_zero(self):
        for path in self.marketing:
            self.sources[path] = self.page(rows="")
            self.metadata["pages"][path] = self.row_evidence(rows="", count=0)
        self.assertEqual(self.errors(), [])

    def test_corrupted_rows_or_counts_are_rejected(self):
        path = next(iter(self.marketing))
        self.sources[path] = self.page(rows=self.rows.replace("licensing", "changed"))
        self.assertTrue(any("hash" in e for e in self.errors()))
        self.sources[path] = self.page()
        self.metadata["pages"][path]["row_count"] = 2
        self.assertTrue(any("count" in e for e in self.errors()))

    def test_missing_source_and_false_ready_gate_are_rejected(self):
        self.metadata["source_readiness"]["sources"].pop("pending_refresh")
        self.assertTrue(any("incomplete" in e for e in self.errors()))
        self.metadata["source_readiness"]["sources"]["pending_refresh"] = {
            "status": "fresh", "latest_status": "error"}
        self.assertTrue(any("contradicts ready" in e for e in self.errors()))

    def test_fresh_label_cannot_override_a_stale_or_future_clock(self):
        source = self.metadata["source_readiness"]["sources"]["pending_refresh"]
        source["last_successful_at"] = "2026-08-03T20:00:00Z"
        self.assertTrue(any("source clock" in e for e in self.errors()))
        source["last_successful_at"] = "2026-10-22T20:00:00Z"
        self.assertTrue(any("source clock" in e for e in self.errors()))

    def test_degraded_artifacts_need_visible_hold_on_every_page(self):
        self.metadata["source_readiness"].update(
            ready=False, status="blocked", reasons=["pending_refresh latest attempt failed"])
        self.assertEqual(len(self.errors()), 8)
        self.sources = {p: self.page("Required sources incomplete — review only; publication and delivery blocked")
                        for p in self.marketing}
        self.assertEqual(self.errors(), [])

    def test_mixed_archive_and_generated_pages_are_rejected(self):
        self.sources[next(iter(self.marketing))] = START + self.rows + END
        self.assertTrue(any("mixed" in e for e in self.errors()))

    def test_missing_page_and_publication_claim_are_rejected(self):
        self.metadata["pages"].pop(next(iter(self.marketing)))
        self.assertTrue(any("inventory" in e for e in self.errors()))
        self.metadata["pages"] = {p: self.row_evidence() for p in self.marketing}
        self.metadata["published_at"] = "2026-10-21T21:00:00Z"
        self.assertTrue(any("unverified" in e for e in self.errors()))

    def test_orphan_sidecar_and_malformed_metadata_are_rejected(self):
        self.sources = {p: START + self.rows + END for p in self.marketing}
        self.assertTrue(any("orphan" in e for e in self.errors()))
        self.sources = {p: self.page() for p in self.marketing}
        (self.root / "data/sample-metadata.json").write_text("[]")
        self.assertTrue(provenance_errors(self.root, self.sources, self.marketing))


if __name__ == "__main__":
    unittest.main()
