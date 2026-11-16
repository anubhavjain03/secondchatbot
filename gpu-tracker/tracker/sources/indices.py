"""Free public market-index readings (Silicon Data index pages). Returned as signals, not price rows."""
from __future__ import annotations

import html as htmllib
import re

from ..common import fetch, now_iso

PAGE = "https://www.silicondata.com/products/silicon-index/{g}"
WANT = {"B200": "B200", "B300": "B300", "H100": "H100"}


def collect() -> tuple[list[dict], list[str]]:
    signals, errors, seen = [], [], set()
    for g in ("h100", "b200", "b300"):
        try:
            raw = fetch(PAGE.format(g=g), retries=2)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{g}: {e}")
            continue
        txt = re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ",
                                                         re.sub(r"<script.*?</script>", "", raw, flags=re.S))))
        upd = re.search(r"updated ([A-Z][a-z]{2} \d{1,2}, \d{4})", txt)
        # Related-indices widget: "B200 Bloomberg ticker: SDB200RT View $6.87 12.3% (7D)"
        for m in re.finditer(r"\b(H100|H200|A100|B200|B300|MI300X) Bloomberg ticker: (\S+) View \$(\d+\.\d+) "
                             r"(\d+\.\d+)% \(7D\)", txt):
            name, ticker, val, chg = m.groups()
            if name not in WANT or name in seen:
                continue
            seen.add(name)
            signals.append({"gpu": name, "index": f"Silicon Data {name} rental index" +
                            (f" ({ticker})" if ticker != "--" else ""), "value": float(val),
                            "change_7d_abs_pct": float(chg), "as_of": upd.group(1) if upd else "",
                            "observed_at": now_iso(), "source_url": PAGE.format(g=name.lower()),
                            "note": "Weighted neocloud rental rate, $/GPU-hr. 7-day change magnitude shown "
                                    "without direction (not exposed as text on the page)."})
    return signals, errors
