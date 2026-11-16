"""Oracle Cloud price list API and Vast.ai marketplace offers."""
from __future__ import annotations

import json
import statistics
import urllib.parse
from collections import defaultdict

from ..common import Row, fetch, gpu_from_text
from ..regions import vast_geo

OCI_API = "https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/?currencyCode=USD"
VAST_API = "https://console.vast.ai/api/v0/bundles/?q="


def oci() -> tuple[list[Row], list[str]]:
    data = fetch(OCI_API, as_json=True)
    rows = []
    for it in data.get("items", []):
        name = it.get("displayName", "")
        if "Compute - GPU" not in name or "Per Hour" not in (it.get("metricName") or ""):
            continue
        gpu = gpu_from_text(name)
        if not gpu:
            continue
        prices = it["currencyCodeLocalizations"][0]["prices"]
        payg = next((p["value"] for p in prices if p.get("model") == "PAY_AS_YOU_GO"), None)
        if not payg:
            continue
        variant = ("GB300 (Grace)" if "GB300" in name else "GB200 (Grace)" if "GB200" in name else
                   "RTX PRO 6000 Server" if gpu == "RTX PRO 6000" else f"HGX {gpu} SXM")
        shape = {"B200": "BM.GPU.B200.8", "B300": "BM.GPU.B300.8"}.get(gpu, "RTX PRO 6000 shapes")
        if "GB" in variant:
            shape = "BM.GPU." + variant.split()[0] + ".4"
        rows.append(Row(gpu=gpu, variant=variant, provider="Oracle Cloud", provider_slug="oracle-cloud",
                        sku=f"{shape} ({it.get('partNumber')})", gpus=1, price_instance_hr=None,
                        price_gpu_hr=float(payg), price_type="on_demand", region="All OCI regions",
                        country="Global", geo="Global", source="oci_price_list_api",
                        source_url="https://www.oracle.com/cloud/price-list/", method="api", confidence="high",
                        notes=f"{name}; OCI uses one price in every commercial region"))
    return rows, ([] if rows else ["no OCI GPU rows matched"])


VAST_NAMES = {"B200": ["B200"], "B300": ["B300"], "RTX PRO 6000": ["RTX PRO 6000 WS", "RTX PRO 6000 S"]}


def vast() -> tuple[list[Row], list[str]]:
    rows, errors = [], []
    for gpu, names in VAST_NAMES.items():
        offers = []
        for n in names:
            q = {"gpu_name": {"eq": n}, "rentable": {"eq": True}, "rented": {"eq": False}, "limit": 500}
            try:
                d = fetch(VAST_API + urllib.parse.quote(json.dumps(q)), as_json=True)
                for o in d.get("offers", []):
                    o["_name"] = n
                    offers.append(o)
            except Exception as e:  # noqa: BLE001
                errors.append(f"vast {n}: {e}")
        by_country = defaultdict(list)
        for o in offers:
            ng = int(o.get("num_gpus") or 0)
            dph = float(o.get("dph_total") or 0)
            if ng <= 0 or dph <= 0:
                continue
            region, country, geo = vast_geo(o.get("geolocation") or "")
            by_country[(country, geo)].append((dph / ng, o, region))
        for (country, geo), lst in by_country.items():
            lst.sort(key=lambda x: x[0])
            best, o, region = lst[0]
            med = statistics.median([x[0] for x in lst])
            rows.append(Row(gpu=gpu, variant=f"{o['_name']} (marketplace host)", provider="Vast.ai",
                            provider_slug="vast-ai", sku=f"{o.get('num_gpus')}x {o['_name']}",
                            gpus=int(o.get("num_gpus")), price_instance_hr=float(o["dph_total"]),
                            price_gpu_hr=best, price_type="on_demand", region=region, country=country, geo=geo,
                            source="vast_api", source_url="https://vast.ai/pricing", method="api",
                            confidence="medium", availability=f"{len(lst)} offers available",
                            notes=f"Lowest of {len(lst)} rentable offers in {country}; median ${med:.2f}/GPU-hr. "
                                  "Marketplace hosts vary in reliability."))
    return rows, errors
