import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from opci import checks, escalation, fred, format_factor

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "data" / "snapshots" / "2026-10-24"
ONE = [{"code": "HX", "fred_id": "A"}, {"code": "TANK", "fred_id": "B"}]


def test_stale_and_discontinued():
    data = {"A": [("2026-08-01", 1.0)], "B": [("2026-01-01", 1.0)], "C": [("2025-06-01", 1.0)]}
    out = {s["fred_id"]: s for s in checks.stale_series(data, "2026-10-24")}
    assert "A" not in out
    assert out["B"]["months"] == 9 and not out["B"]["discontinued"]
    assert out["C"]["discontinued"]


def test_revisions_above_half_a_percent():
    old = {"A": [("2026-07-01", 100.0), ("2026-08-01", 100.0)]}
    new = {"A": [("2026-07-01", 100.4), ("2026-08-01", 101.0), ("2026-09-01", 102.0)]}
    out = checks.revisions(old, new)
    assert [(r["date"], round(r["change"], 3)) for r in out] == [("2026-08-01", 0.01)]


def _snapshot_dir(tmp_path):
    d = tmp_path / "snapshots"
    shutil.copytree(SNAP, d / SNAP.name)
    return d


def test_offline_uses_cached_snapshot_and_says_so(tmp_path, monkeypatch, capsys):
    d = _snapshot_dir(tmp_path)

    def offline(fred_id, api_key=None):
        raise fred.FredError("connection refused")
    monkeypatch.setattr(fred, "fetch_series", offline)
    assert fred.main(["--out", str(d)]) == 0
    err = capsys.readouterr().err
    assert "FRED could not be reached" in err and "cached snapshot 2026-10-24" in err
    assert fred.main(["--out", str(d), "--strict"]) == 1
    # The output names the snapshot it used.
    text = format_factor(escalation("2011", "2026", snapshot=d / "2026-10-24"))
    assert "cached snapshot 2026-10-24" in text


def test_partial_failure_fails_loudly(tmp_path, monkeypatch, capsys):
    d = _snapshot_dir(tmp_path)

    def half(fred_id, api_key=None):
        if fred_id == "WPU114":
            raise fred.FredError("series does not exist")
        return [("2026-09-01", 1.0)]
    monkeypatch.setattr(fred, "fetch_series", half)
    assert fred.main(["--out", str(d)]) == 1
    assert "replacement rule" in capsys.readouterr().err


def test_discontinued_series_fails_refresh(tmp_path, monkeypatch, capsys):
    d = _snapshot_dir(tmp_path)
    data, _ = fred.load_snapshot(SNAP)
    data["WPU114"] = [o for o in data["WPU114"] if o[0] < "2025-01-01"]
    monkeypatch.setattr(fred, "fetch_series", lambda fred_id, api_key=None: data[fred_id])
    assert fred.main(["--out", str(d)]) == 1
    assert "possibly discontinued" in capsys.readouterr().err


def test_revision_report_saved_with_new_snapshot(tmp_path, monkeypatch, capsys):
    d = _snapshot_dir(tmp_path)
    data, _ = fred.load_snapshot(SNAP)
    data["WPU114"] = [(dt, v * 1.02 if dt == "2026-08-01" else v) for dt, v in data["WPU114"]]
    monkeypatch.setattr(fred, "fetch_series", lambda fred_id, api_key=None: data[fred_id])
    assert fred.main(["--out", str(d)]) == 0
    assert "REVISED: WPU114 2026-08" in capsys.readouterr().out
    new = fred.latest_snapshot(d)
    assert new.name != "2026-10-24"
    report = json.loads((new / "refresh_report.json").read_text())
    assert report["previous_snapshot"] == "2026-10-24" and len(report["revisions"]) == 1
