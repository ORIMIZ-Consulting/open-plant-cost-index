"""Best-fit scale against public CEPCI annual values (METHOD section 6.4).

The scale is set by least squares on the log of the ratio OPCI / CEPCI across all
public points, not by matching one year. The scale does not change any escalation
factor. The productivity rate sets the shape and is fitted jointly only as a check.
"""
import csv
import math
from pathlib import Path

from opci.index import DEFAULT_PRODUCTIVITY, compute

ROOT = Path(__file__).resolve().parent.parent
POINTS_FILE = ROOT / "escalation" / "public_points.csv"


def load_points(path=POINTS_FILE, years=None):
    """Return {year: value} of public CEPCI annual averages."""
    with open(path, newline="", encoding="utf-8") as f:
        points = {int(r["year"]): float(r["value"]) for r in csv.DictReader(f)}
    if years is not None:
        points = {y: v for y, v in points.items() if y in set(years)}
    return points


def _unit_series(productivity, investment, snapshot):
    """Annual OPCI with 2019 = 1, full years only."""
    rows, _ = compute(investment=investment, productivity=productivity, anchor=1.0, snapshot=snapshot)
    return {int(r["period"]): r["value"] for r in rows if not r["part"]}


def fit_scale(points=None, productivity=DEFAULT_PRODUCTIVITY, investment="general", snapshot=None):
    """Fit the scale. Returns dict with anchor (OPCI 2019 value), errors by year, worst and rms."""
    points = points if points is not None else load_points()
    unit = _unit_series(productivity, investment, snapshot)
    years = sorted(y for y in points if y in unit)
    if not years:
        raise ValueError("No public points overlap the OPCI series")
    log_anchor = sum(math.log(points[y] / unit[y]) for y in years) / len(years)
    anchor = math.exp(log_anchor)
    errors = {y: anchor * unit[y] / points[y] - 1 for y in years}
    return {
        "anchor": anchor,
        "productivity": productivity,
        "years": years,
        "errors": errors,
        "worst": max(abs(e) for e in errors.values()),
        "rms": math.sqrt(sum(e * e for e in errors.values()) / len(errors)),
        "sse_log": sum(math.log(anchor * unit[y] / points[y]) ** 2 for y in years),
    }


def fit_joint(points=None, investment="general", snapshot=None, lo=0.0, hi=0.04, step=0.0005):
    """Fit scale and productivity rate together (check only). Grid search on the rate."""
    points = points if points is not None else load_points()
    best = None
    n = int(round((hi - lo) / step))
    for i in range(n + 1):
        fit = fit_scale(points, lo + i * step, investment, snapshot)
        if best is None or fit["sse_log"] < best["sse_log"]:
            best = fit
    return best
