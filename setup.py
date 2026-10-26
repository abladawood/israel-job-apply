"""Friendly setup: asks a few questions and creates profile.json for you (no file editing needed).
Run:  python3 setup.py      (Windows: python setup.py)"""
import json, os, shutil, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
example = json.load(open("profile.example.json"))

def ask(q, default=""):
    d = f" [{default}]" if default else ""
    a = input(f"{q}{d}: ").strip()
    return a or default

def ask_list(q, default_list):
    print(f"{q}\n  (separate with commas; press Enter to keep: {', '.join(default_list)})")
    a = input("> ").strip()
    return [x.strip().lower() for x in a.split(",") if x.strip()] if a else default_list

if os.path.exists("profile.json"):
    if input("profile.json already exists. Overwrite it? (y/n): ").strip().lower() != "y":
        sys.exit("Nothing changed.")

print("\n== About you ==")
p = dict(example)
p["first_name"] = ask("First name")
p["last_name"] = ask("Last name")
p["email"] = ask("Email")
p["phone"] = ask("Phone (with country code, e.g. +972501234567)")
p["linkedin"] = ask("LinkedIn profile link (or leave empty)")
p["github"] = ask("GitHub link (or leave empty)")
p["website"] = ask("Personal website link (or leave empty)")
try: p["years_experience"] = int(ask("Years of full-time experience", "3"))
except ValueError: p["years_experience"] = 3

print("\n== Your CV ==")
print("Drag your CV file into this window and press Enter (or type its full path).")
src = input("CV file: ").strip().strip("'\"").replace("\\ ", " ")
os.makedirs("cv", exist_ok=True)
if src and os.path.exists(src):
    ext = os.path.splitext(src)[1] or ".pdf"
    dest = os.path.join("cv", "my_cv" + ext)
    shutil.copy(src, dest)
    p["resume_path"] = dest.replace(os.sep, "/")
    print(f"Copied your CV to {dest}")
else:
    p["resume_path"] = "cv/my_cv.pdf"
    print("CV not found. Put your CV file at cv/my_cv.pdf before you apply.")

print("\n== What jobs do you want? ==")
p["title_include"] = ask_list(
    "Words that should appear in the job title (e.g. marketing, product manager, data analyst):",
    example["title_include"])
p["title_exclude"] = ask_list(
    "Words in titles you do NOT want (e.g. intern, junior, director):", example["title_exclude"])
p["skills"] = ask_list(
    "Your skills/tools (jobs that mention them score higher; e.g. excel, sql, figma):", example["skills"])
p["location_include"] = ask_list(
    "Cities/places you would work in:", example["location_include"])

if not p["linkedin"]: p["linkedin"] = "FILL_ME"
if not p["github"]: p["github"] = ""
json.dump(p, open("profile.json", "w"), indent=2, ensure_ascii=False)
print("\n== Companies ==")
print("The tool checks a built-in list of Israeli tech companies. If you work in another field,")
print("you should add the companies you care about (you can also do this later with: python3 add_company.py).")
print("you can use AI to generate company names that relate to your field")

if input("Add/choose companies now? (y/n) [y]: ").strip().lower() != "n":
    import add_company
    add_company.add_interactive(fresh_start_question=True)

print("\nDone! Saved profile.json (it stays on your computer only).")
print("Next:  python3 collect.py   then   python3 apply.py --min 65 --limit 10")
