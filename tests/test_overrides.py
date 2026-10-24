"""Override files. All values here are made up for the tests; they are not CEPCI."""
import shutil
import subprocess
from pathlib import Path

import pytest

from opci import combined, escalation, format_factor
from opci.cli import main as cli
from opci.overrides import OverrideError, load_override, override_path

ROOT = Path(__file__).resolve().parent.parent


def _write(folder, name, text):
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


def test_clean_file_factor_and_output(tmp_path):
    _write(tmp_path, "private_cepci.csv", "period,value\n2011,100\n2012,102\n2013,104\n2014,110\n")
    r = combined(base="2011", target="2014", to="ID-KAL", index_source="private_cepci",
                 private_folder=tmp_path)
    assert r["escalation"]["factor"] == pytest.approx(1.10)
    assert r["factor"] == pytest.approx(1.10 * 1.20)
    text = format_factor(r)
    assert "index source: private_cepci (private_cepci.csv)" in text
    assert "user override file private_cepci.csv" in text
    assert "covers 2011 to 2014 (annual)" in text
    assert "Gaps" not in text and "Odd jump" not in text


def test_gaps_raise_a_clear_warning(tmp_path):
    _write(tmp_path, "private_cepci.csv", "2011,100\n2012,102\n2015,108\n")
    _, _, warnings = load_override(tmp_path / "private_cepci.csv")
    assert any("Gaps in private_cepci.csv: 2013, 2014" in w for w in warnings)
    r = escalation("2011", "2015", index_source="private_cepci", private_folder=tmp_path)
    assert any("Gaps" in n for n in r["notes"])


def test_date_in_a_gap_is_not_filled(tmp_path):
    _write(tmp_path, "private_cepci.csv", "2011,100\n2012,102\n2015,108\n")
    with pytest.raises(OverrideError, match="no value for the target date 2013.*does not fill gaps"):
        escalation("2011", "2013", index_source="private_cepci", private_folder=tmp_path)


def test_partial_coverage_is_stated(tmp_path):
    _write(tmp_path, "private_cepci.csv", "2018,100\n2019,101\n")
    with pytest.raises(OverrideError, match="covers 2018 to 2019"):
        escalation("2011", "2019", index_source="private_cepci", private_folder=tmp_path)


def test_odd_jump_is_reported(tmp_path):
    _write(tmp_path, "private_cepci.csv", "2011,100\n2012,140\n")
    _, _, warnings = load_override(tmp_path / "private_cepci.csv")
    assert any("Odd jump in private_cepci.csv: 2011 to 2012 +40%" in w for w in warnings)


@pytest.mark.parametrize("text,match", [
    ("2011,abc\n", "not a number"),
    ("2011,100\n2011Q2,101\n", "mixes years and quarters"),
    ("2011,100\n2011,101\n", "appears twice"),
    ("11,100\n", "must be like 2011"),
    ("2011,-5\n", "above zero"),
])
def test_bad_files_rejected(tmp_path, text, match):
    _write(tmp_path, "private_cepci.csv", text)
    with pytest.raises(OverrideError, match=match):
        load_override(tmp_path / "private_cepci.csv")


def test_quarterly_file_needs_quarter_dates(tmp_path):
    _write(tmp_path, "private_cepci.csv", "2011Q1,100\n2011Q2,101\n")
    assert escalation("2011Q1", "2011Q2", index_source="private_cepci",
                      private_folder=tmp_path)["factor"] == pytest.approx(1.01)
    with pytest.raises(OverrideError, match="holds quarterly values"):
        escalation("2011", "2011Q2", index_source="private_cepci", private_folder=tmp_path)


def test_paid_file_by_name_and_single_file(tmp_path):
    _write(tmp_path, "private_paid_ucci.csv", "2020,100\n2021,120\n")
    assert override_path("paid", "ucci", tmp_path).name == "private_paid_ucci.csv"
    assert override_path("paid", None, tmp_path).name == "private_paid_ucci.csv"
    _write(tmp_path, "private_paid_dcci.csv", "2020,100\n")
    with pytest.raises(OverrideError, match="Several paid files"):
        override_path("paid", None, tmp_path)


def test_folder_from_environment(tmp_path, monkeypatch):
    _write(tmp_path, "private_cepci.csv", "2011,100\n2012,103\n")
    monkeypatch.setenv("OPCI_PRIVATE_DIR", str(tmp_path))
    assert escalation("2011", "2012", index_source="private_cepci")["factor"] == pytest.approx(1.03)


def test_cli_override(tmp_path, capsys):
    _write(tmp_path, "private_paid_ucci.csv", "2020,100\n2021,120\n")
    assert cli(["factor", "--base", "2020", "--target", "2021", "--index-source", "paid",
                "--paid-name", "ucci", "--private-dir", str(tmp_path)]) == 0
    assert "Escalation 2020 to 2021:   x1.20" in capsys.readouterr().out
    assert cli(["factor", "--base", "2020", "--index-source", "private_cepci",
                "--private-dir", str(tmp_path)]) == 2


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_no_private_file_is_tracked():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        pytest.skip("not a git checkout")
    tracked = [p for p in out.splitlines() if Path(p).name.startswith("private_")]
    assert tracked == []
