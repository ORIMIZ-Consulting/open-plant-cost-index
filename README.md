# Open Plant Cost Index (OPCI)

A free, open source plant cost index built to track the Chemical Engineering Plant Cost Index (CEPCI) closely, using only public domain data.

Maintained by ORIMIZ Consulting.

> **Status:** under construction. Version 1.0.0 is not released yet. Numbers in this repository may change until then.

## What it does

OPCI answers two questions about process plant construction costs:

1. **Time.** How much have plant costs changed between year A and year B? This is escalation.
2. **Place.** How do plant costs in one country compare with the US Gulf Coast? This is the location factor.

OPCI reports the two numbers apart, then the combined factor. It never blends them silently.

It is built for students, small consultancies, researchers and independent estimators who cannot buy paid cost index data.

## Where the numbers come from

- **Escalation** uses 12 price and wage series from the US Bureau of Labor Statistics (BLS), pulled through FRED (Federal Reserve Economic Data, St. Louis Fed). All are public domain. See [DATA_NOTICE.md](DATA_NOTICE.md).
- **Weights** follow the published 2002 CEPCI component weights, mapped to the 12 series.
- **Scale.** The level of the index is checked against public CEPCI values. It has no effect on any escalation factor.
- **Location factors** come from published group factors (Oxford Institute for Energy Studies) and a stated step rule. Each factor has a range, a confidence level and a source.

The full method is in [METHOD.md](METHOD.md). The check against public CEPCI values is in [VALIDATION.md](VALIDATION.md).

## Quick start

Coming with version 1.0.0. The planned interface:

```
pip install opci
opci factor --base 2011 --target 2026Q3 --location ID-KAL
```

```python
from opci import escalation, location, combined, series

escalation(base="2011", target="2026Q3")
location(to="ID-KAL", frm="US-GC")
```

## Using your own CEPCI or paid data

If you hold a CEPCI subscription or paid index data, you can use it in place of the open index. Put the values in a local file named `private_cepci.csv` or `private_paid_<name>.csv`. These files are ignored by git and must never be committed or published. They are your licensed data.

## Limits

- OPCI is checked against public CEPCI values. It is not CEPCI. Expect differences of up to about 5% in normal years, and more in 2021 and 2022, when supply shocks after the pandemic made index values less certain.
- The data are US prices. Other countries are handled through location factors. These are judgment based and carry wider uncertainty, often plus or minus 15 to 20%.
- The tool assumes plant costs abroad rise at the US rate in dollar terms. This holds well for imported equipment and less well for local labour and materials. Version 2 will address this.
- OPCI is suited to screening and early estimates (AACE International Class 5 and Class 4). For funding decisions, use project-specific data.

## Citing OPCI

See [CITATION.cff](CITATION.cff). A Zenodo DOI (Digital Object Identifier) will be added at the first release.

## Licence

Code is under the MIT licence. Copyright (c) 2026 Syed Zia Haider. See [LICENSE](LICENSE).

CEPCI is a trademark of Chemical Engineering magazine. OPCI is not affiliated with or endorsed by Chemical Engineering.
