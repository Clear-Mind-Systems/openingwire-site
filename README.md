# openingwire.com

Static marketing site for OpeningWire, served by GitHub Pages.

## DNS (Cloudflare) — required records

| Type | Name | Target | Proxy |
|---|---|---|---|
| CNAME | `openingwire.com` (apex — Cloudflare flattens it) | `clear-mind-systems.github.io` | DNS only (grey cloud) until Pages cert issues, then optional |
| CNAME | `www` | `clear-mind-systems.github.io` | same |

GitHub Pages custom domain is set to `openingwire.com` (see CNAME file). HTTPS is
enforced once GitHub issues the certificate (can take up to an hour after DNS).

## Swapping CTAs to Stripe payment links

Each pricing button is a Stripe payment-link `href` in `index.html` under
`id="pricing"`. The three existing checkout destinations are preserved by the
static checker; changing billing destinations requires separate authorization.

## Updating the sample table

The companion `Clear-Mind-Systems/scraper-business` repository is the single
writer of generated rows between `<!-- SAMPLE:START -->` and
`<!-- SAMPLE:END -->`, the `SAMPLE-FRESHNESS` interiors, and the JSON metadata
sidecar in all eight marketing pages. Do not hand-edit those
regions or run the producer against a shared site checkout. Preserve the
`seo-pages:v1` landing-page markers and the homepage metro-link markers.

The static sample labels currently show **refresh time unknown**. Their archive
reference describes the August 3, 2026 snapshot, with record years verified from
committed producer reports. It is not an ingestion or successful-refresh time.
Weekly subscription delivery does not establish public sample freshness.

See [the paired producer contract](docs/sample-generation-contract.md) for
exact regions, UTC meanings, rendered HTML, and the producer's OpenSpec change
`align-site-freshness-regions` in PR #35. PR #3 installs marker boundaries around
the current fallback; only the producer replaces it on an authorized refresh.
Publishing credentials and deployment remain separate operator responsibilities.

## Local verification

No build system or site runtime JavaScript is needed. Run the focused interface
and link checks with the standard library:

```bash
python3 scripts/check_site.py
../scraper-business/.venv/bin/python scripts/check_producer_integration.py --producer-root ../scraper-business
python3 -m http.server 8000 --bind 127.0.0.1
```

Open the local site at desktop and mobile widths. Follow the repository's
`CLAUDE.md` browser guidance. [Validation evidence](docs/validation.md) records
the reviewed widths, temporary metadata fixtures, before/after screenshots,
and producer rendering-test results. Production sample rows must stay unchanged
in static frontend changes; the checker's `--baseline` option accepts the
reviewed starting commit for such a change.
