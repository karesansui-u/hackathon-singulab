# 20-year complement path

- Final global average `S`: `0.3767`
- Final global average horizon: `5.4691` turns
- Final global average cash stability: `0.0756`
- Final global average war burden: `0.0618`
- Final global average domestic burden: `0.1361`
- Final global average protest pressure: `0.34`
- Top resilient: `USA, SAU, JPN`
- Most fragile: `BRA, IND, RUS`
- Most domestically fragile: `IND, RUS, BRA`
- Conflict mix: `gray=18, proxy=14, limited=2`
- Domestic escalation mix: `protest=9, mass=5, riot=16, insurgency=7, civil=3`

## Final Country Snapshot

| Code | S | Horizon | Support Needed | Cash | Domestic Stage | Domestic Burden | Protest | War Burden | War Pressure | Likely Mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USA | 0.5267 | 8.06 | 0.2996 | 0.2656 | protest | 0.1008 | 0.2824 | 0.0053 | 0.2319 | gray_zone |
| SAU | 0.4414 | 6.62 | 0.4186 | 0.3903 | grievance | 0.055 | 0.2239 | 0.0 | 0.0 | none |
| JPN | 0.4285 | 7.03 | 0.4421 | 0.1217 | stable | 0.02 | 0.2591 | 0.0679 | 0.0 | none |
| CHN | 0.3918 | 4.95 | 0.536 | 0.0 | protest | 0.09 | 0.3128 | 0.0316 | 0.4923 | proxy |
| EU | 0.356 | 5.29 | 0.648 | 0.0 | riot | 0.16 | 0.3527 | 0.1737 | 0.0 | none |
| BRA | 0.3391 | 4.88 | 0.551 | 0.0 | riot | 0.16 | 0.3845 | 0.0 | 0.0 | none |
| IND | 0.2473 | 3.71 | 0.7278 | 0.0 | civil_conflict | 0.23 | 0.4328 | 0.0617 | 0.0 | none |
| RUS | 0.2381 | 2.36 | 0.8137 | 0.0 | insurgency | 0.195 | 0.4035 | 0.1167 | 0.403 | proxy |

## Event Timeline

- Turn 1: Baseline dynamics | transfers: USA->JPN:0.0047, USA->IND:0.0043 | conflict: RUS->EU:proxy:0.1871, USA->CHN:gray_zone:0.0289 | domestic: JPN:stable->grievance
- Turn 2: Frontier AI diffuses into white-collar workflows | transfers: USA->JPN:0.0049, USA->IND:0.0045 | conflict: CHN->JPN:limited_war:0.1602, RUS->EU:gray_zone:0.1918 | domestic: RUS:stable->grievance
- Turn 3: Baseline dynamics | transfers: USA->JPN:0.005, USA->IND:0.0046 | conflict: CHN->IND:gray_zone:0.0644 | domestic: JPN:grievance->stable, IND:stable->grievance
- Turn 4: Compute and grid bottlenecks | transfers: USA->JPN:0.0052, USA->IND:0.0048 | conflict: CHN->JPN:proxy:0.1644, RUS->EU:proxy:0.2 | domestic: IND:grievance->stable, BRA:stable->grievance
- Turn 5: Social buffering pilots expand | transfers: USA->JPN:0.0066, USA->IND:0.006, USA->EU:0.0042, CHN->BRA:0.0045 | conflict: CHN->JPN:gray_zone:0.1655, RUS->EU:proxy:0.2076 | domestic: EU:stable->grievance, IND:stable->grievance
- Turn 6: Baseline dynamics | transfers: USA->JPN:0.0054, USA->IND:0.005 | conflict: CHN->JPN:gray_zone:0.1674, RUS->EU:gray_zone:0.2175 | domestic: EU:grievance->protest, JPN:stable->grievance, IND:grievance->protest
- Turn 7: Physical AI enters logistics and warehousing | transfers: USA->JPN:0.0055, USA->IND:0.0051 | conflict: CHN->JPN:gray_zone:0.1679, USA->CHN:gray_zone:0.0306 | domestic: CHN:stable->grievance, EU:protest->mass_protest, IND:protest->grievance, SAU:stable->grievance
- Turn 8: Baseline dynamics | transfers: USA->JPN:0.0056, USA->IND:0.0051 | conflict: CHN->USA:proxy:0.0508 | domestic: JPN:grievance->stable
- Turn 9: Housing and debt squeeze | transfers: USA->JPN:0.0056, USA->IND:0.0051 | conflict: CHN->JPN:proxy:0.1762, USA->RUS:gray_zone:0.0374 | domestic: EU:mass_protest->protest, IND:grievance->protest
- Turn 10: Baseline dynamics | transfers: USA->JPN:0.0056, USA->IND:0.0051 | conflict: CHN->JPN:gray_zone:0.1797, USA->RUS:gray_zone:0.041 | domestic: IND:protest->mass_protest, RUS:grievance->protest
- Turn 11: Climate adaptation gap widens | transfers: USA->JPN:0.0056, USA->IND:0.0051 | conflict: CHN->USA:proxy:0.0592, USA->CHN:gray_zone:0.0338 | domestic: EU:protest->grievance, IND:mass_protest->riot, BRA:grievance->protest
- Turn 12: Baseline dynamics | transfers: USA->JPN:0.0056, USA->IND:0.0051, CHN->BRA:0.004 | conflict: none | domestic: IND:riot->riot, SAU:grievance->stable, RUS:protest->mass_protest
- Turn 13: Strategic blocs harden | transfers: USA->JPN:0.0056, USA->IND:0.0051, SAU->JPN:0.004, CHN->BRA:0.004 | conflict: RUS->EU:proxy:0.3405, USA->CHN:gray_zone:0.0351 | domestic: EU:grievance->protest, IND:riot->insurgency, RUS:mass_protest->riot, BRA:protest->mass_protest
- Turn 14: Baseline dynamics | transfers: USA->JPN:0.0056, USA->IND:0.0051, SAU->JPN:0.0041, CHN->BRA:0.004 | conflict: CHN->JPN:proxy:0.2254, USA->CHN:gray_zone:0.0358 | domestic: CHN:grievance->protest, IND:insurgency->insurgency, RUS:riot->riot
- Turn 15: Resilience capital rotation | transfers: USA->JPN:0.0055, USA->IND:0.0051, SAU->JPN:0.0042 | conflict: CHN->JPN:gray_zone:0.2464, RUS->EU:proxy:0.383 | domestic: EU:protest->mass_protest, IND:insurgency->insurgency, SAU:stable->grievance, RUS:riot->riot
- Turn 16: Baseline dynamics | transfers: USA->JPN:0.0055, USA->IND:0.0051, SAU->JPN:0.0043 | conflict: CHN->JPN:limited_war:0.2674, RUS->EU:proxy:0.3934 | domestic: IND:insurgency->riot, RUS:riot->riot
- Turn 17: Food-water shocks and migration pressure | transfers: USA->JPN:0.0055, USA->IND:0.0051, SAU->JPN:0.0043 | conflict: CHN->JPN:gray_zone:0.2924, RUS->EU:proxy:0.4051 | domestic: USA:stable->grievance, EU:mass_protest->riot, IND:riot->insurgency, RUS:riot->riot, BRA:mass_protest->riot
- Turn 18: Baseline dynamics | transfers: USA->JPN:0.0054, USA->IND:0.005, SAU->JPN:0.0044 | conflict: CHN->JPN:gray_zone:0.316 | domestic: EU:riot->riot, IND:insurgency->civil_conflict, RUS:riot->insurgency, BRA:riot->riot
- Turn 19: Institutional settlement attempt | transfers: USA->JPN:0.0092, USA->IND:0.0085, USA->EU:0.0058, EU->IND:0.0044, JPN->IND:0.0051 | conflict: RUS->EU:proxy:0.4266 | domestic: USA:grievance->protest, EU:riot->riot, IND:civil_conflict->civil_conflict, RUS:insurgency->insurgency, BRA:riot->riot
- Turn 20: Baseline dynamics | transfers: USA->JPN:0.0052, USA->IND:0.0048, SAU->JPN:0.0044 | conflict: RUS->EU:proxy:0.4364, USA->RUS:gray_zone:0.1375 | domestic: EU:riot->riot, IND:civil_conflict->civil_conflict, RUS:insurgency->insurgency, BRA:riot->riot
