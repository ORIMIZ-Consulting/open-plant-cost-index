from pathlib import Path

import yaml

from scripts.check_no_private import main as check_no_private

ROOT = Path(__file__).resolve().parent.parent


def test_general_weights_sum_to_100():
    data = yaml.safe_load((ROOT / "escalation" / "weights_general.yaml").read_text())
    assert round(sum(data["weights"].values()), 2) == 100.00


def test_weights_match_series_list():
    series = yaml.safe_load((ROOT / "escalation" / "series.yaml").read_text())
    weights = yaml.safe_load((ROOT / "escalation" / "weights_general.yaml").read_text())
    assert [s["code"] for s in series["series"]] == list(weights["weights"])


def test_private_files_are_blocked():
    assert check_no_private(["data/private_cepci.csv"]) == 1
    assert check_no_private(["private_paid_ucci.csv"]) == 1
    assert check_no_private(["escalation/series.yaml"]) == 0


def test_gitignore_blocks_private_files():
    assert "private_*" in (ROOT / ".gitignore").read_text().splitlines()
