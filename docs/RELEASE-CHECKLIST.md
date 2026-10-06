# Release checklist (the day the paper is posted)

Sets 4 and 5 are released together with the paper. Each step says who does it.

## Before release day

1. **All runs finished** (operator): Qwen 3.8 27B on set 5 and its runtime-failure retry
   (`work/insurance/set5-qwen.log` ends with "Qwen runtime-failure retries done"); the paper's
   Section 6.1 and Section 8 updated with Qwen.
2. **Reviews done** (author): the blind review of the set-5 disagreements
   (`work/insurance/audit/set5-discordant-review.csv`, then `set5-discordant-key.json`) and the
   Section 6.9 sheet (`analysis/insurance-2026-09-29/taxonomy/taxonomy-review-sheet.csv`); results
   added to the paper. Add the completed discordant sheet's SHA-256 to `docs/SEALING.md`.
3. **Manuscript** (author): author names and affiliations; a final read of the whole paper.
4. **Consent** (author): may the audit sheets name the reviewer? If not, the export writes "author".

## Release day

1. **Verify the sealing** (operator): `python3 scripts/verify-sealing.py` must report no mismatch.
   Only the reviewers' verdict columns may differ from what was sealed (the completed discordant sheet
   is recorded separately in step 2 above).
2. **Release the sets** (operator): remove the "Sealed question sets" lines from `.gitignore`, then
   `python3 scripts/export-results.py --release` (add `--reviewer-consent` only with consent). Commit
   `insurance/heldout/questions-4.json`, `insurance/heldout/questions-5.json`,
   `results/insurance/gold/`, the set-4 and set-5 result folders, and `insurance/audit/` (completed audit
   sheets, adjudications, the discordant review and its key).
3. **Check nothing changed** (operator): re-run the statistics and the paper (docs/REPRODUCE.md, step 2;
   `STATS_SET=5` and `STATS_SET=5 STATS_AS_RECORDED=1` for set 5, `STATS_RUN_SUFFIX=-rep2` and `-rep3`
   for the repeats) and confirm the numbers are identical.
4. **Run archive** (operator builds, author uploads): `python3 scripts/build-run-archive.py` writes
   `work/release/dql-insurance-runs-<date>.tar.zst`. Upload it to Zenodo (author's account), then put
   the DOI in `README.md` and in the paper's data-availability statement.
5. **PDF** (author exports, operator checks): export the final paper to PDF from Google Docs (Pages stops on an import dialog, so automated export fails),
   check equations, figures and tables page by page, and commit it under
   `analysis/insurance-2026-09-29/paper/`.
6. **Push** (operator, on the author's go-ahead): `git fetch origin`, then push `main` to
   github.com/duckcode-ai-labs/dql-benchmarks.
7. **DQL** (author's decision): tag a DQL release that contains builds `49c0e1cb` and `627009a1`
   (both are public as branches `claude/dql-benchmark-final` and `claude/dql-benchmark-final-2`).
8. **arXiv** (author): endorsement for cs.DB if needed; submit the PDF with the metadata in
   `analysis/insurance-2026-09-29/paper/arxiv-metadata.md` (title, abstract, comments, categories).

After posting, the first DQL change made because of anything set 5 showed ends set 5's use as a held-out
set (insurance/PREREGISTRATION-SET5.md).
