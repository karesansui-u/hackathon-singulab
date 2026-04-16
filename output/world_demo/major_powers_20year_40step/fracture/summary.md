# 20-year fracture path

- Final global average `S`: `0.1997`
- Final global average horizon: `1.703` turns
- Final global average cash stability: `0.0005`
- Final global average war burden: `0.1822`
- Final global average domestic burden: `0.2106`
- Final global average protest pressure: `0.5178`
- Top resilient: `BRA, USA, EU`
- Most fragile: `JPN, IND, RUS`
- Most domestically fragile: `RUS, IND, BRA`
- Conflict mix: `gray=32, proxy=34, limited=8`
- Domestic escalation mix: `protest=15, mass=12, riot=65, insurgency=47, civil=30`

## Final Country Snapshot

| Code | S | Horizon | Support Needed | Cash | Domestic Stage | Domestic Burden | Protest | War Burden | War Pressure | Likely Mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BRA | 0.2407 | 2.22 | 0.8708 | 0.0 | civil_conflict | 0.23 | 0.5009 | 0.0486 | 0.0 | none |
| USA | 0.2326 | 2.0 | 0.9717 | 0.0026 | insurgency | 0.195 | 0.5353 | 0.1158 | 0.492 | proxy |
| EU | 0.2129 | 2.57 | 0.9755 | 0.0 | civil_conflict | 0.23 | 0.5169 | 0.3198 | 0.0 | none |
| SAU | 0.2085 | 2.35 | 0.8972 | 0.0 | civil_conflict | 0.23 | 0.4778 | 0.0711 | 0.0 | none |
| CHN | 0.198 | 1.08 | 1.0 | 0.0 | insurgency | 0.195 | 0.5156 | 0.1992 | 0.6833 | limited_war |
| JPN | 0.196 | 2.16 | 1.0 | 0.0 | riot | 0.16 | 0.4818 | 0.3175 | 0.0 | none |
| IND | 0.158 | 1.16 | 1.0 | 0.0 | civil_conflict | 0.23 | 0.5286 | 0.096 | 0.0 | none |
| RUS | 0.154 | 0.35 | 1.0 | 0.0 | civil_conflict | 0.23 | 0.5154 | 0.2762 | 0.5395 | proxy |

## Event Timeline

- Turn 1: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.1867, RUS->EU:proxy:0.2154 | domestic: none
- Turn 2: Baseline dynamics | transfers: none | conflict: USA->RUS:gray_zone:0.0457 | domestic: USA:stable->grievance, IND:stable->grievance
- Turn 3: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.1887 | domestic: USA:grievance->protest, CHN:stable->grievance, RUS:stable->grievance
- Turn 4: Frontier AI diffuses into white-collar workflows | transfers: none | conflict: CHN->JPN:gray_zone:0.1916, USA->RUS:proxy:0.0526 | domestic: CHN:grievance->protest
- Turn 5: Baseline dynamics | transfers: none | conflict: USA->CHN:gray_zone:0.0306 | domestic: none
- Turn 6: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.1986 | domestic: SAU:stable->grievance, BRA:stable->grievance
- Turn 7: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.2044, USA->CHN:gray_zone:0.0316 | domestic: IND:grievance->stable, RUS:grievance->stable, BRA:grievance->stable
- Turn 8: Compute and grid bottlenecks | transfers: none | conflict: RUS->EU:proxy:0.2704, USA->RUS:gray_zone:0.0655 | domestic: SAU:grievance->protest, BRA:stable->grievance
- Turn 9: Baseline dynamics | transfers: none | conflict: CHN->USA:proxy:0.0588 | domestic: CHN:protest->grievance, SAU:protest->mass_protest
- Turn 10: Social buffering pilots expand | transfers: none | conflict: RUS->EU:proxy:0.2943, USA->RUS:gray_zone:0.0728 | domestic: USA:protest->mass_protest, IND:stable->grievance, SAU:mass_protest->protest
- Turn 11: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.24, USA->RUS:proxy:0.091 | domestic: EU:stable->grievance, JPN:stable->grievance, RUS:stable->grievance
- Turn 12: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.2546, USA->CHN:gray_zone:0.0655 | domestic: JPN:grievance->protest
- Turn 13: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.2759, RUS->EU:gray_zone:0.3371 | domestic: CHN:grievance->protest, JPN:protest->grievance
- Turn 14: Physical AI enters logistics and warehousing | transfers: none | conflict: CHN->JPN:gray_zone:0.2971, RUS->EU:proxy:0.3539 | domestic: USA:mass_protest->riot, SAU:protest->grievance
- Turn 15: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.3231, USA->RUS:gray_zone:0.1758 | domestic: USA:riot->riot, CHN:protest->mass_protest
- Turn 16: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.351, RUS->EU:proxy:0.3897 | domestic: USA:riot->riot, JPN:grievance->protest, SAU:grievance->protest, BRA:grievance->stable
- Turn 17: Baseline dynamics | transfers: none | conflict: USA->RUS:proxy:0.2276 | domestic: USA:riot->riot, IND:grievance->protest, BRA:stable->grievance
- Turn 18: Housing and debt squeeze | transfers: none | conflict: CHN->JPN:gray_zone:0.4026, USA->RUS:proxy:0.245 | domestic: USA:riot->insurgency, CHN:mass_protest->riot, EU:grievance->protest, JPN:protest->mass_protest, BRA:grievance->protest
- Turn 19: Baseline dynamics | transfers: none | conflict: CHN->IND:gray_zone:0.3244, USA->RUS:gray_zone:0.2553 | domestic: USA:insurgency->insurgency, CHN:riot->riot, JPN:mass_protest->protest
- Turn 20: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.4292, USA->RUS:gray_zone:0.2671 | domestic: USA:insurgency->insurgency, CHN:riot->riot, EU:protest->grievance, IND:protest->mass_protest, SAU:protest->mass_protest
- Turn 21: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.4403, USA->CHN:proxy:0.2467 | domestic: USA:insurgency->insurgency, CHN:riot->riot, EU:grievance->protest, SAU:mass_protest->riot, RUS:protest->mass_protest
- Turn 22: Climate adaptation gap widens | transfers: none | conflict: CHN->JPN:limited_war:0.4537, RUS->EU:proxy:0.4487 | domestic: USA:insurgency->insurgency, CHN:riot->riot, JPN:protest->grievance, IND:mass_protest->riot, SAU:riot->riot
- Turn 23: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.4628, USA->RUS:proxy:0.304 | domestic: USA:insurgency->insurgency, CHN:riot->mass_protest, EU:protest->mass_protest, JPN:grievance->protest, IND:riot->riot
- Turn 24: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.4713, USA->RUS:gray_zone:0.3173 | domestic: USA:insurgency->insurgency, EU:mass_protest->riot, JPN:protest->mass_protest, IND:riot->riot, SAU:riot->riot
- Turn 25: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.4811, RUS->EU:limited_war:0.48 | domestic: USA:insurgency->insurgency, EU:riot->riot, IND:riot->riot, SAU:riot->riot, RUS:riot->riot
- Turn 26: Strategic blocs harden | transfers: none | conflict: CHN->JPN:limited_war:0.4937, USA->RUS:gray_zone:0.3432 | domestic: USA:insurgency->insurgency, EU:riot->riot, JPN:mass_protest->riot, IND:riot->riot, SAU:riot->riot
- Turn 27: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.5005, RUS->EU:proxy:0.5042 | domestic: USA:insurgency->insurgency, EU:riot->riot, JPN:riot->riot, IND:riot->insurgency, SAU:riot->riot
- Turn 28: Baseline dynamics | transfers: none | conflict: CHN->USA:proxy:0.3774, USA->CHN:gray_zone:0.3256 | domestic: USA:insurgency->insurgency, CHN:mass_protest->riot, EU:riot->riot, JPN:riot->riot, IND:insurgency->insurgency
- Turn 29: Baseline dynamics | transfers: none | conflict: RUS->EU:proxy:0.5206, USA->RUS:gray_zone:0.3722 | domestic: USA:insurgency->insurgency, CHN:riot->riot, EU:riot->riot, JPN:riot->riot, IND:insurgency->insurgency
- Turn 30: Resilience capital rotation | transfers: none | conflict: CHN->JPN:gray_zone:0.5258, RUS->EU:proxy:0.5285 | domestic: USA:insurgency->insurgency, CHN:riot->riot, EU:riot->insurgency, JPN:riot->mass_protest, IND:insurgency->insurgency
- Turn 31: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.5343, USA->CHN:gray_zone:0.3527 | domestic: USA:insurgency->insurgency, CHN:riot->riot, EU:insurgency->insurgency, JPN:mass_protest->riot, IND:insurgency->insurgency
- Turn 32: Baseline dynamics | transfers: none | conflict: RUS->EU:proxy:0.5409, CHN->IND:proxy:0.4741 | domestic: USA:insurgency->insurgency, CHN:riot->riot, EU:insurgency->insurgency, JPN:riot->riot, IND:insurgency->civil_conflict
- Turn 33: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.552, RUS->EU:limited_war:0.5449 | domestic: USA:insurgency->insurgency, CHN:riot->riot, EU:insurgency->insurgency, JPN:riot->riot, IND:civil_conflict->civil_conflict
- Turn 34: Food-water shocks and migration pressure | transfers: none | conflict: CHN->JPN:proxy:0.5591, RUS->EU:proxy:0.5511 | domestic: USA:insurgency->insurgency, CHN:riot->riot, EU:insurgency->insurgency, JPN:riot->riot, IND:civil_conflict->civil_conflict
- Turn 35: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.5657, RUS->EU:proxy:0.5552 | domestic: USA:insurgency->insurgency, CHN:riot->riot, EU:insurgency->insurgency, JPN:riot->riot, IND:civil_conflict->civil_conflict
- Turn 36: Baseline dynamics | transfers: none | conflict: RUS->EU:proxy:0.5599, USA->RUS:gray_zone:0.4137 | domestic: USA:insurgency->insurgency, CHN:riot->riot, EU:insurgency->civil_conflict, JPN:riot->riot, IND:civil_conflict->civil_conflict
- Turn 37: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.5775, USA->RUS:gray_zone:0.4196 | domestic: USA:insurgency->insurgency, CHN:riot->riot, EU:civil_conflict->civil_conflict, JPN:riot->riot, IND:civil_conflict->civil_conflict
- Turn 38: Institutional settlement attempt | transfers: none | conflict: CHN->JPN:gray_zone:0.5823, RUS->EU:proxy:0.5696 | domestic: USA:insurgency->insurgency, CHN:riot->insurgency, EU:civil_conflict->civil_conflict, JPN:riot->riot, IND:civil_conflict->civil_conflict
- Turn 39: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.5905, RUS->EU:proxy:0.573 | domestic: USA:insurgency->insurgency, CHN:insurgency->insurgency, EU:civil_conflict->civil_conflict, JPN:riot->riot, IND:civil_conflict->civil_conflict
- Turn 40: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.5954, USA->RUS:proxy:0.4323 | domestic: USA:insurgency->insurgency, CHN:insurgency->insurgency, EU:civil_conflict->civil_conflict, JPN:riot->riot, IND:civil_conflict->civil_conflict
