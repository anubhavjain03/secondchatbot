# Daily refresh runbook

The scheduled Claude task follows these steps once a day. Dashboard:
https://claude.ai/artifact/BFDFbfSJ7CksLw65UUeS1n (Data-type artifact; datasets are attached JSON files).

All commands run from `gpu-tracker/` on branch `ccr-900c42fd-off1h5`, or `main` once that branch is merged.

## 1. Get yesterday's history
1. Read the dataset docs with `ArtifactData` `list`, collection `datasets`. Note each doc's `version` and
   `source.url` (`/_blob/<asset id>`). Save `{"<dataset>": <version>, ...}` to `out/versions.json` and
   `{"<dataset>": "<old asset id>", ...}` to `out/old_assets.json`.
2. Download the two cumulative files with the `Artifact` tool: `action: "read"`, `url` = the dashboard,
   `path` = the asset id from `history` and then from `history_providers`. Copy the saved files to
   `out/prev/history.json` and `out/prev/history_providers.json`. If a download fails, continue. History then
   restarts from today, so say so in the summary.

## 2. Collect
`python3 -m tracker.collect`. Every collector should be `ok`. A `failed` collector is not fatal; the
dashboard's health table shows it. If a host is refused by the network, report the host name.

## 3. Refresh the evidence (keep it short: at most 4 web searches)
Search for new public readings: the Silicon Data B200/B300 index, Ornn B200 index, new published B200, B300 or
RTX PRO 6000 reserved/commitment prices, AWS Capacity Blocks price changes, and NVIDIA Rubin availability news.
Add new items to `tracker/research.json` `evidence`. Each needs `id`, `gpu`, `kind`, `date` (the date of the
reading, not today), `claim`, `source_name`, a real `source_url` you saw, and `confidence`. Add `value_gpu_hr`
only for a stated $/GPU-hr figure. Never invent a number or a URL. Update `forecast_assumptions` momentum only if
a newer index trend clearly says so, and write the reason in its `notes`.

## 4. Build
`python3 -m tracker.build`. It writes `out/files/*.json` (8 files) and prints the private estimates.
Sanity check: B200 on-demand median should be within roughly $2-$20/GPU-hr. If a number jumps more than 50%
from yesterday, look at the rows behind it before publishing.

## 5. Publish
1. Upload each of the 8 files in `out/files/` with the `Artifact` tool: `url` = dashboard, `asset: true`,
   `file_path` = the file. JSON files go one per call. Record the new ids in `out/new_assets.json`.
2. `python3 -m tracker.publish_plan` prints the batch `writes`. Send them with `ArtifactData` `action: "batch"`.
   If a version conflict is reported, re-list `datasets`, rewrite `out/versions.json` and retry once.
3. Delete each old asset in `out/old_assets.json` that no dataset now names: `Artifact` `action: "delete"`,
   `url` = dashboard, `path` = old asset id. Only delete ids from `out/old_assets.json`.

## 6. Save code changes
If `tracker/research.json` changed, commit it with a one-line message and push the branch.

## 7. Report
Reply with one short summary: rows collected, provider count, collector statuses, the three global
on-demand medians, and any failures.
