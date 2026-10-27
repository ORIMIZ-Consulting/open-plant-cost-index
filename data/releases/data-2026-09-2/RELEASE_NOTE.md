# OPCI data release data-2026-09-2

Open Plant Cost Index (OPCI) v1.1.1 | Maintained by ORIMIZ Consulting  
Data to 2026-09 | snapshot 2026-10-24 | investment type: general | productivity 2% | index source: open

## Contents

- `opci_general_annual.csv` and `.json`: annual values, 2008 to 2026.
- `opci_general_quarterly.csv` and `.json`: quarterly values.
- Columns: period, value, part (part period), supply_shock (2021 or 2022), revised (moved more than 0.5% since the previous release), each component rebased to 2019 = 100, then version and data date.

## Checks

- Scale: OPCI 2019 = 612.9, checked against public CEPCI values on 14 normal years.
- Back-test worst error on normal years: 5.5% (fail limit 8%): pass.
- Supply-shock years worst error: 8.9% (watch limit 10%, reports only).
- Annual values revised by more than 0.5% since data-2026-09: 0.

## Series replacements

- Pumps (PCU333911333911) ended 2017. Replaced by PCU333912333912. Compressors stand in for pumps.

CEPCI is a trademark of Chemical Engineering magazine. OPCI is not affiliated with or endorsed by Chemical Engineering.
