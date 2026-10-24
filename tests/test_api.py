import csv
import json
from pathlib import Path

import pytest

from opci import combined, escalation, format_factor, location, series
from opci.api import parse_period
from opci.cli import main as cli
from opci.index import SUPPLY_SHOCK_NOTE

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "data" / "snapshots" / "2026-10-24"


def test_parse_period():
    assert parse_period("2011") == ("annual", "2011")
    assert parse_period("2026q3") == ("quarterly", "2026Q3")
    with pytest.raises(ValueError):
        parse_period("2026Q5")


def test_spec_sample_factors():
    # Spec 5.1: 2011 to 2026 x1.53, East Kalimantan x1.20, combined x1.84.
    r = combined(base="2011", target="2026", to="ID-KAL", snapshot=SNAP)
    assert round(r["escalation"]["factor"], 2) == 1.53
    assert round(r["location"]["factor"], 2) == 1.20
    assert round(r["factor"], 2) == 1.84


def test_combined_is_escalation_times_location():
    r = combined(base="2015", target="2024Q2", to="ID-KAL", frm="AU-NW", snapshot=SNAP)
    assert r["factor"] == pytest.approx(r["escalation"]["factor"] * r["location"]["factor"])
    assert r["low"] == pytest.approx(r["escalation"]["factor"] * r["location"]["low"])
    assert r["high"] == pytest.approx(r["escalation"]["factor"] * r["location"]["high"])


def test_scale_does_not_change_factor():
    a = escalation("2011", "2025", scale="cepci", snapshot=SNAP)
    b = escalation("2011", "2025", scale="2019", snapshot=SNAP)
    assert a["factor"] == pytest.approx(b["factor"])
    assert a["scale_2019"] == pytest.approx(612.9, abs=0.1)


def test_default_target_is_latest_full_quarter():
    assert escalation("2011", snapshot=SNAP)["target"] == "2026Q3"


def test_part_year_is_labelled():
    r = escalation("2011", "2026", snapshot=SNAP)
    assert "part_year" in r["flags"]
    assert "2026 is a part year (January to September average)." in r["notes"]


def test_supply_shock_note_in_output():
    r = combined(base="2022", target="2025", snapshot=SNAP)
    assert "supply_shock" in r["escalation"]["flags"]
    assert SUPPLY_SHOCK_NOTE in format_factor(r)
    assert "supply_shock" not in escalation("2015", "2025", snapshot=SNAP)["flags"]


def test_every_output_carries_version_and_data_date():
    text = format_factor(combined(base="2011", target="2026Q3", to="ID-KAL", snapshot=SNAP))
    first, second = text.splitlines()[:2]
    assert first == "Open Plant Cost Index (OPCI) v0.1.0 | Maintained by ORIMIZ Consulting"
    assert second == "Data to 2026-09 | investment type: general | productivity 2% | index source: open"
    assert "range 1.08 to 1.38, confidence: medium" in text
    meta = series(start=2020, end=2020, snapshot=SNAP)["meta"]
    assert meta["version"] == "0.1.0" and meta["data_to"] == "2026-09"


def test_productivity_off_label():
    text = format_factor(escalation("2011", "2025", productivity=0.0, snapshot=SNAP))
    assert "productivity off" in text


def test_private_sources_not_yet_available():
    with pytest.raises(NotImplementedError):
        escalation("2011", "2025", index_source="private_cepci", snapshot=SNAP)


def test_series_rows_and_components():
    t = series(start=2019, end=2019, snapshot=SNAP)
    (row,) = t["rows"]
    assert row["period"] == "2019" and row["HX"] == pytest.approx(100)


def test_location_exported():
    assert location(to="ID-KAL")["factor"] == 1.20


def test_cli_factor(capsys):
    assert cli(["factor", "--base", "2011", "--target", "2026", "--location", "ID-KAL"]) == 0
    out = capsys.readouterr().out
    assert "Combined factor:   x1.8" in out and "Maintained by ORIMIZ Consulting" in out


def test_cli_series_csv_and_json(tmp_path):
    out = tmp_path / "s.csv"
    assert cli(["series", "--start", "2020", "--end", "2021", "--out", str(out)]) == 0
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert [r["period"] for r in rows] == ["2020", "2021"]
    assert rows[0]["version"] == "0.1.0" and rows[0]["data_to"]
    assert rows[1]["supply_shock"] == "True"
    js = tmp_path / "s.json"
    assert cli(["series", "--start", "2020", "--end", "2020", "--freq", "quarterly", "--out", str(js)]) == 0
    data = json.loads(js.read_text(encoding="utf-8"))
    assert len(data["rows"]) == 4 and data["meta"]["freq"] == "quarterly"


def test_cli_bad_location(capsys):
    assert cli(["factor", "--base", "2011", "--location", "XX"]) == 2
    assert "Unknown location code 'XX'" in capsys.readouterr().err
