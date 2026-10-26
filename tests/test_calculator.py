"""The web calculator (docs/index.html) must give the same answers as the Python package.

The page's calculation sits in <script id="opci-calc">. These tests run it in Node with
the page's data file (docs/opci_data.js) and compare it with opci.escalation() and
opci.location(). They also check that the data file matches the latest release and
location/factors.csv, so a refresh that forgets to rebuild it fails here.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from opci import escalation, location
from scripts.build_calculator_data import OUT, build, render

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "index.html"

# (base, target, from, to)
CASES = [
    ("2015", "2026Q3", "US-GC", "OM"),
    ("2011", "2026", "AU-NW", "ID-KAL"),
    ("2011Q2", "2026Q3", "AU-NW", "ID-KAL"),
    ("2021", "2015Q4", "CA-BC", "US-GC"),
    ("2008Q1", "2022", "REMOTE", "MY-BIN"),
    ("2019", "2026Q3", "RU-SAK", "RU-SAK"),
    ("2026", "2008", "ID-PAP", "REMOTE"),
]


def _run_page(cases):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is not installed")
    calc = re.search(r'<script id="opci-calc">(.*?)</script>', PAGE.read_text(encoding="utf-8"), re.S)[1]
    program = "\n".join([
        "const window = {};",
        OUT.read_text(encoding="utf-8"),
        calc,
        "const C = opciCalc(window.OPCI_DATA);",
        f"const cases = {json.dumps(cases)};",
        "console.log(JSON.stringify({latest: C.latestQuarter,",
        "  results: cases.map(([b, t, f, to]) => C.combined(b, t, to, f))}));",
    ])
    out = subprocess.run([node, "-"], input=program, capture_output=True, text=True,
                         encoding="utf-8", check=True)
    return json.loads(out.stdout)


@pytest.fixture(scope="module")
def page():
    return _run_page(CASES)


def test_data_file_is_current():
    assert OUT.read_text(encoding="utf-8") == render(build()), \
        "docs/opci_data.js is out of date. Run: python -m scripts.build_calculator_data"


@pytest.mark.parametrize("i", range(len(CASES)))
def test_page_matches_python(page, i):
    base, target, frm, to = CASES[i]
    js = page["results"][i]
    esc = escalation(base=base, target=target)
    loc = location(to=to, frm=frm)
    assert js["escalation"]["factor"] == pytest.approx(esc["factor"], rel=1e-12)
    for k in ("factor", "low", "high"):
        assert js["location"][k] == pytest.approx(loc[k], rel=1e-12), k
    assert js["location"]["confidence"] == loc["confidence"]
    assert js["factor"] == pytest.approx(esc["factor"] * loc["factor"], rel=1e-12)


def test_owner_check_au_nw_to_id_kal(page):
    # Same check as tests/test_locations.py: x0.70, about 0.57 to 0.83.
    loc = page["results"][1]["location"]
    assert round(loc["factor"], 2) == 0.70
    assert loc["low"] == pytest.approx(0.57, abs=0.005) and loc["high"] == pytest.approx(0.83, abs=0.01)


def test_target_stops_at_latest_full_quarter(page):
    from opci.api import latest_full_quarter
    assert page["latest"] == latest_full_quarter()


def test_page_shows_required_text():
    html = PAGE.read_text(encoding="utf-8")
    assert "Prototype" not in html
    assert "Maintained by ORIMIZ Consulting" in html
    assert "CEPCI is a trademark of Chemical Engineering magazine" in html
    assert "10.5281/zenodo.23615226" in html
    assert "For future dates, use the" in html and "github.com/ORIMIZ-Consulting/open-fel1-lng-cost" in html
    assert 'src="opci_data.js"' in html
