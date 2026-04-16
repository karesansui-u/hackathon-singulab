# 20-year complement path

- Final global average `S`: `0.2082`
- Final global average horizon: `2.0529` turns
- Final global average cash stability: `0.0`
- Final global average war burden: `0.1773`
- Final global average domestic burden: `0.2072`
- Final global average protest pressure: `0.497`
- Top resilient: `EU, USA, SAU`
- Most fragile: `IND, RUS, CHN`
- Most domestically fragile: `CHN, RUS, IND`
- Conflict mix: `gray=25, proxy=31, limited=9`
- Domestic escalation mix: `protest=14, mass=13, riot=67, insurgency=34, civil=43`

## Final Country Snapshot

| Code | S | Horizon | Support Needed | Cash | Domestic Stage | Domestic Burden | Protest | War Burden | War Pressure | Likely Mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EU | 0.2799 | 3.86 | 0.8084 | 0.0 | mass_protest | 0.1302 | 0.4124 | 0.1526 | 0.0 | none |
| USA | 0.2643 | 2.69 | 0.9164 | 0.0 | civil_conflict | 0.23 | 0.518 | 0.0978 | 0.4286 | proxy |
| SAU | 0.2514 | 3.22 | 0.7933 | 0.0 | riot | 0.16 | 0.408 | 0.0029 | 0.0 | none |
| JPN | 0.2133 | 2.83 | 0.9895 | 0.0 | insurgency | 0.195 | 0.4571 | 0.3393 | 0.0 | none |
| BRA | 0.2077 | 1.95 | 0.8906 | 0.0 | civil_conflict | 0.23 | 0.5115 | 0.0707 | 0.0 | none |
| IND | 0.1589 | 1.4 | 1.0 | 0.0 | civil_conflict | 0.23 | 0.5232 | 0.1292 | 0.0 | none |
| RUS | 0.1542 | 0.66 | 1.0 | 0.0 | civil_conflict | 0.23 | 0.5119 | 0.1967 | 0.4797 | proxy |
| CHN | 0.1434 | 0.34 | 1.0 | 0.0 | civil_conflict | 0.23 | 0.5466 | 0.3209 | 0.6364 | limited_war |

## Event Timeline

- Turn 1: Baseline dynamics | transfers: USA->JPN:0.0047, USA->IND:0.0043 | conflict: RUS->EU:proxy:0.1875, USA->CHN:proxy:0.0289 | domestic: CHN:stable->grievance, SAU:stable->grievance, RUS:stable->grievance
- Turn 2: Baseline dynamics | transfers: USA->JPN:0.0049, USA->IND:0.0045 | conflict: CHN->JPN:proxy:0.1597, RUS->EU:gray_zone:0.1923 | domestic: EU:stable->grievance
- Turn 3: Baseline dynamics | transfers: USA->JPN:0.005, USA->IND:0.0046 | conflict: CHN->JPN:gray_zone:0.1611 | domestic: USA:stable->grievance, EU:grievance->protest, RUS:grievance->protest
- Turn 4: Frontier AI diffuses into white-collar workflows | transfers: USA->JPN:0.0052, USA->IND:0.0048 | conflict: CHN->JPN:proxy:0.1632, RUS->EU:proxy:0.2102 | domestic: none
- Turn 5: Baseline dynamics | transfers: USA->JPN:0.0053, USA->IND:0.0049 | conflict: none | domestic: USA:grievance->protest, BRA:stable->grievance
- Turn 6: Baseline dynamics | transfers: USA->JPN:0.0054, USA->IND:0.005 | conflict: CHN->JPN:proxy:0.1641, USA->RUS:gray_zone:0.0304 | domestic: USA:protest->grievance, CHN:grievance->protest
- Turn 7: Baseline dynamics | transfers: USA->JPN:0.0055, USA->IND:0.0051 | conflict: CHN->JPN:proxy:0.1677, USA->RUS:gray_zone:0.0317 | domestic: USA:grievance->protest, SAU:grievance->stable, BRA:grievance->protest
- Turn 8: Compute and grid bottlenecks | transfers: USA->JPN:0.0056, USA->IND:0.0051 | conflict: CHN->IND:gray_zone:0.0821 | domestic: BRA:protest->grievance
- Turn 9: Baseline dynamics | transfers: USA->JPN:0.0056, USA->IND:0.0051 | conflict: CHN->JPN:proxy:0.1802, USA->RUS:gray_zone:0.0396 | domestic: USA:protest->mass_protest, IND:stable->grievance, RUS:protest->mass_protest
- Turn 10: Social buffering pilots expand | transfers: USA->JPN:0.0069, USA->IND:0.0063, USA->EU:0.0044, EU->IND:0.0042, SAU->JPN:0.0045 | conflict: RUS->EU:gray_zone:0.3131 | domestic: CHN:protest->mass_protest
- Turn 11: Baseline dynamics | transfers: USA->JPN:0.0056, USA->IND:0.0051, CHN->BRA:0.004 | conflict: CHN->JPN:limited_war:0.2088 | domestic: SAU:stable->grievance, RUS:mass_protest->riot
- Turn 12: Baseline dynamics | transfers: USA->JPN:0.0056, USA->IND:0.0051 | conflict: CHN->JPN:gray_zone:0.231, RUS->EU:proxy:0.3632 | domestic: RUS:riot->riot
- Turn 13: Baseline dynamics | transfers: USA->JPN:0.0056, USA->IND:0.0051, SAU->JPN:0.004 | conflict: CHN->JPN:gray_zone:0.2532 | domestic: IND:grievance->protest, RUS:riot->riot
- Turn 14: Physical AI enters logistics and warehousing | transfers: USA->JPN:0.0055, USA->IND:0.0051, SAU->JPN:0.0041 | conflict: CHN->JPN:limited_war:0.2801 | domestic: USA:mass_protest->riot, CHN:mass_protest->riot, SAU:grievance->protest, RUS:riot->riot, BRA:grievance->protest
- Turn 15: Baseline dynamics | transfers: USA->JPN:0.0052, USA->IND:0.0048, SAU->JPN:0.0042 | conflict: none | domestic: USA:riot->riot, CHN:riot->riot, IND:protest->mass_protest, SAU:protest->mass_protest, RUS:riot->riot
- Turn 16: Baseline dynamics | transfers: USA->JPN:0.0048, USA->IND:0.0044, SAU->JPN:0.0043 | conflict: CHN->JPN:gray_zone:0.3377, USA->RUS:proxy:0.1478 | domestic: USA:riot->riot, CHN:riot->riot, SAU:mass_protest->protest, RUS:riot->riot
- Turn 17: Baseline dynamics | transfers: USA->JPN:0.0043, USA->IND:0.004, SAU->JPN:0.0043 | conflict: CHN->JPN:limited_war:0.3622, USA->CHN:gray_zone:0.1292 | domestic: USA:riot->riot, CHN:riot->insurgency, SAU:protest->grievance, RUS:riot->riot
- Turn 18: Housing and debt squeeze | transfers: SAU->JPN:0.0044 | conflict: RUS->EU:proxy:0.4155 | domestic: USA:riot->riot, CHN:insurgency->insurgency, EU:protest->mass_protest, JPN:stable->grievance, RUS:riot->riot
- Turn 19: Baseline dynamics | transfers: SAU->JPN:0.0044 | conflict: CHN->JPN:limited_war:0.3898, RUS->EU:proxy:0.4242 | domestic: USA:riot->riot, CHN:insurgency->insurgency, EU:mass_protest->riot, RUS:riot->riot
- Turn 20: Baseline dynamics | transfers: SAU->JPN:0.0044 | conflict: CHN->JPN:limited_war:0.4009 | domestic: USA:riot->riot, CHN:insurgency->insurgency, EU:riot->riot, RUS:riot->riot, BRA:protest->mass_protest
- Turn 21: Baseline dynamics | transfers: SAU->JPN:0.0044 | conflict: CHN->IND:proxy:0.3321 | domestic: USA:riot->mass_protest, CHN:insurgency->insurgency, EU:riot->riot, JPN:grievance->protest, IND:mass_protest->riot
- Turn 22: Climate adaptation gap widens | transfers: SAU->JPN:0.0044 | conflict: CHN->JPN:limited_war:0.4237, RUS->EU:proxy:0.4471 | domestic: CHN:insurgency->insurgency, EU:riot->mass_protest, IND:riot->riot, RUS:riot->riot
- Turn 23: Baseline dynamics | transfers: SAU->JPN:0.0044 | conflict: CHN->JPN:gray_zone:0.435, USA->RUS:gray_zone:0.2611 | domestic: CHN:insurgency->civil_conflict, EU:mass_protest->protest, IND:riot->riot, RUS:riot->riot, BRA:mass_protest->riot
- Turn 24: Baseline dynamics | transfers: SAU->JPN:0.0044 | conflict: CHN->JPN:proxy:0.4483 | domestic: CHN:civil_conflict->civil_conflict, IND:riot->insurgency, SAU:protest->mass_protest, RUS:riot->riot, BRA:riot->riot
- Turn 25: Baseline dynamics | transfers: SAU->JPN:0.0043 | conflict: CHN->JPN:proxy:0.4592, USA->CHN:gray_zone:0.2425 | domestic: CHN:civil_conflict->civil_conflict, IND:insurgency->insurgency, RUS:riot->insurgency, BRA:riot->riot
- Turn 26: Strategic blocs harden | transfers: SAU->JPN:0.0042 | conflict: RUS->EU:gray_zone:0.4756, CHN->IND:proxy:0.4077 | domestic: USA:mass_protest->riot, CHN:civil_conflict->civil_conflict, IND:insurgency->insurgency, SAU:mass_protest->riot, RUS:insurgency->insurgency
- Turn 27: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.4866, RUS->EU:proxy:0.4841 | domestic: USA:riot->riot, CHN:civil_conflict->civil_conflict, IND:insurgency->insurgency, SAU:riot->riot, RUS:insurgency->civil_conflict
- Turn 28: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.496, USA->RUS:proxy:0.3106 | domestic: USA:riot->riot, CHN:civil_conflict->civil_conflict, IND:insurgency->insurgency, SAU:riot->riot, RUS:civil_conflict->civil_conflict
- Turn 29: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.5051, USA->CHN:proxy:0.2906 | domestic: USA:riot->riot, CHN:civil_conflict->civil_conflict, JPN:protest->mass_protest, IND:insurgency->insurgency, SAU:riot->riot
- Turn 30: Resilience capital rotation | transfers: none | conflict: CHN->JPN:gray_zone:0.5122, USA->RUS:gray_zone:0.3262 | domestic: USA:riot->riot, CHN:civil_conflict->civil_conflict, IND:insurgency->insurgency, SAU:riot->riot, RUS:civil_conflict->civil_conflict
- Turn 31: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.5203, RUS->EU:proxy:0.51 | domestic: USA:riot->riot, CHN:civil_conflict->civil_conflict, JPN:mass_protest->riot, IND:insurgency->insurgency, SAU:riot->riot
- Turn 32: Baseline dynamics | transfers: none | conflict: RUS->EU:proxy:0.514, CHN->IND:gray_zone:0.4667 | domestic: USA:riot->riot, CHN:civil_conflict->civil_conflict, JPN:riot->riot, IND:insurgency->insurgency, SAU:riot->insurgency
- Turn 33: Baseline dynamics | transfers: none | conflict: RUS->EU:proxy:0.5175, CHN->IND:gray_zone:0.4746 | domestic: USA:riot->riot, CHN:civil_conflict->civil_conflict, JPN:riot->riot, IND:insurgency->insurgency, SAU:insurgency->riot
- Turn 34: Food-water shocks and migration pressure | transfers: none | conflict: RUS->EU:proxy:0.5211, USA->RUS:gray_zone:0.3467 | domestic: USA:riot->riot, CHN:civil_conflict->civil_conflict, EU:protest->grievance, JPN:riot->riot, IND:insurgency->insurgency
- Turn 35: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.5465 | domestic: USA:riot->insurgency, CHN:civil_conflict->civil_conflict, EU:grievance->stable, JPN:riot->mass_protest, IND:insurgency->civil_conflict
- Turn 36: Baseline dynamics | transfers: none | conflict: CHN->IND:proxy:0.4965, RUS->EU:limited_war:0.5267 | domestic: USA:insurgency->insurgency, CHN:civil_conflict->civil_conflict, EU:stable->grievance, JPN:mass_protest->riot, IND:civil_conflict->civil_conflict
- Turn 37: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.5593, USA->RUS:proxy:0.3632 | domestic: USA:insurgency->insurgency, CHN:civil_conflict->civil_conflict, JPN:riot->insurgency, IND:civil_conflict->civil_conflict, SAU:riot->riot
- Turn 38: Institutional settlement attempt | transfers: none | conflict: CHN->JPN:proxy:0.5661, RUS->EU:proxy:0.5317 | domestic: USA:insurgency->insurgency, CHN:civil_conflict->civil_conflict, EU:grievance->protest, JPN:insurgency->insurgency, IND:civil_conflict->civil_conflict
- Turn 39: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.5707, USA->CHN:proxy:0.3693 | domestic: USA:insurgency->civil_conflict, CHN:civil_conflict->civil_conflict, EU:protest->mass_protest, JPN:insurgency->insurgency, IND:civil_conflict->civil_conflict
- Turn 40: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.5761, USA->CHN:gray_zone:0.3787 | domestic: USA:civil_conflict->civil_conflict, CHN:civil_conflict->civil_conflict, JPN:insurgency->insurgency, IND:civil_conflict->civil_conflict, SAU:riot->riot
