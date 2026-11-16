"""Azure Retail Prices API (public, no auth)."""
from __future__ import annotations

import re
import urllib.parse

from ..common import Row, fetch
from ..regions import azure_geo

API = "https://prices.azure.com/api/retail/prices"
FILTER = ("serviceName eq 'Virtual Machines' and (contains(productName,'GB200') or contains(productName,'B200') "
          "or contains(productName,'B300') or contains(productName,'RTX6k') or contains(productName,'RTX6K'))")


def _gpus_for(sku: str) -> tuple[str, int, str] | None:
    s = sku.upper()
    if "GB300" in s:
        return ("B300", 4, "GB300 (Grace)")
    if "GB200" in s:
        return ("B200", 4, "GB200 (Grace)")  # ND GB200 v6: 4 Blackwell GPUs per VM
    if "RTXPRO6000" in s:
        m = re.search(r"NC(\d+)L?DS", s)
        vcpu = int(m.group(1)) if m else 0
        # Only sizes whose GPU count we can infer from price ratios / aggregator listings.
        if vcpu in (128, 132, 144):
            return ("RTX PRO 6000", 1, "RTX PRO 6000 Server")
        if vcpu in (256, 264, 288):
            return ("RTX PRO 6000", 2, "RTX PRO 6000 Server")
        return None  # fractional or unknown sizes skipped
    return None


def collect() -> tuple[list[Row], list[str]]:
    rows, errors = [], []
    url = API + "?" + urllib.parse.urlencode({"$filter": FILTER})
    pages = 0
    while url and pages < 40:
        data = fetch(url, as_json=True)
        pages += 1
        for it in data.get("Items", []):
            if "Windows" in it.get("productName", "") or it.get("type") == "DevTestConsumption":
                continue
            g = _gpus_for(it.get("armSkuName", ""))
            if not g or it.get("unitOfMeasure") != "1 Hour" or it.get("currencyCode") != "USD":
                continue
            gpu, n, variant = g
            price = float(it.get("retailPrice") or 0)
            if price <= 0:
                continue
            term = None
            ptype = "on_demand"
            if it.get("type") == "Reservation":
                years = 3 if "3" in (it.get("reservationTerm") or "") else 1
                term = 12 * years
                price = price / (8760 * years)  # reservation price is for the whole term
                ptype = "reserved"
            elif "Spot" in it.get("skuName", ""):
                ptype = "spot"
            elif "Low Priority" in it.get("skuName", ""):
                continue
            region = it.get("armRegionName", "")
            rows.append(Row(gpu=gpu, variant=variant, provider="Microsoft Azure", provider_slug="microsoft-azure",
                            sku=it["armSkuName"], gpus=n, price_instance_hr=price, price_gpu_hr=price / n,
                            price_type=ptype, term_months=term, region=region, country=it.get("location", ""),
                            geo=azure_geo(region), source="azure_retail_api",
                            source_url="https://azure.microsoft.com/pricing/details/virtual-machines/linux/",
                            method="api", confidence="high" if "GB200" in it["armSkuName"] else "medium",
                            interconnect="NVLink + InfiniBand" if "GB" in it["armSkuName"] else "",
                            notes="Linux retail price" + (" (GPU count inferred from VM size)" if gpu == "RTX PRO 6000" else "")))
        url = data.get("NextPageLink")
    return rows, errors
