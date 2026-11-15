#!/usr/bin/env python3
"""Fetch the Alina et al. 2019 filament table and write src/data/orientations.json.

Source: VizieR J/MNRAS/485/2825/tablea1 (MNRAS 485, 2825; arXiv:1712.09325),
read from the CfA mirror because the main CDS server is not always up.

The table has one row per filament (138 rows). Per row: position, length,
width, SupRHT position angle of the filament, mean column density over the
filament (NHtot), over the filament without clumps (NHfil), over the background
region (NHbkg), and for 93 rows the mean field angle inside the filament
(psi1, circular statistics, with its dispersion; psi2, Gaussian fit).
It has no field angle for the background, no pixel data, no distances.

Run: python3 scripts/fetch_catalogues.py
The checks at the end compare the table with numbers the paper states in the
text and print every disagreement. They do not abort the run.
"""
import json
import statistics as st
import urllib.request
from pathlib import Path

URL = (
    "https://vizier.cfa.harvard.edu/viz-bin/asu-tsv?-source=J/MNRAS/485/2825/tablea1"
    "&-out.max=999"
)
OUT = Path(__file__).resolve().parent.parent / "src" / "data" / "orientations.json"


def num(s):
    s = s.strip()
    return float(s) if s else None


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "ism-website-build"})
    with urllib.request.urlopen(req, timeout=60) as r:
        text = r.read().decode("utf-8")
    lines = [l.rstrip("\n").split("\t") for l in text.splitlines() if l.strip() and not l.startswith("#")]
    head = lines[0]
    return [dict(zip(head, r)) for r in lines[3:]]  # skip the unit and rule lines


def fold180(a):
    return a % 180.0


def main():
    raw = fetch()
    rows = []
    for r in raw:
        rows.append(
            {
                "id": int(r["ID"]),  # PGCC number
                "l": num(r["GLON"]),
                "b": num(r["GLAT"]),
                "len": num(r["s"]),  # arcmin
                "wid": num(r["w"]),  # arcmin
                "pa": fold180(num(r["PAfil2"])),  # filament position angle, deg, IAU, mod 180
                "nh": num(r["NHtot"]),  # 1e20 cm-2, mean over the filament
                "nhfil": num(r["NHfil"]),  # 1e20 cm-2, filament without clumps
                "psi1": None if num(r["psi1"]) is None else fold180(num(r["psi1"])),
                "psi2": None if num(r["psi2"]) is None else fold180(num(r["psi2"])),
                "sig": num(r["e_psi1"]),  # dispersion of the field angle in the filament, deg
            }
        )
    rows.sort(key=lambda r: r["id"])

    n = len(rows)
    withpsi = [r for r in rows if r["psi1"] is not None]
    checks = []

    def check(label, paper, ours, ok):
        checks.append({"label": label, "paper": paper, "table": ours, "agree": bool(ok)})

    check("filaments in the table vs pre-selection in Sect. 2.2", 137, n, n == 137)
    check("filaments with a field angle vs 'uniform background' selection (Sect. 3.1)", 90, len(withpsi), len(withpsi) == 90)
    sig = [r["sig"] for r in withpsi]
    check("field-angle dispersion range, deg (Sect. 3.2: 6 to 73)", "6 to 73", f"{min(sig):.0f} to {max(sig):.0f}", round(min(sig)) == 6 and round(max(sig)) == 73)
    check("mean field-angle dispersion, deg (Sect. 3.2: 40)", 40, round(st.mean(sig)), round(st.mean(sig)) == 40)
    ln = [r["len"] for r in rows]
    check("filament length range, arcmin (Sect. 3.2: 34 to 104)", "34 to 104", f"{min(ln):.0f} to {max(ln):.0f}", min(ln) == 34 and abs(max(ln) - 104) <= 1)
    check("mean length, arcmin (Sect. 3.2: 66)", 66, round(st.mean(ln), 1), abs(st.mean(ln) - 66) < 1.5)
    wd = [r["wid"] for r in rows]
    check("filament width range, arcmin (Sect. 3.2: 4 to 20)", "4 to 20", f"{min(wd):.0f} to {max(wd):.0f}", min(wd) == 4 and max(wd) == 20)
    check("mean width, arcmin (Sect. 3.2: 8)", 8, round(st.mean(wd), 1), abs(st.mean(wd) - 8) < 0.5)
    dup = sum(1 for r in raw if r["NHtot"].strip() == r["NHbkg"].strip() and r["e_NHtot"].strip() == r["e_NHbkg"].strip())
    check("rows where NHbkg differs from NHtot (needed for the contrast, Eq. 7)", "differ", n - dup, n - dup > n // 2)

    out = {
        "source": {
            "paper": "Alina et al. 2019, MNRAS 485, 2825",
            "bibcode": "2019MNRAS.485.2825A",
            "arxiv": "1712.09325",
            "vizier": "J/MNRAS/485/2825/tablea1",
            "fetched_from": URL,
        },
        "columns": ["id", "l", "b", "len", "wid", "pa", "nh", "nhfil", "psi1", "psi2", "sig"],
        "rows": [[r[k] for k in ("id", "l", "b", "len", "wid", "pa", "nh", "nhfil", "psi1", "psi2", "sig")] for r in rows],
        "checks": checks,
    }
    OUT.write_text(json.dumps(out, separators=(",", ":")) + "\n")

    print(f"{n} rows, {len(withpsi)} with a field angle -> {OUT}")
    for c in checks:
        print(("ok       " if c["agree"] else "MISMATCH ") + f"{c['label']}: paper {c['paper']}, table {c['table']}")


if __name__ == "__main__":
    main()
