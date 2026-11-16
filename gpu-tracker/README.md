# Blackwell GPU Price Tracker

A daily tracker of public cloud prices for NVIDIA **B200**, **B300** and **RTX PRO 6000**. It covers
on-demand, spot, AWS Capacity Blocks, published reserved rates, an estimate of the best private (negotiated)
rate, and a 12-month forecast. Results show on a Claude Data dashboard:
https://claude.ai/artifact/BFDFbfSJ7CksLw65UUeS1n

## Sources (all public, no keys)
| Collector | What it reads |
|---|---|
| `aws_on_demand` | AWS public price JSON per region (p6-b200, p6-b300, g7e) |
| `aws_capacity_blocks` | AWS EC2 Capacity Blocks for ML pricing page |
| `azure_retail_api` | Azure Retail Prices API (GB200 and RTX PRO 6000 VMs: on-demand, spot, 1- and 3-year reservations) |
| `oci_price_list` | Oracle Cloud price list API |
| `vast_marketplace` | Vast.ai public offers API (cheapest and median per country) |
| `getdeploying_aggregator` | getdeploying.com GPU pages (about 60 neoclouds, marketplaces and serverless platforms) |
| `silicondata_index` | Silicon Data public index pages (B200, B300, H100 rental indices) |

Hand-curated evidence (index readings, published commitment prices, press) lives in `tracker/research.json`.

## Run it
```
cd gpu-tracker
python3 -m tracker.collect   # -> out/rows.json, out/signals.json, out/runs.json
python3 -m tracker.build     # -> out/files/*.json (dashboard datasets)
```
Python 3.10+ with the standard library only. The daily publish steps are in `tracker/RUNBOOK.md`.

## Method notes
- Prices are USD per GPU-hour. Duplicate SKUs are collapsed to the cheapest per provider, region, term and size.
  Summary numbers count each provider once, at its cheapest offer.
- **Private estimate**: the 35th percentile of providers' published reserved rates (6 months or longer) plus index
  and commitment evidence. The range runs from the lowest credible rate to the 25th percentile of on-demand. It is
  an estimate, not an observed price.
- **Forecast**: monthly log-price drift is an analog depreciation rate plus decaying momentum (3-month half-life).
  The range widens with the square root of the horizon. After 30 days of history, the tracker's own trend
  supplies half the momentum. Assumptions are in `research.json`.
- GB200 and GB300 (Grace) systems are grouped under B200 and B300, with the variant shown.
- Azure RTX PRO 6000 GPU counts per VM size are inferred, and fractional sizes are skipped.
