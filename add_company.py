"""Add companies to companies.json by pasting careers-page links or company names.
Run:  python3 add_company.py      (also used by setup.py)
Recognised links: boards.greenhouse.io/<name>, jobs.lever.co/<name>, jobs.ashbyhq.com/<name>,
comeet.com/jobs/<name>/<id>, <company>.wdN.myworkdayjobs.com/<site>.  A plain company name is
also accepted: it is tried on Greenhouse, Lever and Ashby (unknown names are skipped)."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

def parse(text):
    """returns ("names", slug) | ("comeet", {...}) | ("workday", {...}) | None"""
    t = text.strip()
    if not t: return None
    m = re.search(r"greenhouse\.io/(?:embed/job_board\?for=)?([A-Za-z0-9_-]+)", t) \
        or re.search(r"lever\.co/([A-Za-z0-9_-]+)", t) \
        or re.search(r"ashbyhq\.com/([A-Za-z0-9_.%-]+)", t)
    if m: return ("names", m.group(1).lower())
    m = re.search(r"comeet\.com/jobs/([^/\s?]+)/([0-9A-Za-z.]+)", t)
    if m:
        return ("comeet", {"name": m.group(1).lower(), "url": f"https://www.comeet.com/jobs/{m.group(1)}/{m.group(2)}"})
    m = re.search(r"https?://([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([^/?#\s]+)", t)
    if m:
        return ("workday", {"name": m.group(1), "host": f"{m.group(1)}.{m.group(2)}.myworkdayjobs.com",
                            "tenant": m.group(1), "site": m.group(3)})
    if re.fullmatch(r"[A-Za-z0-9 ._-]{2,40}", t):          # plain company name
        return ("names", re.sub(r"[^a-z0-9-]", "", t.lower().replace(" ", "")))
    return None

def add_interactive(fresh_start_question=True):
    path = os.path.join(HERE, "companies.json")
    C = json.load(open(path))
    if fresh_start_question:
        a = input("The tool comes with a list of ~250 Israeli tech companies. Keep it? (y = keep, n = start empty) [y]: ").strip().lower()
        if a == "n":
            C = {"names": [], "comeet": [], "workday": []}
    print("\nAdd companies you want to apply to. Paste a link to the company's careers page or to one of its")
    print("job postings (best), or just type the company name. One per line. Press Enter on an empty line to finish.")
    added = 0
    while True:
        line = input("> ").strip()
        if not line: break
        r = parse(line)
        if not r:
            print("  Couldn't recognise that. Paste a job link from the company's careers page, or type just the company name.")
            continue
        kind, val = r
        if kind == "names":
            if val and val not in C.setdefault("names", []):
                C["names"].append(val); added += 1; print(f"  Added '{val}' (the tool will check whether it has a job board).")
            else: print("  Already in the list.")
        else:
            lst = C.setdefault(kind, [])
            if any(e["name"] == val["name"] for e in lst): print("  Already in the list.")
            else: lst.append(val); added += 1; print(f"  Added {kind}: {val['name']}")
    json.dump(C, open(path, "w"), indent=1, ensure_ascii=False)
    if os.path.exists(os.path.join(HERE, "boards_cache.json")):
        os.remove(os.path.join(HERE, "boards_cache.json"))   # re-check boards on the next collect
    print(f"\nSaved companies.json ({added} added). The next 'collect.py' run will check them.")

if __name__ == "__main__":
    add_interactive(fresh_start_question=False)
