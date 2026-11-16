"""AWS: public on-demand price JSON (per region) + EC2 Capacity Blocks pricing page."""
from __future__ import annotations

import json
import re
import urllib.parse

from ..common import Row, fetch, gpu_from_text
from ..regions import AWS_LOCATIONS

OD_URL = ("https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/"
          "ec2-ondemand-without-sec-sel/{loc}/Linux/index.json")
CB_URL = "https://aws.amazon.com/ec2/capacityblocks/pricing/"

# instance type -> (gpu, gpus per instance, variant, interconnect)
INSTANCES = {
    "p6-b200.48xlarge": ("B200", 8, "HGX B200 SXM", "NVLink + 3.2 Tbps EFA"),
    "p6-b300.48xlarge": ("B300", 8, "HGX B300 SXM", "NVLink + 6.4 Tbps EFA"),
    "g7e.2xlarge": ("RTX PRO 6000", 1, "RTX PRO 6000 Server", "50 Gbps"),
    "g7e.4xlarge": ("RTX PRO 6000", 1, "RTX PRO 6000 Server", "50 Gbps"),
    "g7e.8xlarge": ("RTX PRO 6000", 1, "RTX PRO 6000 Server", "100 Gbps"),
    "g7e.12xlarge": ("RTX PRO 6000", 2, "RTX PRO 6000 Server", "400 Gbps"),
    "g7e.24xlarge": ("RTX PRO 6000", 4, "RTX PRO 6000 Server", "800 Gbps"),
    "g7e.48xlarge": ("RTX PRO 6000", 8, "RTX PRO 6000 Server", "1600 Gbps"),
}


def on_demand() -> tuple[list[Row], list[str]]:
    rows, errors = [], []
    for loc, (code, geo) in AWS_LOCATIONS.items():
        url = OD_URL.format(loc=urllib.parse.quote(loc))
        try:
            data = fetch(url, as_json=True, retries=1, timeout=40)
        except Exception as e:  # many locations have no file; that's fine
            if "404" not in str(e) and "403" not in str(e):
                errors.append(f"{loc}: {e}")
            continue
        for _, items in data.get("regions", {}).items():
            for _, v in items.items():
                it = v.get("Instance Type")
                if it not in INSTANCES:
                    continue
                gpu, n, variant, ic = INSTANCES[it]
                price = float(v["price"])
                if price <= 0:
                    continue
                rows.append(Row(gpu=gpu, variant=variant, provider="AWS", provider_slug="aws", sku=it, gpus=n,
                                price_instance_hr=price, price_gpu_hr=price / n, price_type="on_demand",
                                region=code, country=loc, geo=geo, source="aws_price_json",
                                source_url="https://aws.amazon.com/ec2/pricing/on-demand/", method="api",
                                confidence="high", interconnect=ic,
                                notes=f"Linux on-demand, {v.get('vCPU')} vCPU, {v.get('Memory')}"))
    return rows, errors


def capacity_blocks() -> tuple[list[Row], list[str]]:
    html = fetch(CB_URL)
    rows, errors = [], []
    # The page embeds tables as JSON strings: "itemHeading":"P6-B300 Pricing" ... "itemTableData":"[...]"
    for m in re.finditer(r'"itemTableData":"(\[.*?\])","dark"[^}]*?"itemHeading":"([^"]+)"', html):
        heading = m.group(2)
        try:
            table = json.loads(m.group(1).encode().decode("unicode_escape"))
        except Exception as e:  # noqa: BLE001
            errors.append(f"parse {heading}: {e}")
            continue
        for r in table:
            cells = {k: re.sub(r"<[^>]+>", "", str(v)).strip() for k, v in r.items()}
            region_txt, price_txt, accel = cells.get("2", ""), cells.get("3", ""), cells.get("4", "")
            gpu = gpu_from_text(accel) or gpu_from_text(heading)
            if not gpu:
                continue
            nums = [float(x.replace(",", "")) for x in re.findall(r"\$([\d,]+\.?\d*)", price_txt)]
            if len(nums) < 2:
                continue
            n_m = re.search(r"(\d+)\s*x", accel)
            n = int(n_m.group(1)) if n_m else 8
            loc = region_txt.replace(" Local Zone", "").strip()
            code, geo = AWS_LOCATIONS.get(loc, (loc, "Global"))
            sku = heading.replace(" Pricing", "").lower() + f" ({n} GPU)"
            variant = "GB200 (Grace) UltraServer" if "GB200" in accel.upper() or "p6e" in sku else (
                "RTX PRO 6000 Server" if gpu == "RTX PRO 6000" else f"HGX {gpu} SXM")
            rows.append(Row(gpu=gpu, variant=variant, provider="AWS", provider_slug="aws", sku=sku, gpus=n,
                            price_instance_hr=nums[0], price_gpu_hr=nums[1], price_type="capacity_block",
                            region=code, country=region_txt, geo=geo, source="aws_capacity_blocks_page",
                            source_url=CB_URL, method="page", confidence="high",
                            notes="Effective hourly rate on the public Capacity Blocks page; actual offers are "
                                  "dynamically priced at purchase time."))
    if not rows:
        errors.append("no capacity block rows parsed (page layout may have changed)")
    return rows, errors
