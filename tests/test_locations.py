import ast
from pathlib import Path

import pytest

from opci.locations import RANGE_RULE, load_factors, load_sources, location, version

ROOT = Path(__file__).resolve().parent.parent


def test_every_row_complete():
    sources = load_sources()
    for code, r in load_factors().items():
        assert r["name"] and r["method"] and r["as_of"], code
        assert r["source"] in sources, code
        assert r["confidence"] in RANGE_RULE, code
        assert r["low"] < r["factor"] < r["high"], code


def test_ranges_follow_decided_rule():
    for code, r in load_factors().items():
        down, up = RANGE_RULE[r["confidence"]]
        assert r["low"] == pytest.approx(r["factor"] * (1 - down), abs=0.006), code
        assert r["high"] == pytest.approx(r["factor"] * (1 + up), abs=0.006), code


def test_reference_is_one():
    assert load_factors()["US-GC"]["factor"] == 1.0


def test_from_reference_returns_table_row():
    r = location(to="ID-KAL")
    assert (r["factor"], r["low"], r["high"], r["confidence"]) == (1.20, 1.08, 1.38, "medium")
    assert "OIES" in r["source"] and r["location_version"] == version()


def test_a_to_b_is_ratio():
    # Spec 7.4: Ichthys (North West Australia) moved to East Kalimantan: x 0.70.
    r = location(to="ID-KAL", frm="AU-NW")
    assert r["factor"] == pytest.approx(1.20 / 1.72)
    assert round(r["factor"], 2) == 0.70
    t = load_factors()
    for a in t:
        for b in t:
            assert location(to=b, frm=a)["factor"] == pytest.approx(t[b]["factor"] / t[a]["factor"])


def test_confidence_is_the_lower():
    assert location(to="REMOTE", frm="ID-KAL")["confidence"] == "low"
    assert location(to="ID-KAL", frm="US-GC")["confidence"] == "medium"


def test_unknown_code():
    with pytest.raises(KeyError, match="Unknown location code"):
        location(to="XX")


def test_no_shared_code_with_escalation():
    tree = ast.parse((ROOT / "opci" / "locations.py").read_text())
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    imported |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not {m for m in imported if m and m.startswith("opci")}
