# Changelog

All notable changes to OPCI are listed here. Code versions and data releases are tracked apart.

## Unreleased

### Added
- Repository skeleton: README, licence, data notice, citation file, folder layout.
- `.gitignore` rule and pre-commit check that block any `private_*` file.
- Series list (`escalation/series.yaml`) and general process plant weights (`escalation/weights_general.yaml`).
- FRED (Federal Reserve Economic Data) pull (`opci/fred.py`) with cached snapshots in `data/snapshots/`. CSV download by default, FRED API when `FRED_API_KEY` is set.
- Monthly GitHub Action (`.github/workflows/refresh.yml`) that pulls the data and commits the snapshot.

### Changed
- LICENSE copyright holder corrected to Syed Zia Haider.

### Series replacements
- Pumps: BLS series PCU333911333911 ended in 2017. Compressors (PCU333912333912) stand in for it.
