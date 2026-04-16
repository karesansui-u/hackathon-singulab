# 20-year fracture path

- Final global average `S`: `0.3706`
- Final global average horizon: `5.2541` turns
- Final global average cash stability: `0.0258`
- Final global average war burden: `0.0633`
- Final global average domestic burden: `0.1214`
- Final global average protest pressure: `0.3506`
- Top resilient: `USA, SAU, EU`
- Most fragile: `JPN, CHN, RUS`
- Most domestically fragile: `CHN, RUS, USA`
- Conflict mix: `gray=18, proxy=19, limited=0`
- Domestic escalation mix: `protest=11, mass=3, riot=5, insurgency=5, civil=0`

## Final Country Snapshot

| Code | S | Horizon | Support Needed | Cash | Domestic Stage | Domestic Burden | Protest | War Burden | War Pressure | Likely Mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USA | 0.4484 | 6.7 | 0.4478 | 0.0241 | riot | 0.16 | 0.3632 | 0.0388 | 0.3309 | proxy |
| SAU | 0.4086 | 6.02 | 0.4789 | 0.2422 | protest | 0.09 | 0.2675 | 0.0 | 0.0 | none |
| EU | 0.403 | 6.08 | 0.5332 | 0.0 | protest | 0.09 | 0.3272 | 0.1012 | 0.0 | none |
| BRA | 0.3922 | 5.62 | 0.4641 | 0.1302 | protest | 0.12 | 0.3235 | 0.0 | 0.0 | none |
| IND | 0.3493 | 5.21 | 0.527 | 0.0268 | grievance | 0.055 | 0.3347 | 0.0008 | 0.0 | none |
| JPN | 0.3373 | 5.02 | 0.6499 | 0.0 | grievance | 0.0606 | 0.3315 | 0.1449 | 0.0 | none |
| CHN | 0.3094 | 3.55 | 0.7143 | 0.0 | insurgency | 0.195 | 0.401 | 0.111 | 0.5907 | limited_war |
| RUS | 0.2708 | 2.7 | 0.7726 | 0.0 | riot | 0.19 | 0.3668 | 0.0879 | 0.4368 | proxy |

## Event Timeline

- Turn 1: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.1867, RUS->EU:proxy:0.2154 | domestic: EU:stable->grievance, BRA:stable->grievance
- Turn 2: Frontier AI diffuses into white-collar workflows | transfers: none | conflict: CHN->JPN:gray_zone:0.1873 | domestic: CHN:stable->grievance, JPN:stable->grievance, RUS:stable->grievance
- Turn 3: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.1911, RUS->EU:proxy:0.2255 | domestic: EU:grievance->protest
- Turn 4: Compute and grid bottlenecks | transfers: none | conflict: CHN->JPN:gray_zone:0.1955, USA->RUS:gray_zone:0.052 | domestic: JPN:grievance->stable
- Turn 5: Social buffering pilots expand | transfers: none | conflict: RUS->EU:gray_zone:0.2404, CHN->IND:gray_zone:0.1013 | domestic: JPN:stable->grievance
- Turn 6: Baseline dynamics | transfers: none | conflict: RUS->EU:proxy:0.2517, CHN->IND:gray_zone:0.1038 | domestic: JPN:grievance->protest, BRA:grievance->protest
- Turn 7: Physical AI enters logistics and warehousing | transfers: none | conflict: CHN->JPN:proxy:0.2021, RUS->EU:proxy:0.2638 | domestic: USA:stable->grievance, EU:protest->grievance, BRA:protest->grievance
- Turn 8: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.2065, RUS->EU:proxy:0.2753 | domestic: JPN:protest->grievance
- Turn 9: Housing and debt squeeze | transfers: none | conflict: CHN->JPN:gray_zone:0.2128, USA->CHN:proxy:0.0335 | domestic: CHN:grievance->protest, JPN:grievance->stable
- Turn 10: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.221 | domestic: USA:grievance->stable, IND:stable->grievance
- Turn 11: Climate adaptation gap widens | transfers: none | conflict: CHN->JPN:proxy:0.2386, USA->RUS:gray_zone:0.076 | domestic: JPN:stable->grievance
- Turn 12: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.2585, RUS->EU:proxy:0.3347 | domestic: USA:stable->grievance, JPN:grievance->protest, RUS:grievance->protest, BRA:grievance->stable
- Turn 13: Strategic blocs harden | transfers: none | conflict: CHN->JPN:gray_zone:0.2881 | domestic: USA:grievance->protest, CHN:protest->mass_protest, BRA:stable->grievance
- Turn 14: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.3156, USA->RUS:gray_zone:0.0994 | domestic: SAU:stable->grievance
- Turn 15: Resilience capital rotation | transfers: none | conflict: CHN->JPN:proxy:0.3453, RUS->EU:proxy:0.4053 | domestic: CHN:mass_protest->riot, EU:grievance->stable
- Turn 16: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.3794, RUS->EU:proxy:0.4126 | domestic: USA:protest->mass_protest, CHN:riot->insurgency, IND:grievance->protest, SAU:grievance->protest
- Turn 17: Food-water shocks and migration pressure | transfers: none | conflict: CHN->JPN:proxy:0.4148, USA->RUS:gray_zone:0.1542 | domestic: CHN:insurgency->insurgency, EU:stable->grievance
- Turn 18: Baseline dynamics | transfers: none | conflict: USA->RUS:gray_zone:0.1808, CHN->USA:proxy:0.2644 | domestic: USA:mass_protest->riot, CHN:insurgency->insurgency, EU:grievance->protest, IND:protest->grievance
- Turn 19: Institutional settlement attempt | transfers: USA->JPN:0.0053, USA->IND:0.0049, SAU->JPN:0.0046 | conflict: CHN->JPN:gray_zone:0.4408, RUS->EU:proxy:0.4358 | domestic: USA:riot->riot, CHN:insurgency->insurgency, RUS:protest->mass_protest
- Turn 20: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.452, USA->RUS:proxy:0.2454 | domestic: USA:riot->riot, CHN:insurgency->insurgency, JPN:protest->grievance, RUS:mass_protest->riot, BRA:grievance->protest
