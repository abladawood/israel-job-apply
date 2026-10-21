"""Collect jobs from public career-board APIs, score them against your profile, write jobs.csv.

Supported systems: Greenhouse, Lever, Ashby (by company name), Comeet (by careers-page URL),
Workday (by tenant details). Boards that don't exist are skipped automatically.

Usage:
  python3 collect.py            only jobs NEW since your last run (daily mode)
  python3 collect.py --all      every open matching job you haven't applied to
  python3 collect.py --rescan   re-discover which Greenhouse/Lever/Ashby boards exist
"""
import json, csv, sys, os, re, ssl, datetime as dt, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

try:
    import certifi; CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    CTX = ssl.create_default_context()

HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
if not os.path.exists("profile.json"):
    sys.exit("profile.json not found. Copy profile.example.json to profile.json and edit it.")
P = json.load(open("profile.json")); C = json.load(open("companies.json"))
ALL = "--all" in sys.argv
UA = {"User-Agent": "Mozilla/5.0"}

def http(url, data=None, headers=None, timeout=25):
    h = dict(UA); h.update(headers or {})
    body = json.dumps(data).encode() if data is not None else None
    if body: h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read().decode("utf-8", "replace")

def get(url): return json.loads(http(url))

def strip_html(s): return re.sub(r"<[^>]+>", " ", s or "")

def score(title, loc, text):
    t, l, x = title.lower(), (loc or "").lower(), (text or "").lower()
    if any(b in t for b in P["title_exclude"]): return 0
    if not any(a in t for a in P["title_include"]): return 0
    if not any(a in l for a in P["location_include"]): return 0
    s = 40 + min(40, sum(1 for k in P["skills"] if k in x or k in t) * 5)
    if any(p in t for p in P["seniority_penalty"]): s -= 20
    m = re.findall(r"(\d+)\+?\s*(?:-\s*\d+\s*)?years", x)
    if m and max(int(n) for n in m[:3]) > P["years_experience"] + 2: s -= 20
    return max(0, min(100, s))

# ---------- fetchers: each returns a list of {title, loc, text, posted, url} or None ----------
def fetch(ats, tok):
    try:
        if ats == "greenhouse":
            d = get(f"https://boards-api.greenhouse.io/v1/boards/{tok}/jobs?content=true")
            return [dict(title=j["title"], loc=(j.get("location") or {}).get("name", ""),
                         text=j.get("content", ""), posted=(j.get("updated_at") or "")[:10],
                         url=j["absolute_url"]) for j in d.get("jobs", [])]
        if ats == "lever":
            out = []
            for j in get(f"https://api.lever.co/v0/postings/{tok}?mode=json"):
                ts = j.get("createdAt")
                out.append(dict(title=j["text"], loc=(j.get("categories") or {}).get("location", "") or "",
                    text=j.get("descriptionPlain", ""), url=j["hostedUrl"],
                    posted=dt.datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d") if ts else ""))
            return out
        if ats == "ashby":
            d = get(f"https://api.ashbyhq.com/posting-api/job-board/{tok}")
            return [dict(title=j["title"], loc=j.get("location", "") or "", text=j.get("descriptionPlain", ""),
                         posted=(j.get("publishedAt") or "")[:10], url=j["jobUrl"]) for j in d.get("jobs", [])]
    except urllib.error.HTTPError as e:
        if e.code not in (404, 400): print(f"  error {ats}/{tok}: HTTP {e.code}", file=sys.stderr)
    except Exception as e:
        print(f"  error {ats}/{tok}: {e}", file=sys.stderr)
    return None

def fetch_comeet(entry):
    """entry: {"name": "...", "url": "https://www.comeet.com/jobs/<name>/<uid>"}"""
    try:
        m = re.search(r"comeet\.com/jobs/([^/]+)/([0-9A-Za-z.]+)", entry["url"])
        if not m: raise ValueError("bad comeet url")
        uid = m.group(2)
        html = http(f"https://www.comeet.com/jobs/{m.group(1)}/{uid}")
        t = re.search(r'"token"\s*:\s*"([0-9A-Za-z.]+)"', html) or re.search(r"token=([0-9A-Za-z.]+)", html)
        if not t: raise ValueError("token not found on careers page")
        d = get(f"https://www.comeet.co/careers-api/2.0/company/{uid}/positions?token={t.group(1)}&details=true")
        out = []
        for j in d:
            loc = j.get("location") or {}
            loc_s = ", ".join(filter(None, [loc.get("city"), loc.get("country"), loc.get("name")]))
            text = strip_html(" ".join(str(x.get("value", "")) for x in (j.get("details") or [])))
            out.append(dict(title=j.get("name", ""), loc=loc_s, text=text,
                posted=(j.get("time_updated") or "")[:10],
                url=j.get("url_active_page") or j.get("url_comeet_hosted_page") or j.get("position_url") or ""))
        return out
    except Exception as e:
        print(f"  comeet/{entry.get('name')}: {str(e)[:100]}", file=sys.stderr)
        return None

def fetch_workday(entry):
    """entry: {"name","host":"intel.wd1.myworkdayjobs.com","tenant":"intel","site":"External"}"""
    try:
        base = f"https://{entry['host']}"
        api = f"{base}/wday/cxs/{entry['tenant']}/{entry['site']}/jobs"
        out, off = [], 0
        while off < 200:
            d = json.loads(http(api, data={"appliedFacets": {}, "limit": 20, "offset": off,
                                           "searchText": entry.get("search", "Israel")}))
            posts = d.get("jobPostings", [])
            if not posts: break
            for j in posts:
                path = j.get("externalPath", "")
                loc = (j.get("locationsText") or "") + " " + path.split("/")[2].replace("-", " ") if path.count("/") >= 2 else (j.get("locationsText") or "")
                pt = (j.get("postedOn") or "").lower(); posted = ""
                if "today" in pt: posted = dt.date.today().isoformat()
                elif "yesterday" in pt: posted = (dt.date.today() - dt.timedelta(days=1)).isoformat()
                else:
                    n = re.search(r"(\d+)", pt)
                    if n: posted = (dt.date.today() - dt.timedelta(days=int(n.group(1)))).isoformat()
                out.append(dict(title=j.get("title", ""), loc=loc, text="", posted=posted,
                                url=f"{base}/en-US/{entry['site']}{path}"))
            off += 20
            if off >= d.get("total", 0): break
        return out
    except Exception as e:
        print(f"  workday/{entry.get('name')}: {str(e)[:100]}", file=sys.stderr)
        return None

# ---------- 1) discover Greenhouse/Lever/Ashby boards (cached) ----------
cache = json.load(open("boards_cache.json")) if os.path.exists("boards_cache.json") and "--rescan" not in sys.argv else {}
names = sorted(set(C.get("names", [])))
todo = [(a, n) for n in names for a in ("greenhouse", "lever", "ashby") if f"{a}/{n}" not in cache]
if todo:
    print(f"discovering boards ({len(todo)} checks, first run only)...")
    with ThreadPoolExecutor(16) as ex:
        for (a, n), jobs in zip(todo, ex.map(lambda t: fetch(*t), todo)):
            cache[f"{a}/{n}"] = jobs is not None
    json.dump(cache, open("boards_cache.json", "w"))
live = sorted(k for k, v in cache.items() if v)

# ---------- 2) fetch everything ----------
tasks = [(k.split("/")[0], k.split("/", 1)[1], lambda k=k: fetch(*k.split("/", 1))) for k in live]
tasks += [("comeet", e["name"], lambda e=e: fetch_comeet(e)) for e in C.get("comeet", [])]
tasks += [("workday", e["name"], lambda e=e: fetch_workday(e)) for e in C.get("workday", [])]
with ThreadPoolExecutor(12) as ex:
    results = list(ex.map(lambda t: t[2](), tasks))
ok = [f"{t[0]}/{t[1]}" for t, r in zip(tasks, results) if r is not None]
print(f"{len(ok)} boards responded: {', '.join(ok)}")

rows = []
for (ats, tok, _), jobs in zip(tasks, results):
    for j in jobs or []:
        sc = score(j["title"], j["loc"], j["text"])
        if sc and j["url"]:
            rows.append(dict(score=sc, company=tok, title=j["title"], location=j["loc"].strip(),
                             posted=j["posted"], ats=ats, url=j["url"]))

# ---------- 3) drop applied / previously seen ----------
applied = {r["url"] for r in csv.DictReader(open("applied.csv"))} if os.path.exists("applied.csv") else set()
seen = set(json.load(open("seen_jobs.json"))) if os.path.exists("seen_jobs.json") else set()
rows = [r for r in rows if r["url"] not in applied]
new_rows = [r for r in rows if r["url"] not in seen]
out = rows if ALL else new_rows
out.sort(key=lambda r: (r["score"], r["posted"]), reverse=True)
json.dump(sorted(seen | {r["url"] for r in rows}), open("seen_jobs.json", "w"))
with open("jobs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["score", "company", "title", "location", "posted", "ats", "url"])
    w.writeheader(); w.writerows(out)
print(f"\n{len(new_rows)} NEW matching jobs ({len(rows)} open matches not yet applied). jobs.csv has {len(out)} rows. Top 15:")
for r in out[:15]: print(r["score"], r["company"], "|", r["title"], "|", r["location"], "|", r["posted"])
