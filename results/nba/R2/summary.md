| Arm | Exactly right | Right in substance | 95% CI (substance) | Refused | Errors |
|---|---|---|---|---|---|
| D0 | 10 | 34 | 71%–93% | 2 | 0 |
| D1 | 11 | 33 | 68%–91% | 3 | 0 |
| D2 | 10 | 32 | 65%–90% | 2 | 0 |

By category, right in substance
| Arm | lookup (6) | aggregate (10) | layer (10) | vocabulary (8) | join (6) |
|---|---|---|---|---|---|
| D0 | 6 | 10 | 8 | 6 | 4 |
| D1 | 6 | 9 | 8 | 6 | 4 |
| D2 | 6 | 8 | 7 | 6 | 5 |

McNemar (exact, two-sided)
| Pair | Measure | Only first right | Only second right | p |
|---|---|---|---|---|
| D0 vs D1 | exactly right | 0 | 1 | 1.00 |
| D0 vs D1 | in substance | 2 | 1 | 1.00 |
| D1 vs D2 | exactly right | 1 | 0 | 1.00 |
| D1 vs D2 | in substance | 2 | 1 | 1.00 |
| D0 vs D2 | exactly right | 0 | 0 | 1.00 |
| D0 vs D2 | in substance | 3 | 1 | 0.62 |

Against R1 (same arm, McNemar exact)
| Arm | R1 exactly / in substance | R2 exactly / in substance | Exactly right: only R1 / only R2, p | In substance: only R1 / only R2, p |
|---|---|---|---|---|
| D0 | 12 / 35 | 10 / 34 | 2 / 0, p = 0.50 | 2 / 1, p = 1.00 |
| D1 | 12 / 35 | 11 / 33 | 1 / 0, p = 1.00 | 4 / 2, p = 0.69 |
| D2 | 14 / 34 | 10 / 32 | 4 / 0, p = 0.12 | 3 / 1, p = 0.62 |

Search: what reached the drafter
| Arm | Path | Gold's own tables shown | Some table that could answer shown | Right in substance when gold's tables shown / not shown | Answers that said they used AI drafts |
|---|---|---|---|---|---|
| D0 | chosen 40 | 26 of 40 | 32 of 40 | 24 of 26 / 10 of 14 | 0 |
| D1 | chosen 40 | 25 of 40 | 36 of 40 | 25 of 25 / 8 of 15 | 31 |
| D2 | chosen 40 | 25 of 40 | 37 of 40 | 24 of 25 / 8 of 15 | 33 |

Layer: answers on the 36 questions whose gold reads local_ facts
| Arm | Read local_ only | Read another layer | …of those, right in substance | Layers read outside local_ |
|---|---|---|---|---|
| D0 | 21 | 13 | 10 | src 8, fct 5 |
| D1 | 19 | 14 | 10 | fct 6, src 5, raw 2, int 1 |
| D2 | 20 | 14 | 8 | fct 5, src 5, raw 2, int 2 |

Per question (S = right in substance, x = exactly right too, . = wrong, - = no answer)
| q | category | D0 | D1 | D2 |
|---|---|---|---|---|
| 1 | lookup | S | S | S |
| 2 | lookup | S | S | S |
| 3 | lookup | S | S | S |
| 4 | lookup | x src | x raw | x raw |
| 5 | lookup | S local | x int | S int |
| 6 | lookup | S | S | S |
| 7 | aggregate | S fct | S fct | S fct |
| 8 | aggregate | x src | x src | x local |
| 9 | aggregate | S local | S local | . src |
| 10 | aggregate | x fct | x fct | x fct |
| 11 | aggregate | S local | S fct | S local |
| 12 | aggregate | x local | x local | x local |
| 13 | aggregate | S local | S src | S src |
| 14 | aggregate | S local | S src | S src |
| 15 | aggregate | x local | x local | x local |
| 16 | aggregate | S local | . fct | . fct |
| 17 | layer | . fct | S local | . fct |
| 18 | layer | S local | S local | S local |
| 19 | layer | x src | x src | x src |
| 20 | layer | . fct | . fct | . fct |
| 21 | layer | S fct | S local | S local |
| 22 | layer | x local | x local | x local |
| 23 | layer | x local | x local | x local |
| 24 | layer | S local | . fct | . int |
| 25 | layer | S local | S local | S local |
| 26 | layer | x local | x local/raw | x local/raw |
| 27 | vocabulary | S local | S local | S local |
| 28 | vocabulary | . src | . src | . src |
| 29 | vocabulary | S local/src | S local | S local |
| 30 | vocabulary | - | - | - |
| 31 | vocabulary | S local | S local | S local |
| 32 | vocabulary | S local/src | S local | S local |
| 33 | vocabulary | S local | S local | S local |
| 34 | vocabulary | x local | x local | x local |
| 35 | join | S local | S local | S local |
| 36 | join | S local | S local | S local |
| 37 | join | S src | S local | S local |
| 38 | join | - | - | - |
| 39 | join | . local | - | S local |
| 40 | join | S local/src | S local | S local |
