"""Data releases (spec sections 8 and 10).

Each refresh that passes the checks makes a release folder named by its data month:

  data/releases/data-2026-09/
    opci_general_annual.csv   opci_general_annual.json
    opci_general_quarterly.csv opci_general_quarterly.json
    RELEASE_NOTE.md

Releases are never changed after they are made, so a calling tool can pin one by
name. If the data for the same month change (for example after BLS revisions), a
new folder is made with a -2, -3 suffix. --force makes a new folder even when the
data are unchanged, so the version column names the OPCI version that built it.

Run:  python -m opci.release [--snapshot data/snapshots/<date>] [--force]
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import yaml

from opci import CREDIT, paths
from opci.api import series
from opci.calibrate import FAIL_LIMIT, WATCH_LIMIT, backtest
from opci.cli import write_series
from opci.fred import latest_snapshot, load_snapshot

RELEASE_DIR = paths.RELEASE_DIR
INVESTMENT = "general"
FREQS = ("annual", "quarterly")
REVISED_LIMIT = 0.005   # a value that moved more than 0.5% since the last release is flagged


def _release_order(p):
    name = p.name[len("data-"):]
    suffix = name[8:]
    return (name[:7], int(suffix) if suffix else 1)


def list_releases(release_dir=RELEASE_DIR):
    d = Path(release_dir)
    if not d.exists():
        return []
    return sorted((p for p in d.iterdir() if p.name.startswith("data-") and p.is_dir()),
                  key=_release_order)


def read_release(name, freq="annual", investment=INVESTMENT, release_dir=RELEASE_DIR):
    """Read a pinned release, e.g. read_release('data-2026-09'). Returns {'meta', 'rows'}."""
    path = Path(release_dir) / name / f"opci_{investment}_{freq}.json"
    if not path.exists():
        known = ", ".join(p.name for p in list_releases(release_dir)) or "none"
        raise ValueError(f"No release file {path.name} in {name}. Releases: {known}")
    return json.loads(path.read_text(encoding="utf-8"))


def _flag_revisions(table, previous):
    """Add 'revised' to each row: True when the value moved more than 0.5% since `previous`."""
    before = {r["period"]: r["value"] for r in previous["rows"]} if previous else {}
    count = 0
    for r in table["rows"]:
        old = before.get(r["period"])
        r["revised"] = bool(old and abs(r["value"] / old - 1) > REVISED_LIMIT)
        count += r["revised"]
    return count


def _note(name, meta, bt, revised, previous_name, snapshot):
    report_path = Path(snapshot) / "refresh_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else None
    replacements = yaml.safe_load((paths.ESCALATION_DIR / "series.yaml").read_text())["replacements"]
    lines = [
        f"# OPCI data release {name}",
        "",
        f"Open Plant Cost Index (OPCI) v{meta['version']} | {CREDIT}  ",
        f"Data to {meta['data_to']} | snapshot {meta['snapshot']} | investment type: {meta['investment']} | "
        f"productivity {meta['productivity']:.0%} | index source: open",
        "",
        "## Contents",
        "",
        f"- `opci_{INVESTMENT}_annual.csv` and `.json`: annual values, 2008 to {meta['data_to'][:4]}.",
        f"- `opci_{INVESTMENT}_quarterly.csv` and `.json`: quarterly values.",
        "- Columns: period, value, part (part period), supply_shock (2021 or 2022), revised "
        "(moved more than 0.5% since the previous release), each component rebased to 2019 = 100, "
        "then version and data date.",
        "",
        "## Checks",
        "",
        f"- Scale: OPCI 2019 = {bt['anchor']:.1f}, checked against public CEPCI values on "
        f"{len(bt['years'])} normal years.",
        f"- Back-test worst error on normal years: {bt['worst'] * 100:.1f}% (fail limit {FAIL_LIMIT:.0%}): "
        f"{'pass' if bt['passed'] else 'FAIL'}.",
        f"- Supply-shock years worst error: {bt['watch_worst'] * 100:.1f}% "
        f"(watch limit {WATCH_LIMIT:.0%}, reports only).",
    ]
    if report:
        lines.append(f"- Stale series (no new data for more than 6 months): "
                     f"{', '.join(s['fred_id'] for s in report['stale']) or 'none'}.")
        lines.append(f"- BLS values revised by more than 0.5% since snapshot "
                     f"{report['previous_snapshot']}: {len(report['revisions'])}.")
    lines += [
        f"- Annual values revised by more than 0.5% since {previous_name or 'the previous release (none)'}: "
        f"{revised}.",
        "",
        "## Series replacements",
        "",
    ]
    lines += [f"- {r['old_component']} ({r['old_fred_id']}) ended {r['ended']}. "
              f"Replaced by {r['replaced_by']}. {r['note']}" for r in replacements]
    lines += ["", "CEPCI is a trademark of Chemical Engineering magazine. "
              "OPCI is not affiliated with or endorsed by Chemical Engineering.", ""]
    return "\n".join(lines)


def _content(table):
    """The data of a table: rows without 'revised' flags (they depend on the release
    before) and meta without the tool version (a new code version alone is not new data)."""
    rows = [{k: v for k, v in r.items() if k != "revised"} for r in table["rows"]]
    meta = {k: v for k, v in table["meta"].items() if k != "version"}
    return {"meta": meta, "rows": rows}


def _identical(folder, tables):
    for freq, table in tables.items():
        path = folder / f"opci_{INVESTMENT}_{freq}.json"
        if not path.exists() or _content(json.loads(path.read_text(encoding="utf-8"))) != _content(table):
            return False
    return True


def make_release(snapshot=None, release_dir=None, force=False):
    """Build a release from a snapshot. Returns (folder, created).

    Default folder: data/releases in a clone, ~/.opci/releases after pip install.
    force: make a new release even if the data match the latest one (for example to
    record a new OPCI version in the version column). Values are never changed.
    """
    snapshot = Path(snapshot) if snapshot else latest_snapshot()
    release_dir = Path(release_dir) if release_dir else (
        RELEASE_DIR if paths.IN_REPO else paths.user_dir() / "releases")
    previous = list_releases(release_dir)
    previous = previous[-1] if previous else None

    tables, revised = {}, {}
    for freq in FREQS:
        table = series(start=2008, freq=freq, snapshot=snapshot)
        prior = read_release(previous.name, freq, release_dir=release_dir) if previous else None
        revised[freq] = _flag_revisions(table, prior)
        tables[freq] = json.loads(json.dumps(table))   # plain JSON types, as stored

    if previous and not force and _identical(previous, tables):
        return previous, False

    _, manifest = load_snapshot(snapshot)
    base = f"data-{manifest['data_to']}"
    folder, n = release_dir / base, 1
    while folder.exists():
        n += 1
        folder = release_dir / f"{base}-{n}"
    folder.mkdir(parents=True)
    for freq, table in tables.items():
        stem = folder / f"opci_{INVESTMENT}_{freq}"
        write_series(table, stem.with_suffix(".csv"))
        stem.with_suffix(".json").write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")
    bt = backtest(snapshot=snapshot)
    note = _note(folder.name, tables["annual"]["meta"], bt, revised["annual"],
                 previous.name if previous else None, snapshot)
    (folder / "RELEASE_NOTE.md").write_text(note, encoding="utf-8")
    return folder, True


def main(argv=None):
    ap = argparse.ArgumentParser(description="Make an OPCI data release from the latest snapshot.")
    ap.add_argument("--snapshot", default=None)
    ap.add_argument("--force", action="store_true",
                    help="make a new release even if the data are unchanged")
    args = ap.parse_args(argv)
    folder, created = make_release(args.snapshot, force=args.force)
    print(f"{'Release written' if created else 'No change. Latest release stays'}: {folder.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
