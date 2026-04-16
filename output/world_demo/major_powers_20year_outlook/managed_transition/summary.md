# 20-year managed transition

- Final global average `S`: `0.3941`
- Final global average horizon: `5.7138` turns
- Final global average cash stability: `0.063`
- Final global average war burden: `0.0515`
- Final global average domestic burden: `0.1083`
- Final global average protest pressure: `0.3313`
- Top resilient: `USA, EU, SAU`
- Most fragile: `IND, CHN, RUS`
- Most domestically fragile: `CHN, BRA, USA`
- Conflict mix: `gray=13, proxy=12, limited=1`
- Domestic escalation mix: `protest=10, mass=4, riot=8, insurgency=0, civil=0`

## Final Country Snapshot

| Code | S | Horizon | Support Needed | Cash | Domestic Stage | Domestic Burden | Protest | War Burden | War Pressure | Likely Mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USA | 0.475 | 7.23 | 0.3958 | 0.1267 | riot | 0.16 | 0.3421 | 0.0149 | 0.2668 | proxy |
| EU | 0.4709 | 7.37 | 0.3929 | 0.1688 | stable | 0.0297 | 0.2652 | 0.1243 | 0.0 | none |
| SAU | 0.3903 | 5.73 | 0.5119 | 0.1495 | protest | 0.0944 | 0.2899 | 0.0 | 0.0 | none |
| JPN | 0.3864 | 6.2 | 0.5352 | 0.0335 | grievance | 0.0714 | 0.2947 | 0.1023 | 0.0 | none |
| BRA | 0.3496 | 4.96 | 0.5386 | 0.0 | riot | 0.16 | 0.3828 | 0.0 | 0.0 | none |
| IND | 0.3404 | 5.05 | 0.5533 | 0.0 | protest | 0.09 | 0.3476 | 0.025 | 0.0 | none |
| CHN | 0.3366 | 4.0 | 0.6543 | 0.0 | riot | 0.16 | 0.3711 | 0.0536 | 0.5491 | proxy |
| RUS | 0.3088 | 3.21 | 0.6737 | 0.0024 | grievance | 0.055 | 0.3224 | 0.0562 | 0.3882 | proxy |

## Event Timeline

- Turn 1: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.1694 | domestic: CHN:stable->grievance, SAU:stable->grievance, RUS:stable->grievance
- Turn 2: Frontier AI diffuses into white-collar workflows | transfers: none | conflict: USA->RUS:proxy:0.0316 | domestic: CHN:grievance->protest, SAU:grievance->protest, RUS:grievance->stable
- Turn 3: Baseline dynamics | transfers: none | conflict: none | domestic: EU:stable->grievance, JPN:stable->grievance, RUS:stable->grievance
- Turn 4: Compute and grid bottlenecks | transfers: none | conflict: CHN->JPN:proxy:0.1788 | domestic: none
- Turn 5: Social buffering pilots expand | transfers: USA->JPN:0.0047, USA->IND:0.0043 | conflict: CHN->IND:proxy:0.0856 | domestic: JPN:grievance->stable, SAU:protest->grievance, RUS:grievance->stable
- Turn 6: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.1851, RUS->EU:gray_zone:0.2296 | domestic: CHN:protest->grievance
- Turn 7: Physical AI enters logistics and warehousing | transfers: none | conflict: CHN->JPN:gray_zone:0.189 | domestic: CHN:grievance->protest, IND:stable->grievance
- Turn 8: Baseline dynamics | transfers: none | conflict: CHN->USA:gray_zone:0.0561 | domestic: CHN:protest->grievance
- Turn 9: Housing and debt squeeze | transfers: none | conflict: CHN->JPN:gray_zone:0.1978, USA->RUS:gray_zone:0.051 | domestic: BRA:stable->grievance
- Turn 10: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.2079, RUS->EU:proxy:0.2748 | domestic: EU:grievance->stable, JPN:stable->grievance, SAU:grievance->stable
- Turn 11: Climate adaptation gap widens | transfers: none | conflict: CHN->JPN:limited_war:0.2231 | domestic: USA:stable->grievance, BRA:grievance->protest
- Turn 12: Baseline dynamics | transfers: none | conflict: USA->CHN:gray_zone:0.0351 | domestic: CHN:grievance->protest, EU:stable->grievance, JPN:grievance->stable
- Turn 13: Strategic blocs harden | transfers: none | conflict: CHN->JPN:gray_zone:0.269 | domestic: EU:grievance->stable, IND:grievance->stable, SAU:stable->grievance, RUS:stable->grievance
- Turn 14: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.2943 | domestic: CHN:protest->mass_protest, SAU:grievance->protest, RUS:grievance->protest
- Turn 15: Resilience capital rotation | transfers: none | conflict: CHN->JPN:gray_zone:0.3212 | domestic: IND:stable->grievance
- Turn 16: Baseline dynamics | transfers: none | conflict: CHN->JPN:proxy:0.348 | domestic: USA:grievance->protest, EU:stable->grievance, IND:grievance->protest, RUS:protest->grievance
- Turn 17: Food-water shocks and migration pressure | transfers: none | conflict: CHN->JPN:proxy:0.3753, USA->RUS:gray_zone:0.1118 | domestic: USA:protest->mass_protest, BRA:protest->mass_protest
- Turn 18: Baseline dynamics | transfers: none | conflict: RUS->EU:proxy:0.3903, CHN->IND:proxy:0.3031 | domestic: CHN:mass_protest->riot, SAU:protest->mass_protest, BRA:mass_protest->riot
- Turn 19: Institutional settlement attempt | transfers: USA->JPN:0.0073, USA->IND:0.0067, USA->EU:0.0046, EU->IND:0.0051, SAU->JPN:0.0056 | conflict: RUS->EU:proxy:0.3965, CHN->USA:gray_zone:0.2443 | domestic: USA:mass_protest->riot, CHN:riot->riot, EU:grievance->stable, JPN:stable->grievance, BRA:riot->riot
- Turn 20: Baseline dynamics | transfers: none | conflict: CHN->JPN:gray_zone:0.4155, RUS->EU:proxy:0.4029 | domestic: USA:riot->riot, CHN:riot->riot, SAU:mass_protest->protest, BRA:riot->riot
