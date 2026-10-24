# Open Plant Cost Index (OPCI)

A free, open source plant cost index, checked against the Chemical Engineering Plant Cost Index (CEPCI), using only public domain data.

Maintained by ORIMIZ Consulting.

> **Status:** version 1.0.0. Pin a data release (see below) so your estimates do not change when the data refresh.

## What it does

At the very start of a project, before any engineering is done, an owner needs a first cost estimate to decide whether the idea is worth pursuing. AACE International (Association for the Advancement of Cost Engineering) calls this a Class 5 estimate, made in the pre-feasibility phase, also known as FEL 1 (Front-End Loading 1). It is usually built from analogue projects: plants already built, whose known costs are adjusted (normalized) to match the new project. Two of the key adjustments are time, because costs change from year to year, and place, because costs differ from country to country. OPCI provides both.

OPCI answers two questions about process plant construction costs:

1. **Time.** How much have plant costs changed between year A and year B? This is escalation.
2. **Place.** How do plant costs in one country compare with the US Gulf Coast? This is the location factor.

OPCI reports the two numbers apart, then the combined factor. It never blends them silently.

It is built for students, small consultancies, researchers and independent estimators who cannot buy paid cost index data.

## Where the numbers come from

- **Escalation** uses 12 price and wage series from the US Bureau of Labor Statistics (BLS), pulled through FRED (Federal Reserve Economic Data, St. Louis Fed). All are public domain. See [DATA_NOTICE.md](DATA_NOTICE.md).
- **Weights** follow the published 2002 CEPCI component weights, mapped to the 12 series.
- **Scale.** The level of the index estimated by OPCI is checked against public CEPCI values. The scale has no effect on any escalation factor.
- **Location factors** come from published group factors (Oxford Institute for Energy Studies) and a stated step rule. Each factor has a range, a confidence level and a source.

The full method is in [METHOD.md](METHOD.md). The check against public CEPCI values is in [VALIDATION.md](VALIDATION.md).

## Quick start

```
pip install opci
```

The package carries its own copy of the data, so it works outside a clone. `opci refresh` saves newer data in `~/.opci` (or the folder named by `OPCI_HOME`). To work on OPCI itself, clone the repository and run `pip install -e ".[dev]"`.

Command line:

```
opci factor --base 2011 --target 2026 --location ID-KAL
opci factor --base 2015 --location ID-KAL --from AU-NW
opci series --start 2008 --freq quarterly --out opci_general.csv
opci series --start 2008 --chart opci_general.html
opci refresh
opci validate
```

Sample output:

```
Open Plant Cost Index (OPCI) v1.0.0 | Maintained by ORIMIZ Consulting
Data to 2026-09 | investment type: general | productivity 2% | index source: open
Escalation 2011 to 2026:   x1.53
Location US Gulf Coast to East Kalimantan, Indonesia:   x1.20  (range 1.08 to 1.38, confidence: medium)
Combined factor:   x1.84
Sources: BLS via FRED (12 series, cached snapshot 2026-10-24); location: ID-KAL: step rule (see location table, version 0.1.0)
Note: 2026 is a part year (January to September average).
```

If you leave out `--target`, OPCI uses the latest full quarter and says so under the escalation line:

```
Escalation 2011 to 2026Q3:   x1.56
Target: 2026Q3 (latest quarter). Use --target 2026 for the year average.
```

Python:

```python
from opci import escalation, location, combined, series, format_factor

escalation(base="2011", target="2026Q3")
location(to="ID-KAL", frm="AU-NW")
print(format_factor(combined(base="2011", target="2026", to="ID-KAL")))
series(start=2008, freq="annual")
```

Dates are a year (`2011`) or a year and quarter (`2011Q2`). The target date defaults to the latest full quarter. Location codes are in [location/factors.csv](location/factors.csv).

## Pinning a data release

Each monthly refresh that passes its checks makes a data release, for example `data-2026-09`. Releases are never changed after they are made. A tool that uses OPCI must name a release, never "latest", so its estimates do not change overnight:

- Files: `data/releases/data-2026-09/opci_general_annual.csv` (also quarterly, and JSON). Each release has a `RELEASE_NOTE.md` and a git tag of the same name.
- Python: `from opci import read_release; read_release("data-2026-09")`

## Using your own CEPCI or paid data

If you hold a CEPCI subscription or paid index data, you can use it in place of the open index. Put the values in a local file:

- `private_cepci.csv` for your CEPCI values, or
- `private_paid_<name>.csv` for paid data, for example `private_paid_ucci.csv`.

The format is `period,value`, with periods as years (`2011`) or years and quarters (`2011Q2`), one kind per file. The tool looks in the current folder, or in the folder named by the `OPCI_PRIVATE_DIR` environment variable.

```
opci factor --base 2011 --target 2025 --location ID-KAL --index-source private_cepci
opci factor --base 2011 --target 2025 --index-source paid --paid-name ucci
```

The tool says what the file covers, warns about gaps and jumps above 25% between periods, and never fills gaps. The output names the file used.

These files are ignored by git, blocked by a pre-commit check and checked again by the tests. Never commit or publish them. They are your licensed data.

## Limits

- OPCI is checked against public CEPCI values. It is not CEPCI. Expect differences of up to about 5% in normal years, and more in 2021 and 2022, when supply shocks after the pandemic made index values less certain.
- The data are US prices. Other countries are handled through location factors. These are judgment based and carry wider uncertainty, often plus or minus 15 to 20%.
- The tool assumes plant costs abroad rise at the US rate in dollar terms. This holds well for imported equipment and less well for local labour and materials. Version 2 will address this.
- OPCI is suited to screening and early estimates (AACE International Class 5 and Class 4). For funding decisions, use project-specific data.

## Citing OPCI

<!-- Zenodo DOI badge goes here after the 1.0.0 GitHub release:
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.NNNNNNN.svg)](https://doi.org/10.5281/zenodo.NNNNNNN) -->

Please cite OPCI with the version and data release you used:

> Haider, S. Z. (2026). *Open Plant Cost Index (OPCI)* (Version 1.0.0, data release data-2026-09) [Computer software]. Maintained by ORIMIZ Consulting. https://github.com/ORIMIZ-Consulting/open-plant-cost-index

GitHub shows a "Cite this repository" button built from [CITATION.cff](CITATION.cff). A Zenodo DOI (Digital Object Identifier) will be added at the 1.0.0 release.

## Licence

Code is under the MIT licence. Copyright (c) 2026 Syed Zia Haider. See [LICENSE](LICENSE).

CEPCI is a trademark of Chemical Engineering magazine. OPCI is not affiliated with or endorsed by Chemical Engineering.
