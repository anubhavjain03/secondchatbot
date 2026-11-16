"""Write the ArtifactData batch that points each dashboard dataset at its newly uploaded file.

Inputs : out/new_assets.json  {"prices": "<32-hex asset id>", ...}   (from today's uploads)
         out/versions.json    {"prices": <version int>, ...}         (from ArtifactData list of "datasets")
Output : out/store/upd__<id>.json per dataset, and prints the `writes` array for ArtifactData action "batch".
Usage  : python -m tracker.publish_plan
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "out"
DATASETS = ["prices", "history", "history_providers", "forecast", "private", "evidence", "health", "drivers"]


def main() -> None:
    assets = json.loads((OUT / "new_assets.json").read_text())
    versions = json.loads((OUT / "versions.json").read_text())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (OUT / "store").mkdir(exist_ok=True)
    writes = []
    for ds in DATASETS:
        if ds not in assets:
            continue
        aid = assets[ds]
        assert len(aid) == 32 and all(c in "0123456789abcdef" for c in aid), f"bad asset id for {ds}: {aid}"
        body = {"source": {"url": f"/_blob/{aid}"},
                "updated": {"at": now, "by": "Daily collector run (Claude scheduled task)"},
                "edit": {"via": "claude", "at": now}}
        p = OUT / "store" / f"upd__{ds}.json"
        p.write_text(json.dumps(body))
        w = {"op": "update", "collection": "datasets", "doc_id": ds, "file_path": str(p)}
        if ds in versions:
            w["if_version"] = int(versions[ds])
        writes.append(w)
    print(json.dumps(writes))


if __name__ == "__main__":
    main()
