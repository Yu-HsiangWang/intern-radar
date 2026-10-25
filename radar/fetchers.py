"""One fetcher per careers-site system. Each returns a list of dicts:
   {company, title, url, locations: [str], posted: "YYYY-MM-DD" or "", req: str or None}
Fetchers raise on transport errors; build.py records the error per source and moves on.
"""
import datetime
import html
import json
import re
import time
from urllib.parse import quote

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
TIMEOUT = 30
PAUSE = 0.4


def _today():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4))).date()


def _iso(d):
    return d.isoformat() if d else ""


def _from_ts(x):
    try:
        x = float(x)
        if x > 1e12:
            x /= 1000.0
        return datetime.datetime.fromtimestamp(x, datetime.timezone.utc).date().isoformat()
    except Exception:
        return ""


def _from_text_date(s):
    s = re.sub(r"\s+", " ", (s or "").strip())
    m = re.match(r"(\d{4})[-/]?(\d{2})[-/]?(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%m/%d/%Y", "%d %B %Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date().isoformat()
        except Exception:
            pass
    return ""


def _strip(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s or "")).strip()


# --------------------------------------------------------------------------- Workday
def _workday_posted(s):
    s = (s or "").lower()
    t = _today()
    if "today" in s:
        return _iso(t)
    if "yesterday" in s:
        return _iso(t - datetime.timedelta(days=1))
    m = re.search(r"(\d+)\+?\s*day", s)
    if m:
        return _iso(t - datetime.timedelta(days=int(m.group(1))))
    return ""


def workday(company, host, tenant, site, queries=("intern",), max_pages=40):
    out = {}
    url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    for q in queries:
        offset, total = 0, None
        while True:
            r = S.post(url, json={"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": q},
                       headers={"Accept": "application/json", "Content-Type": "application/json"},
                       timeout=TIMEOUT)
            r.raise_for_status()
            j = r.json()
            if total is None:
                total = int(j.get("total") or 0)
            posts = j.get("jobPostings") or []
            for p in posts:
                path = p.get("externalPath") or ""
                if not path:
                    continue
                parts = path.split("/")
                seg = parts[2] if len(parts) > 2 else ""
                req = None
                bf = p.get("bulletFields") or []
                if bf:
                    req = str(bf[0])
                out[path] = dict(company=company, title=p.get("title", ""),
                                 url=f"https://{host}/{site}{path}",
                                 locations=[x for x in (p.get("locationsText") or "", seg) if x],
                                 posted=_workday_posted(p.get("postedOn")), req=req)
            offset += 20
            if not posts or offset >= total or offset >= max_pages * 20:
                break
            time.sleep(PAUSE)
    return list(out.values())


# --------------------------------------------------------------------------- Greenhouse / Ashby / Lever
def greenhouse(company, board):
    r = S.get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs", timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        out.append(dict(company=company, title=j.get("title", ""), url=j.get("absolute_url", ""),
                        locations=[(j.get("location") or {}).get("name", "")],
                        posted=(j.get("first_published") or j.get("updated_at") or "")[:10],
                        req=str(j.get("id"))))
    return out


def ashby(company, org):
    r = S.get(f"https://api.ashbyhq.com/posting-api/job-board/{org}?includeCompensation=false", timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        if j.get("isListed") is False:
            continue
        locs = [j.get("location") or ""] + [x.get("location", "") for x in (j.get("secondaryLocations") or [])]
        out.append(dict(company=company, title=j.get("title", ""), url=j.get("jobUrl") or j.get("applyUrl", ""),
                        locations=[x for x in locs if x], posted=(j.get("publishedAt") or "")[:10],
                        req=str(j.get("id"))))
    return out


def lever(company, account, region=""):
    host = "api.eu.lever.co" if region == "eu" else "api.lever.co"
    r = S.get(f"https://{host}/v0/postings/{account}?mode=json", timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for j in r.json():
        cat = j.get("categories") or {}
        locs = cat.get("allLocations") or [cat.get("location", "")]
        out.append(dict(company=company, title=j.get("text", ""), url=j.get("hostedUrl", ""),
                        locations=[x for x in locs if x], posted=_from_ts(j.get("createdAt")),
                        req=str(j.get("id"))))
    return out


# --------------------------------------------------------------------------- Eightfold (Qualcomm, Microsoft)
def eightfold(company, host, domain, queries=("intern",), max_items=400):
    out = {}
    for q in queries:
        start = 0
        while start < max_items:
            url = (f"https://{host}/api/apply/v2/jobs?domain={domain}&start={start}&num=50"
                   f"&query={quote(q)}&sort_by=timestamp")
            r = S.get(url, headers={"Accept": "application/json"}, timeout=TIMEOUT)
            positions = None
            if r.status_code == 200:
                try:
                    positions = r.json().get("positions")
                except ValueError:
                    positions = None
            if positions is None:
                url = (f"https://{host}/api/pcsx/search?domain={domain}&query={quote(q)}"
                       f"&location=&start={start}&sort_by=timestamp")
                r = S.get(url, headers={"Accept": "application/json"}, timeout=TIMEOUT)
                r.raise_for_status()
                positions = (r.json().get("data") or {}).get("positions") or []
            for p in positions:
                pid = str(p.get("id"))
                link = p.get("canonicalPositionUrl") or p.get("positionUrl") or f"/careers/job/{pid}"
                if link.startswith("/"):
                    link = f"https://{host}{link}"
                locs = p.get("locations") or [p.get("location", "")]
                posted = _from_ts(p.get("t_create") or p.get("postedTs") or p.get("t_update"))
                out[pid] = dict(company=company, title=p.get("name", ""), url=link,
                                locations=[x for x in locs if x], posted=posted, req=pid)
            start += 50
            if len(positions) < 50:
                break
            time.sleep(PAUSE)
    return list(out.values())


# --------------------------------------------------------------------------- SmartRecruiters / Oracle HCM
def smartrecruiters(company, account, queries=("intern",)):
    out = {}
    for q in queries:
        r = S.get(f"https://api.smartrecruiters.com/v1/companies/{account}/postings?q={quote(q)}&limit=100",
                  timeout=TIMEOUT)
        r.raise_for_status()
        for j in r.json().get("content", []):
            loc = j.get("location") or {}
            full = loc.get("fullLocation") or ", ".join(x for x in (loc.get("city"), loc.get("region"), loc.get("country")) if x)
            out[j["id"]] = dict(company=company, title=j.get("name", ""),
                                url=f"https://jobs.smartrecruiters.com/{account}/{j['id']}",
                                locations=[full], posted=(j.get("releasedDate") or "")[:10], req=str(j.get("id")))
    return list(out.values())


def oracle_hcm(company, host, site, keyword="intern"):
    url = (f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
           f"&expand=requisitionList.secondaryLocations"
           f"&finder=findReqs;siteNumber={site},limit=100,keyword=%22{quote(keyword)}%22,sortBy=POSTING_DATES_DESC")
    r = S.get(url, headers={"Accept": "application/json"}, timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for item in r.json().get("items", []):
        for j in item.get("requisitionList", []) or []:
            locs = [j.get("PrimaryLocation", "")] + [x.get("Name", "") for x in (j.get("secondaryLocations") or [])]
            out.append(dict(company=company, title=j.get("Title", ""),
                            url=f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{j.get('Id')}",
                            locations=[x for x in locs if x], posted=(j.get("PostedDate") or "")[:10],
                            req=str(j.get("Id"))))
    return out


# --------------------------------------------------------------------------- Amazon / AMD / Tesla
def amazon(queries):
    out = {}
    for q, category in queries:
        url = (f"https://www.amazon.jobs/en/search.json?base_query={quote(q)}&result_limit=100&offset=0"
               f"&sort=recent&country=USA")
        if category:
            url += f"&category%5B%5D={quote(category)}"
        r = S.get(url, headers={"Accept": "application/json"}, timeout=TIMEOUT)
        r.raise_for_status()
        for j in r.json().get("jobs", []):
            jid = str(j.get("id_icims") or j.get("id"))
            out[jid] = dict(company="Amazon", title=j.get("title", ""),
                            url="https://www.amazon.jobs" + (j.get("job_path") or f"/en/jobs/{jid}"),
                            locations=[j.get("normalized_location") or j.get("location", "")],
                            posted=_from_text_date(j.get("posted_date")), req=jid)
        time.sleep(PAUSE)
    return list(out.values())


def amd(queries=("intern",), max_pages=6):
    out = {}
    for q in queries:
        for page in range(1, max_pages + 1):
            r = S.get(f"https://careers.amd.com/api/jobs?keywords={quote(q)}&page={page}&limit=100"
                      f"&sortBy=posted_date&descending=true", headers={"Accept": "application/json"},
                      timeout=TIMEOUT)
            r.raise_for_status()
            jobs = r.json().get("jobs", [])
            for item in jobs:
                d = item.get("data", item)
                rid = str(d.get("req_id") or d.get("slug"))
                locs = [d.get("full_location") or d.get("location_name") or
                        ", ".join(x for x in (d.get("city"), d.get("state"), d.get("country")) if x)]
                for extra in d.get("additional_locations") or []:
                    if isinstance(extra, dict):
                        locs.append(extra.get("full_location") or ", ".join(
                            x for x in (extra.get("city"), extra.get("state"), extra.get("country")) if x))
                    elif isinstance(extra, str):
                        locs.append(extra)
                out[rid] = dict(company="AMD", title=d.get("title", ""),
                                url=f"https://careers.amd.com/careers-home/jobs/{rid}",
                                locations=[x for x in locs if x], posted=(d.get("posted_date") or "")[:10], req=rid)
            if len(jobs) < 100:
                break
            time.sleep(PAUSE)
    return list(out.values())


def tesla():
    r = S.get("https://www.tesla.com/cua-api/apps/careers/state", headers={"Accept": "application/json"},
              timeout=TIMEOUT)
    r.raise_for_status()
    j = r.json()
    lookup = (j.get("lookup") or {}).get("locations") or {}
    out = []
    for l in j.get("listings", []):
        title = l.get("t") or l.get("title") or ""
        if not re.search(r"intern", title, re.I):
            continue
        loc = lookup.get(str(l.get("l")), "") if isinstance(lookup, dict) else ""
        out.append(dict(company="Tesla", title=title, url=f"https://www.tesla.com/careers/search/job/{l.get('id')}",
                        locations=[loc] if loc else [], posted="", req=str(l.get("id"))))
    return out


# --------------------------------------------------------------------------- HTML-rendered sites
def google(searches):
    """searches: list of (query, location). Parses the server-rendered results page."""
    out = {}
    for q, loc in searches:
        for page in (1, 2, 3):
            url = ("https://www.google.com/about/careers/applications/jobs/results/?employment_type=INTERN"
                   f"&location={quote(loc)}&q={quote(q)}&page={page}")
            r = S.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            text = r.text
            found = 0
            # Job data rides in AF_initDataCallback arrays: ["<id>","<title>", ...
            for jid, title in re.findall(r'\["(\d{15,20})","([^"\\]{4,200})"', text):
                if jid in out:
                    continue
                out[jid] = dict(company="Google", title=html.unescape(title),
                                url=f"https://www.google.com/about/careers/applications/jobs/results/{jid}",
                                locations=[loc], posted="", req=jid)
                found += 1
            if not found:
                for jid, slug in re.findall(r'jobs/results/(\d{15,20})-([a-z0-9-]+)', text):
                    if jid in out:
                        continue
                    out[jid] = dict(company="Google", title=slug.replace("-", " ").title(),
                                    url=f"https://www.google.com/about/careers/applications/jobs/results/{jid}-{slug}",
                                    locations=[loc], posted="", req=jid)
                    found += 1
            if not found:
                break
            time.sleep(PAUSE)
    return list(out.values())


def apple(location="united-states-USA", pages=6):
    out = {}
    for page in range(1, pages + 1):
        url = f"https://jobs.apple.com/en-us/search?location={location}&team=internships-STDNT-INTRN&page={page}"
        r = S.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        text = r.text
        found = 0
        for href, inner in re.findall(r'<a[^>]+href="(/en-us/details/[^"?#]+)[^"]*"[^>]*>(.*?)</a>', text, re.S):
            title = _strip(inner)
            m = re.match(r"/en-us/details/([\d-]+)", href)
            if not m or not title or title.lower() in ("see full role description", "learn more"):
                continue
            jid = m.group(1)
            if jid in out:
                continue
            out[jid] = dict(company="Apple", title=title, url="https://jobs.apple.com" + href,
                            locations=["United States"], posted="", req=jid.split("-")[0])
            found += 1
        if not found:
            # Hydration JSON fallback
            blob = text.replace('\\"', '"')
            for jid, title in re.findall(r'"positionId":"([\d-]+)".{0,600}?"postingTitle":"([^"]+)"', blob, re.S):
                if jid not in out:
                    out[jid] = dict(company="Apple", title=title,
                                    url=f"https://jobs.apple.com/en-us/details/{jid}",
                                    locations=["United States"], posted="", req=jid.split("-")[0])
                    found += 1
        if not found:
            break
        time.sleep(PAUSE)
    return list(out.values())


def meta(queries):
    out = {}
    for q in queries:
        r = S.get(f"https://www.metacareers.com/jobs?q={quote(q)}", timeout=TIMEOUT)
        r.raise_for_status()
        text = r.text.replace('\\"', '"').replace("\\/", "/")
        for jid, title in re.findall(r'"id":"(\d{12,20})","title":"([^"]{4,200})"', text):
            out.setdefault(jid, dict(company="Meta", title=html.unescape(title),
                                     url=f"https://www.metacareers.com/jobs/{jid}/", locations=[],
                                     posted="", req=jid))
        for jid, inner in re.findall(r'href="/jobs/(\d{12,20})/?"[^>]*>(.*?)</a>', text, re.S):
            title = _strip(inner)
            if title:
                out.setdefault(jid, dict(company="Meta", title=title, url=f"https://www.metacareers.com/jobs/{jid}/",
                                         locations=[], posted="", req=jid))
        time.sleep(PAUSE)
    return list(out.values())


def arm(pages=3):
    out = {}
    for page in range(1, pages + 1):
        url = ("https://careers.arm.com/search-jobs/results?ActiveFacetID=0&CurrentPage="
               f"{page}&RecordsPerPage=100&Distance=50&RadiusUnitType=0&Keywords=intern&Location="
               "&ShowRadius=False&IsPagination=True&FacetType=0&SearchResultsModuleName=Search+Results"
               "&SearchFiltersModuleName=Search+Filters&SortCriteria=0&SortDirection=0&SearchType=5")
        r = S.get(url, headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"},
                  timeout=TIMEOUT)
        r.raise_for_status()
        try:
            text = r.json().get("results", "")
        except ValueError:
            text = r.text
        found = 0
        for block in re.findall(r'<a[^>]+href="(/job/[^"]+)"[^>]*>(.*?)</a>', text, re.S):
            href, inner = block
            tm = re.search(r"<h2[^>]*>(.*?)</h2>", inner, re.S)
            lm = re.search(r'class="job-location"[^>]*>(.*?)<', inner, re.S)
            title = _strip(tm.group(1) if tm else inner)
            if not title:
                continue
            jid = href.rstrip("/").split("/")[-1]
            if jid in out:
                continue
            out[jid] = dict(company="Arm", title=title, url="https://careers.arm.com" + href,
                            locations=[_strip(lm.group(1))] if lm else [], posted="", req=jid)
            found += 1
        if not found:
            break
        time.sleep(PAUSE)
    return list(out.values())


def job104(keywords):
    """Taiwan's 104 job bank (MediaTek, Realtek, GUC, Novatek and others post 暑期實習 there)."""
    out = {}
    for kw in keywords:
        ref = f"https://www.104.com.tw/jobs/search/?keyword={quote(kw)}"
        items = None
        r = S.get(f"https://www.104.com.tw/jobs/search/api/jobs?jobsource=index_s&keyword={quote(kw)}"
                  f"&mode=s&order=15&page=1&pagesize=50", headers={"Referer": ref, "Accept": "application/json"},
                  timeout=TIMEOUT)
        if r.status_code == 200:
            try:
                d = r.json().get("data")
                items = d if isinstance(d, list) else (d or {}).get("list")
            except ValueError:
                items = None
        if items is None:
            r = S.get(f"https://www.104.com.tw/jobs/search/list?ro=0&kwop=7&keyword={quote(kw)}&order=15&asc=0"
                      f"&page=1&mode=s&jobsource=2018indexpoc", headers={"Referer": ref}, timeout=TIMEOUT)
            r.raise_for_status()
            items = (r.json().get("data") or {}).get("list") or []
        for j in items:
            link = (j.get("link") or {}).get("job") or ""
            if link.startswith("//"):
                link = "https:" + link
            link = link.split("?")[0]
            jid = link.rstrip("/").split("/")[-1] or str(j.get("jobNo"))
            out[jid] = dict(company=j.get("custName", ""), title=j.get("jobName", ""), url=link,
                            locations=[j.get("jobAddrNoDesc") or j.get("jobAddress") or "台灣"],
                            posted=_from_text_date(str(j.get("appearDate") or "")), req=jid)
        time.sleep(PAUSE)
    return list(out.values())
