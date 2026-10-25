"""SimplifyJobs Summer 2027 list (github.com/SimplifyJobs/Summer2027-Internships):
broad aggregator that also covers companies whose sites we do not scrape directly."""
import datetime

import requests

import rules

URL = "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json"
TERM = "Summer 2027"
HW_FLAVOUR = [r"hardware", r"embedded", r"firmware", r"compiler", r"cuda", r"kernel", r"performance",
              r"inference", r"\bhpc\b"]


def fetch():
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    return r.json()


def rows(listings):
    out = []
    for x in listings:
        if not x.get("active") or not x.get("is_visible", True):
            continue
        if TERM not in (x.get("terms") or []):
            continue
        title = x.get("title", "")
        comp = x.get("company_name", "")
        degs = x.get("degrees") or []
        if degs and "Bachelor's" not in degs:
            continue
        locs = x.get("locations") or []
        region = rules.region_for(locs)
        if region is None:
            continue
        cat = x.get("category", "")
        tier, kws = rules.tier_for(title, cat)
        if not tier:
            continue
        hardware_cat = cat in ("Hardware", "Hardware Engineering")
        if not hardware_cat and tier != "core" and not rules.hit(HW_FLAVOUR, title.lower()):
            continue
        posted = datetime.datetime.fromtimestamp(x.get("date_posted", 0), datetime.timezone.utc).strftime("%Y-%m-%d")
        out.append({
            "id": "s_" + x["id"].replace("-", "")[:24],
            "company": comp,
            "title": title,
            "url": x.get("url", ""),
            "locations": locs[:6],
            "posted": posted,
            "tier": tier,
            "keywords": kws,
            "degrees": degs,
            "usPersonLikely": rules.us_person_likely(comp, title),
            "big": rules.is_big(comp),
            "source": "SimplifyJobs",
            "official": False,
            "region": region,
            "term": TERM,
            "group": "simplify",
        })
    return out
