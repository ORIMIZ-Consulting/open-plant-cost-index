# Using OPCI with AI chat tools

Open Plant Cost Index (OPCI). Maintained by ORIMIZ Consulting.

This guide is for people who want to use OPCI through an artificial intelligence (AI) chat tool such as Gemini or ChatGPT, instead of installing it. You upload three data files, give the tool the formulas below and ask it to do the arithmetic.

> **The OPCI tool's own output is the reference.** AI chat tools can misread tables and make arithmetic mistakes. Check any AI answer against the tool (`pip install opci`, then `opci factor ...`) or against the worked example below before you use it.

## 1. Files to upload

All three files are pinned to OPCI version 1.0.0 and data release `data-2026-09` (data to September 2026). Download them from these raw GitHub links, then upload them to the chat:

| File | What it holds | Raw link |
|---|---|---|
| `opci_general_quarterly.csv` | OPCI by quarter, 2008Q1 onward | https://raw.githubusercontent.com/ORIMIZ-Consulting/open-plant-cost-index/v1.0.0/data/releases/data-2026-09/opci_general_quarterly.csv |
| `opci_general_annual.csv` | OPCI by year, 2008 onward | https://raw.githubusercontent.com/ORIMIZ-Consulting/open-plant-cost-index/v1.0.0/data/releases/data-2026-09/opci_general_annual.csv |
| `location/factors.csv` | Location factors against the US Gulf Coast, with ranges | https://raw.githubusercontent.com/ORIMIZ-Consulting/open-plant-cost-index/v1.0.0/location/factors.csv |

Newer data releases appear in [data/releases](data/releases) each month, for example `data-2026-10`. Name the release you used in your estimate, so it can be reproduced.

### Columns that matter

- **Index files:** `period` (a year such as `2015`, or a quarter such as `2026Q3`), `value` (the OPCI index), `part` (`True` when the period has fewer months than full), `supply_shock` (`True` for 2021 and 2022), `revised` (`True` when the value moved more than 0.5% since the previous release). The other columns are the component series and the version and data date.
- **Location file:** `code`, `name`, `factor` (central value), `low` and `high` (range), `confidence`, `method`, `source`, `as_of` and `notes`.

A year from the annual file and a quarter from the quarterly file are on the same scale, so you can mix them, for example a 2015 base with a 2026Q3 target.

## 2. Formulas

### Escalation (time)

```
escalation = index at target / index at base
```

Take the base value and the target value from the `value` column. Use the annual file for a year and the quarterly file for a quarter.

### Location (place)

```
location factor A to B = factor(B) / factor(A)
```

- **From the US Gulf Coast (`US-GC`, factor 1.00):** the range is B's `low` and `high` exactly as they stand in the file.
- **Between two other places:** combine the two ranges by root sum of squares of their relative deviations. For each place, the low deviation is `1 - low / factor` and the high deviation is `high / factor - 1`. Then:

```
low deviation  = sqrt( B_low_dev^2  + A_high_dev^2 )
high deviation = sqrt( B_high_dev^2 + A_low_dev^2 )

low  = factor(B) / factor(A) x (1 - low deviation)
high = factor(B) / factor(A) x (1 + high deviation)
```

  Check: North West Australia (`AU-NW`) to East Kalimantan (`ID-KAL`) gives x0.70, with a range of 0.57 to 0.82.
- **Confidence:** the lower of the two places.

### Combined factor

```
combined factor = escalation x location factor
new cost        = old cost x combined factor
range           = old cost x escalation x location low  to  old cost x escalation x location high
```

Report escalation and location apart, then the combined factor. Do not blend them.

## 3. Supply-shock note

If the base date or the target date falls in 2021 or 2022 (`supply_shock` is `True`), add this note to the answer:

> Note: 2021 and 2022 were unusual years. Supply shocks after the pandemic pushed equipment and material prices up quickly and unevenly. Index values for these years are less certain than for other years. Escalation from a 2021 or 2022 cost date may be somewhat overstated, and escalation to a 2021 or 2022 target date may be somewhat understated. See METHOD.md.

Also say so when a period is a part year or part quarter (`part` is `True`).

## 4. Worked example

**Question:** a plant cost USD 100 million in 2015 on the US Gulf Coast. What would it cost in Oman in the third quarter of 2026?

| Step | Source | Value |
|---|---|---|
| Index at base, 2015 | `opci_general_annual.csv`, period `2015` | 570.3834 |
| Index at target, 2026Q3 | `opci_general_quarterly.csv`, period `2026Q3` | 872.2010 |
| Escalation | 872.2010 / 570.3834 | **x1.529** |
| Location US Gulf Coast to Oman | `factors.csv`: `OM` 1.00 / `US-GC` 1.00 | **x1.00** (range 0.90 to 1.15, confidence medium) |
| Combined factor | 1.529 x 1.00 | **x1.529** |
| Cost in Oman, 2026Q3 | USD 100 million x 1.529 | **USD 152.9 million** |
| Range | USD 100 million x 1.529 x 0.90 to x 1.15 | **USD 137.6 million to USD 175.9 million** |

Neither date is in 2021 or 2022 and neither period is a part period, so no notes apply.

The same result from the OPCI tool:

```
opci factor --base 2015 --target 2026Q3 --location OM

Open Plant Cost Index (OPCI) v1.0.0 | Maintained by ORIMIZ Consulting
Data to 2026-09 | investment type: general | productivity 2% | index source: open
Escalation 2015 to 2026Q3:   x1.53
Location US Gulf Coast to Oman (Qalhat):   x1.00  (range 0.90 to 1.15, confidence: medium)
Combined factor:   x1.53
Sources: BLS via FRED (12 series, cached snapshot 2026-10-24); location: OM: step rule (see location table, version 0.1.0)
```

If an AI answer for this question is not about USD 153 million (range about 138 to 176), it has misread a file or made an arithmetic mistake.

## 5. A prompt you can paste

> I have uploaded three files from the Open Plant Cost Index (OPCI) 1.0.0, data release data-2026-09: opci_general_annual.csv, opci_general_quarterly.csv and factors.csv. A plant cost [amount] in [base year or quarter] in [place, by code from factors.csv]. Estimate its cost in [target year or quarter] in [place].
> Use escalation = index at target / index at base, taking `value` from the annual file for a year and the quarterly file for a quarter. Use location factor A to B = factor(B) / factor(A). If A is US-GC, use B's low and high as the range; otherwise combine the ranges by root sum of squares of the relative deviations (low dev = sqrt(B_low_dev^2 + A_high_dev^2), high dev = sqrt(B_high_dev^2 + A_low_dev^2)). Combined factor = escalation x location. Show each value you read from the files and each step. Report escalation, location (with range and confidence) and the combined factor apart. If a date falls in 2021 or 2022, or a period is marked part, say so.

Then check the answer against the OPCI tool.

## 6. Limits

- OPCI is checked against public Chemical Engineering Plant Cost Index (CEPCI) values. It is not CEPCI. Expect differences of up to about 5% in normal years, and more in 2021 and 2022.
- Location factors are judgment based and carry wide ranges.
- OPCI suits screening and early estimates (AACE International Class 5 and Class 4). For funding decisions, use project-specific data.

The full method is in [METHOD.md](METHOD.md) and [location/METHOD_LOCATION.md](location/METHOD_LOCATION.md).

CEPCI is a trademark of Chemical Engineering magazine. OPCI is not affiliated with or endorsed by Chemical Engineering.
