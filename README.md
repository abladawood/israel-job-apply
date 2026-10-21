# Israel Job Apply

A small Python toolkit that finds new software-engineering jobs in Israel from company career boards,
scores them against your profile, and helps you apply quickly: it opens each job in Chrome, pre-fills
your details and CV, and **you review and press Submit yourself**.

It does not auto-submit. Custom questions (work authorization, salary...) are always left for you.

## How it works

1. `collect.py` pulls open jobs from public career-board APIs, scores each one against `profile.json`
   (title, location, skills, seniority) and writes `jobs.csv`. Only jobs that are **new since your last run**
   are listed (use `--all` to see everything).
2. `apply.py` opens each job from `jobs.csv` in Google Chrome, fills your name, email, phone, links and CV,
   waits for you to review and submit, and logs the result in `applied.csv` so nothing repeats.

Supported systems: **Greenhouse, Lever, Ashby** (by company name), **Comeet** (by careers-page URL),
**Workday** (collect only; Workday applications need an account on each company's site).

## Setup (macOS / Linux)

```bash
git clone https://github.com/<you>/israel-job-apply.git
cd israel-job-apply
python3 -m pip install -r requirements.txt      # use a venv if pip complains
cp profile.example.json profile.json            # then edit it with your details
mkdir -p cv && cp /path/to/your_cv.pdf cv/      # match "resume_path" in profile.json
```

`apply.py` uses your installed **Google Chrome**, so no browser download is needed.
On macOS with Python from python.org, run `Install Certificates.command` once if you see SSL errors.

## Daily use

```bash
python3 collect.py                         # find jobs that are new since last time
python3 apply.py --min 65 --limit 10       # go through the best ones
```

- `--min` is the minimum match score (0-100) a job needs. Lower it to see more roles, raise it for fewer, better ones.
- `--limit` is the maximum number of jobs per run.
- For each job: click **Apply** in Chrome if the form isn't showing, press **Enter** in the terminal to fill the form,
  check everything and answer custom questions, press **Submit** in Chrome, then answer `y` (applied), `s` (skip) or `q` (quit).
- Don't close the Chrome window while the script is running.

Other options: `python3 collect.py --all` (include already-seen jobs), `--rescan` (re-discover boards).

## Configure

- `profile.json`: your details, skills, and the title/location filters used for scoring.
- `companies.json`:
  - `names`: company board names to try on Greenhouse, Lever and Ashby (the part in `boards.greenhouse.io/<name>`,
    `jobs.lever.co/<name>`, `jobs.ashbyhq.com/<name>`). Names that don't exist are skipped.
  - `comeet`: `{ "name": "...", "url": "https://www.comeet.com/jobs/<company>/<uid>" }`
  - `workday`: `{ "name", "host", "tenant", "site" }` taken from the company's `*.myworkdayjobs.com` URL.

## Privacy

`profile.json`, your CV, `applied.csv`, `jobs.csv` and the caches are in `.gitignore`, so your personal data is not committed.

## Notes and limits

- Scores are a rough keyword match, not a judgment of fit. Always read the job description.
- Career-site layouts change; Comeet and Workday support is best-effort. Boards that fail are skipped with a message.
- Be respectful of the sites you use and apply only to roles you actually want.

## License

MIT
