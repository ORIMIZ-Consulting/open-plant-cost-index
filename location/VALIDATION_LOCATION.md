# Location validation

Open Plant Cost Index (OPCI) location module, version 0.1.0. Maintained by ORIMIZ Consulting.

This page compares OPCI location factors with published factors. In version 1 the only published source is the Oxford Institute for Energy Studies (OIES) group factors. A cross-check against World Bank International Comparison Program (ICP) construction price levels comes in version 2.

## Factors by method

| Code | Location | Factor | Range | Confidence | Method | Published value | Check |
|---|---|---|---|---|---|---|---|
| US-GC | US Gulf Coast | 1.00 | 0.90 to 1.10 | High | Reference | 1.00 (reference) | Matches by definition |
| RU-YAM | Yamal, Arctic Russia | 1.25 | 1.13 to 1.44 | Medium | Published group | OIES | Figure and page to be checked |
| PG | Papua New Guinea | 1.29 | 1.16 to 1.48 | Medium | Published group | OIES | Figure and page to be checked |
| AU-QLD | Queensland, Australia | 1.34 | 1.21 to 1.54 | Medium | Published group | OIES | Figure and page to be checked |
| AU-NW | North West Australia | 1.72 | 1.55 to 1.98 | Medium | Published group | OIES | Figure and page to be checked |
| REMOTE | Remote greenfield, generic | 1.30 | 1.11 to 1.63 | Low | Published group | OIES | Figure and page to be checked |
| RU-SAK | Sakhalin, Russian Far East | 1.40 | 1.26 to 1.61 | Medium | Step rule, practitioner judgment | None | No published factor |
| ID-KAL | East Kalimantan, Indonesia | 1.20 | 1.08 to 1.38 | Medium | Step rule | None | No published factor |
| MY-BIN | Bintulu, Malaysia | 1.10 | 0.99 to 1.27 | Medium | Step rule | None | No published factor |
| QA-RLF | Qatar (Ras Laffan) | 1.00 | 0.90 to 1.15 | Medium | Step rule | None | No published factor |
| AE | UAE (Das Island, Ruwais) | 1.00 | 0.90 to 1.15 | Medium | Step rule | None | No published factor |
| OM | Oman (Qalhat) | 1.00 | 0.90 to 1.15 | Medium | Step rule | None | No published factor |
| CA-BC | British Columbia, Canada (Kitimat) | 1.40 | 1.26 to 1.61 | Medium | Step rule | None | No published factor |

Source for the OIES rows: Songhurst, B. (2018). LNG Plant Cost Reduction 2014-18. Oxford Institute for Energy Studies, OIES Paper NG 137.

## Checks run by the tests

- Every row has a name, method, source and `as_of` year.
- Every range follows the decided range rule for its confidence level.
- The US Gulf Coast is 1.00.
- Factor A to B equals factor(B) / factor(A) for every pair.
- The location code shares no code with the escalation module.

## Context from the OIES paper

The paper places the Queensland, Papua New Guinea and Yamal plants in a cost band well above the US Gulf plants. It finds Queensland plants cost much less than the North West Australia plants, in part because Queensland is less remote. The OPCI factors agree in direction: US-GC 1.00, Yamal 1.25, Papua New Guinea 1.29, Queensland 1.34 and North West Australia 1.72.
