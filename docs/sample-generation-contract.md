# Sample generation contract — paired integration

This contract is implemented together by scraper-business PR #35 and
openingwire-site PR #3, including the QA follow-up change
`align-site-freshness-regions`. The paired implementation starts from producer
`65f0694ffcb64f3327d820b7e6602aa1bd2ea4f6` and consumer
`e3e7fc3360ddf5032146884619984af3c84de9f2`. It supersedes the earlier unagreed
`source_ingested_at` / `rendered_at` / `stale_after` proposal. Source changes and
local test success do not establish production recovery or deployment.

## Owners and concrete region agreement

`Clear-Mind-Systems/scraper-business` is the single writer of SAMPLE interiors,
SAMPLE-FRESHNESS interiors, `data/sample-metadata.json`, and the publication
workflow. The site owns the surrounding static copy, layout, accessible table
wrappers, styles, navigation, legal pages, sitemap, pricing and checkout links.
No site script fetches data or updates production samples.

The same two disjoint marker pairs apply to all eight paths in the provenance
table below. The freshness region must precede the table; SAMPLE remains inside
it. All eight pages retain their current fallback text and existing SAMPLE bytes
when the marker boundaries are first installed:

```diff
+<!-- SAMPLE-FRESHNESS:START -->
 <div class="sample-freshness" id="sample-freshness" aria-labelledby="sample-status-title">
   ...existing unknown-refresh explanation and explicitly historical archive reference...
 </div>
+<!-- SAMPLE-FRESHNESS:END -->
```

On a later authorized refresh, the real producer replaces the entire card with
one of the forms below and replaces SAMPLE rows in the same prepared page
string. It does not also append a table freshness row. Every marker pair must be
unique and ordered, disjoint from the other region, and outside/inside the table
as specified. All eight pages are validated before any write. An unmarked
freshness card, mixed old/new page modes, or malformed pair fails before writes.
Legacy pages with no freshness card and no SAMPLE-FRESHNESS markers retain the
producer's original final-row interface; they cannot carry a conflicting card.

Every page output is prepared before the existing per-file write pass. The JSON
sidecar is written last. This is not a filesystem transaction across pages: a
write error must stop publication, and the owner reviews the complete successful
output before publishing. The site adds no second writer or deployment path.

## Fields and clocks

The implementation uses the producer's version-1 JSON contract. The October 21
repair adds required-source readiness to generated bundles without changing the
existing clock fields:

| Field | Meaning |
| --- | --- |
| `contract_version` | `1`. Unsupported versions do not establish provenance. |
| `source_ingest_succeeded_at` | Latest recorded successful ingest completion, UTC ISO8601 with `Z`, or null. Not a venue opening, current clock, file time, watermark or git commit time. |
| `generated_at` | Actual rendering time for this payload/provenance version; retained for identical output. Must follow valid source success. |
| `published_at` | Null; HTML always says publication unverified. A push or HTTP 200 is not exact-artifact publication evidence. |
| `source_freshness` | `fresh`, `stale`, `missing`, or `invalid`, evaluated at generation. Missing/invalid show unknown. |
| `source_readiness` | Explicit `ready` gate, `ready`/`blocked` status, reasons, and separate evidence for `pending_applications`, `issued_licenses`, and `pending_refresh`. A newer failed attempt blocks readiness even when an older ingest success is fresh. |
| `freshness_thresholds_hours` | Source ingest 48 hours; generated artifact 192 hours. Exactly 48 source hours is fresh. |
| `pages[path]` | `kind`, real venue `row_count`, and `rows_sha256` of UTF-8 venue/teaser rows with LF separators and no final LF. Excludes freshness and marker indentation. |

Known states show absolute UTC ingest and generation timestamps including years.
These are static observations evaluated at generation, not a live age timer.
The card explicitly says it does not update between publications. A newer failed
ingest does not advance source success; missing/malformed evidence stays unknown;
a stale ingest remains stale even when the render succeeds. No recent records or
source timestamps are fabricated. Empty selections may still have known ingest
provenance. Row dates are source issue/application dates and include the year.

A missing JSON sidecar does not get reconstructed by this static site from file
or commit dates. The next producer refresh rebuilds actual provenance; operators
use the producer's read-only freshness checker for current health. Readers see
only the rendered observation and absolute dates, never a claim of live health.

All three required source jobs must have current successful evidence for the
generation gate to pass. A recent zero-record incremental ingest does not prove
that a full pending snapshot succeeded. The producer defaults to blocking output
when readiness fails; explicitly requested local degraded review artifacts carry
the visible words **publication and delivery blocked** on every page. Generating a
review artifact does not authorize publishing or sending it. The consumer checks
all eight page entries, exact row hashes and counts, source evidence, coherent
archive/generated mode, and the visible hold before accepting a generated bundle.

## Representative rendered HTML — synthetic fixtures only

The following are emitted by the actual producer renderer for labelled local
test inputs. They are not production timestamps or publishable venue samples.
The static checker can write layout fixtures outside the checkout. The separate
paired checker calls the actual producer with an in-memory database and asserts
one coherent card across all eight real pages for each source state.

Fresh:

```html
    <div class="sample-freshness" id="sample-freshness" aria-labelledby="sample-status-title" data-source-freshness="fresh">
      <h3 id="sample-status-title">Sample source ingest recorded</h3>
      <p>Source ingest within 48 hours at generation. Source ingest: <time datetime="2026-10-17T19:00:00Z">2026-10-17 19:00:00 UTC</time>. Sample generated: <time datetime="2026-10-17T20:00:00Z">2026-10-17 20:00:00 UTC</time>. Publication: unverified. Required sources complete at generation.</p>
      <p>This status is evaluated at generation and does not update between publications. Source ingest is not a venue opening date. Request a current sample if these dates are too old for your needs.</p>
      <p><a href="mailto:founders@openingwire.com?subject=OpeningWire%20sample%20request&amp;body=Please%20send%20an%20available%20sample%20for%20my%20metro%3A%20">Request an available sample for your metro</a>.</p>
    </div>
```

Stale:

```html
    <div class="sample-freshness" id="sample-freshness" aria-labelledby="sample-status-title" data-source-freshness="stale">
      <h3 id="sample-status-title">Sample source data stale</h3>
      <p>Source data stale: successful ingest older than 48 hours at generation. Source ingest: <time datetime="2026-10-04T13:27:46Z">2026-10-04 13:27:46 UTC</time>. Sample generated: <time datetime="2026-10-17T20:00:00Z">2026-10-17 20:00:00 UTC</time>. Publication: unverified. Required sources incomplete — REVIEW ONLY; publication and delivery blocked. pending_applications: successful refresh stale; issued_licenses: successful refresh stale; pending_refresh: successful refresh stale</p>
      <p>This status is evaluated at generation and does not update between publications. Source ingest is not a venue opening date. Request a current sample if these dates are too old for your needs.</p>
      <p><a href="mailto:founders@openingwire.com?subject=OpeningWire%20sample%20request&amp;body=Please%20send%20an%20available%20sample%20for%20my%20metro%3A%20">Request an available sample for your metro</a>.</p>
    </div>
```

Missing:

```html
    <div class="sample-freshness" id="sample-freshness" aria-labelledby="sample-status-title" data-source-freshness="missing">
      <h3 id="sample-status-title">Sample refresh time unknown</h3>
      <p>Source freshness unknown: no valid successful ingest timestamp. Source ingest: unknown. Sample generated: <time datetime="2026-10-17T20:00:00Z">2026-10-17 20:00:00 UTC</time>. Publication: unverified. Required sources incomplete — REVIEW ONLY; publication and delivery blocked. pending_applications: latest attempt missing; pending_applications: successful refresh missing; issued_licenses: latest attempt missing; issued_licenses: successful refresh missing; pending_refresh: latest attempt missing; pending_refresh: successful refresh missing; ingest: latest attempt missing</p>
      <p>This status is evaluated at generation and does not update between publications. Source ingest is not a venue opening date. Request a current sample if these dates are too old for your needs.</p>
      <p><a href="mailto:founders@openingwire.com?subject=OpeningWire%20sample%20request&amp;body=Please%20send%20an%20available%20sample%20for%20my%20metro%3A%20">Request an available sample for your metro</a>.</p>
    </div>
```

Synthetic long-name row for layout testing only:

```html
<tr><td>SYNTHETIC Cafe with a deliberately long display name for layout testing</td><td>Restaurant</td><td>Newly Licensed</td><td>Austin</td><td>Austin</td><td>Oct 16, 2026</td></tr>
```

## Verification and publication dependency

Run static-only protection against the reviewed frontend baseline separately
from actual producer integration:

```bash
python3 scripts/check_site.py
python3 scripts/test_check_site.py
python3 scripts/check_site.py --write-fixtures /tmp/openingwire-layout-fixtures
../scraper-business/.venv/bin/python scripts/check_producer_integration.py --producer-root ../scraper-business
```

The paired command blocks sockets and writes only temporary copies, uses no
production database, tests fresh/stale/missing/future-invalid evidence and marker
failure behavior, verifies row hashes and counts, and checks byte-stable reruns
and preservation of all non-owned bytes. Static SAMPLE equality remains required
for frontend-only changes; it is deliberately not imposed on generated output.
After a producer publication, pass its reviewed commit with `--baseline`; the
static checker accepts known producer states and verifies their UTC fields
against the sidecar instead of demanding the old unknown fallback.
The test requires the reviewed producer checkout and its existing test dependencies;
there is no implicit download, provider call or live refresh.

Review/coordinate both PRs before the next authorized production refresh. The
existing runner and SITE_PUSH_TOKEN recovery actions remain owner work. No
merge, dispatch, deployment, credential operation or SMTP send follows from
passing these tests. Production publication must verify the matching deployed
version and all reviewed rows and provenance separately.

## Baseline date provenance

All 115 venue rows in the eight baseline sample regions were matched read-only
to committed `reports/*/statewide.csv` records using display name (legal suffix
normalization), city, and rendered month/day. Each match produced one distinct
full record date, with year **2026**. No database was opened, generator run, or
provider called. These are record dates, not verified ingestion or delivery
times.

| Site artifact | Baseline record dates | Producer artifact evidence |
| --- | --- | --- |
| `index.html` | License dates July 30–31, 2026 | W32 lines 4, 6, 7, 9, 14, 15, 24, 28, 30, 38 |
| `new-restaurants-austin/index.html` | License dates June 26–July 30, 2026 | W30 lines 7–23; W32 lines 30, 38, 59, 60, 80 |
| `new-restaurants-dallas/index.html` | License dates July 27–31, 2026 | W32 lines 7–63 |
| `new-restaurants-houston/index.html` | License dates July 27–31, 2026 | W32 lines 4–73 |
| `new-restaurants-san-antonio/index.html` | License dates June 30–July 31, 2026 | W30 lines 18–129; W32 lines 24, 28, 45, 57 |
| `pre-opening-restaurant-leads-texas/index.html` | License dates July 29–31, 2026 | W32 lines 4–59 |
| `restaurant-activity-report-alternative/index.html` | License dates July 29–31, 2026 | W32 lines 4–59 |
| `tabc-license-application-tracker/index.html` | Application dates July 26–August 2, 2026 | W31 line 2; W32 lines 3–112 |

Immutable CSV references:
[W30](https://github.com/Clear-Mind-Systems/scraper-business/blob/8c6ce53742b5d7fee2e118359c8e52efedba3736/reports/2026-W30/statewide.csv),
[W31](https://github.com/Clear-Mind-Systems/scraper-business/blob/f61abe482eb62ba833effefcfb990cfd86327d71/reports/2026-W31/statewide.csv),
[W32](https://github.com/Clear-Mind-Systems/scraper-business/blob/db4be16f52a11b8b5a8198dcfc57c8e8c54766ba/reports/2026-W32/statewide.csv).
Site commit publication on August 3, 2026 is repository provenance only. Neither
that commit time nor these record dates establish an ingestion timestamp.
Baseline labels must remain explicitly tied to this archived snapshot; they
must not describe rows supplied by a later publisher as though independently
verified by this frontend change.
