# High automation / low adaptation

- Final global average `S`: `0.4093`
- Final global average horizon: `5.4352` turns
- Final global average cash stability: `0.2596`
- Final global average war burden: `0.0464`
- Final global average domestic burden: `0.0635`
- Final global average protest pressure: `0.3045`
- Top resilient: `USA, SAU, EU`
- Most fragile: `JPN, IND, RUS`
- Most domestically fragile: `BRA, CHN, RUS`
- Conflict mix: `gray=8, proxy=9, limited=1`
- Domestic escalation mix: `protest=6, mass=0, riot=0, insurgency=0, civil=0`

## Final Country Snapshot

| Code | S | Horizon | Support Needed | Cash | Domestic Stage | Domestic Burden | Protest | War Burden | War Pressure | Likely Mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USA | 0.513 | 6.82 | 0.5006 | 0.4094 | stable | 0.02 | 0.2762 | 0.0056 | 0.3365 | proxy |
| SAU | 0.4278 | 6.12 | 0.4992 | 0.4754 | grievance | 0.06 | 0.2389 | 0.0 | 0.0 | none |
| EU | 0.4172 | 6.12 | 0.5647 | 0.1553 | grievance | 0.055 | 0.3114 | 0.1254 | 0.0 | none |
| BRA | 0.3987 | 5.35 | 0.5601 | 0.2722 | protest | 0.12 | 0.3128 | 0.0 | 0.0 | none |
| CHN | 0.3945 | 4.49 | 0.69 | 0.2598 | protest | 0.1008 | 0.3162 | 0.0489 | 0.6071 | limited_war |
| JPN | 0.3816 | 5.79 | 0.6271 | 0.2316 | grievance | 0.0714 | 0.3008 | 0.1243 | 0.0 | none |
| IND | 0.3492 | 4.77 | 0.6574 | 0.2069 | grievance | 0.055 | 0.3239 | 0.0027 | 0.0 | none |
| RUS | 0.3105 | 2.85 | 0.7885 | 0.1241 | grievance | 0.085 | 0.3051 | 0.0662 | 0.4801 | proxy |

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
