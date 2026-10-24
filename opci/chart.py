"""Back-test chart for VALIDATION.md: OPCI annual line against public CEPCI points.

Writes a plain SVG with no dependencies. It follows the viewer's light or dark
theme. Each point carries a <title>, so hovering shows its value where the SVG
is opened directly.
"""
import math
from xml.sax.saxutils import escape

W, H = 760, 390
LEFT, RIGHT, TOP, BOTTOM = 56, 120, 58, 40

STYLE = """
  .surface { fill: #fcfcfb; }
  .grid { stroke: #e1e0d9; stroke-width: 1; }
  .axis { stroke: #c3c2b7; stroke-width: 1; }
  .tick { fill: #898781; font: 12px system-ui, -apple-system, "Segoe UI", sans-serif; font-variant-numeric: tabular-nums; }
  .label { fill: #0b0b0b; font: 600 13px system-ui, -apple-system, "Segoe UI", sans-serif; }
  .note { fill: #52514e; font: 12px system-ui, -apple-system, "Segoe UI", sans-serif; }
  .band { fill: #f0efec; }
  .opci { stroke: #2a78d6; stroke-width: 2; fill: none; stroke-linejoin: round; stroke-linecap: round; }
  .opci-part { stroke: #2a78d6; stroke-width: 2; fill: none; stroke-dasharray: 4 4; }
  .opci-dot { fill: #2a78d6; }
  .cepci { fill: #eb6834; stroke: #fcfcfb; stroke-width: 2; }
  .cepci-watch { fill: #fcfcfb; stroke: #eb6834; stroke-width: 2; }
  @media (prefers-color-scheme: dark) {
    .surface { fill: #1a1a19; }
    .grid { stroke: #2c2c2a; }
    .axis { stroke: #383835; }
    .label { fill: #f0efec; }
    .note { fill: #c3c2b7; }
    .band { fill: #262624; }
    .opci, .opci-part { stroke: #3987e5; }
    .opci-dot { fill: #3987e5; }
    .cepci { fill: #d95926; stroke: #1a1a19; }
    .cepci-watch { fill: #1a1a19; stroke: #d95926; }
  }
"""


def _nice_range(lo, hi, step=100):
    return math.floor(lo / step) * step, math.ceil(hi / step) * step


def build_svg(opci, points, watch_years, part_label=None):
    """opci: {year: value}; points: {year: CEPCI value}; watch_years: supply-shock years.

    part_label: text for the last OPCI year when it is a part year (drawn dashed).
    """
    years = sorted(opci)
    x0, x1 = years[0], years[-1]
    y0, y1 = _nice_range(min(min(opci.values()), min(points.values())) - 10,
                         max(max(opci.values()), max(points.values())) + 10)
    pw, ph = W - LEFT - RIGHT, H - TOP - BOTTOM

    def x(year):
        return LEFT + (year - x0) / (x1 - x0) * pw

    def y(v):
        return TOP + (y1 - v) / (y1 - y0) * ph

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'role="img" aria-labelledby="t d">',
           '<title id="t">OPCI against public CEPCI annual values</title>',
           '<desc id="d">Line: OPCI annual index. Dots: public CEPCI annual averages. '
           'Shaded: supply-shock years, left out of the scale check.</desc>',
           f"<style>{STYLE}</style>",
           f'<rect class="surface" x="0" y="0" width="{W}" height="{H}" rx="8"/>']

    # Supply-shock band, behind everything else.
    for yr in watch_years:
        out.append(f'<rect class="band" x="{x(yr - 0.5):.1f}" y="{TOP}" '
                   f'width="{x(yr + 0.5) - x(yr - 0.5):.1f}" height="{ph}"/>')
    if watch_years:
        mid = (min(watch_years) + max(watch_years)) / 2
        out.append(f'<text class="note" x="{x(mid):.1f}" y="{TOP - 6}" text-anchor="middle">'
                   f'Supply-shock years</text>')

    # Grid and y ticks.
    for v in range(int(y0), int(y1) + 1, 100):
        out.append(f'<line class="grid" x1="{LEFT}" x2="{LEFT + pw}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>')
        out.append(f'<text class="tick" x="{LEFT - 8}" y="{y(v) + 4:.1f}" text-anchor="end">{v}</text>')
    out.append(f'<line class="axis" x1="{LEFT}" x2="{LEFT + pw}" y1="{TOP + ph}" y2="{TOP + ph}"/>')
    for yr in years:
        if yr % 2 == 0:
            out.append(f'<text class="tick" x="{x(yr):.1f}" y="{TOP + ph + 18}" text-anchor="middle">{yr}</text>')

    # OPCI line: solid over full years, dashed into a part year.
    full = years[:-1] if part_label else years
    path = " ".join(f"{'M' if i == 0 else 'L'}{x(yr):.1f},{y(opci[yr]):.1f}" for i, yr in enumerate(full))
    out.append(f'<path class="opci" d="{path}"/>')
    if part_label:
        a, b = years[-2], years[-1]
        out.append(f'<path class="opci-part" d="M{x(a):.1f},{y(opci[a]):.1f} L{x(b):.1f},{y(opci[b]):.1f}"/>')
    for yr in years:
        label = f"{yr}: OPCI {opci[yr]:.1f}" + (f" ({part_label})" if part_label and yr == years[-1] else "")
        out.append(f'<circle class="opci-dot" cx="{x(yr):.1f}" cy="{y(opci[yr]):.1f}" r="2.5">'
                   f'<title>{escape(label)}</title></circle>')

    # Public CEPCI points.
    for yr, v in sorted(points.items()):
        cls = "cepci-watch" if yr in watch_years else "cepci"
        diff = opci[yr] / v - 1 if yr in opci else None
        tip = f"{yr}: public CEPCI {v:.1f}" + (f", OPCI {diff * 100:+.1f}%" if diff is not None else "")
        out.append(f'<circle class="{cls}" cx="{x(yr):.1f}" cy="{y(v):.1f}" r="5">'
                   f'<title>{escape(tip)}</title></circle>')

    # Direct label for the line. The points are named by the legend; a label at the
    # last point would sit on the OPCI line.
    last = years[-1]
    out.append(f'<text class="label" x="{x(last) + 10:.1f}" y="{y(opci[last]) + 4:.1f}">OPCI</text>')
    if part_label:
        out.append(f'<text class="note" x="{x(last) + 10:.1f}" y="{y(opci[last]) + 20:.1f}">'
                   f'{escape(part_label)}</text>')

    # Legend, top left.
    lx, ly = LEFT, 20
    out += [
        f'<line class="opci" x1="{lx}" x2="{lx + 20}" y1="{ly}" y2="{ly}"/>',
        f'<text class="note" x="{lx + 26}" y="{ly + 4}">OPCI (annual)</text>',
        f'<circle class="cepci" cx="{lx + 130}" cy="{ly}" r="5"/>',
        f'<text class="note" x="{lx + 140}" y="{ly + 4}">Public CEPCI (normal year)</text>',
        f'<circle class="cepci-watch" cx="{lx + 320}" cy="{ly}" r="5"/>',
        f'<text class="note" x="{lx + 330}" y="{ly + 4}">Public CEPCI (supply-shock year)</text>',
        "</svg>",
    ]
    return "\n".join(out) + "\n"
