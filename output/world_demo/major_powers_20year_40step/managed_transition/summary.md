# 20-year managed transition

- Final global average `S`: `0.2106`
- Final global average horizon: `1.9453` turns
- Final global average cash stability: `0.0006`
- Final global average war burden: `0.1873`
- Final global average domestic burden: `0.207`
- Final global average protest pressure: `0.4943`
- Top resilient: `SAU, JPN, USA`
- Most fragile: `BRA, CHN, IND`
- Most domestically fragile: `CHN, IND, BRA`
- Conflict mix: `gray=25, proxy=38, limited=8`
- Domestic escalation mix: `protest=14, mass=7, riot=24, insurgency=28, civil=40`

## Final Country Snapshot

| Code | S | Horizon | Support Needed | Cash | Domestic Stage | Domestic Burden | Protest | War Burden | War Pressure | Likely Mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SAU | 0.3223 | 3.95 | 0.6875 | 0.0 | protest | 0.12 | 0.3317 | 0.0 | 0.0 | none |
| JPN | 0.2473 | 3.17 | 0.93 | 0.0 | protest | 0.1008 | 0.3994 | 0.1533 | 0.0 | none |
| USA | 0.2465 | 2.36 | 0.9501 | 0.0 | civil_conflict | 0.23 | 0.5207 | 0.1082 | 0.4494 | proxy |
| EU | 0.239 | 3.08 | 0.9205 | 0.0 | insurgency | 0.195 | 0.4748 | 0.2734 | 0.0 | none |
| RUS | 0.2094 | 1.27 | 0.9763 | 0.0 | riot | 0.16 | 0.4399 | 0.1422 | 0.4768 | proxy |
| BRA | 0.1865 | 1.51 | 0.9297 | 0.0 | civil_conflict | 0.23 | 0.527 | 0.086 | 0.0 | none |
| CHN | 0.1838 | 0.97 | 1.0 | 0.0031 | civil_conflict | 0.23 | 0.5176 | 0.2248 | 0.6425 | limited_war |
| IND | 0.1536 | 1.01 | 1.0 | 0.0 | civil_conflict | 0.23 | 0.5272 | 0.2323 | 0.0 | none |

## Event Timeline

- Turn 1: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.1708, RUS->EU:proxy:0.1994 | domestic: IND:stable->grievance, BRA:stable->grievance
- Turn 2: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.173, USA->CHN:proxy:0.0293 | domestic: USA:stable->grievance
- Turn 3: Baseline dynamics | transfers: none | conflict: CHN->USA:proxy:0.0458 | domestic: RUS:stable->grievance
- Turn 4: Frontier AI diffuses into white-collar workflows | transfers: none | conflict: CHN->JPN:gray_zone:0.1771, RUS->EU:proxy:0.2122 | domestic: none
- Turn 5: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.1792, RUS->EU:gray_zone:0.2208 | domestic: none
- Turn 6: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.1791, USA->RUS:proxy:0.041 | domestic: CHN:stable->grievance, JPN:stable->grievance
- Turn 7: Baseline dynamics | transfers: none | conflict: CHN->IND:gray_zone:0.0876 | domestic: EU:stable->grievance, JPN:grievance->stable, IND:grievance->protest
- Turn 8: Compute and grid bottlenecks | transfers: none | conflict: CHN->JPN:gray_zone:0.19, USA->CHN:gray_zone:0.0318 | domestic: CHN:grievance->protest, EU:grievance->stable
- Turn 9: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.1972, USA->RUS:proxy:0.0504 | domestic: USA:grievance->stable
- Turn 10: Social buffering pilots expand | transfers: USA->JPN:0.0048, USA->IND:0.0044 | conflict: none | domestic: BRA:grievance->protest
- Turn 11: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.2166 | domestic: USA:stable->grievance
- Turn 12: Baseline dynamics | transfers: none | conflict: USA->RUS:gray_zone:0.0593 | domestic: none
- Turn 13: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.2491, RUS->EU:proxy:0.312 | domestic: CHN:protest->grievance, JPN:stable->grievance
- Turn 14: Physical AI enters logistics and warehousing | transfers: none | conflict: USA->RUS:gray_zone:0.0673 | domestic: IND:protest->grievance
- Turn 15: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.2774, RUS->EU:proxy:0.3424 | domestic: CHN:grievance->stable, EU:stable->grievance, SAU:stable->grievance
- Turn 16: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.2924, RUS->EU:proxy:0.3587 | domestic: USA:grievance->protest, EU:grievance->stable, SAU:grievance->protest
- Turn 17: Baseline dynamics | transfers: none | conflict: CHN->IND:gray_zone:0.2224 | domestic: USA:protest->mass_protest, JPN:grievance->stable
- Turn 18: Housing and debt squeeze | transfers: none | conflict: CHN->JPN:gray_zone:0.3302, RUS->EU:proxy:0.3873 | domestic: USA:mass_protest->riot, IND:grievance->protest, BRA:protest->mass_protest
- Turn 19: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.351, RUS->EU:proxy:0.3943 | domestic: USA:riot->riot, CHN:stable->grievance, SAU:protest->grievance, RUS:grievance->protest
- Turn 20: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.3765, RUS->EU:proxy:0.4027 | domestic: USA:riot->riot, EU:stable->grievance, IND:protest->mass_protest, BRA:mass_protest->riot
- Turn 21: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.3897, RUS->EU:proxy:0.4096 | domestic: USA:riot->riot, IND:mass_protest->riot, RUS:protest->grievance, BRA:riot->riot
- Turn 22: Climate adaptation gap widens | transfers: none | conflict: CHN->JPN:limited_war:0.4004 | domestic: USA:riot->riot, EU:grievance->protest, IND:riot->riot, BRA:riot->insurgency
- Turn 23: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.4109, RUS->EU:limited_war:0.4193 | domestic: USA:riot->riot, CHN:grievance->protest, IND:riot->riot, BRA:insurgency->insurgency
- Turn 24: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.4207, RUS->EU:proxy:0.4254 | domestic: USA:riot->riot, EU:protest->grievance, JPN:stable->grievance, IND:riot->riot, BRA:insurgency->insurgency
- Turn 25: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.4312, RUS->EU:proxy:0.431 | domestic: USA:riot->insurgency, CHN:protest->mass_protest, IND:riot->riot, BRA:insurgency->insurgency
- Turn 26: Strategic blocs harden | transfers: none | conflict: CHN->JPN:gray_zone:0.4477, RUS->EU:proxy:0.4417 | domestic: USA:insurgency->insurgency, CHN:mass_protest->riot, EU:grievance->protest, IND:riot->riot, BRA:insurgency->insurgency
- Turn 27: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.4584, USA->RUS:gray_zone:0.2916 | domestic: USA:insurgency->insurgency, CHN:riot->insurgency, EU:protest->mass_protest, JPN:grievance->protest, IND:riot->mass_protest
- Turn 28: Baseline dynamics | transfers: none | conflict: USA->RUS:gray_zone:0.3018, CHN->USA:proxy:0.3268 | domestic: USA:insurgency->insurgency, CHN:insurgency->civil_conflict, SAU:stable->grievance, BRA:insurgency->insurgency
- Turn 29: Baseline dynamics | transfers: none | conflict: RUS->EU:proxy:0.4625, USA->CHN:gray_zone:0.2816 | domestic: USA:insurgency->insurgency, CHN:civil_conflict->civil_conflict, EU:mass_protest->riot, IND:mass_protest->riot, BRA:insurgency->insurgency
- Turn 30: Resilience capital rotation | transfers: none | conflict: CHN->JPN:limited_war:0.4879, RUS->EU:proxy:0.4688 | domestic: USA:insurgency->insurgency, CHN:civil_conflict->civil_conflict, EU:riot->riot, IND:riot->insurgency, RUS:grievance->protest
- Turn 31: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.4967, RUS->EU:proxy:0.475 | domestic: USA:insurgency->civil_conflict, CHN:civil_conflict->civil_conflict, EU:riot->riot, IND:insurgency->civil_conflict, BRA:insurgency->insurgency
- Turn 32: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.5049, RUS->EU:proxy:0.4782 | domestic: USA:civil_conflict->civil_conflict, CHN:civil_conflict->civil_conflict, EU:riot->riot, JPN:protest->grievance, IND:civil_conflict->civil_conflict
- Turn 33: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.5126, RUS->EU:proxy:0.4815 | domestic: USA:civil_conflict->civil_conflict, CHN:civil_conflict->civil_conflict, EU:riot->insurgency, IND:civil_conflict->civil_conflict, BRA:insurgency->insurgency
- Turn 34: Food-water shocks and migration pressure | transfers: none | conflict: CHN->IND:proxy:0.4673, USA->RUS:proxy:0.3601 | domestic: USA:civil_conflict->civil_conflict, CHN:civil_conflict->civil_conflict, EU:insurgency->insurgency, JPN:grievance->stable, IND:civil_conflict->civil_conflict
- Turn 35: Baseline dynamics | transfers: none | conflict: CHN->IND:proxy:0.4764, RUS->EU:proxy:0.4915 | domestic: USA:civil_conflict->civil_conflict, CHN:civil_conflict->civil_conflict, EU:insurgency->insurgency, JPN:stable->grievance, IND:civil_conflict->civil_conflict
- Turn 36: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.5399, USA->RUS:gray_zone:0.376 | domestic: USA:civil_conflict->civil_conflict, CHN:civil_conflict->civil_conflict, EU:insurgency->insurgency, IND:civil_conflict->civil_conflict, BRA:civil_conflict->civil_conflict
- Turn 37: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.5473, RUS->EU:proxy:0.5039 | domestic: USA:civil_conflict->civil_conflict, CHN:civil_conflict->civil_conflict, EU:insurgency->insurgency, IND:civil_conflict->civil_conflict, BRA:civil_conflict->civil_conflict
- Turn 38: Institutional settlement attempt | transfers: SAU->JPN:0.0047 | conflict: CHN->JPN:gray_zone:0.5551, RUS->EU:proxy:0.509 | domestic: USA:civil_conflict->civil_conflict, CHN:civil_conflict->civil_conflict, EU:insurgency->insurgency, IND:civil_conflict->civil_conflict, RUS:mass_protest->riot
- Turn 39: Baseline dynamics | transfers: none | conflict: CHN->IND:proxy:0.5156, RUS->EU:proxy:0.5152 | domestic: USA:civil_conflict->civil_conflict, CHN:civil_conflict->civil_conflict, EU:insurgency->insurgency, JPN:grievance->protest, IND:civil_conflict->civil_conflict
- Turn 40: Baseline dynamics | transfers: none | conflict: CHN->IND:proxy:0.5221, USA->RUS:gray_zone:0.4016 | domestic: USA:civil_conflict->civil_conflict, CHN:civil_conflict->civil_conflict, EU:insurgency->insurgency, IND:civil_conflict->civil_conflict, SAU:grievance->protest
