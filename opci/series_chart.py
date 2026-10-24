"""Interactive HTML chart for `opci series --chart` (spec section 5.2).

One self-contained file: inline SVG, a hover tooltip with crosshair, light and dark
themes, and a table view. No external scripts or fonts.
"""
import json
from html import escape

W, H = 880, 400
LEFT, RIGHT, TOP, BOTTOM = 60, 24, 24, 44

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OPCI series</title>
<style>
  :root {{ color-scheme: light; --surface:#fcfcfb; --page:#f9f9f7; --ink:#0b0b0b; --ink2:#52514e;
    --muted:#898781; --grid:#e1e0d9; --axis:#c3c2b7; --band:#f0efec; --line:#2a78d6;
    --border:rgba(11,11,11,0.10); }}
  @media (prefers-color-scheme: dark) {{ :root:where(:not([data-theme="light"])) {{ color-scheme: dark;
    --surface:#1a1a19; --page:#0d0d0d; --ink:#f0efec; --ink2:#c3c2b7; --grid:#2c2c2a; --axis:#383835;
    --band:#262624; --line:#3987e5; --border:rgba(255,255,255,0.10); }} }}
  :root[data-theme="dark"] {{ color-scheme: dark; --surface:#1a1a19; --page:#0d0d0d; --ink:#f0efec;
    --ink2:#c3c2b7; --grid:#2c2c2a; --axis:#383835; --band:#262624; --line:#3987e5;
    --border:rgba(255,255,255,0.10); }}
  body {{ margin:0; background:var(--page); color:var(--ink);
    font:14px system-ui,-apple-system,"Segoe UI",sans-serif; }}
  main {{ max-width:920px; margin:0 auto; padding:24px 16px; }}
  h1 {{ font-size:20px; margin:0 0 4px; }}
  .meta {{ color:var(--ink2); margin:0 0 16px; line-height:1.5; }}
  .card {{ background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:12px;
    position:relative; }}
  svg {{ width:100%; height:auto; display:block; }}
  .grid {{ stroke:var(--grid); }} .axis {{ stroke:var(--axis); }}
  .tick {{ fill:var(--muted); font-size:12px; font-variant-numeric:tabular-nums; }}
  .band {{ fill:var(--band); }} .bandlabel {{ fill:var(--ink2); font-size:12px; }}
  .line {{ stroke:var(--line); stroke-width:2; fill:none; stroke-linejoin:round; }}
  .part {{ stroke:var(--line); stroke-width:2; fill:none; stroke-dasharray:4 4; }}
  .dot {{ fill:var(--line); }} .cross {{ stroke:var(--axis); }}
  .tip {{ position:absolute; pointer-events:none; background:var(--surface); color:var(--ink);
    border:1px solid var(--border); border-radius:6px; padding:6px 8px; font-size:13px;
    box-shadow:0 2px 8px rgba(0,0,0,.12); display:none; white-space:nowrap; }}
  .tip b {{ font-variant-numeric:tabular-nums; }}
  .notes {{ color:var(--ink2); margin:12px 0 0; padding-left:18px; }}
  details {{ margin-top:16px; }}
  table {{ border-collapse:collapse; font-variant-numeric:tabular-nums; margin-top:8px; }}
  th, td {{ text-align:right; padding:4px 12px; border-bottom:1px solid var(--grid); }}
  th:first-child, td:first-child {{ text-align:left; }}
</style>
</head>
<body>
<main>
  <h1>Open Plant Cost Index (OPCI), {freq} series</h1>
  <p class="meta">{header}</p>
  <div class="card">
    <svg viewBox="0 0 {W} {H}" role="img" aria-label="OPCI {freq} values, {first} to {last}">{svg}</svg>
    <div class="tip" id="tip"></div>
  </div>
  <ul class="notes">{notes}</ul>
  <details><summary>Table view</summary><table>
    <thead><tr><th>Period</th><th>OPCI</th><th>Flags</th></tr></thead>
    <tbody>{table}</tbody></table></details>
</main>
<script>
const pts = {points};
const svg = document.querySelector("svg"), tip = document.getElementById("tip");
const cross = document.getElementById("cross"), hot = document.getElementById("hot");
function show(evt) {{
  const box = svg.getBoundingClientRect(), k = {W} / box.width;
  const x = (evt.clientX - box.left) * k;
  let best = pts[0];
  for (const p of pts) if (Math.abs(p.x - x) < Math.abs(best.x - x)) best = p;
  cross.setAttribute("x1", best.x); cross.setAttribute("x2", best.x); cross.style.display = "";
  hot.setAttribute("cx", best.x); hot.setAttribute("cy", best.y); hot.style.display = "";
  tip.innerHTML = best.label + ": <b>" + best.v.toFixed(1) + "</b>" + (best.flags ? "<br>" + best.flags : "");
  tip.style.display = "block";
  const left = best.x / k + 12, top = best.y / k - 10;
  tip.style.left = Math.min(left, box.width - tip.offsetWidth) + "px";
  tip.style.top = Math.max(0, top) + "px";
}}
svg.addEventListener("mousemove", show);
svg.addEventListener("mouseleave", () => {{ tip.style.display = "none"; cross.style.display = "none"; hot.style.display = "none"; }});
</script>
</body>
</html>
"""


def _nice(lo, hi, step):
    import math
    return math.floor(lo / step) * step, math.ceil(hi / step) * step


def build_series_html(table, header_lines):
    """table: {'meta', 'rows'} from opci.series(); header_lines: the two output header lines."""
    rows, meta = table["rows"], table["meta"]
    values = [r["value"] for r in rows]
    step = 100 if max(values) - min(values) > 200 else 50
    y0, y1 = _nice(min(values) - 5, max(values) + 5, step)
    n = len(rows)
    pw, ph = W - LEFT - RIGHT, H - TOP - BOTTOM

    def x(i):
        return LEFT + (i / (n - 1) if n > 1 else 0.5) * pw

    def y(v):
        return TOP + (y1 - v) / (y1 - y0) * ph

    out = []
    # Supply-shock band behind the line.
    shock = [i for i, r in enumerate(rows) if r["supply_shock"]]
    if shock:
        half = pw / (n - 1) / 2 if n > 1 else 10
        bx0, bx1 = x(shock[0]) - half, x(shock[-1]) + half
        out.append(f'<rect class="band" x="{bx0:.1f}" y="{TOP}" width="{bx1 - bx0:.1f}" height="{ph}"/>')
        out.append(f'<text class="bandlabel" x="{(bx0 + bx1) / 2:.1f}" y="{TOP + 14}" '
                   f'text-anchor="middle">Supply-shock years</text>')
    v = y0
    while v <= y1:
        out.append(f'<line class="grid" x1="{LEFT}" x2="{LEFT + pw}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>')
        out.append(f'<text class="tick" x="{LEFT - 8}" y="{y(v) + 4:.1f}" text-anchor="end">{v:g}</text>')
        v += step
    out.append(f'<line class="axis" x1="{LEFT}" x2="{LEFT + pw}" y1="{TOP + ph}" y2="{TOP + ph}"/>')
    years = sorted({r["period"][:4] for r in rows})
    every = 1 if len(years) <= 10 else 2
    for yr in years[::every]:
        i = next(i for i, r in enumerate(rows) if r["period"].startswith(yr))
        out.append(f'<text class="tick" x="{x(i):.1f}" y="{TOP + ph + 20}" text-anchor="middle">{yr}</text>')

    full = [i for i, r in enumerate(rows) if not r["part"]]
    if full:
        d = " ".join(f"{'M' if k == 0 else 'L'}{x(i):.1f},{y(values[i]):.1f}" for k, i in enumerate(full))
        out.append(f'<path class="line" d="{d}"/>')
    for i, r in enumerate(rows):
        if r["part"] and i > 0:
            out.append(f'<path class="part" d="M{x(i - 1):.1f},{y(values[i - 1]):.1f} '
                       f'L{x(i):.1f},{y(values[i]):.1f}"/>')
    out.append(f'<line class="cross" id="cross" x1="0" x2="0" y1="{TOP}" y2="{TOP + ph}" style="display:none"/>')
    out.append('<circle class="dot" id="hot" r="4" style="display:none"/>')

    def flags(r):
        f = []
        if r["part"]:
            f.append("part period")
        if r["supply_shock"]:
            f.append("supply-shock year")
        if r.get("revised"):
            f.append("revised")
        return ", ".join(f)

    points = [{"x": round(x(i), 1), "y": round(y(r["value"]), 1), "v": r["value"],
               "label": r["period"], "flags": flags(r)} for i, r in enumerate(rows)]
    table_rows = "".join(f"<tr><td>{escape(r['period'])}</td><td>{r['value']:.1f}</td>"
                         f"<td>{escape(flags(r))}</td></tr>" for r in rows)
    notes = "".join(f"<li>{escape(n)}</li>" for n in meta.get("notes", []))
    return PAGE.format(
        W=W, H=H, freq=escape(meta["freq"]), first=escape(rows[0]["period"]), last=escape(rows[-1]["period"]),
        header="<br>".join(escape(h) for h in header_lines), svg="".join(out), notes=notes,
        table=table_rows, points=json.dumps(points),
    )
