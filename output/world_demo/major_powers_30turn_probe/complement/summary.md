# High automation / high adaptation

- Final global average `S`: `0.261`
- Final global average horizon: `2.6897` turns
- Final global average cash stability: `0.0001`
- Final global average war burden: `0.1324`
- Final global average domestic burden: `0.2031`
- Final global average protest pressure: `0.4539`
- Top resilient: `USA, EU, CHN`
- Most fragile: `BRA, JPN, RUS`
- Most domestically fragile: `JPN, RUS, BRA`
- Conflict mix: `gray=22, proxy=20, limited=3`
- Domestic escalation mix: `protest=14, mass=9, riot=33, insurgency=14, civil=14`

## Final Country Snapshot

| Code | S | Horizon | Support Needed | Cash | Domestic Stage | Domestic Burden | Protest | War Burden | War Pressure | Likely Mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USA | 0.2966 | 3.12 | 0.924 | 0.0 | civil_conflict | 0.23 | 0.4881 | 0.077 | 0.3822 | proxy |
| EU | 0.2959 | 3.91 | 0.8638 | 0.0 | mass_protest | 0.155 | 0.3962 | 0.2503 | 0.0 | none |
| CHN | 0.2548 | 1.99 | 1.0 | 0.0 | insurgency | 0.225 | 0.4448 | 0.1743 | 0.5861 | limited_war |
| SAU | 0.2496 | 2.47 | 1.0 | 0.0 | insurgency | 0.225 | 0.4204 | 0.014 | 0.0 | none |
| IND | 0.2476 | 2.66 | 0.9428 | 0.0 | riot | 0.16 | 0.4555 | 0.0044 | 0.0 | none |
| BRA | 0.2307 | 1.67 | 1.0 | 0.0 | civil_conflict | 0.23 | 0.5112 | 0.0748 | 0.0 | none |
| JPN | 0.2101 | 2.89 | 1.0 | 0.0 | civil_conflict | 0.26 | 0.4663 | 0.3221 | 0.0 | none |
| RUS | 0.1887 | 0.25 | 1.0 | 0.0032 | civil_conflict | 0.23 | 0.4959 | 0.1575 | 0.4436 | proxy |

## Event Timeline

- Turn 1: Baseline dynamics | transfers: USA->JPN:0.0117, USA->IND:0.0107, USA->EU:0.0073, EU->IND:0.0061, EU->BRA:0.0044 | conflict: RUS->EU:gray_zone:0.1744, CHN->USA:proxy:0.0446 | domestic: CHN:stable->grievance, RUS:stable->grievance
- Turn 2: Frontier model diffusion wave | transfers: USA->JPN:0.0118, USA->IND:0.0108, USA->EU:0.0074, EU->IND:0.0063, EU->BRA:0.0045 | conflict: USA->CHN:gray_zone:0.0289 | domestic: USA:stable->grievance, SAU:stable->grievance
- Turn 3: Advanced semiconductor controls tighten | transfers: USA->JPN:0.0118, USA->IND:0.0108, USA->EU:0.0074, EU->IND:0.0065, EU->BRA:0.0046 | conflict: none | domestic: none
- Turn 4: Maritime chokepoint disruption | transfers: USA->JPN:0.0117, USA->IND:0.0107, USA->EU:0.0073, EU->IND:0.0066, EU->BRA:0.0047 | conflict: USA->CHN:proxy:0.0298 | domestic: USA:grievance->protest, CHN:grievance->stable, SAU:grievance->stable, RUS:grievance->stable
- Turn 5: Public adaptation fork | transfers: USA->JPN:0.0115, USA->IND:0.0105, USA->EU:0.0072, EU->IND:0.0066, EU->BRA:0.0048 | conflict: none | domestic: USA:protest->grievance, SAU:stable->grievance, RUS:stable->grievance, BRA:stable->grievance
- Turn 6: Heat and crop volatility | transfers: USA->JPN:0.0113, USA->IND:0.0103, USA->EU:0.0071, EU->IND:0.0066, EU->BRA:0.0048 | conflict: RUS->EU:proxy:0.2243 | domestic: USA:grievance->protest
- Turn 7: Resilience funds open | transfers: USA->JPN:0.011, USA->IND:0.0101, USA->EU:0.0069, EU->IND:0.0065, EU->BRA:0.0047 | conflict: USA->CHN:gray_zone:0.0413 | domestic: none
- Turn 8: Sanctions and bloc pressure escalate | transfers: USA->JPN:0.0106, USA->IND:0.0097, USA->EU:0.0066, EU->IND:0.0064, EU->BRA:0.0046 | conflict: CHN->JPN:proxy:0.1953, USA->CHN:gray_zone:0.0465 | domestic: USA:protest->grievance, CHN:stable->grievance, RUS:grievance->stable
- Turn 9: Multilateral resilience compact | transfers: USA->JPN:0.0177, USA->IND:0.0161, USA->EU:0.0109, EU->IND:0.0109, EU->BRA:0.0078 | conflict: CHN->JPN:gray_zone:0.209, USA->CHN:gray_zone:0.0518 | domestic: CHN:grievance->stable, EU:stable->grievance, BRA:grievance->stable
- Turn 10: Baseline dynamics | transfers: USA->JPN:0.0092, USA->IND:0.0084, USA->EU:0.0058, EU->IND:0.0058, EU->BRA:0.0042 | conflict: CHN->JPN:proxy:0.2367 | domestic: EU:grievance->protest, RUS:stable->grievance
- Turn 11: Baseline dynamics | transfers: USA->JPN:0.0086, USA->IND:0.0079, USA->EU:0.0054, EU->IND:0.0055, JPN->IND:0.0052 | conflict: USA->RUS:gray_zone:0.1061 | domestic: USA:grievance->protest, IND:stable->grievance
- Turn 12: Baseline dynamics | transfers: USA->JPN:0.0078, USA->IND:0.0071, USA->EU:0.0049, EU->IND:0.0052, JPN->IND:0.0049 | conflict: CHN->JPN:gray_zone:0.3028 | domestic: IND:grievance->protest
- Turn 13: Baseline dynamics | transfers: USA->JPN:0.007, USA->IND:0.0064, USA->EU:0.0044, EU->IND:0.0048, JPN->IND:0.0044 | conflict: CHN->IND:gray_zone:0.249 | domestic: BRA:stable->grievance
- Turn 14: Baseline dynamics | transfers: USA->JPN:0.0062, USA->IND:0.0057, EU->IND:0.0043, SAU->JPN:0.0056, SAU->IND:0.0044 | conflict: CHN->JPN:gray_zone:0.3727, RUS->EU:proxy:0.4147 | domestic: IND:protest->grievance, SAU:grievance->protest
- Turn 15: Baseline dynamics | transfers: USA->JPN:0.0054, USA->IND:0.0049, SAU->JPN:0.0053, SAU->IND:0.0041, CHN->BRA:0.0041 | conflict: CHN->JPN:gray_zone:0.4036, USA->RUS:proxy:0.2461 | domestic: CHN:stable->grievance, JPN:stable->grievance, BRA:grievance->protest
- Turn 16: Baseline dynamics | transfers: USA->JPN:0.0043, SAU->JPN:0.0048 | conflict: RUS->EU:proxy:0.4414, CHN->USA:proxy:0.2718 | domestic: USA:protest->mass_protest, JPN:grievance->protest
- Turn 17: Baseline dynamics | transfers: SAU->JPN:0.0044 | conflict: CHN->USA:gray_zone:0.2816 | domestic: CHN:grievance->protest, SAU:protest->mass_protest
- Turn 18: Baseline dynamics | transfers: none | conflict: CHN->IND:proxy:0.3479, USA->RUS:gray_zone:0.2839 | domestic: USA:mass_protest->riot, IND:grievance->protest, SAU:mass_protest->riot
- Turn 19: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.4442, USA->RUS:gray_zone:0.2923 | domestic: USA:riot->riot, IND:protest->grievance, SAU:riot->riot
- Turn 20: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.4485, USA->CHN:gray_zone:0.2588 | domestic: USA:riot->riot, EU:protest->grievance, JPN:protest->mass_protest, SAU:riot->riot, RUS:grievance->protest
- Turn 21: Baseline dynamics | transfers: none | conflict: RUS->EU:proxy:0.4925, CHN->USA:gray_zone:0.3063 | domestic: USA:riot->riot, JPN:mass_protest->riot, IND:grievance->protest, SAU:riot->riot, BRA:mass_protest->riot
- Turn 22: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.4595 | domestic: USA:riot->riot, CHN:protest->mass_protest, JPN:riot->riot, SAU:riot->riot, BRA:riot->insurgency
- Turn 23: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.4654, RUS->EU:gray_zone:0.4971 | domestic: USA:riot->riot, EU:grievance->protest, JPN:riot->riot, IND:protest->mass_protest, SAU:riot->mass_protest
- Turn 24: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.4694, RUS->EU:proxy:0.5035 | domestic: USA:riot->insurgency, EU:protest->grievance, JPN:riot->riot, RUS:mass_protest->riot, BRA:insurgency->civil_conflict
- Turn 25: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.4752, RUS->EU:proxy:0.5084 | domestic: USA:insurgency->insurgency, CHN:mass_protest->riot, EU:grievance->stable, JPN:riot->riot, IND:mass_protest->riot
- Turn 26: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.4819, RUS->EU:proxy:0.5119 | domestic: USA:insurgency->insurgency, CHN:riot->riot, JPN:riot->insurgency, IND:riot->riot, RUS:riot->riot
- Turn 27: Baseline dynamics | transfers: none | conflict: USA->CHN:gray_zone:0.2947 | domestic: USA:insurgency->insurgency, CHN:riot->insurgency, JPN:insurgency->insurgency, IND:riot->riot, SAU:mass_protest->riot
- Turn 28: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.4944, RUS->EU:proxy:0.5215 | domestic: USA:insurgency->civil_conflict, CHN:insurgency->riot, EU:stable->grievance, JPN:insurgency->insurgency, IND:riot->riot
- Turn 29: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.4994, RUS->EU:proxy:0.5282 | domestic: USA:civil_conflict->civil_conflict, CHN:riot->riot, EU:grievance->protest, JPN:insurgency->insurgency, IND:riot->riot
- Turn 30: Baseline dynamics | transfers: none | conflict: CHN->JPN:limited_war:0.5047, RUS->EU:proxy:0.5326 | domestic: USA:civil_conflict->civil_conflict, CHN:riot->insurgency, EU:protest->mass_protest, JPN:insurgency->civil_conflict, IND:riot->riot
