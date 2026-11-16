"""getdeploying.com GPU comparison pages: broad neocloud / marketplace / serverless coverage.

Providers that have a first-party API collector (AWS, Azure, Oracle, Vast) are skipped here
to avoid double counting.
"""
from __future__ import annotations

import html as htmllib
import re

from ..common import Row, fetch
from ..regions import country_from_text

PAGES = {"B200": "nvidia-b200", "B300": "nvidia-b300", "RTX PRO 6000": "nvidia-rtx-pro-6000"}
SKIP = {"aws", "microsoft-azure", "oracle-cloud", "vast-ai"}
BASE = "https://getdeploying.com/gpus/"

TR = re.compile(r"<tr\s+data-gpus=\"(\d+)\"(.*?)>(.*?)</tr>", re.S)


def _attr(attrs: str, name: str) -> str:
    m = re.search(name + r'="([^"]*)"', attrs)
    return m.group(1) if m else ""


def _text(s: str) -> str:
    s = re.sub(r"<svg.*?</svg>", "", s, flags=re.S)
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def _ptype(billing: str, badges: list[str]) -> tuple[str, int | None] | None:
    b = " ".join(badges).lower()
    if "spot" in b:
        return ("spot", None)
    m = re.search(r"reserved \((\d+)mo\)", b)
    if m:
        return ("reserved", int(m.group(1)))
    if "reserved" in b:
        return ("reserved", None)
    if "on-demand" in b:
        return ("on_demand", None)
    return None  # custom / quote only


def collect() -> tuple[list[Row], list[str]]:
    rows, errors = [], []
    for gpu, slug in PAGES.items():
        url = BASE + slug
        try:
            page = fetch(url)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{slug}: {e}")
            continue
        cards = page.split('<div data-search="')[1:]
        if not cards:
            errors.append(f"{slug}: no provider cards found (layout changed?)")
        for card in cards:
            search = card[: card.find('"')]
            pm = re.search(r'id="provider-([^"]+)"', card)
            nm = re.search(r'class="link-line">([^<]+)<', card)
            if not pm:
                continue
            pslug, pname = pm.group(1), htmllib.unescape(nm.group(1)) if nm else pm.group(1)
            if pslug in SKIP:
                continue
            country, geo = country_from_text(search)
            link = re.search(r'href="(https?://[^"]+)"[^>]*rel="noopener nofollow"', card)
            prov_url = htmllib.unescape(link.group(1)).split("?")[0] if link else f"https://getdeploying.com/{pslug}"
            for m in TR.finditer(card):
                n = int(m.group(1))
                attrs, body = m.group(2), m.group(3)
                price, pgpu = _attr(attrs, "data-price"), _attr(attrs, "data-pricegpu")
                if not pgpu:
                    continue
                cells = body.split("</td>")
                cfg = _text(cells[0]) if cells else ""
                hint = re.search(r'title="([^"]*)"', cells[0]) if cells else None
                badges = [b.strip() for b in re.findall(r'badge badge-sm [a-z]+">\s*([^<]+?)\s*<', body)]
                pt = _ptype(_attr(attrs, "data-billing"), badges)
                if not pt:
                    continue
                avail = next((b for b in badges if b.lower() in ("in stock", "out of stock", "not reported",
                                                                  "pre-order", "waitlist")), "")
                variant = re.sub(r"^\d+x\s*", "", cfg.split(hint.group(1))[0].strip() if hint else cfg).strip()
                rows.append(Row(gpu=gpu, variant=variant or gpu, provider=pname, provider_slug=pslug,
                                sku=(hint.group(1) if hint else cfg)[:80], gpus=n,
                                price_instance_hr=float(price) if price else None, price_gpu_hr=float(pgpu),
                                price_type=pt[0], term_months=pt[1], region=country, country=country, geo=geo,
                                source="getdeploying", source_url=prov_url, method="aggregator",
                                confidence="medium", availability=avail,
                                notes=f"Listed price via getdeploying.com/gpus/{slug}; verify on provider site."))
    return rows, errors
