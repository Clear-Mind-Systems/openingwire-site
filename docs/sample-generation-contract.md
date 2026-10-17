# Sample publication contract proposal

Status: **proposed, not agreed or implemented by the producer**. Audited October
17, 2026. The frontend change supplies truthful static copy and an unknown-refresh
fallback; it does not publish new samples or establish successful delivery.

## Owners and coordination

`Clear-Mind-Systems/scraper-business` owns report generation, sample selection,
generated rows and freshness metadata, and the publication workflow. This site
owns static copy, styles, table labels, accessibility, and explanatory text
outside generated regions. There is one writer for each generated region.

No freshness/publication OpenSpec proposal or open producer PR was available at
audit time. All remote branches were checked. The active producer change was
`enroll-remote-development-toolkit`; it does not define this interface. The
producer owner must adopt or revise this artifact diff in its existing OpenSpec
lifecycle, with deltas to `site-sample-refresh`, `seo-metro-pages`, and
`b2b-seo-pages`. Record the accepted producer change/PR and exact artifact diff
here before integrating genuine output. This document is a handoff attached to
the frontend PR, not an assertion of agreement or a competing update process.

## Audited implementation

Producer main was
[`8e2be732ee93478978782d451771e6ab35a580bc`](https://github.com/Clear-Mind-Systems/scraper-business/tree/8e2be732ee93478978782d451771e6ab35a580bc).
Site main was
[`f97528e7fd3350782da46bc85450c10a7623ce59`](https://github.com/Clear-Mind-Systems/openingwire-site/tree/f97528e7fd3350782da46bc85450c10a7623ce59).

| Evidence at producer SHA | Actual behavior |
| --- | --- |
| [`config.yaml:9`](https://github.com/Clear-Mind-Systems/scraper-business/blob/8e2be732ee93478978782d451771e6ab35a580bc/config.yaml#L9) | Sources are TABC pending applications (`mxm5-tdpj`) and issued retail licenses (`7hf9-qc9f`); there is no separate business-filings feed. |
| [`pipeline/site_sample.py:49`](https://github.com/Clear-Mind-Systems/scraper-business/blob/8e2be732ee93478978782d451771e6ab35a580bc/pipeline/site_sample.py#L49) | `fmt_licensed()` removes the year; missing/invalid dates render empty. Selection orders by `COALESCE(stage_changed_at, first_seen)`, without a current-week cutoff. |
| [`pipeline/site_sample.py:118`](https://github.com/Clear-Mind-Systems/scraper-business/blob/8e2be732ee93478978782d451771e6ab35a580bc/pipeline/site_sample.py#L118) | `inject(path, rows)` replaces only the first `SAMPLE` marker region and preserves all surrounding bytes. Missing markers fail. No freshness metadata is emitted. |
| [`pipeline/seo_pages.py:438`](https://github.com/Clear-Mind-Systems/scraper-business/blob/8e2be732ee93478978782d451771e6ab35a580bc/pipeline/seo_pages.py#L438) | Generated teasers make unsupported current-week/universal-coverage claims; pending zero-count text also promises same-day delivery. They are producer-owned and covered by producer tests. |
| [`pipeline/seo_pages.py:642`](https://github.com/Clear-Mind-Systems/scraper-business/blob/8e2be732ee93478978782d451771e6ab35a580bc/pipeline/seo_pages.py#L642) | With `<!-- seo-pages:v1 -->` present, existing landing pages receive marker-only updates. A missing/different version triggers a full shell rewrite. |
| [`pipeline/seo_pages.py:684`](https://github.com/Clear-Mind-Systems/scraper-business/blob/8e2be732ee93478978782d451771e6ab35a580bc/pipeline/seo_pages.py#L684) | Homepage `METRO-LINKS` and `B2B-LINKS` blocks are also producer-owned; `update_footer_links()` regenerates their labels and links independently of the page version. |
| [`pipeline/seo_pages.py:729`](https://github.com/Clear-Mind-Systems/scraper-business/blob/8e2be732ee93478978782d451771e6ab35a580bc/pipeline/seo_pages.py#L729) | Sitemap regeneration depends on URL-set changes. Its `lastmod` is not sample-ingestion evidence. |
| [`weekly-report.yml:68`](https://github.com/Clear-Mind-Systems/scraper-business/blob/8e2be732ee93478978782d451771e6ab35a580bc/.github/workflows/weekly-report.yml#L68) | Checkout, homepage injection, and SEO generation are separate steps. Scheduled jobs push site changes; manual jobs open/update a PR. The schedule is Monday 13:00 UTC. |

The site's older architecture description of a `PAGE_PROFILES` injector and
per-refresh sitemap dates does not match current producer code. Historical
implementation is not proof of current behavior.

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

## Proposed artifact diff

Apply the same contract to the eight paths above. Retain exactly one existing
`<!-- SAMPLE:START -->` / `<!-- SAMPLE:END -->` pair per page and retain
`<!-- seo-pages:v1 -->` on the seven landing pages. Keep the six table columns.
Do not put status blocks inside `<table>` or nest marker regions.

The current frontend fallback is an ordinary static `div.sample-freshness` with
`id="sample-freshness"`, labelled by `sample-status-title`. Only after agreement,
the producer integration adds the following distinct region around/replacing
that block, before the table. It then owns all bytes inside the new markers:

```diff
+<!-- SAMPLE-FRESHNESS:START -->
 <div class="sample-freshness" id="sample-freshness" aria-labelledby="sample-status-title">
-  ...static unknown-refresh fallback and explicitly archived provenance...
+  ...producer-rendered status, dates, and provenance for these exact rows...
 </div>
+<!-- SAMPLE-FRESHNESS:END -->
```

The frontend does **not** install those proposed markers or generated values in
this PR. Old `inject()` remains compatible because its exact `SAMPLE` tokens
do not match `SAMPLE-FRESHNESS` tokens. The producer must add a separate strict
injector, validating one ordered pair of each marker before writing anything.
Prepare both row and metadata replacements in memory, validate them, and write
the page atomically. Never publish new metadata with old rows after a failure.

The producer's reviewed artifact diff must also:

- Render record dates with a year and machine-readable `<time datetime="YYYY-MM-DD">`;
  use explicit "Date unavailable" for missing/invalid record dates. Issued pages
  use TABC original issue dates; the tracker uses application submission dates.
- Replace unsupported generated teasers with neutral text scoped to the
  classified TABC restaurant/bar feed, and remove undated "this week" counts.
  Until then, frontend CSS suppresses `.seo-teaser` and a static explanatory
  label supplies the truthful coverage limit; generated bytes remain intact.
- Update producer-owned footer labels where needed, including "New openings by
  metro" to "License leads by metro". Preserve both existing `METRO-LINKS` and
  `B2B-LINKS` marker pairs and their bytes in this frontend-only change.
- Preserve frontend copy, table wrappers, focus styles, canonical URLs,
  structured data, checkout links, and fallback/sample-request accessibility.
  A template-version bump requires reviewed synchronization of these shells;
  it must not reintroduce the old marketing claims.
- Keep freshness rendering inside the existing producer publication path.
  Timestamp semantics do not authorize a workflow dispatch, deployment, or
  a second writer in this site repository.

## Timestamp and state semantics to agree

All instant values use RFC 3339 UTC with `Z`, including seconds. Human-readable
values include the year and "UTC". Date-only record values retain source calendar
dates; do not pretend they are UTC midnight events or venue-opening dates.

| Field | Meaning and rule |
| --- | --- |
| `source_ingested_at` | Verified completed successful ingest represented by the artifact's database snapshot. The producer must document the evidence linking that ingest to these rows. A commit timestamp, watermark, latest license date, or current clock is not a substitute. If not provable, omit and render unknown. |
| `rendered_at` | When this artifact was rendered, also the instant at which its status was evaluated. It is not ingestion, publication, subscriber delivery, or a venue opening. |
| `record_date_start` / `record_date_end` | Min/max valid issue dates for issued rows, or submission dates for pending rows actually included in this artifact. Unknown dates are disclosed separately. |
| `stale_after` | Explicit UTC boundary for the next expected snapshot under the agreed policy. Proposed policy: eight days after the verified source ingest (weekly cadence plus one day); producer owner must confirm or replace it. |
| `state` | `available`, `stale`, or `missing`, evaluated at `rendered_at`; meaning is described below. |

`available` means all required provenance is valid and `rendered_at` is before
`stale_after`. The UI says "Sample snapshot available", never "Live now".
`stale` means valid provenance exists but the artifact was already past that
boundary when rendered. `missing` means refresh provenance is absent,
malformed, inconsistent, or in the future; show "Sample refresh time unknown".
An empty qualified selection is explicitly "No sample records available" and
does not justify inventing records or dates; it can still have known ingest
provenance. Partial/missing record dates do not themselves establish refresh
provenance.

No client script or timer is added. These state labels are frozen at rendering;
an `available` artifact does not automatically become `stale` when the publisher
stops. Every known state therefore shows its absolute dates, the evaluated-as-of
time, and "This status does not update between publications. If the expected
update has passed, request a current sample." No elapsed-age badge is promised.

## Representative rendered HTML — fixtures only

The following invented timestamps are test examples, never production content.
All three replace only the fallback block in temporary copies for visual QA.
The production unknown fallback continues to show actual archived provenance.

Available (the fresh-at-render scenario):

```html
<div class="sample-freshness" id="sample-freshness" aria-labelledby="sample-status-title" data-sample-state="available">
  <h3 id="sample-status-title">Sample snapshot available</h3>
  <p>Source data ingested <time datetime="2026-10-12T11:32:00Z">October 12, 2026 at 11:32 UTC</time>. Snapshot rendered and status checked <time datetime="2026-10-12T13:00:00Z">October 12, 2026 at 13:00 UTC</time>.</p>
  <p>License dates: October 5–11, 2026. These are license dates, not opening dates. Expected update by <time datetime="2026-10-20T11:32:00Z">October 20, 2026 at 11:32 UTC</time>.</p>
  <p>This status does not update between publications. If the expected update has passed, <a href="mailto:founders@openingwire.com?subject=OpeningWire%20sample%20request&amp;body=Please%20send%20an%20available%20sample%20for%20my%20metro%3A%20">request a current sample</a>.</p>
</div>
```

Stale at render:

```html
<div class="sample-freshness" id="sample-freshness" aria-labelledby="sample-status-title" data-sample-state="stale">
  <h3 id="sample-status-title">Sample update overdue when checked</h3>
  <p>Source data ingested <time datetime="2026-10-01T11:32:00Z">October 1, 2026 at 11:32 UTC</time>. Expected update by <time datetime="2026-10-09T11:32:00Z">October 9, 2026 at 11:32 UTC</time>.</p>
  <p>Status checked when rendered <time datetime="2026-10-12T13:00:00Z">October 12, 2026 at 13:00 UTC</time>. License dates: September 25–30, 2026; these are not opening dates.</p>
  <p>These historical records do not confirm current availability. This status does not update between publications. <a href="mailto:founders@openingwire.com?subject=OpeningWire%20sample%20request&amp;body=Please%20send%20an%20available%20sample%20for%20my%20metro%3A%20">Request a current sample</a>.</p>
</div>
```

Missing/unknown refresh provenance:

```html
<div class="sample-freshness" id="sample-freshness" aria-labelledby="sample-status-title" data-sample-state="missing">
  <h3 id="sample-status-title">Sample refresh time unknown</h3>
  <p>No verified source-ingestion or sample-update timestamp is available. License/application dates describe records, not when this feed was updated or a venue opened.</p>
  <p>Treat this as a historical example, not a current-week feed. <a href="mailto:founders@openingwire.com?subject=OpeningWire%20sample%20request&amp;body=Please%20send%20an%20available%20sample%20for%20my%20metro%3A%20">Request a current sample</a>.</p>
</div>
```

Long-name/year fixture row (temporary table only):

```html
<tr><td>Example Restaurant With A Very Long Venue Name For Layout Testing</td><td><span class="tag r">Restaurant</span></td><td><span class="tag new">Newly Licensed</span></td><td>San Antonio</td><td>San Antonio</td><td><time datetime="2026-10-11">Oct 11, 2026</time></td></tr>
```

## Integration checks and owner actions

The existing producer tests are
[`tests/test_site_sample.py`](https://github.com/Clear-Mind-Systems/scraper-business/blob/8e2be732ee93478978782d451771e6ab35a580bc/tests/test_site_sample.py)
and
[`tests/test_seo_pages.py`](https://github.com/Clear-Mind-Systems/scraper-business/blob/8e2be732ee93478978782d451771e6ab35a580bc/tests/test_seo_pages.py).
They cover marker preservation, outside-region hand edits, template-version
rewrites, date formatting, teaser wording, deterministic JSON-LD, and no-change
idempotency. They currently assert yearless dates and legacy teaser claims;
they do not implement or test the proposed freshness region. `tests/conftest.py`
uses in-memory databases, redirects production database paths, and clears LLM
keys. Run only fixture-based tests, never producer entry points against the
shared site checkout or committed database.

Validation on October 17, 2026: **125 tests passed** from those two unchanged
producer test files, using an isolated scratch virtual environment and blocked
socket connections. A separate HTML-only compatibility check copied all eight
modified frontend pages to a temporary directory, blocked database and network
connections, and exercised the actual `inject()`, `update_page()`, and
`update_b2b_page()` functions with a synthetic row. All eight preserved every
byte outside `SAMPLE`, retained the fallback card, and returned unchanged on
the second injection. `update_footer_links()` also returned unchanged. The
shared frontend and producer files were not written by those checks. These
results validate compatibility with the existing updater, not future metadata
support.

Producer acceptance must add focused tests for all three freshness states,
invalid/future timestamps, missing and empty records, year-bearing dates,
escaped long names, ordered unique marker pairs, atomic row/metadata writes,
idempotency, and preservation of the frontend's exact surrounding HTML. Confirm
the clock/cutoff policy in its OpenSpec design. Existing template tests remain
the integration starting point; frontend temporary renders cannot prove producer
support for the proposed metadata.

Publication remains blocked independently of this frontend work.
[Issue 27](https://github.com/Clear-Mind-Systems/scraper-business/issues/27) is
open. The
[September 28 run](https://github.com/Clear-Mind-Systems/scraper-business/actions/runs/36475714914/job/109108784072)
shows reports, sample CSVs, digest generation, and their commit succeeding;
"Checkout site repo" failed, and both site render steps were skipped. The audit
input identifies "Bad credentials"; job-step status was independently confirmed
but log download access was unavailable in this session. Do not describe that
run as a site refresh or as a complete report-generation failure.

The producer owner must resolve publication authentication through its authorized
operations path, review and implement the agreed contract, supply genuine
generated artifacts in its own reviewed change, and verify their deployed
result when separately authorized. This task changes no credentials, dispatches
no workflow, merges nothing, and does not deploy. Until then, unknown refresh
recency remains visible and no frontend fixture is promoted to production data.
