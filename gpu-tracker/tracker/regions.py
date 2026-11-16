"""Normalize provider regions to a common geography used by the dashboard dropdown."""
from __future__ import annotations

GEOS = ["US East", "US West", "US Central", "US (unspecified)", "Canada", "Latin America", "UK",
        "EU West", "EU Central", "EU North", "EU South", "Middle East", "India", "APAC", "Africa",
        "Global"]

# AWS pricing location name -> (region code, geo)
AWS_LOCATIONS = {
    "US East (N. Virginia)": ("us-east-1", "US East"),
    "US East (Ohio)": ("us-east-2", "US East"),
    "US West (N. California)": ("us-west-1", "US West"),
    "US West (Oregon)": ("us-west-2", "US West"),
    "US East (Atlanta)": ("us-east-1-atl-2", "US East"),
    "US West (Los Angeles)": ("us-west-2-lax-1", "US West"),
    "US East (Dallas)": ("us-east-1-dfw-2", "US Central"),
    "US West (Phoenix)": ("us-west-2-phx-2", "US West"),
    "AWS GovCloud (US-East)": ("us-gov-east-1", "US East"),
    "AWS GovCloud (US-West)": ("us-gov-west-1", "US West"),
    "Canada (Central)": ("ca-central-1", "Canada"),
    "Canada West (Calgary)": ("ca-west-1", "Canada"),
    "South America (Sao Paulo)": ("sa-east-1", "Latin America"),
    "Mexico (Central)": ("mx-central-1", "Latin America"),
    "Europe (London)": ("eu-west-2", "UK"),
    "Europe (Ireland)": ("eu-west-1", "EU West"),
    "Europe (Paris)": ("eu-west-3", "EU West"),
    "Europe (Frankfurt)": ("eu-central-1", "EU Central"),
    "Europe (Zurich)": ("eu-central-2", "EU Central"),
    "Europe (Stockholm)": ("eu-north-1", "EU North"),
    "Europe (Milan)": ("eu-south-1", "EU South"),
    "Europe (Spain)": ("eu-south-2", "EU South"),
    "Middle East (Bahrain)": ("me-south-1", "Middle East"),
    "Middle East (UAE)": ("me-central-1", "Middle East"),
    "Israel (Tel Aviv)": ("il-central-1", "Middle East"),
    "Africa (Cape Town)": ("af-south-1", "Africa"),
    "Asia Pacific (Mumbai)": ("ap-south-1", "India"),
    "Asia Pacific (Hyderabad)": ("ap-south-2", "India"),
    "Asia Pacific (Tokyo)": ("ap-northeast-1", "APAC"),
    "Asia Pacific (Seoul)": ("ap-northeast-2", "APAC"),
    "Asia Pacific (Osaka)": ("ap-northeast-3", "APAC"),
    "Asia Pacific (Singapore)": ("ap-southeast-1", "APAC"),
    "Asia Pacific (Sydney)": ("ap-southeast-2", "APAC"),
    "Asia Pacific (Jakarta)": ("ap-southeast-3", "APAC"),
    "Asia Pacific (Melbourne)": ("ap-southeast-4", "APAC"),
    "Asia Pacific (Malaysia)": ("ap-southeast-5", "APAC"),
    "Asia Pacific (Thailand)": ("ap-southeast-7", "APAC"),
    "Asia Pacific (Hong Kong)": ("ap-east-1", "APAC"),
    "Asia Pacific (Taipei)": ("ap-east-2", "APAC"),
}

AZURE_PREFIX_GEO = [
    ("eastus", "US East"), ("westus", "US West"), ("centralus", "US Central"),
    ("northcentralus", "US Central"), ("southcentralus", "US Central"), ("westcentralus", "US Central"),
    ("canada", "Canada"), ("brazil", "Latin America"), ("mexico", "Latin America"), ("chile", "Latin America"),
    ("uk", "UK"), ("westeurope", "EU West"), ("northeurope", "EU West"), ("france", "EU West"),
    ("germany", "EU Central"), ("switzerland", "EU Central"), ("poland", "EU Central"), ("austria", "EU Central"),
    ("sweden", "EU North"), ("norway", "EU North"), ("finland", "EU North"), ("denmark", "EU North"),
    ("italy", "EU South"), ("spain", "EU South"), ("uae", "Middle East"), ("qatar", "Middle East"),
    ("israel", "Middle East"), ("saudi", "Middle East"), ("southafrica", "Africa"),
    ("centralindia", "India"), ("southindia", "India"), ("westindia", "India"), ("jioindia", "India"),
    ("india", "India"), ("japan", "APAC"), ("korea", "APAC"), ("australia", "APAC"), ("southeastasia", "APAC"),
    ("eastasia", "APAC"), ("indonesia", "APAC"), ("malaysia", "APAC"), ("newzealand", "APAC"), ("taiwan", "APAC"),
]


def azure_geo(arm_region: str) -> str:
    r = arm_region.lower()
    if r.startswith("usgov") or r.startswith("usdod"):
        return "US East" if "east" in r or "virginia" in r else "US Central"
    for prefix, geo in AZURE_PREFIX_GEO:
        if r.startswith(prefix):
            return geo
    return "Global"


# country name (lowercase) -> (display, geo)
COUNTRIES = {
    "united states of america": ("United States", "US (unspecified)"),
    "united states": ("United States", "US (unspecified)"),
    "us": ("United States", "US (unspecified)"),
    "canada": ("Canada", "Canada"), "brazil": ("Brazil", "Latin America"), "mexico": ("Mexico", "Latin America"),
    "chile": ("Chile", "Latin America"), "argentina": ("Argentina", "Latin America"),
    "united kingdom": ("United Kingdom", "UK"), "ireland": ("Ireland", "EU West"),
    "france": ("France", "EU West"), "netherlands": ("Netherlands", "EU West"), "belgium": ("Belgium", "EU West"),
    "luxembourg": ("Luxembourg", "EU West"), "portugal": ("Portugal", "EU South"), "spain": ("Spain", "EU South"),
    "italy": ("Italy", "EU South"), "greece": ("Greece", "EU South"), "germany": ("Germany", "EU Central"),
    "switzerland": ("Switzerland", "EU Central"), "austria": ("Austria", "EU Central"),
    "poland": ("Poland", "EU Central"), "czechia": ("Czechia", "EU Central"), "czech republic": ("Czechia", "EU Central"),
    "lithuania": ("Lithuania", "EU North"), "latvia": ("Latvia", "EU North"), "estonia": ("Estonia", "EU North"),
    "serbia": ("Serbia", "EU Central"), "romania": ("Romania", "EU Central"), "bulgaria": ("Bulgaria", "EU Central"),
    "hungary": ("Hungary", "EU Central"), "slovenia": ("Slovenia", "EU Central"), "croatia": ("Croatia", "EU Central"),
    "sweden": ("Sweden", "EU North"), "norway": ("Norway", "EU North"), "finland": ("Finland", "EU North"),
    "denmark": ("Denmark", "EU North"), "iceland": ("Iceland", "EU North"),
    "united arab emirates": ("UAE", "Middle East"), "saudi arabia": ("Saudi Arabia", "Middle East"),
    "qatar": ("Qatar", "Middle East"), "israel": ("Israel", "Middle East"), "turkey": ("Turkey", "Middle East"),
    "india": ("India", "India"), "japan": ("Japan", "APAC"), "south korea": ("South Korea", "APAC"),
    "korea": ("South Korea", "APAC"), "singapore": ("Singapore", "APAC"), "hong kong": ("Hong Kong", "APAC"),
    "taiwan": ("Taiwan", "APAC"), "australia": ("Australia", "APAC"), "new zealand": ("New Zealand", "APAC"),
    "indonesia": ("Indonesia", "APAC"), "malaysia": ("Malaysia", "APAC"), "thailand": ("Thailand", "APAC"),
    "vietnam": ("Vietnam", "APAC"), "philippines": ("Philippines", "APAC"), "china": ("China", "APAC"),
    "south africa": ("South Africa", "Africa"), "nigeria": ("Nigeria", "Africa"), "kenya": ("Kenya", "Africa"),
}

US_STATES_GEO = {
    "east": {"virginia", "new york", "new jersey", "pennsylvania", "georgia", "north carolina", "south carolina",
             "florida", "massachusetts", "maryland", "ohio", "delaware", "connecticut", "maine", "vermont",
             "new hampshire", "rhode island", "west virginia", "michigan", "indiana", "kentucky", "tennessee"},
    "west": {"california", "oregon", "washington", "nevada", "arizona", "utah", "idaho", "colorado", "new mexico",
             "montana", "wyoming", "alaska", "hawaii"},
    "central": {"texas", "illinois", "iowa", "missouri", "minnesota", "kansas", "nebraska", "oklahoma",
                "wisconsin", "arkansas", "louisiana", "mississippi", "alabama", "north dakota", "south dakota"},
}


def country_from_text(text: str) -> tuple[str, str]:
    """Find the first known country in free text. Returns (country, geo)."""
    t = " " + text.lower() + " "
    best = None
    for name, val in COUNTRIES.items():
        if len(name) <= 2:
            continue
        i = t.find(" " + name + " ")
        if i >= 0 and (best is None or i < best[0]):
            best = (i, val)
    if "distributed" in t or "worldwide" in t or "global" in t:
        if best is None:
            return ("Global", "Global")
    return best[1] if best else ("Unknown", "Global")


def vast_geo(geoloc: str) -> tuple[str, str, str]:
    """Vast geolocation like 'California, US' -> (region, country, geo)."""
    parts = [p.strip() for p in (geoloc or "").split(",")]
    code = parts[-1].upper() if parts else ""
    state = parts[0].lower() if len(parts) > 1 else ""
    iso = {"US": ("United States", None), "CA": ("Canada", "Canada"), "GB": ("United Kingdom", "UK"),
           "DE": ("Germany", "EU Central"), "FR": ("France", "EU West"), "NL": ("Netherlands", "EU West"),
           "SE": ("Sweden", "EU North"), "NO": ("Norway", "EU North"), "FI": ("Finland", "EU North"),
           "PL": ("Poland", "EU Central"), "CZ": ("Czechia", "EU Central"), "ES": ("Spain", "EU South"),
           "IT": ("Italy", "EU South"), "JP": ("Japan", "APAC"), "KR": ("South Korea", "APAC"),
           "SG": ("Singapore", "APAC"), "TW": ("Taiwan", "APAC"), "AU": ("Australia", "APAC"),
           "IN": ("India", "India"), "AE": ("UAE", "Middle East"), "BR": ("Brazil", "Latin America"),
           "HK": ("Hong Kong", "APAC"), "IS": ("Iceland", "EU North"), "BG": ("Bulgaria", "EU Central"),
           "RO": ("Romania", "EU Central"), "LT": ("Lithuania", "EU North"), "EE": ("Estonia", "EU North"),
           "VN": ("Vietnam", "APAC"), "TH": ("Thailand", "APAC"), "ZA": ("South Africa", "Africa")}
    country, geo = iso.get(code, (code or "Unknown", "Global"))
    if code == "US":
        geo = "US (unspecified)"
        for g, states in US_STATES_GEO.items():
            if state in states:
                geo = {"east": "US East", "west": "US West", "central": "US Central"}[g]
    return (geoloc or "Unknown", country, geo)
