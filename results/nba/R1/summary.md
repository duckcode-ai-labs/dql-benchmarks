| Arm | Exactly right | Right in substance | 95% CI (substance) | Refused | Errors |
|---|---|---|---|---|---|
| C | 30 | 40 | 91%–100% | 0 | 0 |
| D0 | 12 | 35 | 74%–95% | 2 | 0 |
| D1 | 12 | 35 | 74%–95% | 1 | 0 |
| D2 | 14 | 34 | 71%–93% | 3 | 0 |
| W0 | 10 | 40 | 91%–100% | 0 | 0 |
| W1 | 9 | 39 | 87%–100% | 0 | 0 |

By category, right in substance
| Arm | lookup (6) | aggregate (10) | layer (10) | vocabulary (8) | join (6) |
|---|---|---|---|---|---|
| C | 6 | 10 | 10 | 8 | 6 |
| D0 | 6 | 9 | 8 | 7 | 5 |
| D1 | 6 | 8 | 8 | 8 | 5 |
| D2 | 6 | 8 | 9 | 7 | 4 |
| W0 | 6 | 10 | 10 | 8 | 6 |
| W1 | 6 | 9 | 10 | 8 | 6 |

McNemar (exact, two-sided)
| Pair | Measure | Only first right | Only second right | p |
|---|---|---|---|---|
| D0 vs D1 | exactly right | 0 | 0 | 1.00 |
| D0 vs D1 | in substance | 1 | 1 | 1.00 |
| D1 vs D2 | exactly right | 1 | 3 | 0.62 |
| D1 vs D2 | in substance | 2 | 1 | 1.00 |
| D0 vs D2 | exactly right | 1 | 3 | 0.62 |
| D0 vs D2 | in substance | 2 | 1 | 1.00 |
| W0 vs W1 | exactly right | 1 | 0 | 1.00 |
| W0 vs W1 | in substance | 1 | 0 | 1.00 |
| D0 vs W0 | exactly right | 2 | 0 | 0.50 |
| D0 vs W0 | in substance | 0 | 5 | 0.06 |
| D1 vs W1 | exactly right | 3 | 0 | 0.25 |
| D1 vs W1 | in substance | 1 | 5 | 0.22 |

Search: what reached the drafter
| Arm | Path | Gold's own tables shown | Some table that could answer shown | Right in substance when gold's tables shown / not shown | Answers that said they used AI drafts |
|---|---|---|---|---|---|
| D0 | chosen 40 | 27 of 40 | 32 of 40 | 24 of 27 / 11 of 13 | 0 |
| D1 | chosen 40 | 28 of 40 | 35 of 40 | 25 of 28 / 10 of 12 | 14 |
| D2 | chosen 40 | 27 of 40 | 34 of 40 | 25 of 27 / 9 of 13 | 36 |
| W0 | whole 40 | 40 of 40 | 40 of 40 | 40 of 40 / 0 of 0 | 0 |
| W1 | whole 40 | 40 of 40 | 40 of 40 | 39 of 40 / 0 of 0 | 40 |

Layer: answers on the 36 questions whose gold reads local_ facts
| Arm | Read local_ only | Read another layer | …of those, right in substance | Layers read outside local_ |
|---|---|---|---|---|
| C | 24 | 12 | 12 | raw 12 |
| D0 | 21 | 13 | 10 | src 7, fct 6 |
| D1 | 20 | 15 | 11 | src 7, fct 6, raw 2 |
| D2 | 22 | 11 | 8 | src 5, fct 4, raw 2, int 1 |
| W0 | 27 | 9 | 9 | raw 9 |
| W1 | 27 | 9 | 8 | raw 7, int 1, src 1 |

Per question (S = right in substance, x = exactly right too, . = wrong, - = no answer)
| q | category | C | D0 | D1 | D2 | W0 | W1 |
|---|---|---|---|---|---|---|---|
| 1 | lookup | x | S | S | S | S | S |
| 2 | lookup | x | S | S | S | S | S |
| 3 | lookup | x | S | S | S | S | S |
| 4 | lookup | x raw | x src | x src | x src | x raw | x raw |
| 5 | lookup | S local | x local | x src | x raw/src | S local | S local |
| 6 | lookup | x | S | S | S | S | S |
| 7 | aggregate | x local | S fct | S local | S fct | S local | S local |
| 8 | aggregate | x raw | x src | x src | x src | x raw | x raw |
| 9 | aggregate | S raw | . fct | . fct | . fct | S local | S local |
| 10 | aggregate | x local | x fct | x fct | x local | x local | x local |
| 11 | aggregate | S local | S local | S fct | S local | S local | S local |
| 12 | aggregate | x raw | x local | x local | x local | x raw | x raw |
| 13 | aggregate | S local | S local | S raw | S raw | S local | . int |
| 14 | aggregate | S raw | S local | S local | S local | S raw | S raw |
| 15 | aggregate | x local | x local | x local | x local | x local | x local |
| 16 | aggregate | S local | S local | . fct | . int | S local | S local |
| 17 | layer | x local | . fct | . fct | . fct | S local | S local |
| 18 | layer | x local | S local | S local | x local | S local | S local |
| 19 | layer | x raw | x local | x src | x src | x raw | x raw |
| 20 | layer | x local | . fct | . fct | S local | S local | S local |
| 21 | layer | x local | S fct | S local | S fct | S local | S local |
| 22 | layer | x local | x local | x local | x local | x local | x local |
| 23 | layer | x local | x local | x local | x local | x local | x local |
| 24 | layer | S local | S local | S local | S local | S local | S local |
| 25 | layer | x local | S local | S local | S local | S local | S local |
| 26 | layer | x raw | x local/src | x local/raw | x local | S local | S local |
| 27 | vocabulary | S local | S local | S local | S local | S local | S local |
| 28 | vocabulary | x local | x src | x src | S src | x raw | S src |
| 29 | vocabulary | x raw | S src | S local | S local | S raw | S raw |
| 30 | vocabulary | x local | - | S local | - | S local | S local |
| 31 | vocabulary | x local | S local | S local | x local | S local | S local |
| 32 | vocabulary | x raw | S local/src | S local/src | S local | S local | S local |
| 33 | vocabulary | S local | S local | S local | S local | S local | S local |
| 34 | vocabulary | x local | x local | x local | x local | x raw | x local |
| 35 | join | x raw | S local | S local | S local | S local | S local |
| 36 | join | x raw | S local | S local | - | S local | S local |
| 37 | join | S raw | S local | S src | S local | S raw | S raw |
| 38 | join | x local | - | - | - | S local | S local |
| 39 | join | x local | S local | S local | x local | S local | S local |
| 40 | join | x local | S local/src | S local | S local | S local | S local |
