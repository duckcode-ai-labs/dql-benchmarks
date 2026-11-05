# Ranking inside a large area (design study, 2026-11-05)

For `AI-Agents/docs/ask-area-ranking-design-2026-11-05.md`. No AI calls except the stand-in AI pick.

1. `python3 -I gitlab/rank/steps.py > work/gitlab/rank-steps.json`
   Pulls each Z4 question's schema step (title, tables shown, catalog-search picks, columns read) from the stored runs (Z4, Z4-fill, Z4-fill2).
2. `python3 -I gitlab/rank/rank.py <gitlab-z4 dql dir> [--no-anchors] [--questions gitlab/rank/reworded-questions.json]`
   Rebuilds Ask's routing (model-routing.ts at zlens main ffc48804), then ranks the gold table inside the chosen area: today's order against word-score (BM25) variants.
3. `python3 -I gitlab/rank/oracle.py <gitlab-z4 dql dir> prepare|score work/gitlab/oracle`
   Gives the gold table's own area (more than 30 tables), then compares the word score with an AI pick from the area's one-line index (`table-index.ts` format and prompt).

`reworded-questions.json` holds the 40 questions reworded by an agent that saw only the questions, plus, for each, the words of its gold tables' names and columns to avoid. It is the worst case: no question uses the tables' own words.
