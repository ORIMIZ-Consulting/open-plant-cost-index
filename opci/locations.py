"""OPCI location module (location/METHOD_LOCATION.md).

Location factors against the US Gulf Coast (= 1.00), with range, confidence and
source. This module shares no code with the escalation module. The two meet only
at the combined factor step.
"""
import csv
import math

import yaml

from opci import paths

LOCATION_DIR = paths.LOCATION_DIR
REFERENCE = "US-GC"
CONFIDENCE_ORDER = ("low", "medium", "high")

# Decided range rule (spec 7.2): ranges lean upward.
RANGE_RULE = {"high": (0.10, 0.10), "medium": (0.10, 0.15), "low": (0.15, 0.25)}


def version():
    return (LOCATION_DIR / "VERSION").read_text().strip()


def load_sources():
    return yaml.safe_load((LOCATION_DIR / "sources.yaml").read_text(encoding="utf-8"))


def load_factors():
    """Return {code: row} from location/factors.csv, with numbers as floats."""
    with open(LOCATION_DIR / "factors.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    table = {}
    for r in rows:
        for k in ("factor", "low", "high"):
            r[k] = float(r[k])
        r["as_of"] = int(r["as_of"])
        table[r["code"]] = r
    return table


def _get(table, code):
    if code not in table:
        raise KeyError(f"Unknown location code {code!r}. Known codes: {', '.join(table)}")
    return table[code]


def _devs(row):
    """Relative low and high deviations of a row's range from its central factor."""
    return 1 - row["low"] / row["factor"], row["high"] / row["factor"] - 1


def location(to, frm=REFERENCE):
    """Location factor for moving a cost from `frm` to `to`.

    factor = factor(to) / factor(frm).
    From the reference: the range of `to` as it stands in the table.
    Between two other places: relative deviations combined by root sum of squares,
      low  dev = sqrt(to_low_dev^2  + frm_high_dev^2)
      high dev = sqrt(to_high_dev^2 + frm_low_dev^2)
    applied to the central ratio. Same place: factor 1 with no range.
    Confidence is the lower of the two.
    """
    table = load_factors()
    sources = load_sources()
    b, a = _get(table, to), _get(table, frm)
    conf = min(a["confidence"], b["confidence"], key=CONFIDENCE_ORDER.index)
    rows = [b] if frm == to or frm == REFERENCE else [a, b]
    ratio = b["factor"] / a["factor"]
    if frm == to:
        low, high = 1.0, 1.0
    elif frm == REFERENCE:
        low, high = b["low"], b["high"]
    else:
        b_low, b_high = _devs(b)
        a_low, a_high = _devs(a)
        low = ratio * (1 - math.hypot(b_low, a_high))
        high = ratio * (1 + math.hypot(b_high, a_low))
    return {
        "factor": ratio,
        "low": low,
        "high": high,
        "confidence": conf,
        "to": to,
        "frm": frm,
        "to_name": b["name"],
        "frm_name": a["name"],
        "method": "; ".join(f"{r['code']}: {r['method']}" for r in rows),
        "source": " | ".join(sorted({sources.get(r["source"], r["source"]).strip() for r in rows})),
        "as_of": min(r["as_of"] for r in rows),
        "notes": {r["code"]: r["notes"] for r in rows if r["notes"]},
        "location_version": version(),
    }
