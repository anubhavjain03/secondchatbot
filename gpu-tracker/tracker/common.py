"""Shared helpers: HTTP fetch, row schema, GPU naming, provider categories."""
from __future__ import annotations

import gzip
import json
import time
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

UA = "gpu-price-tracker/1.0 (personal research; public pricing only)"

GPUS = ["B200", "B300", "RTX PRO 6000"]
PRICE_TYPES = ["on_demand", "spot", "capacity_block", "reserved", "private_estimate"]

HYPERSCALERS = {"aws", "microsoft-azure", "google-cloud", "oracle-cloud"}
MARKETPLACES = {"vast-ai", "lium", "spheron", "runcrate", "gpuaas", "openrelay", "tensordock",
                "sf-compute", "shadeform", "prime-intellect", "akash", "gpu-ai", "voltagegpu",
                "ecohash", "gpuhub", "packet-ai", "cloudzy"}
SERVERLESS = {"beam", "cerebrium", "fal-ai", "modal", "koyeb", "huggingface", "baseten",
              "replicate", "lightning-ai", "daytona", "geodd", "enverge"}


def category(slug: str) -> str:
    if slug in HYPERSCALERS:
        return "hyperscaler"
    if slug in MARKETPLACES:
        return "marketplace"
    if slug in SERVERLESS:
        return "serverless"
    return "neocloud"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def fetch(url: str, *, timeout: int = 60, retries: int = 3, as_json: bool = False):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
            if body[:2] == b"\x1f\x8b":
                body = gzip.decompress(body)
            text = body.decode("utf-8", "replace")
            return json.loads(text) if as_json else text
        except Exception as e:  # noqa: BLE001 - surface any network/parse failure to run health
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"fetch failed for {url}: {last}")


@dataclass
class Row:
    gpu: str                      # B200 | B300 | RTX PRO 6000
    variant: str                  # e.g. "HGX B200 SXM", "GB200 (Grace)", "RTX PRO 6000 Server"
    provider: str                 # display name
    provider_slug: str
    sku: str
    gpus: int
    price_instance_hr: float | None
    price_gpu_hr: float | None
    price_type: str               # one of PRICE_TYPES
    region: str                   # provider's own region label
    country: str
    geo: str                      # normalized geography (regions.py)
    source: str                   # collector name
    source_url: str
    method: str                   # api | page | aggregator | research | estimate
    confidence: str               # high | medium | low
    term_months: int | None = None
    availability: str = ""
    interconnect: str = ""
    notes: str = ""
    observed_at: str = field(default_factory=now_iso)
    category: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        if not d["category"]:
            d["category"] = category(self.provider_slug)
        for k in ("price_instance_hr", "price_gpu_hr"):
            if d[k] is not None:
                d[k] = round(float(d[k]), 4)
        return d


def gpu_from_text(t: str) -> str | None:
    s = t.upper().replace("-", " ")
    if "RTX PRO 6000" in s or "RTXPRO6000" in s.replace(" ", "") or "RTX6K" in s.replace(" ", ""):
        return "RTX PRO 6000"
    if "B300" in s:
        return "B300"
    if "B200" in s:
        return "B200"
    return None
