# High automation / low adaptation

- Final global average `S`: `0.2291`
- Final global average horizon: `1.5173` turns
- Final global average cash stability: `0.0006`
- Final global average war burden: `0.1535`
- Final global average domestic burden: `0.1882`
- Final global average protest pressure: `0.5145`
- Top resilient: `USA, SAU, EU`
- Most fragile: `BRA, IND, RUS`
- Most domestically fragile: `IND, BRA, CHN`
- Conflict mix: `gray=21, proxy=28, limited=9`
- Domestic escalation mix: `protest=15, mass=7, riot=27, insurgency=39, civil=16`

## Final Country Snapshot

| Code | S | Horizon | Support Needed | Cash | Domestic Stage | Domestic Burden | Protest | War Burden | War Pressure | Likely Mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USA | 0.2956 | 2.41 | 1.0 | 0.0028 | insurgency | 0.195 | 0.5206 | 0.1286 | 0.5644 | proxy |
| SAU | 0.2917 | 2.27 | 0.9888 | 0.0 | protest | 0.09 | 0.4039 | 0.0 | 0.0 | none |
| EU | 0.2646 | 2.83 | 1.0 | 0.0 | protest | 0.09 | 0.4495 | 0.1812 | 0.0 | none |
| CHN | 0.2391 | 1.19 | 1.0 | 0.0 | insurgency | 0.225 | 0.5023 | 0.1466 | 0.7334 | limited_war |
| JPN | 0.1796 | 1.33 | 1.0 | 0.0 | insurgency | 0.195 | 0.5463 | 0.3057 | 0.0 | none |
| BRA | 0.1749 | 0.21 | 1.0 | 0.0 | civil_conflict | 0.23 | 0.5753 | 0.087 | 0.0 | none |
| IND | 0.1664 | 0.49 | 1.0 | 0.0 | civil_conflict | 0.23 | 0.5591 | 0.1131 | 0.0 | none |
| RUS | 0.1474 | 0.0 | 1.0 | 0.0 | insurgency | 0.195 | 0.542 | 0.3101 | 0.5818 | proxy |

## Event Timeline

- Turn 1: Baseline dynamics | transfers: none | conflict: CHN->IND:proxy:0.1328 | domestic: IND:stable->grievance, SAU:stable->grievance
- Turn 2: Frontier model diffusion wave | transfers: none | conflict: USA->RUS:proxy:0.0925, CHN->USA:gray_zone:0.07 | domestic: EU:stable->grievance, RUS:stable->grievance
- Turn 3: Advanced semiconductor controls tighten | transfers: none | conflict: CHN->JPN:gray_zone:0.2404, RUS->EU:gray_zone:0.2748 | domestic: SAU:grievance->stable
- Turn 4: Maritime chokepoint disruption | transfers: none | conflict: CHN->JPN:limited_war:0.2477, RUS->EU:proxy:0.2925 | domestic: EU:grievance->protest, IND:grievance->protest, BRA:stable->grievance
- Turn 5: Public adaptation fork | transfers: none | conflict: CHN->JPN:proxy:0.2618, RUS->EU:proxy:0.3122 | domestic: CHN:stable->grievance
- Turn 6: Heat and crop volatility | transfers: none | conflict: CHN->JPN:gray_zone:0.2774 | domestic: IND:protest->grievance, BRA:grievance->protest
- Turn 7: Resilience funds open | transfers: none | conflict: CHN->JPN:gray_zone:0.2936, RUS->EU:proxy:0.3573 | domestic: CHN:grievance->protest, RUS:grievance->stable
- Turn 8: Sanctions and bloc pressure escalate | transfers: none | conflict: CHN->JPN:gray_zone:0.3259, RUS->EU:proxy:0.391 | domestic: CHN:protest->grievance, SAU:stable->grievance, BRA:protest->grievance
- Turn 9: Multilateral resilience compact | transfers: USA->JPN:0.0134, USA->IND:0.0123, USA->EU:0.0084, EU->IND:0.0067, EU->BRA:0.0048 | conflict: CHN->JPN:proxy:0.3639, RUS->EU:proxy:0.4186 | domestic: CHN:grievance->protest, EU:protest->grievance, JPN:stable->grievance
- Turn 10: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.4072, USA->RUS:gray_zone:0.1874 | domestic: RUS:stable->grievance, BRA:grievance->protest
- Turn 11: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.4527, RUS->EU:proxy:0.4837 | domestic: JPN:grievance->protest, BRA:protest->mass_protest
- Turn 12: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.5039, RUS->EU:proxy:0.5111 | domestic: USA:stable->grievance, BRA:mass_protest->riot
- Turn 13: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.5347, USA->RUS:gray_zone:0.2991 | domestic: EU:grievance->stable, JPN:protest->mass_protest, IND:grievance->protest, BRA:riot->insurgency
- Turn 14: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.5518, USA->RUS:gray_zone:0.3311 | domestic: JPN:mass_protest->riot, IND:protest->mass_protest, RUS:grievance->protest, BRA:insurgency->insurgency
- Turn 15: Baseline dynamics | transfers: none | conflict: RUS->EU:proxy:0.556, USA->RUS:gray_zone:0.3642 | domestic: USA:grievance->protest, JPN:riot->riot, RUS:protest->mass_protest, BRA:insurgency->insurgency
- Turn 16: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.5634, RUS->EU:limited_war:0.5752 | domestic: EU:stable->grievance, JPN:riot->riot, IND:mass_protest->riot, RUS:mass_protest->riot, BRA:insurgency->insurgency
- Turn 17: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.569, USA->CHN:gray_zone:0.3381 | domestic: EU:grievance->protest, JPN:riot->riot, IND:riot->mass_protest, RUS:riot->insurgency, BRA:insurgency->insurgency
- Turn 18: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.575, USA->RUS:proxy:0.3878 | domestic: USA:protest->mass_protest, JPN:riot->riot, RUS:insurgency->insurgency, BRA:insurgency->insurgency
- Turn 19: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.5786, USA->RUS:gray_zone:0.3975 | domestic: USA:mass_protest->riot, CHN:protest->grievance, JPN:riot->riot, IND:mass_protest->riot, SAU:grievance->protest
- Turn 20: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.5822, RUS->EU:proxy:0.6203 | domestic: USA:riot->riot, EU:protest->grievance, JPN:riot->riot, IND:riot->riot, RUS:insurgency->insurgency
- Turn 21: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.5854, RUS->EU:proxy:0.627 | domestic: USA:riot->riot, EU:grievance->stable, JPN:riot->riot, IND:riot->insurgency, RUS:insurgency->insurgency
- Turn 22: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.5889, RUS->EU:proxy:0.6292 | domestic: USA:riot->riot, CHN:grievance->protest, EU:stable->grievance, JPN:riot->insurgency, IND:insurgency->insurgency
- Turn 23: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.596, RUS->EU:proxy:0.6304 | domestic: USA:riot->insurgency, CHN:protest->mass_protest, JPN:insurgency->insurgency, IND:insurgency->insurgency, RUS:insurgency->insurgency
- Turn 24: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.6015, RUS->EU:proxy:0.6313 | domestic: USA:insurgency->insurgency, JPN:insurgency->riot, IND:insurgency->insurgency, SAU:protest->grievance, RUS:insurgency->insurgency
- Turn 25: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.6058, USA->RUS:proxy:0.4365 | domestic: USA:insurgency->insurgency, CHN:mass_protest->riot, JPN:riot->riot, IND:insurgency->civil_conflict, SAU:grievance->protest
- Turn 26: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.6134, RUS->EU:proxy:0.6338 | domestic: USA:insurgency->insurgency, CHN:riot->riot, JPN:riot->riot, IND:civil_conflict->civil_conflict, RUS:insurgency->insurgency
- Turn 27: Baseline dynamics | transfers: none | conflict: CHN->IND:proxy:0.5537, USA->RUS:proxy:0.4481 | domestic: USA:insurgency->insurgency, CHN:riot->riot, EU:grievance->protest, JPN:riot->riot, IND:civil_conflict->civil_conflict
- Turn 28: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.6235, RUS->EU:proxy:0.6368 | domestic: USA:insurgency->insurgency, CHN:riot->riot, JPN:riot->riot, IND:civil_conflict->civil_conflict, RUS:insurgency->insurgency
- Turn 29: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.6294, USA->RUS:proxy:0.4596 | domestic: USA:insurgency->insurgency, CHN:riot->riot, JPN:riot->insurgency, IND:civil_conflict->civil_conflict, RUS:insurgency->insurgency
- Turn 30: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.6356, USA->RUS:proxy:0.4655 | domestic: USA:insurgency->insurgency, CHN:riot->insurgency, JPN:insurgency->insurgency, IND:civil_conflict->civil_conflict, RUS:insurgency->insurgency
