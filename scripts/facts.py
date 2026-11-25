"""Facts shared with the website, read from src/data/facts.json (the one place they are typed)."""
import json
from pathlib import Path

FACTS = json.loads((Path(__file__).resolve().parent.parent / "src" / "data" / "facts.json").read_text())


def field(name):
    """(Galactic l, b, width) in degrees of a sky field the site shows on a card."""
    f = FACTS["fields"][name]
    return f["l"], f["b"], f["width"]
