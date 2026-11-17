#!/usr/bin/env python3
"""Convert cv.md from the ShengKaiHsu/cv repository into data/cv.json for Hugo.

Usage:
    python3 scripts/sync_cv.py                 # fetch cv.md from GitHub
    python3 scripts/sync_cv.py path/to/cv.md   # use a local copy

If the fetch or parse fails, the existing data/cv.json is left untouched and
the script exits non-zero, so a broken CV never wipes the site.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

CV_URL = "https://raw.githubusercontent.com/ShengKaiHsu/cv/main/cv.md"
OUT = Path(__file__).resolve().parent.parent / "data" / "cv.json"
ME = "**Hsu, S.-K.**"
CO_FIRST = "\\*"  # cv.md marks co-first authorship as  **Hsu, S.-K.**\*

PUB_RE = re.compile(
    r"^(?P<authors>.*?) \((?P<year>\d{4})\)\. \*\*(?P<title>.+?)\*\*\.\s*"
    r"(?P<venue>.*?)\s*(?P<doi>https?://doi\.org/\S+)?\s*$"
)
TALK_RE = re.compile(
    r"^(?P<year>\d{4})\s+\*\*(?P<title>.+?)\*\*\s*\*(?P<kind>[^*]+)\*,?\s*(?P<venue>.*)$"
)


def read_source(argv):
    if len(argv) > 1:
        return Path(argv[1]).read_text(encoding="utf-8")
    with urllib.request.urlopen(CV_URL, timeout=30) as r:
        return r.read().decode("utf-8")


def split_sections(text):
    """Return {heading: [lines]} for both '#' and '##' headings."""
    sections, current = {}, "_header"
    sections[current] = []
    for line in text.splitlines():
        m = re.match(r"^#{1,2}\s+(.*)$", line)
        if m:
            current = m.group(1).strip()
            sections[current] = []
        else:
            sections[current].append(line)
    return sections


def parse_header(lines):
    info = {}
    for line in lines:
        m = re.match(r"^\*\*(.+?):\*\*\s*(.*?)\s*$", line)
        if not m:
            continue
        key, val = m.group(1).strip().lower(), m.group(2).strip()
        link = re.match(r"^\[(.+?)\]\((.+?)\)$", val)
        if link:
            info[key] = {"label": link.group(1), "url": link.group(2)}
        else:
            info[key] = val
    return info


def parse_positions(lines):
    rows = []
    for line in lines:
        if not line.strip().startswith("|") or set(line.strip()) <= set("|-: "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0].lower() == "year":
            continue
        when, what = cells[0], cells[1]
        if not when and rows:
            # continuation row, e.g. "*Advisor: ...*"
            rows[-1]["note"] = what.strip("*").strip()
            continue
        kind = "education" if re.match(r"^(Ph\.?D|M\.?Sc|B\.?Sc|M\.?S|B\.?S)", what) else "position"
        title, _, place = what.partition(",")
        rows.append({
            "years": when.replace("present", "present"),
            "title": title.strip(),
            "place": place.strip(),
            "kind": kind,
        })
    return rows


def parse_pubs(lines):
    pubs = []
    for line in lines:
        m = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if not m:
            continue
        body = m.group(1).strip()
        p = PUB_RE.match(body)
        if not p:
            print(f"warning: could not parse publication: {body[:80]}", file=sys.stderr)
            pubs.append({"raw": body})
            continue
        authors = p.group("authors").strip()
        co_first = (ME + CO_FIRST) in authors
        plain = authors.replace(ME + CO_FIRST, ME)
        venue = p.group("venue").strip().rstrip(".").strip()
        pubs.append({
            "authors": authors,
            "year": int(p.group("year")),
            "title": p.group("title").strip(),
            "venue": venue,
            "doi": (p.group("doi") or "").rstrip("."),
            "first_author": plain.startswith(ME) and not co_first,
            "co_first_author": co_first,
            "senior_author": plain.rstrip(".").endswith(ME) and not plain.startswith(ME),
        })
    return pubs


def parse_talks(lines):
    talks = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("_"):
            continue
        t = TALK_RE.match(line)
        if t:
            talks.append({
                "year": int(t.group("year")),
                "title": t.group("title").strip().rstrip("."),
                "kind": t.group("kind").strip().replace(" presentation", "").capitalize(),
                "venue": t.group("venue").strip(),
            })
    return talks


def main(argv):
    text = read_source(argv)
    s = split_sections(text)
    name = next((k for k in s if k not in ("_header",) and s[k] is not None), "")
    updated = re.search(r"_Last updated:\s*([0-9-]+)_", text)
    data = {
        "name": name,
        "info": parse_header(s.get(name, [])),
        "positions": parse_positions(s.get("Positions & Education", [])),
        "publications": parse_pubs(s.get("Peer-reviewed Publications", [])),
        "preprints": parse_pubs(s.get("Preprints", [])),
        "presentations": parse_talks(s.get("Presentations", [])),
        "updated": updated.group(1) if updated else "",
    }
    if not data["publications"] or not data["positions"]:
        sys.exit("error: parsed CV looks empty; leaving data/cv.json unchanged")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT}: {len(data['publications'])} papers, "
          f"{len(data['preprints'])} preprints, {len(data['presentations'])} talks")


if __name__ == "__main__":
    main(sys.argv)
