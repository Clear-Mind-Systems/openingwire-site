# Static truth and freshness validation

Validated October 17, 2026 against baseline
`f97528e7fd3350782da46bc85450c10a7623ce59`. The original static and browser checks below
record the frontend baseline; the paired integration follow-up is recorded at
the end of this document. Console exceptions are disclosed below. This verifies
frontend source behavior and compatibility with the reviewed producer;
it does not establish a successful source refresh, subscriber delivery, or live
deployment. The [producer contract](sample-generation-contract.md) now specifies the paired
implementation in scraper PR #35 and site PR #3; live publication remains an
owner operation.

## Changed-page inventory

All eight pages received scoped coverage/cadence copy, visible unknown-refresh
status and archived date provenance, date explanations, and accessible scrolling
for the existing table:

| Page | Baseline document width at a 390px viewport | Final document width |
| --- | ---: | ---: |
| `index.html` | 603px | 390px |
| `new-restaurants-austin/index.html` | 582px | 390px |
| `new-restaurants-dallas/index.html` | 570px | 390px |
| `new-restaurants-houston/index.html` | 590px | 390px |
| `new-restaurants-san-antonio/index.html` | 574px | 390px |
| `pre-opening-restaurant-leads-texas/index.html` | 579px | 390px |
| `restaurant-activity-report-alternative/index.html` | 579px | 390px |
| `tabc-license-application-tracker/index.html` | 572px | 390px |

The homepage also clarifies its generated metro-link labels outside that owned
region. All seven landing-page FAQ JSON-LD blocks match their visible FAQs.
Legal pages, canonical destinations, sitemap URL coverage, pricing, and all three
Stripe checkout destinations are preserved.

## Checks and results

Run from the site checkout:

```bash
python3 scripts/check_site.py
python3 scripts/check_site.py --write-fixtures /tmp/openingwire-freshness-fixtures
git diff --check
```

Results: the focused standard-library checker passes all eight marketing pages;
the four temporary fixtures are generated outside the checkout; the whitespace
check passes. The checker compares **every byte** between each `SAMPLE` marker
pair with the baseline, verifies all existing sample/footer/version markers and
six-column headers, and preserves producer-owned `METRO-LINKS`/`B2B-LINKS`
regions. It also checks internal URLs and fragments, sample-request recipient and
query fields, canonical URLs, exact eight-page sitemap coverage, legal links,
prices/Stripe targets, FAQ JSON-LD, accessible names and descriptions, and absence
of executable client scripts. Generated venue rows were not rewritten; their
yearless date format remains producer-owned. The visible provenance card supplies
the verified archived record-date range with a year.

Browser QA used the repository-required gstack `/browse` headless fallback with
Chromium on Linux. Tools and browser state lived outside the site checkout; no
framework, project dependency, build step, or browser package was added. The
baseline was served from a separate `git archive` copy at `127.0.0.1:4174`, the
edited checkout at `127.0.0.1:4173`, and synthetic fixtures at `127.0.0.1:4175`.

- All eight page requests loaded with HTTP 200. The retained homepage desktop
  console record contains a resource 404; its URL is not identified in the saved
  evidence, so a console-clean run and the resource identity are not established.
- All **24 page/width combinations** at 1280, 390, and 320px had document width
  equal to viewport width after the change. The table alone scrolls horizontally.
- Full-page desktop/mobile captures of all eight pages were visually reviewed.
  The neutral headings, unknown status, dated archive explanation, and request
  link are readable. The selected evidence below was recaptured after the final
  archive wording change.
- Actual `Tab` presses reached the sample-request link, then the table region,
  on every page at 390px. Both displayed the 3px focus outline. `ArrowRight`
  scrolled each table while page horizontal scroll stayed zero. Mail links and
  checkout destinations were inspected without sending mail or opening checkout.
- The table has a caption, scoped column headers, a keyboard-focusable named
  region, and a description explaining horizontal scrolling and record dates.
- Four temporary states at all three widths passed **12 additional layout
  checks**: available/fresh at render, stale at render, missing provenance, and
  the production unknown fallback. All were free of page overflow. The retained
  fresh-fixture console record contains an unidentified resource 404; the saved
  evidence does not establish that this was a favicon or any specific asset. A synthetic long venue name wrapped within the table; `Oct 11, 2026`
  remained readable and its column was reachable at the right scroll edge.
  Proposed known states display explicit UTC ingest/render/expected dates and
  explain that status does not update between publications. This checks their
  presentation, not an implemented producer state classifier.

Measured WCAG contrast ratios for the actual solid-color text/background pairs:

| Text/background | Ratio |
| --- | ---: |
| Body `#141a24` / white | 17.46:1 |
| Secondary `#5a6577` / soft `#f4f6fa` | 5.45:1 |
| CTA white / `#0b5fcc` | 5.96:1 |
| Link/focus `#0a54ba` / soft `#f4f6fa` | 6.49:1 |
| Restaurant tag `#08683c` / `#e7f2ec` | 5.99:1 |
| Bar tag `#5b3fd4` / `#ede9fc` | 5.69:1 |
| License tag `#0b5fcc` / `#e8f0fe` | 5.20:1 |

Each tested text pair exceeds 4.5:1. These checks are not a full screen-reader or
cross-browser accessibility audit. Exact width, interaction, fixture, and contrast
results are retained in [qa-evidence/results.json](qa-evidence/results.json).

Session browser commands (the scratch scripts orchestrated only gstack commands):

```bash
python3 /workspace/scratch/capture-openingwire.py http://127.0.0.1:4174 /workspace/scratch/openingwire-before
python3 /workspace/scratch/capture-openingwire.py http://127.0.0.1:4173 /workspace/scratch/openingwire-after
python3 /workspace/scratch/interaction-openingwire.py
python3 /workspace/scratch/evidence-openingwire.py
python3 /workspace/scratch/fixtures-openingwire.py
```

To repeat manually after starting `python3 -m http.server 4173 --bind 127.0.0.1`,
use the installed browse binary for each page and width:

```bash
B="$HOME/.claude/skills/gstack/browse/dist/browse"
"$B" viewport 390x900
"$B" goto http://127.0.0.1:4173/
"$B" js 'JSON.stringify({viewport:innerWidth,documentWidth:document.documentElement.scrollWidth})'
"$B" console --errors
"$B" screenshot --selector '#sample' /tmp/openingwire-sample.png
"$B" press Tab
```

Continue Tab to the request link and table, inspect `:focus-visible`, then press
ArrowRight and read `.table-scroll.scrollLeft`. Repeat at 1280 and 320px. Fixture
generation uses the literal HTML examples from the proposed contract and never
modifies production pages or generated regions.

## Producer compatibility

The producer audit ran its two existing fixture-based rendering suites at
`8e2be732ee93478978782d451771e6ab35a580bc`: **125 passed**. Dependencies were
installed into `/workspace/scratch/producer-test-venv`. From the producer checkout:

```bash
PYTHONDONTWRITEBYTECODE=1 /workspace/scratch/producer-test-venv/bin/python - <<'PY'
import socket, pytest
def deny_network(*args, **kwargs):
    raise AssertionError('Network forbidden during producer fixture tests')
socket.create_connection = deny_network
socket.socket.connect = deny_network
raise SystemExit(pytest.main(['-q', '-p', 'no:cacheprovider',
    'tests/test_site_sample.py', 'tests/test_seo_pages.py']))
PY
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 /workspace/scratch/producer-test-venv/bin/python /workspace/scratch/check_producer_compatibility.py
```

The separate HTML-only compatibility check copied all eight edited site pages to
a temporary directory, blocked database/network connections, and exercised the
real `inject()`, `update_page()`, and `update_b2b_page()` functions with a synthetic
row. It preserved every byte outside `SAMPLE`, retained the fallback and markers,
and returned unchanged on the second injection. `update_footer_links()` also
returned unchanged. Original site/producer files and the producer database were
untouched. These historical tests establish compatibility with that baseline
updater. The actual new freshness writer is covered by the paired integration
follow-up below.

## Rendered evidence

Screenshots are compressed JPEG browser captures. The homepage images capture the
whole sample section at 1280/390px; Austin images are 1280x1100 and 390x1200
viewports. The claims comparison stacks two 1280x950 captures. The fixture sheet
combines four 390px state-card captures with the desktop long-name/year row and
is explicitly labelled synthetic.

| View | Before | After |
| --- | --- | --- |
| Homepage sample, desktop | [Before](qa-evidence/home-before-desktop.jpg) | [After](qa-evidence/home-after-desktop.jpg) |
| Homepage sample, mobile | [Before](qa-evidence/home-before-mobile.jpg) | [After](qa-evidence/home-after-mobile.jpg) |
| Austin landing page, desktop | [Before](qa-evidence/austin-before-desktop.jpg) | [After](qa-evidence/austin-after-desktop.jpg) |
| Austin landing page, mobile | [Before](qa-evidence/austin-before-mobile.jpg) | [After](qa-evidence/austin-after-mobile.jpg) |

[Homepage coverage/cadence comparison](qa-evidence/home-claims-before-after.jpg)
and [synthetic status/layout fixtures](qa-evidence/synthetic-freshness-states.jpg).

## Remaining owner actions

The paired interface is now implemented through the producer's OpenSpec
follow-up and must be reviewed in both PRs before the next authorized refresh.
Only the producer writes year-bearing sample rows and matching metadata through
its existing publication path. An authorized operator must separately resolve the documented publishing
credential failure and verify a genuine publication/deployment. No workflow was
dispatched, no report generated, no provider queried, and no merge or deployment
performed for this validation. The production page therefore keeps its explicit
unknown-refresh fallback.

## Paired integration QA follow-up — October 17, 2026

The original literal fixtures above did not test producer PR #35. Real paired
rendering revealed a second, contradictory unknown-refresh card after valid
source evidence was emitted. All eight pages now mark the existing card with
SAMPLE-FRESHNESS boundaries. The paired producer replaces that region, instead
of adding a second freshness row. Existing production SAMPLE and footer bytes,
checkout destinations, current fallback text and static shell remain preserved.

`check_producer_integration.py` runs the actual reviewed producer with synthetic
in-memory data against temporary copies of all eight current pages. It checks
fresh, stale, missing and future-invalid evidence, one coherent accessible card,
source/generation/publication semantics, row counts/hashes, escaped venue text,
all non-owned bytes, idempotence, and rejection before writes for malformed
markers. Socket connections are denied. It does not inspect production data or
publish its fixtures. The static-only checker still separately protects existing
generated bytes; literal layout fixtures are not a substitute for this test.

No new visual, mobile-width, contrast or console-clean pass is claimed for this
follow-up. Prior screenshots remain evidence of their original revision, and
the two saved resource 404 observations have not been reclassified or erased.
