# Changelog

All notable changes to OPCI are listed here. Code versions and data releases are tracked apart.

## Unreleased

### Added
- Repository skeleton: README, licence, data notice, citation file, folder layout.
- `.gitignore` rule and pre-commit check that block any `private_*` file.
- Series list (`escalation/series.yaml`) and general process plant weights (`escalation/weights_general.yaml`).
- FRED (Federal Reserve Economic Data) pull (`opci/fred.py`) with cached snapshots in `data/snapshots/`. CSV download by default, FRED API when `FRED_API_KEY` is set.
- Monthly GitHub Action (`.github/workflows/refresh.yml`) that pulls the data and commits the snapshot.
- Escalation calculation (`opci/index.py`): annual and quarterly series, productivity adjustment, anchor setting, part period flag. Reproduces the prototype values (spec section 6.6) within 0.06 from the 2026-10-24 snapshot.
- Public calibration points (`escalation/public_points.csv`): 16 CEPCI annual averages, 2008 to 2023, each with its public source. No public value found yet for 2024 or 2025.
- Best-fit scale (`opci/calibrate.py`): least squares on the log ratio, plus a joint fit of the productivity rate as a check.
- Supply-shock years 2021 and 2022: left out of the scale fit, shown on the validation page against a 10% watch limit that reports only. The 8% fail limit applies to the 14 normal years. Fitted scale: OPCI 2019 = 612.9. Worst error on normal years 5.5% (2016).
- Supply-shock warning when a base or target date falls in 2021 or 2022 (OPCI ran about 6 to 9% below CEPCI in those years).
- Back-test and validation page (`opci/validate.py`, `VALIDATION.md`), run by the refresh Action.
- METHOD.md.

### Changed
- LICENSE copyright holder corrected to Syed Zia Haider.

### Series replacements
- Pumps: BLS series PCU333911333911 ended in 2017. Compressors (PCU333912333912) stand in for it.
