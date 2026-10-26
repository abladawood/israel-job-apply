# Israel Job Apply

A small Python toolkit that finds new jobs in Israel from company career boards, scores them against your
profile, and helps you apply quickly. It opens each job in Chrome, pre-fills your details and CV, and
**you review the form and press Submit yourself**.

It never submits for you. Custom questions (work authorization, salary...) are always left for you.

---

## Start here: setup for beginners (no file editing)

You need two free programs and about 15 minutes.

### 1. Install what you need

- **Python 3**: download from [python.org/downloads](https://www.python.org/downloads/) and install it.
  On Windows, tick **"Add python.exe to PATH"** on the first installer screen.
- **Google Chrome**: [google.com/chrome](https://www.google.com/chrome/). The tool uses it to open the job forms.

### 2. Get the project

On the GitHub page of this project, click the green **Code** button, then **Download ZIP**, and unzip it.
You now have a folder called `israel-job-apply`. Remember where it is (for example in Downloads).

### 3. Open the terminal and go to the folder

The terminal is a window where you type commands. Every command in this guide is typed there, then you press **Enter**.

**On a Mac**
1. Press **Cmd + Space**, type **Terminal**, press Enter.
2. Type `cd ` (the letters c and d, then a space), then **drag the `israel-job-apply` folder** from Finder into the Terminal window. The folder path appears. Press Enter.
3. Type `ls` and press Enter. You should see files like `setup.py`, `collect.py` and `apply.py`. If you do, you're in the right place.

**On Windows**
1. Open the `israel-job-apply` folder in File Explorer.
2. Click the address bar at the top, type `cmd`, and press Enter. A black window opens, already in the right folder.
3. Type `dir` and press Enter. You should see `setup.py`, `collect.py` and `apply.py`.

> **Mac vs Windows:** on a Mac, type `python3`. On Windows, type `python` instead (for example `python setup.py`).
> Every command below is shown with `python3`.

### 4. Install the one extra package

```
python3 -m pip install -r requirements.txt
```

Wait until it finishes and you see your prompt again.

### 5. Create your profile with the setup wizard

```
python3 setup.py
```

It asks simple questions and creates your private `profile.json` for you:

- your name, email, phone and links (LinkedIn, website). You can leave links empty.
- years of experience.
- your CV: **drag your CV file into the terminal window** and press Enter. It is copied into a `cv` folder for you. A PDF works best.
- the kind of jobs you want: words that should appear in the job title (for example `marketing, product manager`),
  words you don't want (`intern, junior`), your skills, and the cities you'd work in.
- **the companies to check.** The tool comes with ~250 Israeli tech companies. If you work in another field,
  answer `n` to "Keep it?" and add your own: paste a link to a company's careers page (or to one of its job postings),
  or just type the company name. One per line, empty line to finish.

You only do this once. To change your answers later, run `python3 setup.py` again.

### 6. Find jobs

```
python3 collect.py
```

The first run takes a few minutes. It checks many company career pages and prints the matching jobs
with a score from 0 to 100. A higher score means a closer match. The list is saved in `jobs.csv`.

### 7. Apply

```
python3 apply.py --min 65 --limit 10
```

- `--min 65` means only jobs scoring 65 or more. Use a lower number (like 55) to see more jobs.
- `--limit 10` means at most 10 jobs this time.

For each job, Chrome opens and the terminal shows the job. Then:

1. If you don't see the application form, click **Apply** in Chrome.
2. Go back to the terminal and press **Enter**. The tool fills in your details and attaches your CV. You will see `CV attached.`
3. In Chrome, **check every field**, answer any questions yourself, and press **Submit**.
4. Go back to the terminal and type one letter, then Enter:
   - `y` = I submitted it
   - `s` = skip this job
   - `q` = quit for today

Don't close the Chrome window while the tool is running. Jobs you answered `y` or `s` for never come back.

---

## Every day after that

Open the terminal in the project folder (step 3), then run:

```
python3 collect.py
python3 apply.py --min 65 --limit 10
```

`collect.py` only shows jobs that are **new since your last run**, so some days there are only a few, or none.
That is normal. To see every open job you haven't applied to yet, run `python3 collect.py --all`.

To see what you've already handled: `cat applied.csv` (Mac) or `type applied.csv` (Windows).

---

## If something goes wrong

| What you see | What to do |
|---|---|
| `command not found: python3` | Python isn't installed, or the terminal was open during the install. Install Python, then open a **new** terminal window. On Windows use `python`. |
| `No such file or directory` / file not found | You're not in the project folder. Repeat step 3 and check with `ls` (Mac) or `dir` (Windows). |
| `SSL: CERTIFICATE_VERIFY_FAILED` (Mac) | Open Finder, go to Applications, open the **Python 3.x** folder and double-click **Install Certificates.command**. Then run the command again. |
| `Need profile.json` | You haven't run the wizard yet. Run `python3 setup.py`. |
| `CV NOT FOUND` | Your CV isn't in the `cv` folder. Run `python3 setup.py` again and drag your CV in, or copy it to `cv/my_cv.pdf`. |
| Chrome doesn't open / browser error | Install Google Chrome and try again. |
| `0 NEW matching jobs` | Nothing new since your last run. Try `python3 collect.py --all`, or lower `--min`. |
| Few or no jobs at all | Your job-title words may be too narrow. Run `python3 setup.py` again with more title words. |
| Form fields stay empty | Click **Apply** first, then press Enter in the terminal. If a form still doesn't fill, fill it by hand and carry on. |

To stop the tool at any time, press **Ctrl + C** in the terminal.

---

## How it works

1. `collect.py` pulls open jobs from public career-board systems (Greenhouse, Lever, Ashby, Comeet and Workday),
   scores each job against your profile (title, location, skills, seniority) and writes `jobs.csv`.
2. `apply.py` opens each job in Chrome, fills your details and CV, waits for you to submit,
   and logs the result in `applied.csv` so nothing repeats.

Workday jobs are listed but need an account on each company's site, so you fill those in yourself.

## Customize (optional)

- `profile.json`: your details and the filters used for scoring. Re-run `setup.py` to change them.
- Add more companies later: `python3 add_company.py`, then paste careers-page links or company names.
  Tip: open a job on the company's careers site; if the address contains `greenhouse`, `lever`, `ashbyhq`,
  `comeet` or `myworkdayjobs`, the tool understands it. A company with its own custom careers site can't be added.
- `companies.json`: the companies the tool checks (the commands above edit it for you). Add the company name as it appears in its careers-page address
  (`boards.greenhouse.io/<name>`, `jobs.lever.co/<name>`, `jobs.ashbyhq.com/<name>`). Names that don't exist are skipped.
  Comeet and Workday entries need more details; copy the examples already in the file.

## For developers: manual setup

```bash
git clone https://github.com/<you>/israel-job-apply.git
cd israel-job-apply
python3 -m pip install -r requirements.txt
cp profile.example.json profile.json     # edit it, or run python3 setup.py
mkdir -p cv && cp /path/to/your_cv.pdf cv/
```

## Privacy

`profile.json`, your CV, `applied.csv`, `jobs.csv` and the caches are in `.gitignore`, so your personal data
is not committed. They stay on your computer only.

## Notes and limits

- Scores are a rough keyword match, not a judgment of fit. Always read the job description.
- Career sites change; Comeet and Workday support is best-effort. Boards that fail are skipped with a message.
- Apply only to roles you actually want, and respect the terms of the sites you use.

## License

MIT
