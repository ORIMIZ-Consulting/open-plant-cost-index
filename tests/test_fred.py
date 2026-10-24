from datetime import datetime, timezone

import pytest

from opci import fred

SAMPLE_CSV = "observation_date,WPU114\n2019-01-01,210.5\n2019-02-01,.\n2019-03-01,211.0\n"


def test_parse_csv_drops_missing_values():
    assert fred.parse_csv(SAMPLE_CSV, "WPU114") == [("2019-01-01", 210.5), ("2019-03-01", 211.0)]


def test_parse_csv_rejects_wrong_series():
    with pytest.raises(fred.FredError):
        fred.parse_csv(SAMPLE_CSV, "WPU117")


def test_parse_api_json():
    text = '{"observations": [{"date": "2019-01-01", "value": "1.5"}, {"date": "2019-02-01", "value": "."}]}'
    assert fred.parse_api_json(text, "X") == [("2019-01-01", 1.5)]


def test_snapshot_round_trip(tmp_path):
    data = {
        "WPU114": [("2019-01-01", 210.5), ("2019-02-01", 211.25)],
        "WPU117": [("2019-01-01", 99.1)],
    }
    folder = fred.write_snapshot(data, "fred_csv", tmp_path, datetime(2026, 10, 24, tzinfo=timezone.utc))
    assert fred.latest_snapshot(tmp_path) == folder
    loaded, manifest = fred.load_snapshot(folder)
    assert loaded == data
    assert manifest["data_to"] == "2019-01"
    assert manifest["series"]["WPU114"]["count"] == 2


def test_snapshot_is_never_overwritten(tmp_path):
    day = datetime(2026, 10, 24, tzinfo=timezone.utc)
    first = fred.write_snapshot({"X": [("2019-01-01", 1.0)]}, "fred_csv", tmp_path, day)
    manifest = (first / "manifest.json").read_text()
    # Same data again: nothing new, nothing rewritten.
    assert fred.write_snapshot({"X": [("2019-01-01", 1.0)]}, "fred_csv", tmp_path, day) == first
    assert (first / "manifest.json").read_text() == manifest
    # Revised data on the same day: a new folder, the first one kept.
    second = fred.write_snapshot({"X": [("2019-01-01", 1.1)]}, "fred_csv", tmp_path, day)
    assert second.name == "2026-10-24-2"
    assert fred.load_snapshot(first)[0] == {"X": [("2019-01-01", 1.0)]}
    assert fred.latest_snapshot(tmp_path) == second


def test_failed_series_fails_loudly(monkeypatch):
    def boom(fred_id, api_key=None):
        if fred_id == "PCU332410332410":
            raise fred.FredError("gone")
        return [("2026-09-01", 1.0)]
    monkeypatch.setattr(fred, "fetch_series", boom)
    with pytest.raises(fred.FredError, match="replacement rule"):
        fred.pull_all([{"code": "HX", "fred_id": "PCU332410332410"}, {"code": "MACH", "fred_id": "WPU114"}])


def test_all_series_failing_means_offline(monkeypatch):
    def down(fred_id, api_key=None):
        raise fred.FredError("connection refused")
    monkeypatch.setattr(fred, "fetch_series", down)
    with pytest.raises(fred.FredOffline):
        fred.pull_all([{"code": "HX", "fred_id": "PCU332410332410"}, {"code": "MACH", "fred_id": "WPU114"}])


def test_series_list_has_12_series():
    assert len(fred.load_series_list()) == 12
