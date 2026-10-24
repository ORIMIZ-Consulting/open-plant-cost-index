from pathlib import Path

from opci.validate import build_report

ROOT = Path(__file__).resolve().parent.parent
FIRST_SNAPSHOT = ROOT / "data" / "snapshots" / "2026-10-24"


def test_report_and_chart():
    text, svg, bt = build_report(FIRST_SNAPSHOT)
    assert bt["passed"]
    assert "Maintained by ORIMIZ Consulting" in text and "Data to 2026-09" in text
    assert "## Supply-shock years (2021 and 2022)" in text
    assert "docs/validation_chart.svg" in text
    assert "CEPCI is a trademark of Chemical Engineering magazine." in text
    assert svg.startswith("<svg") and "Supply-shock years" in svg
    # 16 public points, 2 of them supply-shock years, plus one legend marker of each kind.
    assert svg.count('class="cepci"') == 14 + 1 and svg.count('class="cepci-watch"') == 2 + 1
