"""Diagnostics for careers-site fetchers (run by .github/workflows/probe.yml).
Uses the same honest User-Agent as the scanner; it does not try to get around blocks."""
import re

import requests

UA = "intern-radar/1.0 (+https://github.com/Yu-HsiangWang/intern-radar; daily job-posting digest)"
H = {"User-Agent": UA}


def tryit(label, fn):
    try:
        fn()
    except Exception as e:
        print(f"\n===== {label}: EXC {type(e).__name__}: {e}")


def arm():
    url = ("https://careers.arm.com/search-jobs/results?ActiveFacetID=0&CurrentPage=1&RecordsPerPage=100&Distance=50"
           "&RadiusUnitType=0&Keywords=intern&Location=&ShowRadius=False&IsPagination=True&FacetType=0"
           "&SearchResultsModuleName=Search+Results&SearchFiltersModuleName=Search+Filters&SortCriteria=0"
           "&SortDirection=0&SearchType=5")
    r = requests.get(url, headers=dict(H, **{"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"}), timeout=30)
    print(f"\n===== ARM HTTP {r.status_code} {r.headers.get('content-type')}")
    t = r.json().get("results", "") if "json" in r.headers.get("content-type", "") else r.text
    i = t.find("/job/")
    print(t[max(0, i - 300): i + 1500].replace("\n", " "))


def workday(label, host, tenant, site, q):
    r = requests.post(f"https://{host}/wday/cxs/{tenant}/{site}/jobs",
                      json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": q},
                      headers=dict(H, Accept="application/json"), timeout=30)
    print(f"\n===== WORKDAY {label} q={q!r}: HTTP {r.status_code}")
    j = r.json()
    print("   total:", j.get("total"), " facets:", [f.get("facetParameter") for f in j.get("facets", [])])
    for p in j.get("jobPostings", [])[:20]:
        print("   ", p.get("title"), "|", p.get("locationsText"), "|", p.get("externalPath"), "|", p.get("postedOn"))
    for f in j.get("facets", []):
        vals = f.get("values") or []
        print("   facet", f.get("facetParameter"), [(v.get("descriptor"), v.get("id"), v.get("count")) for v in vals][:12])
    if j.get("jobPostings"):
        path = j["jobPostings"][0]["externalPath"]
        d = requests.get(f"https://{host}/wday/cxs/{tenant}/{site}{path}", headers=dict(H, Accept="application/json"),
                         timeout=30).json()
        info = d.get("jobPostingInfo", {})
        print("   detail keys:", sorted(info.keys())[:40])
        print("   detail location:", info.get("location"), "| additional:", info.get("additionalLocations"),
              "| startDate:", info.get("startDate"), "| country:", (info.get("country") or {}).get("descriptor"))


def eightfold(host, domain):
    for start, num in ((0, 50), (10, 10)):
        r = requests.get(f"https://{host}/api/apply/v2/jobs?domain={domain}&start={start}&num={num}&query=intern"
                         f"&sort_by=timestamp", headers=dict(H, Accept="application/json"), timeout=30)
        print(f"\n===== EIGHTFOLD {host} start={start} num={num}: HTTP {r.status_code}")
        j = r.json()
        print("   keys:", list(j.keys())[:15], " count:", j.get("count"), " n:", len(j.get("positions", [])))
        for p in j.get("positions", [])[:4]:
            print("   ", p.get("name"), "|", p.get("location"), "|", p.get("t_create"))


def plain(label, url):
    r = requests.get(url, headers=H, timeout=30)
    print(f"\n===== {label}: HTTP {r.status_code} {r.headers.get('content-type')} len={len(r.content)}")
    print("   ", r.text[:300].replace("\n", " "))


tryit("arm", arm)
tryit("micron", lambda: workday("Micron", "micron.wd1.myworkdayjobs.com", "micron", "External", "intern"))
tryit("nvidia", lambda: workday("NVIDIA", "nvidia.wd5.myworkdayjobs.com", "nvidia", "NVIDIAExternalCareerSite", "intern"))
tryit("broadcom", lambda: workday("Broadcom", "broadcom.wd1.myworkdayjobs.com", "broadcom", "External_Career", "intern"))
tryit("samsung", lambda: workday("Samsung", "sec.wd3.myworkdayjobs.com", "sec", "Samsung_Careers", "intern"))
tryit("qualcomm", lambda: eightfold("careers.qualcomm.com", "qualcomm.com"))
tryit("microsoft", lambda: eightfold("apply.careers.microsoft.com", "microsoft.com"))
tryit("google", lambda: plain("GOOGLE", "https://www.google.com/about/careers/applications/jobs/results/?employment_type=INTERN&location=United%20States&q=hardware"))
tryit("apple", lambda: plain("APPLE", "https://jobs.apple.com/en-us/search?location=united-states-USA&team=internships-STDNT-INTRN"))
tryit("104", lambda: plain("104", "https://www.104.com.tw/jobs/search/list?ro=0&kwop=7&keyword=%E6%9A%91%E6%9C%9F%E5%AF%A6%E7%BF%92&order=15&asc=0&page=1&mode=s&jobsource=2018indexpoc"))
