# Location validation

Open Plant Cost Index (OPCI) location module, version 0.2.0. Maintained by ORIMIZ Consulting.

This page compares OPCI location factors with published factors. In version 1 the only published source is the Oxford Institute for Energy Studies (OIES) paper: Songhurst, B. (2018). LNG Plant Cost Reduction 2014-18. OIES Paper NG 137. A cross-check against World Bank International Comparison Program (ICP) construction price levels comes in version 2.

Page numbers below are the paper's printed page numbers.

## Published group factors: checked against the paper (24 October 2026)

| Code | Location | OPCI factor | Paper value | Where in the paper | Check |
|---|---|---|---|---|---|
| US-GC | US Gulf Coast | 1.00 | USA 100% (base case) | Figure 5, p. 12; Figure 16, p. 41 | Match |
| RU-YAM | Yamal, Arctic Russia | 1.25 | 125% | Figure 5, p. 12; Figure 16, p. 41; Table 9, p. 41 | Match |
| PG | Papua New Guinea | 1.29 | 129% | Figure 5, p. 12; Figure 16, p. 41; Table 8, p. 39 | Match |
| AU-QLD | Queensland, Australia | 1.34 | 134% | Figure 5, p. 12; Figure 16, p. 41 | Match (Table 8, p. 39 shows 135%) |
| AU-NW | North West Australia | 1.72 | 172% | Figure 5, p. 12; Figure 16, p. 41 | Match (Table 8, p. 39 shows 171%; text, p. 12 rounds the group to 170%) |
| REMOTE | Remote greenfield, generic | 1.30 | "Remote Locations 130 per cent (30 per cent uplift)" | Text, p. 12 | Match |

**No mismatches with OPCI values.** The paper itself differs slightly between its tables and its figures. Table 8 gives Queensland 135% and Wheatstone (lean gas basis) 171%. Figures 5 and 16 give 134% and 172%. OPCI follows the figures, which are the paper's own summary.

**About REMOTE 1.30.** The paper sums up location factors as three groups: USA 100%, remote locations 130% and North West Australia 170%. The 130% remote group covers the band of Yamal, Papua New Guinea and Queensland (125% to 134%). The paper uses it in its own worked example: a new train in Papua New Guinea at 700 x 100% x 130% (p. 12).

The paper says the analysis is "in Appendix 4". It is in Appendix 5 (p. 39 to 41).

## Step-rule factors

These have no published factor. Each starts from an OIES group and moves in steps of 0.10. The step trails are in [METHOD_LOCATION.md](METHOD_LOCATION.md) and in the `notes` of [factors.csv](factors.csv).

| Code | Location | Factor | Range | Confidence | Start |
|---|---|---|---|---|---|
| RU-SAK | Sakhalin, Russian Far East | 1.40 | 1.26 to 1.61 | Medium | REMOTE 1.30 (confirmed by practitioner judgment) |
| ID-KAL | East Kalimantan, Indonesia | 1.20 | 1.08 to 1.38 | Medium | REMOTE 1.30 |
| MY-BIN | Bintulu, Malaysia | 1.10 | 0.99 to 1.27 | Medium | REMOTE 1.30 |
| QA-RLF | Qatar (Ras Laffan) | 1.00 | 0.90 to 1.15 | Medium | US-GC 1.00 |
| AE | UAE (Das Island, Ruwais) | 1.00 | 0.90 to 1.15 | Medium | US-GC 1.00 |
| OM | Oman (Qalhat) | 1.00 | 0.90 to 1.15 | Medium | US-GC 1.00 |
| CA-BC | British Columbia, Canada (Kitimat) | 1.40 | 1.26 to 1.61 | Medium | REMOTE 1.30 |
| NG-BON | Bonny, Nigeria | 1.20 | 1.08 to 1.38 | Medium | REMOTE 1.30 |
| MZ-AFU | Afungi, Mozambique | 1.40 | 1.26 to 1.61 | Medium | REMOTE 1.30 |
| AO-SOY | Soyo, Angola | 1.30 | 1.17 to 1.50 | Medium | REMOTE 1.30 |
| ID-SUL | Central Sulawesi, Indonesia (Donggi-Senoro) | 1.30 | 1.17 to 1.50 | Medium | REMOTE 1.30 |
| ID-PAP | Bintuni Bay, West Papua, Indonesia (Tangguh) | 1.20 | 1.08 to 1.38 | Medium | REMOTE 1.30 |

## Checks run by the tests

- Every row has a name, method, source and `as_of` year.
- Every range follows the decided range rule for its confidence level.
- The US Gulf Coast is 1.00.
- Factor A to B equals factor(B) / factor(A) for every pair.
- Ranges between two places follow the root sum of squares rule. North West Australia to East Kalimantan gives x 0.70 (0.57 to 0.83).
- Each step trail starts from its named group and adds up to the row's factor.
- The location code shares no code with the escalation module.
