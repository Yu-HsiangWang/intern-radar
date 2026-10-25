"""Daily build: SimplifyJobs + company careers sites -> data/board.json

data/state.json remembers when each posting was first seen, so the board can flag
what is new. A source that runs successfully for the first time does not flood the
"new" list: its existing postings are dated by their posting date instead.
"""
import datetime
import hashlib
import json
import os
import re
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import rules  # noqa: E402
import simplify  # noqa: E402
import sources  # noqa: E402

ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
MAX_BYTES = 240_000
ET = datetime.timezone(datetime.timedelta(hours=-4))
TODAY = datetime.datetime.now(ET).date().isoformat()

ALIASES = {"advancedmicrodevices": "amd", "amazonwebservices": "amazon", "awsannapurnalabs": "amazon",
           "amazonawsannapurna": "amazon", "hewlettpackardenterprise": "hpe", "samsungsemiconductor": "samsung",
           "samsungelectronics": "samsung", "samsungaustinsemiconductor": "samsung", "metaplatforms": "meta",
           "texasinstruments": "ti", "nvidiacorporation": "nvidia", "intelcorporation": "intel"}
TITLE_NOISE = {"summer", "2027", "intern", "interns", "internship", "internships", "co", "op", "coop", "the",
               "and", "of", "for", "a", "in", "us", "usa", "program"}


def ckey(company):
    k = re.sub(r"[^a-z0-9]", "", (company or "").lower())
    for suffix in ("incorporated", "inc", "corporation", "corp", "llc", "ltd", "technologies", "technology"):
        if k.endswith(suffix) and len(k) > len(suffix) + 2:
            k = k[: -len(suffix)]
    return ALIASES.get(k, k)


def tkey(title, company):
    words = re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).split()
    comp = set(re.sub(r"[^a-z0-9]+", " ", (company or "").lower()).split())
    return " ".join(w for w in words if w not in TITLE_NOISE and w not in comp)


def req_from_url(url):
    path = re.sub(r"[?#].*$", "", url or "")
    ids = re.findall(r"(JR-?\d{5,}|R-?\d{5,}|REQ\d{3,}|\d{6,})", path, re.I)
    return ids[-1].lower().replace("-", "") if ids else None


def norm_req(req):
    if not req:
        return None
    return re.sub(r"[^a-z0-9]", "", str(req).lower()) or None


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def main():
    os.makedirs(DATA, exist_ok=True)
    state = load_json(os.path.join(DATA, "state.json"), {"firstSeen": {}, "lastSeen": {}, "initialized": []})
    initialized = set(state.get("initialized", []))
    rows, by_req, by_title, status = {}, {}, {}, []

    def index(r):
        ck = ckey(r["company"])
        for req in {norm_req(r.get("req")), req_from_url(r.get("url"))}:
            if req:
                by_req[(ck, req)] = r
        by_title[(ck, tkey(r["title"], r["company"]))] = r

    # 1. SimplifyJobs
    t0 = time.time()
    try:
        srows = simplify.rows(simplify.fetch())
        for r in srows:
            r["req"] = req_from_url(r["url"])
            rows[r["id"]] = r
            index(r)
        status.append({"name": "SimplifyJobs", "ok": True, "fetched": len(srows), "kept": len(srows),
                       "error": "", "seconds": round(time.time() - t0, 1)})
    except Exception as e:  # keep going with the company sites
        status.append({"name": "SimplifyJobs", "ok": False, "fetched": 0, "kept": 0,
                       "error": f"{type(e).__name__}: {e}"[:300], "seconds": round(time.time() - t0, 1)})

    # 2. Company careers sites
    for name, fn, args in sources.SOURCES:
        t0 = time.time()
        group = "official:" + name
        try:
            items = fn(*args)
        except Exception as e:
            status.append({"name": name, "ok": False, "fetched": 0, "kept": 0,
                           "error": f"{type(e).__name__}: {e}"[:300], "seconds": round(time.time() - t0, 1)})
            traceback.print_exc()
            continue
        kept = dup = 0
        for it in items:
            title = re.sub(r"\s+", " ", (it.get("title") or "")).strip()
            if not title or not rules.official_ok(title):
                continue
            region = rules.region_for(it.get("locations") or [], strict=True)
            if region is None:
                continue
            posted = it.get("posted") or ""
            # A "Summer" posting from before June of this year belongs to last summer's cycle.
            if posted and posted < TODAY[:4] + "-06-01" and "summer" in title.lower() and "2027" not in title:
                continue
            tier, kws = rules.tier_for(title)
            if not tier:
                continue
            company = it.get("company") or name
            ck = ckey(company)
            req = norm_req(it.get("req")) or req_from_url(it.get("url"))
            match = (by_req.get((ck, req)) if req else None) or by_req.get((ck, req_from_url(it.get("url")))) \
                or by_title.get((ck, tkey(title, company)))
            if match:
                match["official"] = True
                if match.get("source") == "SimplifyJobs":
                    match["url"] = it.get("url") or match["url"]
                dup += 1
                continue
            rid = "o_" + hashlib.sha1(f"{ck}|{req or tkey(title, company)}".encode()).hexdigest()[:16]
            if rid in rows:
                continue
            r = {
                "id": rid, "company": company, "title": title, "url": it.get("url", ""),
                "locations": list(dict.fromkeys(l for l in (it.get("locations") or []) if l))[:4], "posted": posted,
                "tier": tier, "keywords": kws, "degrees": rules.degrees_for(title),
                "usPersonLikely": rules.us_person_likely(company, title), "big": rules.is_big(company),
                "source": "官網", "official": True, "region": region, "term": rules.term_for(title),
                "group": group, "req": req,
            }
            rows[rid] = r
            index(r)
            kept += 1
        status.append({"name": name, "ok": True, "fetched": len(items), "kept": kept, "matchedSimplify": dup,
                       "error": "", "seconds": round(time.time() - t0, 1)})

    # 3. First-seen dates and the "new today" list
    first, last = state.get("firstSeen", {}), state.get("lastSeen", {})
    new_ids = []
    for r in rows.values():
        if r["id"] in first:
            r["firstSeen"] = first[r["id"]]
        elif r["group"] in initialized:
            r["firstSeen"] = TODAY
            new_ids.append(r["id"])
        else:
            r["firstSeen"] = r["posted"] or TODAY
        first[r["id"]] = r["firstSeen"]
        last[r["id"]] = TODAY
    ran = {"simplify"} if status and status[0]["ok"] else set()
    for s in status[1:]:
        if s["ok"] and s["fetched"] > 0:
            ran.add("official:" + s["name"])
    initialized |= ran
    cutoff = (datetime.date.fromisoformat(TODAY) - datetime.timedelta(days=150)).isoformat()
    for rid in [k for k, v in last.items() if v < cutoff]:
        last.pop(rid, None)
        first.pop(rid, None)

    # 4. Board document (kept under the 256 KiB database limit)
    out = []
    for r in rows.values():
        r = dict(r)
        r.pop("group", None)
        r.pop("req", None)
        r["locations"] = list(dict.fromkeys(r.get("locations") or []))[:4]
        r["keywords"] = (r.get("keywords") or [])[:3]
        out.append(r)
    out.sort(key=lambda d: (d["firstSeen"], d["posted"]), reverse=True)

    def size(rs):
        return len(json.dumps(rs, ensure_ascii=False).encode())

    order = {"stretch": 0, "related": 1, "core": 2}
    while size(out) > MAX_BYTES:
        victim = min(range(len(out)), key=lambda i: (order[out[i]["tier"]], out[i]["firstSeen"]))
        out.pop(victim)

    from collections import Counter
    c = Counter(d["tier"] for d in out)
    official_ok = sum(1 for s in status[1:] if s["ok"] and s["fetched"] > 0)
    board = {
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runDate": TODAY,
        "source": f"SimplifyJobs + {official_ok} 個公司官網",
        "counts": {"total": len(out), "core": c["core"], "related": c["related"], "stretch": c["stretch"],
                   "newToday": len([i for i in new_ids if any(r["id"] == i for r in out)]),
                   "official": sum(1 for d in out if d.get("official")),
                   "taiwan": sum(1 for d in out if d.get("region") == "TW")},
        "newIds": [i for i in new_ids if any(r["id"] == i for r in out)],
        "sources": status,
        "rows": out,
    }
    with open(os.path.join(DATA, "board.json"), "w", encoding="utf-8") as f:
        json.dump(board, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(DATA, "status.json"), "w", encoding="utf-8") as f:
        json.dump({"updatedAt": board["updatedAt"], "counts": board["counts"], "sources": status}, f,
                  ensure_ascii=False, indent=1)
    state["firstSeen"], state["lastSeen"], state["initialized"] = first, last, sorted(initialized)
    with open(os.path.join(DATA, "state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, separators=(",", ":"))
    print(json.dumps(board["counts"], ensure_ascii=False))
    for s in status:
        print(f"{'OK ' if s['ok'] else 'ERR'} {s['name']:<45} fetched={s['fetched']:<5} kept={s['kept']:<4} {s['error']}")


if __name__ == "__main__":
    main()
