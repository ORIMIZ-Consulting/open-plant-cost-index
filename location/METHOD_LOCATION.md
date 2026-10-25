# Location method

Open Plant Cost Index (OPCI) location module, version 0.2.0 (see [VERSION](VERSION)). Maintained by ORIMIZ Consulting.

The table holds 18 locations: the US Gulf Coast reference, 5 Oxford Institute for Energy Studies (OIES) group factors and 12 step-rule factors.

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

**Range from the US Gulf Coast.** B's range exactly as it stands in the table.

**Range between two other places (decided, 24 October 2026).** Both places carry uncertainty, so the two ranges are combined by root sum of squares of their relative deviations. For each row, the low deviation is 1 - low / factor and the high deviation is high / factor - 1. Then:

```
low deviation  = sqrt( B_low_dev^2  + A_high_dev^2 )
high deviation = sqrt( B_high_dev^2 + A_low_dev^2 )

low  = factor(B) / factor(A) x (1 - low deviation)
high = factor(B) / factor(A) x (1 + high deviation)
```

A high A pushes the ratio down, so A's high deviation goes with B's low deviation, and the other way round.

Example: North West Australia to East Kalimantan gives x 0.70, with a range of about 0.57 to 0.83.

**Same place.** Moving a cost within one place gives x 1.00 with no range.

**Confidence.** The lower of the two confidence levels.

## 5. Age of the factors

Every row carries an `as_of` year.

- Rows taken from the Oxford Institute for Energy Studies (OIES) groups carry 2018. The groups reflect projects from about 2010 to 2018.
- Step-rule rows carry 2026, the year the judgment was made. Their notes name the starting group and its year.
- The reference row carries 2026.

## 5a. Step trails (approved by the owner, October 2026)

| Code | Start | Steps | Result |
|---|---|---|---|
| ID-KAL | REMOTE 1.30 | -0.10 existing LNG hub (Bontang) | 1.20 |
| MY-BIN | REMOTE 1.30 | -0.10 existing LNG hub; -0.10 local fabrication yards and skilled local labour | 1.10 |
| QA-RLF, AE, OM | US-GC 1.00 | +0.10 extreme heat; +0.10 nearly all equipment imported; -0.10 mature LNG hub; -0.10 lower-cost imported labour | 1.00 |
| CA-BC | REMOTE 1.30 | +0.10 high and scarce skilled labour; +0.10 wet cold climate; -0.10 heavy use of Asian-built modules | 1.40 |
| RU-SAK | REMOTE 1.30 | +0.10 ice and cold climate; +0.10 little local labour and long logistics; -0.10 existing LNG site and infrastructure at Prigorodnoye | 1.40 (confirmed by practitioner judgment) |

Added in location version 0.2.0 (approved by the owner, October 2026):

| Code | Start | Steps | Result |
|---|---|---|---|
| NG-BON | REMOTE 1.30 | -0.10 existing LNG hub (six trains at Bonny) | 1.20 |
| MZ-AFU | REMOTE 1.30 | +0.10 first-of-a-kind remote site with no infrastructure | 1.40 |
| AO-SOY | REMOTE 1.30 | No step (remote single-train site) | 1.30 |
| ID-SUL | REMOTE 1.30 | No step (remote single-train site) | 1.30 |
| ID-PAP | REMOTE 1.30 | -0.10 existing LNG site (Trains 1 and 2) | 1.20 |

All five are medium confidence, with the range -10% / +15% and `as_of` 2026.

A test checks that each trail starts from the named group's factor and adds up to the row's factor.

## 6. Python

```python
from opci import location

location(to="ID-KAL")              # from the US Gulf Coast
location(to="ID-KAL", frm="AU-NW")  # from North West Australia
```

Each result gives the factor, range, confidence, method, full source, `as_of`, notes and the location module version.

## 7. Open items

- Cross-check against World Bank ICP construction price levels: version 2.
