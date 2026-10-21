#!/usr/bin/env python3
"""Check OpeningWire's static publishing interface; uses only Python's stdlib.

Run from any directory: python3 scripts/check_site.py
Optional --write-fixtures /tmp/ow-fixtures writes synthetic browser fixtures
outside the checkout. No source pages or generated sample rows are changed.
"""
import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import parse_qs, unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET

BASELINE = "f97528e7fd3350782da46bc85450c10a7623ce59"
ORIGIN = "https://openingwire.com"
START, END = "<!-- SAMPLE:START -->", "<!-- SAMPLE:END -->"
FRESH_START, FRESH_END = "<!-- SAMPLE-FRESHNESS:START -->", "<!-- SAMPLE-FRESHNESS:END -->"
REQUIRED_SOURCES = {"pending_applications", "issued_licenses", "pending_refresh"}
VOID = set("area base br col embed hr img input link meta param source track wbr".split())


def normalized(value):
    return " ".join(value.split())


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)

    def nodes(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.nodes()

    def raw_text(self):
        return "".join(c.raw_text() if isinstance(c, Node) else c for c in self.children)

    def text(self):
        return normalized(self.raw_text())

    def has_class(self, name):
        return name in self.attrs.get("class", "").split()


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]
        self.feed(source)
        self.close()
        self.nodes = list(self.root.nodes())[1:]
        self.ids = {n.attrs["id"]: n for n in self.nodes if "id" in n.attrs}

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def sample(source):
    if source.count(START) != 1 or source.count(END) != 1:
        raise ValueError("requires exactly one SAMPLE start/end pair")
    start, end = source.index(START) + len(START), source.index(END)
    if start >= end:
        raise ValueError("SAMPLE markers are not ordered")
    return source[start:end]


def public_path(path):
    return "/" + (path[:-10] if path.endswith("index.html") else path)


def faq_objects(value):
    if isinstance(value, dict):
        if value.get("@type") == "FAQPage":
            yield value
        for child in value.values():
            yield from faq_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from faq_objects(child)


def provenance_errors(root, sources, marketing):
    """Verify the complete generated bundle, without inferring deployment.

    The archived fallback deliberately has no sidecar. Generated cards require
    one matching sidecar for all eight pages, including completeness evidence.
    Hashes identify producer rows, not opening status or business qualification.
    """
    generated = {path for path in marketing if Document(sources[path]).ids.get(
        "sample-freshness", Node("missing")).attrs.get("data-source-freshness")}
    metadata_path = root / "data/sample-metadata.json"
    if not generated:
        return ["orphan sample metadata without generated cards"] if metadata_path.exists() else []
    errors = []
    if generated != marketing:
        errors.append("generated and archived sample modes are mixed across pages")
    try:
        metadata = json.loads(metadata_path.read_text())
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")
        pages = metadata["pages"]
        readiness = metadata["source_readiness"]
        if not isinstance(pages, dict) or set(pages) != marketing:
            raise ValueError("metadata page inventory differs from the eight pages")
        if not isinstance(readiness, dict) or type(readiness.get("ready")) is not bool:
            raise ValueError("source readiness needs an explicit boolean")
        if readiness.get("status") != ("ready" if readiness["ready"] else "blocked"):
            raise ValueError("source readiness status contradicts its gate")
        reasons = readiness.get("reasons")
        if not isinstance(reasons, list) or any(not isinstance(r, str) or not r for r in reasons):
            raise ValueError("source readiness reasons must be nonempty strings")
        if readiness["ready"] != (not reasons):
            raise ValueError("source readiness reasons contradict its gate")
        source_evidence = readiness.get("sources")
        if not isinstance(source_evidence, dict) or set(source_evidence) != REQUIRED_SOURCES:
            raise ValueError("required source evidence is incomplete")
        generated_at = datetime.strptime(metadata["generated_at"], "%Y-%m-%dT%H:%M:%SZ")
        threshold = metadata["freshness_thresholds_hours"]["source_ingest"]
        if type(threshold) not in {int, float} or threshold != 48:
            raise ValueError("unsupported source freshness threshold")
        if readiness["ready"] and readiness.get("latest_ingest_status") != "ok":
            raise ValueError("latest ingest status contradicts ready gate")
        for name, evidence in source_evidence.items():
            if not isinstance(evidence, dict) or evidence.get("status") not in {"fresh", "stale", "missing", "invalid"}:
                raise ValueError(f"{name} source evidence has an invalid freshness state")
            if readiness["ready"] and (evidence["status"] != "fresh" or evidence.get("latest_status") != "ok"):
                raise ValueError(f"{name} source contradicts ready gate")
            if evidence["status"] in {"fresh", "stale"}:
                success = datetime.strptime(evidence["last_successful_at"], "%Y-%m-%dT%H:%M:%SZ")
                age_hours = (generated_at - success).total_seconds() / 3600
                expected = "fresh" if 0 <= age_hours <= threshold else "stale"
                if age_hours < 0 or evidence["status"] != expected:
                    raise ValueError(f"{name} freshness contradicts source clock")
                if evidence.get("latest_status") == "ok" and evidence.get("latest_attempt_at") != evidence["last_successful_at"]:
                    raise ValueError(f"{name} latest success clock is inconsistent")
        for path in generated:
            item = pages[path]
            interior = sample(sources[path])
            if not interior.startswith("\n") or "\n" not in interior[1:]:
                raise ValueError(f"{path}: generated row boundaries are invalid")
            rows = interior[1:].rsplit("\n", 1)[0]
            digest = hashlib.sha256(rows.encode()).hexdigest()
            if item.get("rows_sha256") != digest:
                errors.append(f"{path}: sample rows differ from metadata hash")
            venue_rows = [n for n in Document(rows).nodes if n.tag == "tr"
                          and not n.has_class("seo-teaser") and not n.has_class("sample-freshness")]
            if type(item.get("row_count")) is not int or item["row_count"] != len(venue_rows):
                errors.append(f"{path}: sample row count differs from metadata")
            card = Document(sources[path]).ids["sample-freshness"].text()
            if not readiness["ready"] and "publication and delivery blocked" not in card:
                errors.append(f"{path}: blocked sources lack visible publication/delivery hold")
            if readiness["ready"] and "publication and delivery blocked" in card:
                errors.append(f"{path}: ready sources contradict a visible blocked status")
        if metadata.get("published_at") is not None:
            errors.append("publication must remain unverified in local producer metadata")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append(f"missing/invalid producer bundle: {exc}")
    return errors


def check_site(root, baseline):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    tracked = git(root, "ls-tree", "-r", "--name-only", baseline).decode().splitlines()
    previous = {p: git(root, "show", f"{baseline}:{p}").decode() for p in tracked if p.endswith(".html")}
    marketing = {p for p, source in previous.items() if START in source}
    require(len(marketing) == 8, "baseline must contain the eight marketing marker pages")
    sources = {str(p.relative_to(root)): p.read_bytes().decode() for p in root.rglob("*.html") if ".git" not in p.parts}
    docs = {p: Document(source) for p, source in sources.items()}
    require({p for p, s in sources.items() if START in s} == marketing, "marketing marker page inventory changed")
    if marketing <= sources.keys():
        errors.extend(provenance_errors(root, sources, marketing))

    for path, doc in docs.items():
        prefix = f"{path}: "
        ids = [n.attrs["id"] for n in doc.nodes if "id" in n.attrs]
        require(len(ids) == len(set(ids)), prefix + "duplicate HTML ids")
        for node in doc.nodes:
            require(not any(a.startswith("on") for a in node.attrs), prefix + "executable event handler")
            for attr in ("aria-labelledby", "aria-describedby"):
                for target in node.attrs.get(attr, "").split():
                    require(target in doc.ids, prefix + f"{attr} points to missing #{target}")
            if node.tag == "script":
                require(node.attrs.get("type") == "application/ld+json", prefix + "executable JavaScript")
                try:
                    structured = json.loads(node.raw_text())
                except json.JSONDecodeError as exc:
                    errors.append(prefix + f"invalid JSON-LD: {exc}")
                    continue
                for faq in faq_objects(structured):
                    visible = []
                    for section in doc.nodes:
                        if section.has_class("seo-faq") or section.attrs.get("id") == "faq":
                            sequence = [n for n in section.nodes() if n.tag in {"h3", "p"}]
                            visible.extend((sequence[i].text(), sequence[i + 1].text())
                                           for i in range(len(sequence) - 1)
                                           if sequence[i].tag == "h3" and sequence[i + 1].tag == "p")
                    try:
                        structured_pairs = [(normalized(q["name"]), normalized(q["acceptedAnswer"]["text"]))
                                            for q in faq["mainEntity"]]
                        require(structured_pairs == visible and bool(visible), prefix + "FAQ JSON-LD differs from visible FAQ")
                    except (KeyError, TypeError, AttributeError):
                        errors.append(prefix + "malformed FAQ structured data")
            for attr in ("href", "src"):
                if attr not in node.attrs:
                    continue
                href = node.attrs[attr] or ""
                parsed = urlsplit(href)
                require(parsed.scheme != "javascript", prefix + "JavaScript URL")
                if parsed.scheme == "mailto":
                    if "sample" in node.text().lower():
                        require(parsed.path.lower() == "founders@openingwire.com", prefix + "sample-request recipient must be founders@openingwire.com")
                    if parsed.path.lower() == "founders@openingwire.com":
                        query = parse_qs(parsed.query)
                        require(all(query.get(key, [""])[0].strip() for key in ("subject", "body")), prefix + "sample mailto needs subject and body")
                    continue
                target = urlsplit(urljoin(ORIGIN + public_path(path), href))
                if target.scheme not in {"http", "https"} or target.netloc not in {"openingwire.com", "www.openingwire.com"}:
                    continue
                local = unquote(target.path).lstrip("/")
                if not local or local.endswith("/"):
                    local += "index.html"
                require((root / local).is_file(), prefix + f"broken internal URL {href}")
                if target.fragment:
                    require(local in docs and unquote(target.fragment) in docs[local].ids, prefix + f"broken fragment {href}")

    for path in sorted(marketing):
        if path not in docs:
            errors.append(f"missing marketing page: {path}")
            continue
        source, doc, old = sources[path], docs[path], previous[path]
        prefix = f"{path}: "
        try:
            require(sample(source) == sample(old), prefix + "generated SAMPLE bytes changed")
        except ValueError as exc:
            errors.append(prefix + str(exc))
        require(source.count(FRESH_START) == source.count(FRESH_END) == 1,
                prefix + "requires exactly one SAMPLE-FRESHNESS pair")
        if source.count(FRESH_START) == source.count(FRESH_END) == 1:
            start, end = source.index(FRESH_START), source.index(FRESH_END)
            require(start < end < source.find("<table"), prefix + "freshness region must precede table")
            region = Document(source[start:end])
            require("sample-freshness" in region.ids and "sample-status-title" in region.ids,
                    prefix + "freshness markers must contain the complete labelled fallback")
        require(source.count("<!-- seo-pages:v1 -->") == old.count("<!-- seo-pages:v1 -->"), prefix + "changed seo-pages:v1 marker")
        for block in ("METRO-LINKS", "B2B-LINKS"):
            for boundary in ("START", "END"):
                marker = f"<!-- {block}:{boundary} -->"
                require(source.count(marker) == old.count(marker), prefix + f"changed {marker}")
            region = rf"<!-- {block}:START -->.*?<!-- {block}:END -->"
            # The paired producer owns this one conservative label migration.
            # All marker boundaries, destinations and remaining bytes stay fixed.
            old_regions = [value.replace("New openings by metro:", "TABC license records by metro:")
                           .replace("Sell to new restaurants and bars:", "Explore TABC licensing signals:")
                           for value in re.findall(region, old, re.S)]
            require(re.findall(region, source, re.S) == old_regions, prefix + f"producer-owned {block} bytes changed")
        canonicals = [n.attrs.get("href") for n in doc.nodes if n.tag == "link" and n.attrs.get("rel") == "canonical"]
        require(canonicals == [ORIGIN + public_path(path)], prefix + "canonical URL does not match page")
        for element_id, tag in (("sample-title", "h2"), ("sample-status-title", "h3"), ("sample-dates", "p")):
            require(element_id in doc.ids and doc.ids[element_id].tag == tag, prefix + f"missing accessible {tag}#{element_id}")
        limits = doc.ids.get("signal-limits")
        require(limits is not None and all(term in limits.text().lower() for term in
                ("existing venue", "ownership", "separate supporting evidence", "verified business contacts")),
                prefix + "missing conservative licensing-signal and contact limitations")
        status = doc.ids.get("sample-freshness")
        require(status is not None and status.tag == "div" and status.has_class("sample-freshness") and status.attrs.get("aria-labelledby") == "sample-status-title", prefix + "missing labelled freshness explanation")
        if status:
            state = status.attrs.get("data-source-freshness")
            if state is None:
                require("unknown" in status.text().lower() and "unavailable" in status.text().lower(), prefix + "source-refresh fallback must explicitly say unknown/unavailable")
                require(bool(re.search(r"\b20\d{2}\b", status.text())), prefix + "archive provenance lacks a year")
            else:
                require(state in {"fresh", "stale", "missing", "invalid"}, prefix + "unsupported producer freshness state")
                require("does not update between publications" in status.text(), prefix + "generated status must disclose its static clock")
                require("Publication: unverified" in status.text(), prefix + "generation must not claim publication")
                require("Archive reference:" not in status.text(), prefix + "generated provenance retains historical fallback")
                if state in {"fresh", "stale"}:
                    require("unknown" not in status.text().lower() and "unavailable" not in status.text().lower(), prefix + "known source contradicts unknown fallback")
                else:
                    require("Source freshness unknown" in status.text(), prefix + "missing/invalid source must remain unknown")
                try:
                    metadata = json.loads((root / "data/sample-metadata.json").read_text())
                    require(metadata["contract_version"] == 1 and metadata["source_freshness"] == state,
                            prefix + "rendered freshness differs from producer metadata")
                    require(metadata["published_at"] is None, prefix + "publication evidence is not supported by this contract")
                    stamps = [n.attrs.get("datetime") for n in status.nodes() if n.tag == "time"]
                    expected = [v for v in (metadata["source_ingest_succeeded_at"], metadata["generated_at"]) if v]
                    require(stamps == expected and all(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", v) for v in stamps),
                            prefix + "rendered UTC evidence differs from producer metadata")
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    errors.append(prefix + f"missing/invalid producer metadata: {exc}")
            require(any(n.tag == "a" and n.attrs.get("href", "").startswith("mailto:founders@openingwire.com?") for n in status.nodes()), prefix + "freshness explanation needs a sample-request link")
        wrappers = [n for n in doc.nodes if n.has_class("table-scroll")]
        require(len(wrappers) == 1, prefix + "needs one scrollable sample region")
        for wrapper in wrappers:
            require(all(wrapper.attrs.get(k) == v for k, v in {"role": "region", "tabindex": "0", "aria-labelledby": "sample-title", "aria-describedby": "sample-dates"}.items()), prefix + "table scroll region is not keyboard accessible / labelled")
            tables = [n for n in wrapper.nodes() if n.tag == "table"]
            require(len(tables) == 1, prefix + "scroll region needs one sample table")
            for table in tables:
                require(any(n.tag == "caption" and n.text() for n in table.nodes()), prefix + "sample table needs a caption")
                headers = [n for n in table.nodes() if n.tag == "th"]
                require(all(n.attrs.get("scope") == "col" for n in headers), prefix + "table headers need scope=col")
                old_headers = [n.text() for n in Document(old).nodes if n.tag == "th"]
                require([n.text() for n in headers] == old_headers, prefix + "producer table columns changed")
        if 'class="seo-teaser"' in source:
            css = " ".join(n.raw_text() for n in doc.nodes if n.tag == "style")
            require(bool(re.search(r"[^{}]*\.seo-teaser[^{}]*\{[^{}]*\bdisplay\s*:\s*none\b", css)), prefix + "unsupported generated teaser must stay hidden pending producer change")
        links = {urlsplit(urljoin(ORIGIN + public_path(path), n.attrs.get("href", ""))).path for n in doc.nodes if n.tag == "a"}
        require({"/terms.html", "/privacy.html"} <= links, prefix + "legal pages are not linked")

    current, old = docs.get("index.html"), Document(previous["index.html"])
    if current:
        stripe = lambda doc: Counter(n.attrs["href"] for n in doc.nodes if n.attrs.get("href", "").startswith("https://buy.stripe.com/"))
        require(sum(stripe(current).values()) == 3 and stripe(current) == stripe(old), "homepage Stripe checkout targets changed")
        prices = lambda doc: [n.text() for n in doc.nodes if n.has_class("price")]
        require(prices(current) == prices(old), "homepage prices changed")
    try:
        sitemap = ET.parse(root / "sitemap.xml")
        urls = [node.text for node in sitemap.findall("{*}url/{*}loc")]
        require(Counter(urls) == Counter(ORIGIN + public_path(p) for p in marketing), "sitemap must contain exactly the eight marketing URLs (legal pages remain linked)")
    except (ET.ParseError, OSError) as exc:
        errors.append(f"invalid sitemap: {exc}")
    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        return False
    print(f"PASS: {len(marketing)} marketing pages; generated bytes/markers/columns; prices and 3 Stripe URLs; links/mailto/canonical/sitemap/legal; FAQ JSON-LD; static and accessible sample markup.")
    return True


def write_fixtures(root, destination):
    """Render labelled contract examples, never production metadata.

    Actual producer compatibility is tested by check_producer_integration.py.
    """
    if destination == root or root in destination.parents:
        raise ValueError("fixture destination must be outside the checkout")
    contract = (root / "docs/sample-generation-contract.md").read_text()
    examples = re.findall(r"```html\n(.*?)\n```", contract, re.S)
    states, long_row = {}, None
    for example in examples:
        doc = Document(example)
        status = doc.ids.get("sample-freshness")
        if status:
            states[status.attrs.get("data-source-freshness")] = example
        elif any(n.tag == "tr" for n in doc.nodes):
            long_row = example
    if set(states) != {"fresh", "stale", "missing"} or not long_row:
        raise ValueError("contract must supply the three metadata examples and long-name/year row")
    homepage = (root / "index.html").read_text()
    pattern = r'<div\b[^>]*\bid="sample-freshness"[^>]*>.*?</div>'
    fallback = re.search(pattern, homepage, re.S)
    if not fallback:
        raise ValueError("homepage unknown-refresh fallback is missing")
    states["unknown"] = fallback.group()
    destination.mkdir(parents=True, exist_ok=True)
    for state, status in states.items():
        name = state
        doc = Document(status)
        if "sample-status-title" not in doc.ids:
            raise ValueError(f"{state} fixture lacks its status heading")
        for node in doc.nodes:
            if node.tag == "time" and state in {"fresh", "stale"}:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", node.attrs.get("datetime", "")):
                    raise ValueError(f"{state} fixture lacks an explicit UTC timestamp")
            if node.tag == "a":
                link = urlsplit(node.attrs.get("href", ""))
                query = parse_qs(link.query)
                if link.path != "founders@openingwire.com" or not all(query.get(key, [""])[0].strip() for key in ("subject", "body")):
                    raise ValueError(f"{state} fixture has an incomplete sample-request mailto")
        page = homepage[:fallback.start()] + status + homepage[fallback.end():]
        banner = (f'<p style="padding:1rem;border:3px solid #141a24;background:#fff">'
                  f'<strong>Temporary QA fixture: {name}.</strong> '
                  'Example metadata and the extra long-name row are synthetic. '
                  'Archived venue rows are retained for layout testing only.</p>')
        page = page.replace("<main>", "<main>" + banner, 1)
        page = page.replace(START, long_row + "\n      " + START, 1)
        if sample(page) != sample(homepage):
            raise ValueError("fixture modified producer-owned sample bytes")
        (destination / f"{name}.html").write_text(page)
    print(f"PASS: labelled contract fixtures outside checkout: {destination}/{{fresh,stale,missing,unknown}}.html")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default=BASELINE, help="git ref whose generated sample bytes, prices and checkout destinations must survive")
    parser.add_argument("--write-fixtures", type=Path, help="write synthetic freshness/layout pages to a directory outside this checkout")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if not check_site(root, args.baseline):
            return 1
        if args.write_fixtures:
            write_fixtures(root, args.write_fixtures.resolve())
        return 0
    except (OSError, subprocess.CalledProcessError, UnicodeError, ValueError) as exc:
        print(f"FAIL: cannot inspect site/baseline: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
