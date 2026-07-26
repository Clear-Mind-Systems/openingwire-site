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

Each pricing button is a single `href` in `index.html` (three `mailto:` links under
`id="pricing"`). Replace each with its Stripe payment link URL. Nothing else changes.

## Updating the sample table

Rows live in the `id="sample"` table in `index.html`. Source fresh rows from the
pipeline repo (`reports/<week>/statewide.csv`, newest licensed venues with trade names).
