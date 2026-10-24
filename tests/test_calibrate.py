import csv
from pathlib import Path

import pytest

from opci.calibrate import POINTS_FILE, fit_joint, fit_scale, load_points
from opci.index import compute

ROOT = Path(__file__).resolve().parent.parent
FIRST_SNAPSHOT = ROOT / "data" / "snapshots" / "2026-10-24"
SPEC_POINTS = [2009, 2011, 2012, 2013, 2015, 2016, 2017, 2018, 2019, 2023]


def test_every_point_has_a_source():
    with open(POINTS_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows
    for r in rows:
        assert r["source"].strip() and r["url"].startswith("https://"), r["year"]
        assert r["quality"] in ("primary", "secondary"), r["year"]
    assert len({r["year"] for r in rows}) == len(rows)


def test_spec_ten_points_reproduce_spec_scale():
    # Spec 6.4: with the 10 points, 2019 = 611.3 and 2026 = 857.6, joint rate 1.7%.
    pts = load_points(years=SPEC_POINTS)
    fit = fit_scale(pts, snapshot=FIRST_SNAPSHOT)
    assert fit["anchor"] == pytest.approx(611.3, abs=0.5)
    rows, _ = compute(anchor=fit["anchor"], snapshot=FIRST_SNAPSHOT)
    assert next(r for r in rows if r["period"] == "2026")["value"] == pytest.approx(857.6, abs=0.5)
    assert fit_joint(pts, snapshot=FIRST_SNAPSHOT)["productivity"] == pytest.approx(0.017, abs=0.001)


def test_scale_does_not_change_escalation():
    fit = fit_scale(snapshot=FIRST_SNAPSHOT)
    a, _ = compute(anchor=fit["anchor"], snapshot=FIRST_SNAPSHOT)
    b, _ = compute(anchor=100, snapshot=FIRST_SNAPSHOT)
    va = {r["period"]: r["value"] for r in a}
    vb = {r["period"]: r["value"] for r in b}
    assert va["2026"] / va["2011"] == pytest.approx(vb["2026"] / vb["2011"])


def test_fit_minimises_mean_log_error():
    # At the best fit the log errors average to zero.
    import math
    fit = fit_scale(snapshot=FIRST_SNAPSHOT)
    assert sum(math.log(1 + e) for e in fit["errors"].values()) == pytest.approx(0, abs=1e-9)
