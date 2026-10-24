# Data notice

Every number OPCI ships comes from public domain or openly licensed data, or from a stated judgment. This file lists each source and its status.

## Escalation data

| Source | What we use | Status |
|---|---|---|
| US Bureau of Labor Statistics (BLS), Producer Price Index (PPI) | 11 price series for equipment, materials, engineering and buildings | US federal government work. Public domain in the United States. |
| BLS, Current Employment Statistics (CES) | Average hourly earnings, construction production workers | US federal government work. Public domain in the United States. |
| Federal Reserve Bank of St. Louis, FRED (Federal Reserve Economic Data) | Delivery of the BLS series above | We use FRED only to download BLS data. The BLS data keep their public domain status. |

The series list is in [escalation/series.yaml](escalation/series.yaml).

## Validation data

Chemical Engineering magazine posts each year's final CEPCI annual average free on its website. OPCI uses a small number of these values only to set the display scale and to check its accuracy. Each value is cited to its public source in `escalation/public_points.csv`. OPCI does not reproduce the CEPCI series.

CEPCI is a trademark of Chemical Engineering magazine. OPCI is not affiliated with or endorsed by Chemical Engineering.

## Location data

Location factors come from published group factors in Oxford Institute for Energy Studies (OIES) papers, and from a stated step rule. Each factor names its source in [location/factors.csv](location/factors.csv).

## User data

Files named `private_*` hold the user's own licensed data (CEPCI subscription or paid indices). They are ignored by git and are never part of this repository or its releases.
