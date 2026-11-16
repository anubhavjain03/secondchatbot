"""Turn collected rows + research into the artifact database documents for one day.

Inputs : out/rows.json, out/signals.json, out/runs.json, tracker/research.json,
         out/prev/history.json, out/prev/history_providers.json (yesterday's published files, optional)
Outputs: out/files/<dataset>.json  ({rows, meta}) — one file per dashboard dataset, uploaded as assets
Usage  : python -m tracker.build
"""
from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .common import GPUS, today
from .regions import GEOS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
FILES = OUT / "files"
KEEP = ["gpu", "variant", "provider", "provider_slug", "category", "sku", "gpus", "price_instance_hr",
        "price_gpu_hr", "price_type", "term_months", "region", "country", "geo", "availability",
        "interconnect", "source", "source_url", "method", "confidence", "notes", "observed_at"]


def pct(vals: list[float], q: float) -> float:
    v = sorted(vals)
    if not v:
        return float("nan")
    k = (len(v) - 1) * q
    f, c = math.floor(k), math.ceil(k)
    return v[f] if f == c else v[f] + (v[c] - v[f]) * (k - f)


def dedupe(rows: list[dict]) -> list[dict]:
    """Keep the cheapest row per provider/gpu/type/region/term/size so huge SKU matrices don't dominate."""
    best: dict[tuple, dict] = {}
    for r in rows:
        if r.get("price_gpu_hr") in (None, 0):
            continue
        k = (r["provider_slug"], r["gpu"], r["variant"], r["price_type"], r["region"], r.get("term_months"), r["gpus"])
        if k not in best or r["price_gpu_hr"] < best[k]["price_gpu_hr"]:
            best[k] = r
    return [{f: r.get(f) for f in KEEP} for r in best.values()]


def drop_outliers(rows: list[dict]) -> list[dict]:
    """Drop rows below 25% of the gpu/type median (usually fractional-GPU or mislabeled listings)."""
    groups = defaultdict(list)
    for r in rows:
        groups[(r["gpu"], r["price_type"])].append(r["price_gpu_hr"])
    med = {k: statistics.median(v) for k, v in groups.items()}
    keep = []
    for r in rows:
        m = med[(r["gpu"], r["price_type"])]
        if r["price_gpu_hr"] >= 0.25 * m:
            keep.append(r)
        else:
            r["notes"] = (r.get("notes") or "") + " [excluded: below 25% of median, likely fractional/mislabeled]"
    return keep


def private_estimates(rows: list[dict], evidence: list[dict], d: str) -> tuple[list[dict], list[dict]]:
    """Estimate the best private (negotiated) $/GPU-hr per gpu, globally and per geo with enough data."""
    est_rows, detail = [], []
    for gpu in GPUS:
        ev = [e for e in evidence if e.get("gpu") == gpu and e.get("value_gpu_hr")]
        for geo in ["Global"] + [g for g in GEOS if g != "Global"]:
            sel = [r for r in rows if r["gpu"] == gpu and (geo == "Global" or r["geo"] == geo)]
            res = per_provider_min([r for r in sel if r["price_type"] == "reserved" and (r.get("term_months") or 12) >= 6
                                    and r["category"] != "marketplace"])
            od = per_provider_min([r for r in sel if r["price_type"] == "on_demand"
                                   and r["category"] in ("neocloud", "hyperscaler")])
            mkt = per_provider_min([r for r in sel if r["category"] == "marketplace" and r["price_type"] == "on_demand"])
            commit_ev = [e["value_gpu_hr"] for e in ev if e["kind"] in ("published_commit", "index")] if geo == "Global" else []
            if geo != "Global" and len(res) < 2:
                continue
            if not (res or od):
                continue
            pool = sorted(res + commit_ev)
            if pool:
                base = pct(pool, 0.35)
                method = f"35th percentile of published reserved rates from {len(res)} providers" + (
                    f" + {len(commit_ev)} index/commit evidence points" if commit_ev else "")
            else:
                base = 0.65 * statistics.median(od)
                method = "65% of median neocloud/hyperscaler on-demand (no reserved data)"
            lows = pool + [e.get("low_gpu_hr") for e in ev if e.get("low_gpu_hr")] + (mkt if geo == "Global" else [])
            low = max(min(lows) if lows else base * 0.8, 0.45 * base)
            high = min(pct(od, 0.25) if od else base * 1.3, base * 1.6)
            high = max(high, base)
            conf = "medium" if len(res) >= 5 else "low"
            detail.append({"gpu": gpu, "geo": geo, "base": round(base, 3), "low": round(low, 3), "high": round(high, 3),
                           "n_reserved": len(res), "n_on_demand": len(od), "n_evidence": len(commit_ev),
                           "method": method, "confidence": conf})
            est_rows.append({"gpu": gpu, "variant": "All variants", "provider": "Market estimate",
                             "provider_slug": "estimate", "category": "estimate", "sku": "Best private rate (est.)",
                             "gpus": 8, "price_instance_hr": None, "price_gpu_hr": round(base, 4),
                             "price_type": "private_estimate", "term_months": 12, "region": geo, "country": "",
                             "geo": geo, "availability": "", "interconnect": "", "source": "estimate",
                             "source_url": "", "method": "estimate", "confidence": conf,
                             "notes": f"Range ${low:.2f}-${high:.2f}. {method}.", "observed_at": d})
    return est_rows, detail


def per_provider_min(rows: list[dict]) -> list[float]:
    """One value per provider (its cheapest), so providers with many regions/SKUs don't dominate."""
    m: dict[str, float] = {}
    for r in rows:
        v = r["price_gpu_hr"]
        if r["provider"] not in m or v < m[r["provider"]]:
            m[r["provider"]] = v
    return sorted(m.values())


def aggregate(rows: list[dict]) -> tuple[dict, dict]:
    """min / median across providers (each provider counted once at its cheapest) per gpu|type|geo."""
    agg, prov = defaultdict(dict), defaultdict(list)
    for r in rows:
        geos = {r["geo"]} if r["price_type"] == "private_estimate" else {"Global", r["geo"]}
        for geo in geos:
            d = agg[f"{r['gpu']}|{r['price_type']}|{geo}"]
            v = r["price_gpu_hr"]
            if r["provider"] not in d or v < d[r["provider"]]:
                d[r["provider"]] = v
        prov[f"{r['gpu']}|{r['price_type']}|{r['provider']}"].append(r["price_gpu_hr"])
    a = {k: {"min": round(min(v.values()), 3), "median": round(statistics.median(v.values()), 3), "n": len(v)}
         for k, v in agg.items()}
    p = {k: round(min(v), 3) for k, v in prov.items()}
    return a, p


def load_prev(name: str) -> list[dict]:
    """Rows of a previously published dataset file, saved to out/prev/<name>.json by the daily run."""
    f = OUT / "prev" / f"{name}.json"
    if not f.exists():
        return []
    try:
        j = json.loads(f.read_text())
        return j.get("rows", j) if isinstance(j, dict) else j
    except Exception:  # noqa: BLE001
        return []


def forecast(agg: dict, history: dict, assumptions: dict, d: str) -> dict:
    """Monthly low/base/high for 12 months, per gpu x price type x geo (series with a current level)."""
    out = {}
    t0 = date.fromisoformat(d)
    for key, cur in agg.items():
        gpu, ptype, geo = key.split("|")
        if ptype not in ("on_demand", "capacity_block", "private_estimate", "reserved"):
            continue
        a = assumptions.get(gpu, {})
        analog, mom, sig = a.get("analog_monthly", -0.02), a.get("momentum_monthly", 0.0), a.get("sigma_monthly", 0.07)
        level = cur["median"]
        # Own-history momentum once we have >= 30 days for this series.
        pts = sorted(history.get(key, []))
        used_hist = False
        if len(pts) >= 2:
            first_d, first_v = pts[0]
            days = (t0 - date.fromisoformat(first_d)).days
            if days >= 30 and first_v > 0:
                hist_m = math.log(level / first_v) / (days / 30.4)
                mom = 0.5 * mom + 0.5 * max(min(hist_m, 0.15), -0.15)
                used_hist = True
        pts_out, logp = [], math.log(level)
        for h in range(1, 13):
            logp += analog + mom * 0.5 ** ((h - 1) / 3)
            spread = sig * math.sqrt(h) + abs(mom) * 0.5
            m = (t0.month - 1 + h)
            mdate = f"{t0.year + m // 12}-{m % 12 + 1:02d}"
            pts_out.append({"month": mdate, "h": h, "base": round(math.exp(logp), 3),
                            "low": round(math.exp(logp - spread), 3), "high": round(math.exp(logp + spread), 3)})
        out[key] = {"current": level, "points": pts_out, "analog_monthly": analog,
                    "momentum_monthly": round(mom, 4), "own_history": used_hist, "n_now": cur["n"]}
    return out


PT_LABEL = {"on_demand": "On-demand", "spot": "Spot / interruptible", "capacity_block": "Capacity block",
            "reserved": "Reserved (published)", "private_estimate": "Best private (estimated)"}


def write_file(name: str, rows: list[dict], meta: list[dict]) -> Path:
    FILES.mkdir(parents=True, exist_ok=True)
    p = FILES / f"{name}.json"
    p.write_text(json.dumps({"rows": rows, "meta": meta}, separators=(",", ":")))
    return p


def main() -> None:
    d = today()
    rows_raw = json.loads((OUT / "rows.json").read_text())
    signals = json.loads((OUT / "signals.json").read_text()) if (OUT / "signals.json").exists() else []
    runs = json.loads((OUT / "runs.json").read_text())
    research = json.loads((ROOT / "tracker" / "research.json").read_text())
    rows = drop_outliers(dedupe(rows_raw + research.get("rows", [])))
    est_rows, est_detail = private_estimates(rows, research.get("evidence", []), d)
    rows_all = sorted(rows + est_rows, key=lambda r: (r["gpu"], r["price_type"], r["price_gpu_hr"]))
    for i, r in enumerate(rows_all):
        r["id"] = f"r{i:04d}"
        r["price_type_label"] = PT_LABEL.get(r["price_type"], r["price_type"])
    agg, prov = aggregate(rows_all)

    hist_rows = [h for h in load_prev("history") if h.get("date") != d]
    hist_rows += [{"date": d, "key": k, "gpu": k.split("|")[0], "price_type": k.split("|")[1],
                   "geo": k.split("|")[2], **v} for k, v in agg.items()]
    hist_rows.sort(key=lambda h: (h["key"], h["date"]))
    series = defaultdict(list)
    for h in hist_rows:
        if h["date"] != d:
            series[h["key"]].append((h["date"], h["median"]))
    prov_rows = [h for h in load_prev("history_providers") if h.get("date") != d]
    prov_rows += [{"date": d, "gpu": k.split("|")[0], "price_type": k.split("|")[1], "provider": k.split("|")[2],
                   "min": v} for k, v in prov.items()]
    cutoff = (date.fromisoformat(d) - timedelta(days=120)).isoformat()   # provider detail: keep ~4 months
    prov_rows = [h for h in prov_rows if h["date"] >= cutoff]
    for h in prov_rows:
        h["id"] = f"{h['date']}|{h['gpu']}|{h['price_type']}|{h['provider']}"

    fc = forecast(agg, series, research.get("forecast_assumptions", {}), d)
    fc_rows = []
    for key, s in fc.items():
        gpu, ptype, geo = key.split("|")
        base = {"key": key, "gpu": gpu, "price_type": ptype, "geo": geo, "analog_monthly": s["analog_monthly"],
                "momentum_monthly": s["momentum_monthly"], "own_history": s["own_history"], "n_now": s["n_now"]}
        fc_rows.append({**base, "id": f"{key}|0", "month": d[:7], "h": 0, "low": s["current"], "base": s["current"],
                        "high": s["current"]})
        for p in s["points"]:
            fc_rows.append({**base, "id": f"{key}|{p['h']}", **p})

    ev_rows = []
    for e in research.get("evidence", []):
        ev_rows.append({"id": e["id"], "gpu": e["gpu"], "kind": e["kind"], "date": e["date"],
                        "value_gpu_hr": e.get("value_gpu_hr"), "claim": e["claim"], "source_name": e["source_name"],
                        "source_url": e["source_url"], "confidence": e["confidence"]})
    for sgl in signals:
        ev_rows.append({"id": "live-" + sgl["gpu"].lower(), "gpu": sgl["gpu"], "kind": "index (live)",
                        "date": d, "value_gpu_hr": sgl["value"],
                        "claim": f"{sgl['index']}: ${sgl['value']:.2f}/GPU-hr (page updated {sgl['as_of']}; "
                                 f"7-day move {sgl['change_7d_abs_pct']}%).",
                        "source_name": "Silicon Data index page", "source_url": sgl["source_url"],
                        "confidence": "medium"})
    for i, e in enumerate(est_detail):
        e["id"] = f"{e['gpu']}|{e['geo']}"
    health_rows = [{"id": k, "collector": k, "status": v["status"], "rows": v["rows"],
                    "errors": "; ".join(v.get("errors") or [])[:300], "seconds": v.get("seconds")}
                   for k, v in (runs.get("collectors") or {}).items()]
    drivers = [{"id": f"d{i}", **x} for i, x in enumerate(research.get("drivers", []))]
    assumptions = [{"id": g, "gpu": g, **{k: v for k, v in a.items()}}
                   for g, a in research.get("forecast_assumptions", {}).items() if not g.startswith("_")]

    for f in FILES.glob("*.json") if FILES.exists() else []:
        f.unlink()
    built = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    m = [{"label": "Built", "value": built}, {"label": "Collected", "value": runs.get("collected_at") or ""},
         {"label": "Code", "value": "gpu-tracker/tracker in github.com/anubhavjain03/secondchatbot"}]
    write_file("prices", rows_all, m + [{"label": "Rows before de-duplication", "value": str(len(rows_raw))}])
    write_file("history", hist_rows, m + [{"label": "Method", "value": "min / median across providers (each provider at its cheapest) per GPU, price type and geography, one row per day"}])
    write_file("history_providers", prov_rows, m)
    write_file("forecast", fc_rows, m + [{"label": "Method", "value": "log-price drift = analog depreciation + decaying momentum (3-month half-life); band = sigma*sqrt(months). See tracker/build.py forecast()."}])
    write_file("private", est_detail, m + [{"label": "Method", "value": "35th percentile of providers' published reserved rates (>=6 months) plus index/commit evidence; range from the lowest credible rate to the 25th percentile of on-demand. See tracker/build.py private_estimates()."}])
    write_file("evidence", ev_rows, m)
    write_file("health", health_rows, m)
    write_file("drivers", drivers + [{"id": "a-" + a["gpu"], "direction": "assumption",
                                      "text": f"{a['gpu']}: analog {a['analog_monthly']*100:+.1f}%/mo, momentum "
                                              f"{a['momentum_monthly']*100:+.1f}%/mo, sigma {a['sigma_monthly']*100:.0f}%. {a['notes']}"}
                                     for a in assumptions], m)
    providers = sorted({r["provider"] for r in rows})
    sizes = {p.name: p.stat().st_size for p in FILES.glob("*.json")}
    print(f"{len(rows_all)} rows ({len(rows_raw)} raw), {len(providers)} providers; files: {sizes}")
    for e in est_detail:
        if e["geo"] == "Global":
            print(f"  private est {e['gpu']:13s} ${e['low']:.2f} / ${e['base']:.2f} / ${e['high']:.2f}  ({e['method']})")


if __name__ == "__main__":
    main()
