# October 21 Texas pilot repair review

Starting site commit: `6b286cb00944b81f7fee6ceb9eea36bd640bafbb`. Branch:
`codex/texas-pilot-site-review-20261021`. No earlier October 21 repair PR or remote
branch was present when the task inspected this repository. This builds on the
merged October 17 truth/freshness repair, PR #3.

This branch changes local source and checks. It does not publish a refreshed
public sample. All eight archived SAMPLE regions and unknown-refresh cards
remain byte-identical to the starting commit. The archive is still August 3,
2026; it has no source freshness sidecar. No source-success time is inferred
from its record dates, file time, or commit time.

## Changes

Every sample now explains that licensing activity may concern an already-open
venue, ownership/operator change, alcohol addition, renewal, or non-restaurant.
An opening needs separate evidence. Archived rows do not provide verified
business contacts. Homepage audience copy no longer implies that its records
identify new restaurants. Pricing, checkout links, legal pages and founding
eligibility are unchanged.

The corrected producer footer function ran against a temporary homepage copy;
its output changed only `New openings by metro:` to `TABC license records by
metro:`. That exact output is included here. The checker permits only the paired
producer's two literal conservative footer-label migrations while preserving
link destinations, marker boundaries and every remaining byte.

The paired source-readiness addition keeps the existing version-1 clock fields
and adds per-source evidence. The static consumer verifies all eight page hashes
and counts, rejects missing/mixed/orphan provenance, and requires a visible
publication/delivery hold when required sources are blocked. The paired test
uses only synthetic rows/clocks, an in-memory database and disposable site copies;
it blocks socket connections and does not write either input checkout.

## Reproducible checks

```bash
python3 scripts/check_site.py --baseline 6b286cb
python3 scripts/test_check_site.py
../scraper-business/.venv/bin/python scripts/check_producer_integration.py --producer-root ../scraper-business
git diff --check
```

Record final outcomes in the PR. The new consumer failure cases exercise altered
row bytes, wrong counts, omitted required sources, a false ready gate, invisible
degraded holds, mixed archive/generated modes, missing page evidence, malformed
metadata, orphan sidecars and unsupported publication claims. These checks do
not establish browser layout, live source status, email delivery, or production
hosting. The prior [October 17 browser evidence](validation.md) retains its
original date and limitations; it is not a new browser run.

At the final October 21 local check, all eight static pages passed, ten consumer
failure/consistency tests passed, and all seven paired producer tests passed.
The paired cases include fresh, stale, missing, future-invalid and a newer
required-source failure after a fresh aggregate ingest, unresolved historical
closed/currently observed inventory despite fresh sources, and malformed marker
failure before writes. Synthetic fixtures now include exact source IDs and
physical Texas state/country, with an actual pending premises fingerprint or
issued-license link. The checks assert clickable source references, unresolved
opening labels, observation dates and the distinct Application Filed/License
Issued labels. Exact SAMPLE and SAMPLE-FRESHNESS interiors on all eight
pages were also compared to `6b286cb` and remain unchanged. The labelled layout
fixtures were regenerated outside the repository. No site Actions CI workflow is
configured; these are local results. PR #4's external Semgrep check passed on
`35f6e20`; later commits require their own check receipt. Whitespace validation passed.

## Separate operational milestones

Keep these receipts separate when an owner later authorizes publication:

| Milestone | Required evidence | What it establishes |
| --- | --- | --- |
| Source refresh | Per-source successful complete refresh times and latest-attempt status | Source data observed successfully; source record dates remain separate. |
| Report generation | Report timestamp, readiness gate and sample row hashes | A particular artifact was built from recorded source evidence. |
| Committed data | Reviewed commit containing matching artifact hashes | Versioned review artifact; no deployment implication. |
| Deployment | Successful publication receipt identifying that exact commit/artifact | Hosting accepted that version; no served-content implication. |
| Served content | Read-only retrieval of all eight pages plus matching sidecar and row hashes | The intended artifact is being served at that check time. |

An artifact-upload step must identify the intended files and fail when none
exist. A workflow green check, git push, or HTTP 200 alone cannot substitute for
these receipts. In-job alerts cannot detect a job that never starts; an independent
scheduler/monitor must distinguish executed failures from cancelled, queued and
unassigned jobs. Historical cancellation does not establish current runner health.

## Owner decisions before a commercial pilot

- Resolve the founding offer mismatch: the site says first ten customers total;
  templates historically say ten per metro. This repair does not choose either.
- Verify subscription activation, territory mapping, payment failure,
  cancellation and stopped delivery in a supported test lifecycle before relying
  on the existing self-serve cancellation promise. A static cancellation page
  does not establish automation.
- Select a provider-compatible acquisition setup. MXroute prohibits marketing
  and sales pitches, including personalized unsolicited outreach. Evaluate
  informational customer fulfillment separately. No replacement service,
  sending domain, account, credential or purchase is part of this repair.
- Approve a carefully qualified cohort, exact artifact and explicit publication
  and delivery steps separately. This repair is for code review; passing local
  checks does not authorize launch.

No email send, purchase, merge or deployment is performed by these checks.
