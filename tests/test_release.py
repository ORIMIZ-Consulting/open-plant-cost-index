import csv
import shutil
from pathlib import Path

import pytest

from opci import fred, read_release
from opci.release import list_releases, make_release

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "data" / "snapshots" / "2026-10-24"


@pytest.fixture(scope="module")
def first(tmp_path_factory):
    d = tmp_path_factory.mktemp("releases")
    folder, created = make_release(SNAP, d)
    return d, folder, created


def test_first_release(first):
    d, folder, created = first
    assert created and folder.name == "data-2026-09"
    names = {p.name for p in folder.iterdir()}
    assert {"opci_general_annual.csv", "opci_general_annual.json", "opci_general_quarterly.csv",
            "opci_general_quarterly.json", "RELEASE_NOTE.md"} <= names
    note = (folder / "RELEASE_NOTE.md").read_text(encoding="utf-8")
    assert "Maintained by ORIMIZ Consulting" in note and "Data to 2026-09" in note
    assert "Pumps (PCU333911333911) ended 2017" in note
    rows = list(csv.DictReader((folder / "opci_general_annual.csv").open(encoding="utf-8")))
    assert rows[0]["period"] == "2008" and rows[-1]["part"] == "True"
    assert all(r["revised"] == "False" for r in rows)
    assert all(r["version"] and r["data_to"] == "2026-09" for r in rows)


def test_same_data_makes_no_new_release(first):
    d, folder, _ = first
    again, created = make_release(SNAP, d)
    assert not created and again == folder


def test_read_release_pins_by_name(first):
    d, _, _ = first
    t = read_release("data-2026-09", release_dir=d)
    assert t["meta"]["data_to"] == "2026-09" and t["rows"][0]["period"] == "2008"
    with pytest.raises(ValueError, match="Releases: data-2026-09"):
        read_release("data-2030-01", release_dir=d)


def test_revised_data_same_month_gets_new_release(tmp_path):
    rel = tmp_path / "releases"
    make_release(SNAP, rel)
    # A BLS revision of 2% to construction labour in 2025, same data month.
    data, _ = fred.load_snapshot(SNAP)
    data["CES2000000008"] = [(dt, v * 1.02 if dt.startswith("2025") else v)
                             for dt, v in data["CES2000000008"]]
    snap2 = fred.write_snapshot(data, "fred_csv", tmp_path / "snaps")
    folder, created = make_release(snap2, rel)
    assert created and folder.name == "data-2026-09-2"
    assert [p.name for p in list_releases(rel)] == ["data-2026-09", "data-2026-09-2"]
    rows = {r["period"]: r for r in read_release("data-2026-09-2", release_dir=rel)["rows"]}
    assert rows["2025"]["revised"] and not rows["2015"]["revised"]
    # The first release is untouched.
    assert not any(r["revised"] for r in read_release("data-2026-09", release_dir=rel)["rows"])
