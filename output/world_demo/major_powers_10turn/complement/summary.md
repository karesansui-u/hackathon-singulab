# High automation / high adaptation

- Final global average `S`: `0.4611`
- Final global average horizon: `6.6671` turns
- Final global average cash stability: `0.4182`
- Final global average war burden: `0.0137`
- Final global average domestic burden: `0.0547`
- Final global average protest pressure: `0.2461`
- Top resilient: `USA, EU, JPN`
- Most fragile: `CHN, IND, RUS`
- Most domestically fragile: `EU, RUS, USA`
- Conflict mix: `gray=6, proxy=5, limited=0`
- Domestic escalation mix: `protest=3, mass=0, riot=0, insurgency=0, civil=0`

## Final Country Snapshot

| Code | S | Horizon | Support Needed | Cash | Domestic Stage | Domestic Burden | Protest | War Burden | War Pressure | Likely Mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USA | 0.5307 | 7.31 | 0.4566 | 0.4604 | grievance | 0.055 | 0.2526 | 0.0034 | 0.1306 | gray_zone |
| EU | 0.51 | 8.26 | 0.3551 | 0.4727 | protest | 0.12 | 0.233 | 0.0141 | 0.0 | none |
| JPN | 0.4788 | 7.98 | 0.3694 | 0.4683 | stable | 0.02 | 0.2185 | 0.0553 | 0.0 | none |
| SAU | 0.4592 | 6.88 | 0.4162 | 0.5674 | grievance | 0.055 | 0.1984 | 0.0 | 0.0 | none |
| BRA | 0.4446 | 6.36 | 0.4313 | 0.3973 | stable | 0.0262 | 0.263 | 0.0 | 0.0 | none |
| CHN | 0.4373 | 5.45 | 0.576 | 0.4252 | stable | 0.0474 | 0.2372 | 0.03 | 0.3799 | proxy |
| IND | 0.4003 | 6.06 | 0.5097 | 0.3343 | stable | 0.02 | 0.2669 | 0.0 | 0.0 | none |
| RUS | 0.3391 | 3.69 | 0.6983 | 0.2042 | grievance | 0.085 | 0.2734 | 0.0057 | 0.2807 | proxy |

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
