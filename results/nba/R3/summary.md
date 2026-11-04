| Arm | Exactly right | Right in substance | Refused | Gold's tables shown | Path | Wrong layer and wrong | Read a deprecated table |
|---|---|---|---|---|---|---|---|
| R3 DM | 13 | 38 | 2 | 37 of 40 | chosen 40 | 0 [] | 0 [] |
| R2 D0 | 10 | 34 | 2 | 26 of 40 | chosen 40 | 3 [17, 20, 28] | 8 [7, 10, 17, 20, 21, 29, 32, 40] |
| R1 D0 | 12 | 35 | 2 | 27 of 40 | chosen 40 | 3 [9, 17, 20] | 9 [7, 9, 10, 17, 20, 21, 26, 32, 40] |
| R1 W0 | 10 | 40 | 0 | 40 of 40 | whole 40 | 0 [] | 0 [] |

| DM against | Exactly right: only other / only DM, p | In substance: only other / only DM, p |
|---|---|---|
| R2 D0 | 0 / 3, p = 0.25 | 1 / 5, p = 0.22 |
| R1 D0 | 1 / 2, p = 1.00 | 1 / 4, p = 0.38 |
| R1 W0 | 0 / 3, p = 0.25 | 2 / 0, p = 0.50 |

Routes / trust
  R3 DM: {'generated_answer / review_required': 38, 'generated_answer / blocked': 2}
  R2 D0: {'generated_answer / review_required': 37, 'generated_answer / blocked': 3}
  R1 D0: {'generated_answer / review_required': 37, 'generated_answer / blocked': 3}
  R1 W0: {'generated_answer / review_required': 40}

Per question: R3 DM vs R2 D0 (S = in substance, x = exactly too, . wrong, - none), layers read
  q9: R3 DM: S local ['local_player_season_facts'] | R2 D0: S local ['local_player_season_facts'] | R1 D0: . fct ['fct_player_journey'] | R1 W0: S local ['local_player_game_facts']
  q16: R3 DM: S local ['local_player_season_facts'] | R2 D0: S local ['local_player_season_facts'] | R1 D0: S local ['local_player_season_facts'] | R1 W0: S local ['local_player_game_facts']
  q17: R3 DM: x local ['local_player_season_facts'] | R2 D0: . fct ['fct_player_journey'] | R1 D0: . fct ['fct_player_journey'] | R1 W0: S local ['local_player_game_facts']
  q20: R3 DM: S local ['local_player_season_facts'] | R2 D0: . fct ['fct_player_journey'] | R1 D0: . fct ['fct_player_journey'] | R1 W0: S local ['local_player_game_facts']
  q24: R3 DM: S local ['local_player_game_facts'] | R2 D0: S local ['local_player_season_facts'] | R1 D0: S local ['local_player_season_facts'] | R1 W0: S local ['local_player_game_facts']

DM and R2 D0 differ (in substance) on {17: 'DM', 20: 'DM', 28: 'DM', 37: 'D0', 38: 'DM', 39: 'DM'}
