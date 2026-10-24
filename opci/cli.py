"""OPCI command line (spec section 11.2).

  opci factor --base 2011 --target 2026Q3 --location ID-KAL
  opci series --start 2008 --freq quarterly --investment general --out opci_general.csv
  opci refresh
  opci validate
"""
import argparse
import csv
import json
import sys
from pathlib import Path

from opci import api, fred, validate
from opci.index import DEFAULT_PRODUCTIVITY
from opci.locations import REFERENCE

META_COLUMNS = ("version", "data_to", "snapshot", "investment", "productivity", "source", "scale")


def _common(p):
    p.add_argument("--investment", default="general", help="investment type (version 1: general)")
    p.add_argument("--productivity", type=float, default=DEFAULT_PRODUCTIVITY,
                   help="productivity rate on labour and engineering (default 0.02)")
    p.add_argument("--no-productivity", action="store_true", help="turn the productivity adjustment off")
    p.add_argument("--index-source", default="open", choices=api.INDEX_SOURCES)
    p.add_argument("--scale", default="cepci", choices=api.SCALES,
                   help="cepci: CEPCI-comparable scale (default); 2019: 2019 = 100")


def _settings(args):
    return {
        "investment": args.investment,
        "productivity": 0.0 if args.no_productivity else args.productivity,
        "index_source": args.index_source,
        "scale": args.scale,
    }


def cmd_factor(args):
    result = api.combined(base=args.base, target=args.target, to=args.location,
                          frm=getattr(args, "from"), paid_name=args.paid_name,
                          private_folder=args.private_dir, **_settings(args))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(api.format_factor(result))
    return 0


def write_series(table, out):
    meta, rows = table["meta"], table["rows"]
    out = Path(out)
    if out.suffix.lower() == ".json":
        out.write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")
        return
    if out.suffix.lower() != ".csv":
        raise ValueError("--out must end in .csv or .json")
    columns = list(rows[0]) + list(META_COLUMNS)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, columns, lineterminator="\n")
        w.writeheader()
        for r in rows:
            row = {k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()}
            w.writerow({**row, **{k: meta[k] for k in META_COLUMNS}})


def cmd_series(args):
    table = api.series(start=args.start, end=args.end, freq=args.freq, **_settings(args))
    if args.out:
        write_series(table, args.out)
        print(f"Wrote {len(table['rows'])} rows to {args.out}")
        return 0
    print("\n".join(api.header(table["meta"])))
    print(f"{'Period':<8}{'OPCI':>9}  Flags")
    for r in table["rows"]:
        flags = ", ".join(f for f, on in (("part", r["part"]), ("supply shock", r["supply_shock"])) if on)
        print(f"{r['period']:<8}{r['value']:>9.1f}  {flags}")
    for n in table["meta"]["notes"]:
        print(f"Note: {n}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="opci", description="Open Plant Cost Index (OPCI)")
    sub = ap.add_subparsers(dest="command", required=True)

    f = sub.add_parser("factor", help="escalation, location and combined factor")
    f.add_argument("--base", required=True, help="money date of the old cost, e.g. 2011 or 2011Q2")
    f.add_argument("--target", default=None, help="target date (default: latest full quarter)")
    f.add_argument("--location", default=REFERENCE, help="target location code (default US-GC)")
    f.add_argument("--from", default=REFERENCE, help="base location code (default US-GC)")
    f.add_argument("--json", action="store_true", help="print JSON instead of text")
    f.add_argument("--paid-name", default=None,
                   help="with --index-source paid: <name> in private_paid_<name>.csv")
    f.add_argument("--private-dir", default=None,
                   help="folder holding private_* override files (default: current folder or OPCI_PRIVATE_DIR)")
    _common(f)
    f.set_defaults(func=cmd_factor)

    s = sub.add_parser("series", help="index series by year or quarter")
    s.add_argument("--start", type=int, default=2008)
    s.add_argument("--end", type=int, default=None)
    s.add_argument("--freq", default="annual", choices=("annual", "quarterly"))
    s.add_argument("--out", default=None, help="write to a .csv or .json file")
    _common(s)
    s.set_defaults(func=cmd_series)

    r = sub.add_parser("refresh", help="pull the latest data from FRED into a new snapshot")
    r.add_argument("--strict", action="store_true", help="fail when FRED cannot be reached")
    r.set_defaults(func=lambda a: fred.main(["--strict"] if a.strict else []))

    v = sub.add_parser("validate", help="back-test against public CEPCI values; write VALIDATION.md")
    v.set_defaults(func=lambda a: validate.main([]))

    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, KeyError, NotImplementedError) as exc:
        print(f"Error: {exc.args[0] if exc.args else exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
