# Changelog

All notable changes to OPCI are listed here. Code versions (v1.0.0) and data releases (data-2026-09) are tracked apart.

## Roadmap

### 1.2 (planned)
- `series()` returns a pandas table when pandas is installed. The current format (`{'meta', 'rows'}`) stays as the fallback when it is not. (Planned for 1.1; moved here because 1.1.0 holds the new locations only.)
- LNG (liquefied natural gas) weights, once their public basis is documented.
- Quarterly data releases.
- More locations: Egypt, Mexico (Pacific coast), Argentina, Arctic Norway, Saudi Arabia.

### 2.0 (planned)
- Imported and local cost split, World Bank International Comparison Program (ICP) cross-check, local currency output.

## 1.1.0 (25 October 2026)

Adds five LNG locations by the step rule. No existing location value or escalation value changed.

DOI (Digital Object Identifier) for this version: [10.5281/zenodo.23637856](https://doi.org/10.5281/zenodo.23637856).

### Added
- Five locations, approved by the owner, all by the step rule from the Oxford Institute for Energy Studies (OIES) remote group (REMOTE 1.30, 2018), medium confidence, range -10% / +15%, `as_of` 2026:

  | Code | Location | Factor | Range | Step trail |
  |---|---|---|---|---|
  | NG-BON | Bonny, Nigeria | 1.20 | 1.08 to 1.38 | -0.10 existing LNG hub (six trains at Bonny) |
  | MZ-AFU | Afungi, Mozambique | 1.40 | 1.26 to 1.61 | +0.10 first-of-a-kind remote site with no infrastructure |
  | AO-SOY | Soyo, Angola | 1.30 | 1.17 to 1.50 | No step (remote single-train site) |
  | ID-SUL | Central Sulawesi, Indonesia (Donggi-Senoro) | 1.30 | 1.17 to 1.50 | No step (remote single-train site) |
  | ID-PAP | Bintuni Bay, West Papua, Indonesia (Tangguh) | 1.20 | 1.08 to 1.38 | -0.10 existing LNG site (Trains 1 and 2) |

- AI_GUIDE.md: how to use OPCI with artificial intelligence (AI) chat tools, with a worked example.
- Release notes template (`.github/RELEASE_TEMPLATE.md`), with "Update dependent tools: open-fel1-lng-cost" for a first-number (MAJOR) change.
- Tests: the five new rows follow the range rule and carry their step trail; the table holds 18 locations.

### Changed
- Location module version 0.2.0 (was 0.1.0). The table now holds 18 locations.
- AI_GUIDE.md links pinned to v1.1.0.
- Zenodo DOIs in CITATION.cff and the README.

### Values
- Escalation values: unchanged.
- Location values: the 13 existing rows are unchanged. Five new rows.
- Data release used for the checks: data-2026-09.

### Checks
- Tests: all 92 pass.
- Back-test worst error on normal years: 5.5% (fail limit 8%).

CEPCI is a trademark of Chemical Engineering magazine. OPCI is not affiliated with or endorsed by Chemical Engineering.

## 1.0.0 (24 October 2026)

First release of the Open Plant Cost Index (OPCI). Maintained by ORIMIZ Consulting.

DOI (Digital Object Identifier) for this version: [10.5281/zenodo.23615227](https://doi.org/10.5281/zenodo.23615227).

### Changes since 1.0.0-rc1
- When the target date is not given, the output says so under the escalation line, for example "Target: 2026Q3 (latest quarter). Use --target 2026 for the year average." Results carry a `default_target` flag and a `target_note`.
- README: estimating context (AACE International Class 5, FEL 1) and the Scale line reworded.
- The GitHub release notes now hold only the section for the tagged version.

### What OPCI gives you
- **Escalation** for general process plant, by year or quarter, from 2008 to the latest month. Built from 12 public domain US Bureau of Labor Statistics (BLS) series pulled through FRED (Federal Reserve Economic Data), weighted by the published 2002 Chemical Engineering Plant Cost Index (CEPCI) component weights, with a 2% a year productivity adjustment on labour and engineering (switchable).
- **Scale** checked against public CEPCI values on 14 normal years (2008 to 2020 and 2023): OPCI 2019 = 612.9. Switch to 2019 = 100 if you prefer. The scale never changes an escalation factor.
- **Location factors** for 13 places against the US Gulf Coast, each with a range, confidence level, method, source and `as_of` year. Moving a cost between two places uses factor(B) / factor(A), with ranges combined by root sum of squares.
- **Combined factor**: escalation times location, with both shown apart.
- **Outputs** as text, CSV, JSON and an interactive HTML chart. Every output shows the version, data date, investment type, productivity setting and index source.
- **Python** (`escalation`, `location`, `combined`, `series`, `format_factor`, `read_release`) and **command line** (`opci factor`, `opci series`, `opci refresh`, `opci validate`).
- **Overrides**: use your own CEPCI values (`private_cepci.csv`) or paid data (`private_paid_<name>.csv`). Gaps and odd jumps are reported, never filled. These files are never committed.
- **Data releases** for pinning: first release `data-2026-09` (data to September 2026). Releases never change; revisions make a new release.

### Validation (data-2026-09)
- Prototype values in the spec reproduced within 0.06 index points.
- Worst error against public CEPCI on the 14 normal years: 5.5% (2016), within the 8% fail limit. Root mean square error 3.2%.
- Supply-shock years 2021 and 2022 are left out of the scale and checked on a 10% watch limit that reports only: 2021 -6.2%, 2022 -8.9%. The output carries a note when a base or target date falls in those years.
- Oxford Institute for Energy Studies (OIES) group factors checked against Songhurst (2018), OIES Paper NG 137, Figure 5 (p. 12), Figure 16 (p. 41) and the remote group text (p. 12): no mismatches.

### Data refresh
- Monthly GitHub Action: pulls FRED, reports stale series (over 6 months), fails on discontinued series (failed download or over 12 months), reports BLS revisions above 0.5%, runs the back-test, then makes a tagged data release.
- If FRED cannot be reached, OPCI keeps using the cached snapshot and says so.

### Packaging
- The package carries its own copy of the data (`opci/_bundled/`, built by `setup.py`), so `pip install` works outside a clone. `opci refresh` saves newer data in `~/.opci` or `OPCI_HOME`.
- Release workflow (`.github/workflows/release.yml`): tests, build and an install check on every version tag; PyPI trusted publishing and the GitHub release for final tags only.

### Known limits
- OPCI is checked against public CEPCI values. It is not CEPCI. Expect differences of up to about 5% in normal years, more in 2021 and 2022.
- No public CEPCI annual value was found for 2024 or 2025. The 2014 value is from a secondary source.
- General process plant weights only. LNG weights come in version 1.1.
- US prices, with judgment-based location factors. Suitable for screening and early estimates (AACE International Class 5 and Class 4).

### Changes during the build
- LICENSE copyright holder set to Syed Zia Haider.
- Description changed to "A free, open source plant cost index, checked against the Chemical Engineering Plant Cost Index (CEPCI), using only public domain data."

### Series replacements
- Pumps: BLS series PCU333911333911 ended in 2017. Compressors (PCU333912333912) stand in for it.

CEPCI is a trademark of Chemical Engineering magazine. OPCI is not affiliated with or endorsed by Chemical Engineering.

## 1.0.0-rc1 (24 October 2026)

Release candidate. Same content as 1.0.0 above, without the changes listed under "Changes since 1.0.0-rc1". Tagged, not published to PyPI.

CEPCI is a trademark of Chemical Engineering magazine. OPCI is not affiliated with or endorsed by Chemical Engineering.
