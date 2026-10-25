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


def test_range_between_two_places_root_sum_of_squares():
    # Owner check: AU-NW to ID-KAL gives x0.70, about 0.57 to 0.83.
    r = location(to="ID-KAL", frm="AU-NW")
    assert round(r["factor"], 2) == 0.70
    assert r["low"] == pytest.approx(0.57, abs=0.005) and r["high"] == pytest.approx(0.83, abs=0.01)
    b_low, b_high = 1 - 1.08 / 1.20, 1.38 / 1.20 - 1
    a_low, a_high = 1 - 1.55 / 1.72, 1.98 / 1.72 - 1
    ratio = 1.20 / 1.72
    assert r["low"] == pytest.approx(ratio * (1 - (b_low ** 2 + a_high ** 2) ** 0.5))
    assert r["high"] == pytest.approx(ratio * (1 + (b_high ** 2 + a_low ** 2) ** 0.5))


def test_same_place_has_no_range():
    r = location(to="AU-NW", frm="AU-NW")
    assert (r["factor"], r["low"], r["high"]) == (1.0, 1.0, 1.0)


def test_step_rule_rows_have_trail_and_2026():
    table = load_factors()
    for code, r in table.items():
        if r["method"].startswith("step rule"):
            assert r["as_of"] == 2026, code
            # "Start REMOTE 1.30 (OIES ..., 2018); -0.10 ...; +0.10 ... = 1.40."
            # or "Start REMOTE 1.30 (OIES ..., 2018); no step (reason) = 1.30."
            trail = r["notes"].split(" = ")[0]
            start, *steps = [s.strip() for s in trail.split(";")]
            group, value = start.split()[1:3]
            assert table[group]["factor"] == float(value), code
            steps = [s for s in steps if not s.startswith("no step")]
            total = float(value) + sum(float(s.split()[0]) for s in steps)
            assert total == pytest.approx(r["factor"]), code
            assert f"= {r['factor']:.2f}" in r["notes"], code
        elif r["method"] == "published group":
            assert r["as_of"] == 2018, code


NEW_IN_0_2_0 = {
    # code: (factor, trail)
    "NG-BON": (1.20, "Start REMOTE 1.30 (OIES remote group, 2018); -0.10 existing LNG hub (six trains at Bonny) = 1.20."),
    "MZ-AFU": (1.40, "Start REMOTE 1.30 (OIES remote group, 2018); +0.10 first-of-a-kind remote site with no infrastructure = 1.40."),
    "AO-SOY": (1.30, "Start REMOTE 1.30 (OIES remote group, 2018); no step (remote single-train site) = 1.30."),
    "ID-SUL": (1.30, "Start REMOTE 1.30 (OIES remote group, 2018); no step (remote single-train site) = 1.30."),
    "ID-PAP": (1.20, "Start REMOTE 1.30 (OIES remote group, 2018); -0.10 existing LNG site (Trains 1 and 2) = 1.20."),
}


@pytest.mark.parametrize("code", sorted(NEW_IN_0_2_0))
def test_new_locations_in_0_2_0(code):
    factor, trail = NEW_IN_0_2_0[code]
    r = load_factors()[code]
    assert r["factor"] == factor
    assert (r["confidence"], r["method"], r["source"], r["as_of"]) == ("medium", "step rule", "STEP-RULE", 2026)
    # Decided range rule for medium confidence: -10% / +15%.
    assert r["low"] == pytest.approx(factor * 0.90, abs=0.006)
    assert r["high"] == pytest.approx(factor * 1.15, abs=0.006)
    assert r["notes"] == trail


def test_location_count_and_version():
    assert len(load_factors()) == 18
    assert version() == "0.2.0"


def test_confidence_is_the_lower():
    assert location(to="REMOTE", frm="ID-KAL")["confidence"] == "low"
    assert location(to="ID-KAL", frm="US-GC")["confidence"] == "medium"


def test_unknown_code():
    with pytest.raises(KeyError, match="Unknown location code"):
        location(to="XX")


def test_no_shared_code_with_escalation():
    # The location module may use opci.paths (where the data folders are), nothing else from opci.
    tree = ast.parse((ROOT / "opci" / "locations.py").read_text())
    used = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("opci"):
            used |= {f"{n.module}.{a.name}" if n.module == "opci" else n.module for a in n.names}
        elif isinstance(n, ast.Import):
            used |= {a.name for a in n.names if a.name.startswith("opci")}
    assert used <= {"opci.paths"}
