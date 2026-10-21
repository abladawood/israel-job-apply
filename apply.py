import os
"""Assisted apply: opens each job in jobs.csv (score >= MIN), pre-fills standard fields
and uploads your CV, then PAUSES so you review and press Submit yourself.
Usage: python apply.py [--min 60] [--limit 10]
Uses your installed Google Chrome (no browser download needed). Setup: pip install playwright"""
import csv, json, argparse, datetime as dt
from playwright.sync_api import sync_playwright

os.chdir(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists("profile.json") or not os.path.exists("jobs.csv"):
    raise SystemExit("Need profile.json (copy profile.example.json) and jobs.csv (run collect.py first).")
P = json.load(open("profile.json"))
ap = argparse.ArgumentParser(); ap.add_argument("--min", type=int, default=60); ap.add_argument("--limit", type=int, default=10)
a = ap.parse_args()

FIELDS = {  # selector fragments -> profile values
    "first_name": P["first_name"], "last_name": P["last_name"], "email": P["email"],
    "phone": P["phone"], "linkedin": P["linkedin"], "github": P["github"],
}
def fill_frame(fr):
    n = 0
    for inp in fr.query_selector_all("input[type=text],input[type=email],input[type=tel],input[type=url],input:not([type])"):
        key = " ".join(filter(None, [inp.get_attribute("name"), inp.get_attribute("id"),
              inp.get_attribute("aria-label"), inp.get_attribute("placeholder")])).lower()
        val = None
        if "first" in key and "name" in key: val = FIELDS["first_name"]
        elif "last" in key and "name" in key: val = FIELDS["last_name"]
        elif "email" in key: val = FIELDS["email"]
        elif "phone" in key: val = FIELDS["phone"]
        elif "linkedin" in key: val = FIELDS["linkedin"]
        elif "github" in key: val = FIELDS["github"]
        elif key.strip() in ("name", "full_name", "full name", "fullname"): val = f'{FIELDS["first_name"]} {FIELDS["last_name"]}'
        if val and val != "FILL_ME":
            try: inp.fill(val); n += 1
            except Exception: pass
    files = fr.query_selector_all("input[type=file]")
    if files:
        cv = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), P["resume_path"]))
        if not os.path.exists(cv):
            print(f"!! CV NOT FOUND at {cv} -- put your CV PDF there (or fix resume_path in profile.json)")
        else:
            def attrs(f):
                return " ".join(filter(None, [f.get_attribute("name"), f.get_attribute("id"),
                        f.get_attribute("aria-label"), f.get_attribute("data-field"), f.get_attribute("accept")])).lower()
            pick = [f for f in files if any(k in attrs(f) for k in ("resume", "cv")) and "cover" not in attrs(f)]
            if not pick: pick = [f for f in files if "cover" not in attrs(f)][:1]
            for f in pick[:1]:
                try:
                    f.set_input_files(cv); n += 1; fr.wait_for_timeout(1500)
                    print("CV attached.")
                except Exception as e:
                    print(f"!! could not attach CV: {str(e)[:120]}")
    return n

def fill(page):
    # fill the newest open tab AND its embedded frames (Greenhouse often embeds the form in an iframe)
    pages = [pg for pg in page.context.pages if not pg.is_closed()]
    if not pages: return 0
    total = 0
    for fr in pages[-1].frames:
        try: total += fill_frame(fr)
        except Exception: pass
    return total

def click_apply(page):
    for sel in ["a:has-text('Apply for this job')", "a:has-text('Apply Now')", "button:has-text('Apply Now')",
                "a:has-text('Apply')", "button:has-text('Apply')"]:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click(); page.wait_for_timeout(2500); return True
        except Exception: pass
    return False

import os
seen = set()
if os.path.exists("applied.csv"):
    seen = {r["url"] for r in csv.DictReader(open("applied.csv"))}
jobs = [r for r in csv.DictReader(open("jobs.csv")) if int(r["score"]) >= a.min and r["url"] not in seen][: a.limit]
print(f"{len(jobs)} jobs to go through (already handled ones are skipped)")
new = not __import__("os").path.exists("applied.csv")
log = open("applied.csv", "a", newline=""); w = csv.writer(log)
if new: w.writerow(["url","company","title","date","status"])
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=False); ctx = b.new_context()
    for j in jobs:
        page = ctx.new_page(); page.goto(j["url"]); page.wait_for_timeout(2500)
        if j["ats"] == "workday":
            print("(Workday: needs an account/login on that company's site; fill it in manually.)")
        try: click_apply(page)
        except Exception: pass
        try: n = fill(page)
        except Exception: n = 0
        print(f"\n[{j['score']}%] {j['company']} - {j['title']}\nAuto-filled {n} fields.")
        print("If the application form isn't showing, click Apply in Chrome yourself, then come back here.")
        input("Press Enter here to (re)fill the form: ")
        try: n = fill(page)
        except Exception: n = 0
        print(f"Filled {n} fields. Answer custom questions, then press Submit in Chrome.")
        s = input("Submitted? [y]es / [s]kip / [q]uit: ").strip().lower()
        if s not in ("y", "s", "q"): s = "s"   # Enter or anything else = skip, so it never repeats
        if s == "y": w.writerow([j["url"], j["company"], j["title"], dt.date.today(), "applied"])
        elif s == "s": w.writerow([j["url"], j["company"], j["title"], dt.date.today(), "skipped"])
        log.flush()
        try: page.close()
        except Exception: pass
        if s == "q": break
    b.close()
