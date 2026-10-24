from pathlib import Path

import pytest

from opci.index import average, compute, load_weights, supply_shock_warning

ROOT = Path(__file__).resolve().parent.parent
# The prototype check is pinned to the first snapshot. Later snapshots carry BLS revisions.
FIRST_SNAPSHOT = ROOT / "data" / "snapshots" / "2026-10-24"

# Spec section 6.6: general, productivity 2%, 2019 anchor 607.5.
PROTOTYPE = {
    2008: 545.9, 2009: 543.8, 2010: 544.7, 2011: 555.6, 2012: 560.6, 2013: 559.9,
    2014: 564.6, 2015: 565.3, 2016: 566.3, 2017: 572.5, 2018: 594.3, 2019: 607.5,
    2020: 609.3, 2021: 659.0, 2022: 736.4, 2023: 759.9, 2024: 779.4, 2025: 812.0,
    2026: 852.3,
}


@pytest.fixture(scope="module")
def annual():
    rows, _ = compute(snapshot=FIRST_SNAPSHOT, start=2008)
    return {int(r["period"]): r for r in rows}


def test_reproduces_prototype_within_half_a_point(annual):
    for year, expected in PROTOTYPE.items():
        assert annual[year]["value"] == pytest.approx(expected, abs=0.5), year


def test_escalation_2011_to_2026(annual):
    assert annual[2026]["value"] / annual[2011]["value"] == pytest.approx(1.53, abs=0.005)


def test_part_year_is_labelled(annual):
    assert annual[2026]["part"] and annual[2026]["months"] == 9
    assert not annual[2025]["part"]


def test_2019_equals_anchor():
    rows, _ = compute(snapshot=FIRST_SNAPSHOT, anchor=100)
    assert next(r for r in rows if r["period"] == "2019")["value"] == pytest.approx(100)


def test_no_productivity_sensitivity_row():
    # Spec 6.5 sensitivity table: productivity 0% gives OPCI 2026 of about 899.
    rows, _ = compute(snapshot=FIRST_SNAPSHOT, productivity=0.0)
    assert next(r for r in rows if r["period"] == "2026")["value"] == pytest.approx(899, abs=1)


def test_quarterly_average_and_part_quarter():
    obs = [("2026-07-01", 1.0), ("2026-08-01", 2.0), ("2026-09-01", 3.0), ("2026-10-01", 4.0)]
    assert average(obs, "quarterly") == {"2026Q3": (2.0, 3), "2026Q4": (4.0, 1)}


def test_quarterly_series_brackets_annual():
    rows, _ = compute(freq="quarterly", snapshot=FIRST_SNAPSHOT, start=2019, end=2019)
    assert [r["period"] for r in rows] == ["2019Q1", "2019Q2", "2019Q3", "2019Q4"]
    assert sum(r["value"] for r in rows) / 4 == pytest.approx(607.5, abs=0.5)


def test_no_warning_outside_supply_shock_years():
    assert supply_shock_warning("2011", "2026Q3") is None


NOTE = (
    "Note: 2021 and 2022 were unusual years. Supply shocks after the pandemic pushed "
    "equipment and material prices up quickly and unevenly. Index values for these years "
    "are less certain than for other years. Escalation from a 2021 or 2022 cost date may "
    "be somewhat overstated, and escalation to a 2021 or 2022 target date may be somewhat "
    "understated. See METHOD.md."
)


@pytest.mark.parametrize("base,target", [("2022", "2026Q3"), ("2015", "2021Q4"), ("2021Q2", "2022")])
def test_supply_shock_note_exact_text(base, target):
    assert supply_shock_warning(base, target) == NOTE


def test_supply_shock_note_has_no_percentages():
    assert "%" not in NOTE


def test_unknown_investment_type():
    with pytest.raises(ValueError):
        load_weights("lng")
