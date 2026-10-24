# Location method

Open Plant Cost Index (OPCI) location module, version 0.1.0 (see [VERSION](VERSION)). Maintained by ORIMIZ Consulting.

The location module answers one question: how do plant costs in one place compare with the US Gulf Coast? It is judgment driven, unlike escalation, which is data driven. The two are kept apart. They share no code and meet only at the combined factor step.

## 1. What the table holds

[factors.csv](factors.csv) lists location factors against the US Gulf Coast (= 1.00), for process plants and LNG (liquefied natural gas) plants. Each row has:

| Field | Meaning |
|---|---|
| `code` | Location code, for example `ID-KAL`. Codes allow sub-regions, for example `CA-BC`. |
| `name` | Plain name |
| `factor` | Central value |
| `low`, `high` | Range |
| `confidence` | High, medium or low |
| `method` | Reference, published group, step rule, analog or ICP (International Comparison Program) cross-check |
| `source` | Key to the full reference in [sources.yaml](sources.yaml) |
| `as_of` | Year the factor represents |
| `notes` | Plain explanation of the judgment |

The Middle East is kept as separate rows by country, not one regional factor.

## 2. Range rule (decided)

Ranges lean upward, because location surprises push cost up more often than down.

| Confidence | When it applies | Range around central |
|---|---|---|
| High | Reference location, or a recent published factor backed by several projects | -10% / +10% |
| Medium | Published group factor, or step rule from a near published group | -10% / +15% |
| Low | Generic or analog-only factor | -15% / +25% |

A test checks every row against this rule.

## 3. Step rule

When no published factor exists, start from the nearest published group. Move up or down in steps of 0.10, one step for each clear difference:

- an existing industrial hub
- local fabrication yards
- skilled local labour
- remoteness
- extreme climate

Write each step down in `notes`.

## 4. Moving a cost between two places

```
Location factor (A to B) = factor(B) / factor(A)
```

Example: an Ichthys cost (North West Australia, 1.72) moved to East Kalimantan (1.20) gives x 1.20 / 1.72 = x 0.70.

**Range and confidence for A to B.** The range is the range of B divided by the central factor of A. Confidence is the lower of the two. When A is the US Gulf Coast, this gives B's row exactly as it stands in the table.

## 5. Age of the factors

Every row carries an `as_of` year. The Oxford Institute for Energy Studies (OIES) group factors reflect projects from about 2010 to 2018, so those rows and the step-rule rows built from them carry 2018. The reference row carries 2026.

## 6. Python

```python
from opci.locations import location

location(to="ID-KAL")              # from the US Gulf Coast
location(to="ID-KAL", frm="AU-NW")  # from North West Australia
```

Each result gives the factor, range, confidence, method, full source, `as_of`, notes and the location module version.

## 7. Open items

- The OIES figure and page for each published group factor are not yet checked against the paper.
- Step trails (which group each step-rule row started from, and each 0.10 step) are not yet written in `notes`.
- Cross-check against World Bank ICP construction price levels: version 2.
