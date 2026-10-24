"""Back-test OPCI against public CEPCI values and write VALIDATION.md (METHOD section 6.5).

Fails (exit 1) when the worst error on the fit points is above the 8% fail limit.
Supply-shock years are reported against the 10% watch limit but never fail.

Run:  python -m opci.validate [--snapshot data/snapshots/<date>] [--out VALIDATION.md]
"""
import argparse
import csv
import sys
from pathlib import Path

from opci import CREDIT, __version__
from opci.calibrate import (FAIL_LIMIT, POINTS_FILE, WATCH_LIMIT, backtest, fit_joint)
from opci.chart import build_svg
from opci.fred import latest_snapshot, load_snapshot
from opci.index import DEFAULT_PRODUCTIVITY, SUPPLY_SHOCK_YEARS, compute

ROOT = Path(__file__).resolve().parent.parent
SENSITIVITY_RATES = (0.0, 0.01, 0.015, 0.02, 0.025)
CHART_PATH = "docs/validation_chart.svg"   # relative to VALIDATION.md
START_YEAR = 2008                          # version 1 series start


def _pct(x):
    return f"{x * 100:+.1f}%"


def _sources():
    with open(POINTS_FILE, newline="", encoding="utf-8") as f:
        return {int(r["year"]): r for r in csv.DictReader(f)}


def build_report(snapshot=None):
    snapshot = Path(snapshot) if snapshot else latest_snapshot()
    _, manifest = load_snapshot(snapshot)
    bt = backtest(snapshot=snapshot)
    joint = fit_joint(snapshot=snapshot)
    rows, _ = compute(anchor=bt["anchor"], snapshot=snapshot, start=START_YEAR)
    opci = {int(r["period"]): r for r in rows}
    src = _sources()
    shock = " and ".join(str(y) for y in SUPPLY_SHOCK_YEARS)

    out = [
        "# Validation: OPCI against public CEPCI values",
        "",
        f"Open Plant Cost Index (OPCI) v{__version__} | {CREDIT}  ",
        f"Data to {manifest['data_to']} | snapshot {snapshot.name} | investment type: general | "
        f"productivity {DEFAULT_PRODUCTIVITY:.0%} | index source: open",
        "",
        "This page compares OPCI with Chemical Engineering Plant Cost Index (CEPCI) annual averages "
        "that Chemical Engineering has published free. Each value is cited to its source. "
        "The page is rebuilt on every data refresh by `python -m opci.validate`.",
        "",
        "## Result",
        "",
        f"- Scale fitted on {len(bt['years'])} normal years (supply-shock years {shock} left out). "
        f"OPCI 2019 = {bt['anchor']:.1f}.",
        f"- Worst error on the normal years: **{bt['worst'] * 100:.1f}%** "
        f"(fail limit {FAIL_LIMIT:.0%}): **{'PASS' if bt['passed'] else 'FAIL'}**.",
        f"- Root mean square (RMS) error on the normal years: {bt['rms'] * 100:.1f}%.",
        f"- Worst error on the supply-shock years: {bt['watch_worst'] * 100:.1f}% "
        f"(watch limit {WATCH_LIMIT:.0%}, reports only): "
        f"**{'within watch limit' if bt['watch_ok'] else 'ABOVE WATCH LIMIT'}**.",
        "",
        f"![OPCI against public CEPCI annual values, {min(opci)} to {max(opci)}]({CHART_PATH})",
        "",
        "## Normal years (used for the scale fit)",
        "",
        "| Year | Public CEPCI | OPCI | Difference | Source |",
        "|---|---|---|---|---|",
    ]
    for y in bt["years"]:
        s = src[y]
        note = " (secondary source)" if s["quality"] == "secondary" else ""
        out.append(f"| {y} | {s['value']} | {opci[y]['value']:.1f} | {_pct(bt['errors'][y])} | "
                   f"[{s['source']}]({s['url']}){note} |")
    out += [
        "",
        f"## Supply-shock years ({shock})",
        "",
        "In 2021 and 2022 equipment and material prices rose fast after the pandemic. CEPCI rose "
        "faster than the Bureau of Labor Statistics (BLS) series that OPCI uses, so OPCI ran below "
        "CEPCI. These years are left out of the scale fit and checked against a separate watch limit. "
        "The output warns when a base or target date falls in these years. See METHOD.md.",
        "",
        "| Year | Public CEPCI | OPCI | Difference | Source |",
        "|---|---|---|---|---|",
    ]
    for y, e in sorted(bt["watch_errors"].items()):
        s = src[y]
        out.append(f"| {y} | {s['value']} | {opci[y]['value']:.1f} | {_pct(e)} | "
                   f"[{s['source']}]({s['url']}) |")
    out += [
        "",
        "## Productivity rate sensitivity",
        "",
        "Same rate on labour and engineering. Scale refitted on the normal years for each rate.",
        "",
        "| Rate | Worst error | RMS error | OPCI 2019 | OPCI latest |",
        "|---|---|---|---|---|",
    ]
    latest = max(opci)
    for rate in SENSITIVITY_RATES:
        b = backtest(productivity=rate, snapshot=snapshot)
        r, _ = compute(anchor=b["anchor"], productivity=rate, snapshot=snapshot)
        bold = "**" if rate == DEFAULT_PRODUCTIVITY else ""
        out.append(f"| {bold}{rate:.1%}{bold} | {b['worst'] * 100:.1f}% | {b['rms'] * 100:.1f}% | "
                   f"{b['anchor']:.1f} | {r[-1]['value']:.1f} |")
    out += [
        "",
        f"Rate fitted jointly with the scale (check only): {joint['productivity']:.2%} "
        f"(worst error {joint['worst'] * 100:.1f}%, RMS {joint['rms'] * 100:.1f}%). "
        f"The default stays at {DEFAULT_PRODUCTIVITY:.0%}.",
        "",
        f"OPCI latest is {latest}" + (f" ({opci[latest]['months']} months, part year)."
                                      if opci[latest]["part"] else "."),
        "",
        "## Gaps",
        "",
        "- No public annual value found for 2024 or 2025. Chemical Engineering stopped printing "
        "the index in the magazine after August 2024.",
        "- The 2014 value is from a secondary source. No free primary source was found.",
        "",
        "CEPCI is a trademark of Chemical Engineering magazine. "
        "OPCI is not affiliated with or endorsed by Chemical Engineering.",
        "",
    ]
    last = opci[max(opci)]
    part = f"{last['months']} months, part year" if last["part"] else None
    svg = build_svg({y: r["value"] for y, r in opci.items()},
                    {y: float(s["value"]) for y, s in src.items()},
                    SUPPLY_SHOCK_YEARS, part)
    return "\n".join(out), svg, bt


def main(argv=None):
    ap = argparse.ArgumentParser(description="Back-test OPCI and write VALIDATION.md.")
    ap.add_argument("--snapshot", default=None, help="snapshot folder (default: latest)")
    ap.add_argument("--out", default=str(ROOT / "VALIDATION.md"))
    args = ap.parse_args(argv)
    text, svg, bt = build_report(args.snapshot)
    Path(args.out).write_text(text, encoding="utf-8")
    chart = Path(args.out).parent / CHART_PATH
    chart.parent.mkdir(parents=True, exist_ok=True)
    chart.write_text(svg, encoding="utf-8")
    print(f"Worst error on normal years {bt['worst'] * 100:.2f}% (limit {FAIL_LIMIT:.0%}). "
          f"Supply-shock years worst {bt['watch_worst'] * 100:.2f}% (watch {WATCH_LIMIT:.0%}).")
    if not bt["watch_ok"]:
        print("WATCH: supply-shock year error above the watch limit. Reported only.")
    if not bt["passed"]:
        print("FAIL: back-test worst error above the fail limit.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
