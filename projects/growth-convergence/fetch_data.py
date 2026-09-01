import json
import urllib.request
from typing import Dict, List

# pulls GDP per capita (PPP, constant international $) for 1990 and 2023 straight
# from the free World Bank API, no key or account needed, and writes a clean,
# flat json file that the rest of this project reads from. same pattern as the
# clinical-nlp project: live fetch script + a bundled snapshot for offline use.

API_ROOT = "https://api.worldbank.org/v2"
INDICATOR = "NY.GDP.PCAP.PP.KD"  # GDP per capita, PPP (constant international $)
POP_INDICATOR = "SP.POP.TOTL"  # total population, used for the weighted regression
START_YEAR = 1990
END_YEAR = 2023
OUT_PATH = "data/gdp_per_capita_1990_2023.json"


def _get_json(url: str) -> dict:
    # small wrapper so every network call fails with one clear message
    # instead of a raw traceback if the machine has no internet access
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as error:
        raise RuntimeError(f"could not reach the World Bank API ({error})") from error


def fetch_real_country_names() -> Dict[str, str]:
    # the World Bank lumps regions and income groups (like "World" or "High
    # income") into the same /country endpoint as actual countries. the only
    # way to tell them apart is region.id: real countries have a real region,
    # aggregates are always tagged region.id == "NA". this pulls the full
    # reference list and keeps only the real ones.
    names = {}
    page = 1
    while True:
        payload = _get_json(f"{API_ROOT}/country?format=json&per_page=100&page={page}")
        meta, records = payload[0], payload[1]
        for record in records:
            if record["region"]["id"] != "NA":
                names[record["id"]] = record["name"]
        # keep paging until we've covered every page the api reports
        if page >= meta["pages"]:
            break
        page += 1
    return names


def fetch_indicator_for_year(indicator: str, year: int) -> Dict[str, float]:
    # one request gets every country's value for a single year at once,
    # works the same way for gdp per capita or population or any other
    # single-value-per-country-per-year world bank indicator
    url = f"{API_ROOT}/country/all/indicator/{indicator}?date={year}&format=json&per_page=400"
    payload = _get_json(url)
    records = payload[1] or []
    values = {}
    for record in records:
        # some countries have no data for a given year, world bank marks
        # that with value: null, skip those rather than treating as zero
        if record["value"] is not None:
            values[record["countryiso3code"]] = float(record["value"])
    return values


def build_dataset() -> List[dict]:
    # combines gdp for both years plus 1990 population, keeping only real
    # countries that have a usable number for all three, since the whole
    # point of this project is comparing the same country across that span
    # (population is only used to weight the robustness-check regression,
    # see convergence.py, but it travels with the rest of the row)
    real_countries = fetch_real_country_names()
    gdp_start = fetch_indicator_for_year(INDICATOR, START_YEAR)
    gdp_end = fetch_indicator_for_year(INDICATOR, END_YEAR)
    pop_start = fetch_indicator_for_year(POP_INDICATOR, START_YEAR)

    rows = []
    for iso3, name in real_countries.items():
        if iso3 in gdp_start and iso3 in gdp_end and iso3 in pop_start:
            rows.append({
                "iso3": iso3,
                "country": name,
                "gdp_1990": round(gdp_start[iso3], 2),
                "gdp_2023": round(gdp_end[iso3], 2),
                "pop_1990": int(pop_start[iso3]),
            })
    rows.sort(key=lambda r: r["country"])
    return rows


if __name__ == "__main__":
    # running this directly refreshes the bundled data/ file with a live pull
    dataset = build_dataset()
    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(dataset, handle, indent=2)
    print(f"wrote {len(dataset)} countries to {OUT_PATH}")
