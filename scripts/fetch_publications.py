"""Fetch the group's publications from NASA ADS into src/data/publications.json.

The site build reads only the JSON, so it never needs the ADS token. Re-run
this when new papers appear and commit the JSON.

Token: ADS_API_TOKEN, or the first line of ~/.ads/dev_key.
Run: python3 scripts/fetch_publications.py
"""

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "data" / "publications.json"

QUERY = 'author:"Alina, D" collection:astronomy'
FIELDS = "bibcode,title,author,year,pub,volume,page,doi,identifier,doctype,citation_count,orcid_pub,aff,pubdate"
# Name forms that are Dana Alina. Anything else matching "Alina, D" is a
# namesake and is dropped.
NAMES = {"alina, d.", "alina, dana", "alina, d"}

# ADS doctype -> site group. Order is the order on the page.
GROUPS = {
    "article": "Papers",
    "eprint": "Preprints",
    "inproceedings": "Proceedings and talks",
    "abstract": "Proceedings and talks",
    "catalog": "Data and code",
    "software": "Data and code",
    "proposal": "Proposals",
    "phdthesis": "Theses",
}


def token():
    t = os.environ.get("ADS_API_TOKEN")
    if t:
        return t.strip()
    return (Path.home() / ".ads" / "dev_key").read_text().split()[0]


def search():
    q = urllib.parse.urlencode({"q": QUERY, "fl": FIELDS, "rows": 200, "sort": "date desc"})
    req = urllib.request.Request(
        f"https://api.adsabs.harvard.edu/v1/search/query?{q}",
        headers={"Authorization": f"Bearer {token()}"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["response"]["docs"]


def arxiv_id(doc):
    for ident in doc.get("identifier", []):
        if ident.startswith("arXiv:"):
            return ident[6:]
    return None


def main():
    papers = []
    for d in search():
        authors = d.get("author", [])
        idx = next((i for i, a in enumerate(authors) if a.lower() in NAMES), None)
        if idx is None:
            continue
        group = GROUPS.get(d.get("doctype"))
        if group is None:
            continue
        papers.append({
            "bibcode": d["bibcode"],
            "title": d["title"][0],
            "authors": authors,
            "alina_index": idx,
            "year": int(d["year"]),
            "pub": d.get("pub", ""),
            "volume": d.get("volume"),
            "page": (d.get("page") or [None])[0],
            "doi": (d.get("doi") or [None])[0],
            "arxiv": arxiv_id(d),
            "citations": d.get("citation_count", 0),
            "group": group,
            "doctype": d.get("doctype"),
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"query": QUERY, "groups": list(dict.fromkeys(GROUPS.values())), "papers": papers}, indent=1, ensure_ascii=False))
    by = {}
    for p in papers:
        by[p["group"]] = by.get(p["group"], 0) + 1
    print(len(papers), by)


if __name__ == "__main__":
    main()
