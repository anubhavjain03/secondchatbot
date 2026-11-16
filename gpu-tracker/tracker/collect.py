"""Run every structured collector and write out/rows.json + out/runs.json.

Usage (from gpu-tracker/):  python -m tracker.collect
"""
from __future__ import annotations

import json
import time
import traceback
from pathlib import Path

from .common import now_iso, today
from .sources import aws, azure, getdeploying, indices, misc

OUT = Path(__file__).resolve().parent.parent / "out"

COLLECTORS = {
    "aws_on_demand": aws.on_demand,
    "aws_capacity_blocks": aws.capacity_blocks,
    "azure_retail_api": azure.collect,
    "oci_price_list": misc.oci,
    "vast_marketplace": misc.vast,
    "getdeploying_aggregator": getdeploying.collect,
}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    all_rows, health = [], {}
    for name, fn in COLLECTORS.items():
        t0 = time.time()
        try:
            rows, errors = fn()
            status = "ok" if rows and not errors else ("partial" if rows else "failed")
            all_rows.extend(r.to_dict() for r in rows)
            health[name] = {"status": status, "rows": len(rows), "errors": errors[:5],
                            "seconds": round(time.time() - t0, 1)}
        except Exception as e:  # noqa: BLE001
            health[name] = {"status": "failed", "rows": 0, "errors": [f"{e}"],
                            "trace": traceback.format_exc()[-600:], "seconds": round(time.time() - t0, 1)}
        print(f"{name:26s} {health[name]['status']:8s} rows={health[name]['rows']}")
    t0 = time.time()
    try:
        sig, errs = indices.collect()
        health["silicondata_index"] = {"status": "ok" if sig and not errs else ("partial" if sig else "failed"),
                                       "rows": len(sig), "errors": errs[:5], "seconds": round(time.time() - t0, 1)}
    except Exception as e:  # noqa: BLE001
        sig, health["silicondata_index"] = [], {"status": "failed", "rows": 0, "errors": [str(e)], "seconds": 0}
    print(f"{'silicondata_index':26s} {health['silicondata_index']['status']:8s} rows={len(sig)}")
    (OUT / "signals.json").write_text(json.dumps(sig, indent=1))
    (OUT / "rows.json").write_text(json.dumps(all_rows, indent=1))
    (OUT / "runs.json").write_text(json.dumps({"date": today(), "collected_at": now_iso(),
                                               "collectors": health}, indent=1))
    print(f"total rows: {len(all_rows)} -> {OUT/'rows.json'}")


if __name__ == "__main__":
    main()
