"""Fetch the group's publications from NASA ADS into src/data/publications.json.

The site build reads only the JSON, so it never needs the ADS token. Re-run
this when new papers appear and commit the JSON.

Token: ADS_API_TOKEN, or the first line of ~/.ads/dev_key.
Run: python3 scripts/fetch_publications.py
"""

import json
import os
import re
import urllib.parse
import urllib.error
import urllib.request
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "data" / "publications.json"
PUB = ROOT / "public" / "publications.bib"

PEOPLE = ROOT / "src" / "content" / "people"


def site_members():
    """(Surname, First) for everyone with a page on the site, PI included."""
    out = []
    for f in sorted(PEOPLE.glob("*.md")):
        m = re.search(r'^name: "(.*)"', f.read_text(), re.M)
        if m:
            w = m.group(1).split()
            out.append((w[-1], w[0]))
    return out


MEMBERS = site_members()
QUERY = "author:(" + " OR ".join(f'"{last}, {first[0]}"' for last, first in MEMBERS) + ") collection:astronomy"
# Records ADS has no affiliations for (fresh preprints, Zenodo deposits) that a
# member wrote here. Without Dana on them they need to be listed by hand.
ALLOW = set()
FIELDS = "bibcode,title,author,year,pub,volume,page,doi,identifier,doctype,citation_count,orcid_pub,orcid_user,orcid_other,aff,pubdate,abstract"
# Name forms that are Dana Alina. Anything else matching "Alina, D" is a
# namesake and is dropped.
NAMES = {"alina, d.", "alina, dana", "alina, d"}


def member_indices(authors):
    """Author positions that match a site member by surname and first initial."""
    keys = {f"{last.lower()} {first[0].lower()}" for last, first in MEMBERS}
    return [i for i, a in enumerate(authors) if norm(a) in keys]


def is_ours(doc):
    """The author query also finds namesakes ("Andreev, D." for Andreyev, other
    Makarovas). A record is ours if Dana Alina is on it, if a member is listed
    at Nazarbayev University on it, or if it is in ALLOW."""
    authors = doc.get("author", [])
    if any(a.lower() in NAMES for a in authors) or doc["bibcode"] in ALLOW:
        return True
    affs = doc.get("aff") or []
    return any(i < len(affs) and "nazarbayev" in affs[i].lower() for i in member_indices(authors))

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


def search(rows=20):
    """All matching records, in pages: with per-author affiliations the Planck
    papers make one 200-row response large enough that ADS resets the connection."""
    docs, start = [], 0
    while True:
        q = urllib.parse.urlencode({"q": QUERY, "fl": FIELDS, "rows": rows, "start": start, "sort": "date desc"})
        req = urllib.request.Request(
            f"https://api.adsabs.harvard.edu/v1/search/query?{q}",
            headers={"Authorization": f"Bearer {token()}"},
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    res = json.load(r)["response"]
                break
            except (ConnectionResetError, TimeoutError, urllib.error.URLError):
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
        docs += res["docs"]
        start += rows
        if start >= res["numFound"]:
            return docs


def bibtex(bibcodes):
    """BibTeX from the ADS export endpoint, author lists cut at 10 ("and others")
    so the 200-author collaboration papers stay short. Returns {bibcode: entry}."""
    req = urllib.request.Request(
        "https://api.adsabs.harvard.edu/v1/export/bibtex",
        data=json.dumps({"bibcode": bibcodes, "maxauthor": 10, "authorlimit": 10}).encode(),
        headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        text = json.load(r)["export"]
    out = {}
    for entry in re.split(r"\n(?=@)", text.strip()):
        m = re.match(r"@\w+\{([^,]+),", entry)
        if m:
            out[m.group(1)] = entry.strip()
    return out


def norm(name):
    """'Umetaliev, Temirkul' and 'Umetaliev, T.' both become 'umetaliev t'."""
    last, _, first = name.partition(",")
    return f"{last.strip().lower()} {first.strip()[:1].lower()}"


def nu_members(docs):
    """Authors that ADS places at Nazarbayev University on at least one paper.

    ADS has no member list, and records such as Zenodo deposits or fresh arXiv
    preprints carry no affiliations, so an author seen at Nazarbayev anywhere
    in the set counts as a member everywhere. Dana Alina (PI) always counts.
    """
    members = {norm("Alina, D.")}
    for d in docs:
        for a, f in zip(d.get("author", []), d.get("aff") or []):
            if "nazarbayev" in f.lower():
                members.add(norm(a))
    return members


def role_of(authors, members):
    """'first' (member first author), 'led' (member last author), else 'collab'."""
    if norm(authors[0]) in members:
        return "first"
    return "led" if norm(authors[-1]) in members else "collab"


def is_group_led(authors, members):
    """Group-led means a group member is first or last author.

    Group = the PI and the authors that nu_members() finds. A middle-author
    position never counts, so papers where Alina is one of 40 co-authors stay
    collaboration papers.
    """
    return norm(authors[0]) in members or norm(authors[-1]) in members


def orcids(doc):
    """One ORCID iD or None per author. ADS keeps three aligned lists (from the
    publisher, claimed by the author, claimed by someone else); "-" means none."""
    n = len(doc.get("author", []))
    lists = [doc.get(k) or ["-"] * n for k in ("orcid_pub", "orcid_user", "orcid_other")]
    return [next((x for x in col if x and x != "-"), None) for col in zip(*lists)]


def arxiv_id(doc):
    for ident in doc.get("identifier", []):
        if ident.startswith("arXiv:"):
            return ident[6:]
    return None


def main():
    papers = []
    # Filter first: nu_members() spreads membership by name across the whole
    # set, so a namesake's paper would otherwise make its authors "members".
    docs = [d for d in search() if is_ours(d)]
    members = nu_members(docs)
    for d in docs:
        authors = d.get("author", [])
        idx = next((i for i, a in enumerate(authors) if a.lower() in NAMES), None)
        group = GROUPS.get(d.get("doctype"))
        if group is None:
            continue
        papers.append({
            "bibcode": d["bibcode"],
            "title": d["title"][0],
            "authors": authors,
            # Aligned with authors; "-" or "" when ADS has no affiliation.
            "aff": d.get("aff") or [""] * len(authors),
            "orcid": orcids(d),
            "alina_index": idx,  # None on a paper without Dana Alina
            # Positions of authors who have a page on the site.
            "members": member_indices(authors),
            "year": int(d["year"]),
            "pub": d.get("pub", ""),
            "volume": d.get("volume"),
            "page": (d.get("page") or [None])[0],
            "doi": (d.get("doi") or [None])[0],
            "arxiv": arxiv_id(d),
            "citations": d.get("citation_count", 0),
            "group": group,
            "doctype": d.get("doctype"),
            "led": is_group_led(authors, members),
            "role": role_of(authors, members),
            "abstract": d.get("abstract", ""),
        })
    try:
        bib = bibtex([p["bibcode"] for p in papers])
    except (OSError, KeyError) as e:
        print("BibTeX export failed, keeping any earlier entries:", e)
        bib = {}
    old = json.loads(OUT.read_text())["papers"] if OUT.exists() else []
    keep = {p["bibcode"]: p.get("bibtex") for p in old}
    for p in papers:
        p["bibtex"] = bib.get(p["bibcode"]) or keep.get(p["bibcode"]) or ""
    PUB.write_text("\n\n".join(p["bibtex"] for p in papers if p["bibtex"]) + "\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"query": QUERY, "groups": list(dict.fromkeys(GROUPS.values())), "papers": papers}, indent=1, ensure_ascii=False))
    by = {}
    for p in papers:
        by[p["group"]] = by.get(p["group"], 0) + 1
    print(len(papers), by)


if __name__ == "__main__":
    main()
