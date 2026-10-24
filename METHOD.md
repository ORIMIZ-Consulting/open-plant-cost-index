# Method

Open Plant Cost Index (OPCI). Maintained by ORIMIZ Consulting.

This file sets out how OPCI is built: the data, the weights, the formulas and the decisions behind them. The back-test results are in [VALIDATION.md](VALIDATION.md).

## 1. Two numbers, kept apart

OPCI answers two questions and reports them as two numbers:

1. **Escalation (time).** How plant costs changed between two dates. This is data driven.
2. **Location (place).** How plant costs in one place compare with the US Gulf Coast. This is judgment driven.

The combined factor is escalation times location. OPCI never blends the two silently.

## 2. Escalation data

Twelve series from the US Bureau of Labor Statistics (BLS), pulled through FRED (Federal Reserve Economic Data, St. Louis Fed). All are public domain. The list is in [escalation/series.yaml](escalation/series.yaml).

| Code | Component | FRED series ID |
|---|---|---|
| HX | Heat exchangers | PCU332410332410 |
| TANK | Tanks and vessels | PCU332420332420 |
| MACH | Process machinery | WPU114 |
| VALVE | Valves | PCU332911332911 |
| PIPE | Pipe | WPU101706 |
| INST | Instruments | PCU334513334513 |
| COMP | Compressors | PCU333912333912 |
| ELEC | Electrical equipment | WPU117 |
| STRUCT | Structural steel | PCU332312332312 |
| LAB | Construction labour | CES2000000008 |
| ENG | Engineering | PCU541330541330 |
| BLDG | Buildings | PCU236211236211 |

**Replacement.** The pump series PCU333911333911 ended in 2017. Compressors (PCU333912333912) stand in for it.

Each data pull is saved as a snapshot in `data/snapshots/<pull date>/`. If FRED cannot be reached, the tool uses the latest snapshot.

## 3. Weights

General process plant weights follow the Chemical Engineering Plant Cost Index (CEPCI) published 2002 component weights, mapped to the 12 series and scaled from 99.9% to 100%. They are in [escalation/weights_general.yaml](escalation/weights_general.yaml).

| Code | HX | TANK | MACH | VALVE | PIPE | INST | COMP | ELEC | STRUCT | LAB | ENG | BLDG |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Weight % | 8.56 | 8.56 | 6.51 | 4.80 | 4.80 | 5.31 | 3.20 | 3.50 | 5.31 | 29.03 | 15.82 | 4.60 |

Version 1 ships general weights only. LNG (liquefied natural gas) weights come in version 1.1, once their public basis is documented.

## 4. Formula

For each period *t*:

```
OPCI(t) = Scale x sum over series i of [ w_i x ( P_i(t) / P_i(2019) ) x adj_i(t) ]

  w_i      weight of series i (sums to 1)
  P_i(t)   average value of series i in period t
  P_i(2019) average value of series i in 2019
  adj_i(t) (1 - p)^(t - 2019) for LAB and ENG; 1 for all others
  p        productivity rate, default 0.02
```

- Annual values are the average of the months. Quarterly values are the average of the three months.
- A year or quarter with missing months is a part period and is labelled.
- For quarters, *t - 2019* runs from the middle of 2019 to the middle of the quarter. For example, 2020Q1 is 0.625 years. The four 2019 quarters then average back to the 2019 annual value.

**Why the productivity adjustment.** Construction wages rise faster than the cost of the work done, because output per worker also rises. Without the adjustment the index runs well ahead of CEPCI over 15 years.

## 5. Scale

The scale sets the level of the index. It has no effect on any escalation factor.

- **Default:** a CEPCI-comparable scale, set by best fit to public CEPCI annual averages. The fit is least squares on the log of the ratio OPCI / CEPCI. It does not match any single year.
- **Switch:** 2019 = 100.

OPCI is never forced through the public points. Doing so would rebuild CEPCI from its own numbers.

### 5.1 Public points

Public CEPCI annual averages are stored with their sources in [escalation/public_points.csv](escalation/public_points.csv). Each row has a `use` field:

- `fit`: a normal year, used for the scale fit and the back-test.
- `watch`: a supply-shock year, left out of the fit and checked on a watch limit.

One point is added each year when Chemical Engineering publishes the new annual average. The scale is then refitted.

### 5.2 Supply-shock years (decided, 24 October 2026)

**Decision.** 2021 and 2022 are treated as supply-shock years. They are left out of the scale fit.

**Why.** After the pandemic, equipment and material prices rose fast. CEPCI picked up the rise faster than the BLS series OPCI uses. With all 16 public points in the fit, 2022 alone pulled the scale up and its error reached 8.0%, just over the fail limit. A short shock should not set the level of the whole index.

**What it means.**

- The scale is fitted on the 14 normal years (2008 to 2020 and 2023).
- The 8% fail limit applies to the normal years. If the worst error there goes above 8%, the build fails.
- 2021 and 2022 are still shown on the validation page, marked as supply-shock years. They are checked against a separate 10% watch limit. Going above the watch limit is reported but does not fail the build.
- When a base or target date falls in 2021 or 2022, the output carries a warning. OPCI ran below CEPCI in those years. A base date in those years may overstate escalation from it. A target date in those years may understate escalation to it.

**Result with the 2026-10-24 snapshot:** scale gives OPCI 2019 = 612.9. Worst error on the 14 normal years is 5.5% (2016). Supply-shock years: 2021 is -6.2% and 2022 is -8.9%.

## 6. Productivity rate

The default is 2% a year on labour and engineering. The validation page also shows the rate fitted jointly with the scale, as a check only. The default does not move with that fit.

## 7. Limits

- OPCI tracks CEPCI. It is not CEPCI. Expect differences of up to about 5% in normal years, and more in supply-shock years.
- The data are US prices. Other places are handled through location factors, which are judgment based.
- OPCI assumes plant costs abroad rise at the US rate in dollar terms.
- OPCI suits screening and early estimates (AACE International Class 5 and Class 4).

## 8. Location

The location method is kept apart from escalation, in `location/` with its own method note. It is built in a later step.

CEPCI is a trademark of Chemical Engineering magazine. OPCI is not affiliated with or endorsed by Chemical Engineering.
