# Release checklist (the day the paper is posted)

1. Tag the DQL release that contains builds `49c0e1cb` and `627009a1` and record it in
   `insurance/PREREGISTRATION-SET5.md` only if it is the build frozen for set 5 (otherwise record that
   build separately; the pre-registration text itself does not change).
2. Remove the set-4 lines from `.gitignore`, then:
   `python3 scripts/export-results.py --release` and commit `insurance/heldout/questions-4.json`,
   `results/insurance/{fl4,ag4,ag4m}-sonnet55/` and the completed set-4 audit sheet
   (`insurance/audit/set4-audit-completed.csv`, reviewer name only with consent).
3. Re-run the statistics and the paper (docs/REPRODUCE.md, step 2) and check nothing changed.
4. Build the run archive: `work/insurance/runs/<run>/*/<set>/{report.json,evals.yml,cassettes/,project/.dql/local/agent-runs.sqlite}`
   for every run in the paper, as a .tar.zst; upload to Zenodo and put the DOI in README.md and the paper.
5. Add the posted PDF under `analysis/insurance-2026-09-29/paper/`.
6. Make the GitHub repository public.

Set 5 stays sealed until its pre-registered run is reported; then repeat steps 2–6 for set 5.
