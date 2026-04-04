# Testing & Launch Plan

## What You Have

- A working Mac-only CLI that scans storage and memory
- Gives letter grades, dad-style commentary, HTML reports
- Standalone executable — no Python needed
- 8.4MB ZIP ready to share

## Testing Phases

### Phase 1: Family (This Week)

**Goal:** Does it work on someone else's Mac without you there?

**How to share:** AirDrop or iMessage the ZIP.

**What to tell them:**

> I made a thing that scans your Mac and tells you what's eating your storage. Download this, open Terminal, and type:
>
> cd ~/Downloads/yourdad
> chmod +x yourdad
> ./yourdad
>
> It'll open a report in your browser. Tell me if anything breaks or confuses you.

**What to watch for:**
- Do they get stuck on the security warning? (This will be the #1 issue)
- Does the executable run on their macOS version?
- Does the HTML report open correctly?
- Do the grades make sense for their machine?
- Do they understand what to do with the information?

**Ask them:**
1. Did anything confuse you?
2. Did the grades match how your Mac feels?
3. Would you run this again?

### Phase 2: Friends / Colleagues (Week 2)

**Goal:** Does it work on Macs you've never seen with setups you can't predict?

Same ZIP, but now you can't walk them through it. The README has to do the work. If people get stuck, that's a README problem, not a code problem.

**Expand the test surface:**
- Different macOS versions (Monterey, Ventura, Sonoma, Sequoia)
- Different hardware (Intel vs Apple Silicon)
- Different disk states (full, empty, external drives)
- Different permission states (with/without Full Disk Access)

### Phase 3: Reddit (Week 3+)

**Goal:** Does anyone besides people who know you care?

**Where to post:**
- r/macapps — the primary audience. People who try Mac utilities.
- r/mac — broader, but relevant. Good for "I built a thing" posts.
- r/commandline — appreciates CLI tools, will give technical feedback.
- r/opensource — if you've pushed to a public GitHub repo.

**Do NOT post to:**
- r/apple — they'll remove it (no self-promotion)
- r/programming — too generic, will get buried

---

## Reddit Post Strategy

### Title Options (pick one)

Short, specific, no hype:
- "I built a free CLI tool that grades your Mac's storage health (A-F)"
- "yourdad — a Mac cleanup scanner that gives your disk a report card"
- "Made a tool that finds what's eating your Mac's storage and gives it a letter grade"

### Post Body Template

```
I built a free, open-source command-line tool for Mac that scans your
storage and memory usage, then gives you a report card with letter
grades (A-F) and an HTML report showing exactly what's taking up space.

It's read-only — it never deletes anything. Just tells you what's there.

**What it does:**
- Scans storage: finds your biggest files and folders, grades your free space,
  checks Downloads/Desktop clutter
- Scans memory: shows what apps are hogging RAM, groups Chrome/Safari processes,
  tells you if memory pressure is a problem
- Generates an interactive HTML report you can browse

**How to run it:**
Download the ZIP, extract, open Terminal:
    cd ~/Downloads/yourdad
    chmod +x yourdad
    ./yourdad

Report opens in your browser automatically.

It's a standalone executable — no Python or dependencies needed.
macOS will show a security warning on first run (not code-signed yet) —
right-click → Open to get past it.

GitHub: [link]
Download: [GitHub Releases link]

Looking for feedback on whether the grades make sense and if the report
is useful. Built this because I got tired of explaining disk space to
family members.

MIT licensed / free / no tracking / no data leaves your machine.
```

### What Makes Reddit Posts Work

**Do:**
- Include a screenshot of the HTML report. Reddit is visual. A text post about a CLI tool with no images gets scrolled past.
- Reply to every comment in the first 2 hours. Engagement drives visibility.
- Be honest about what it is: "POC", "looking for feedback", "built this for fun". Reddit respects humility.
- Mention it's free, open source, and doesn't phone home. Trust matters.

**Don't:**
- Don't call it "AI-powered" or use buzzwords. r/macapps will roast you.
- Don't post the same thing to 5 subreddits on the same day. That looks like spam.
- Don't argue with critics. Say "good point, I'll look at that" and move on.

---

## GitHub Release Setup

Before posting to Reddit, set up a proper GitHub Release so the download link looks legitimate:

```bash
# Tag the release
git tag -a v0.1-poc -m "v0.1-poc: Initial proof of concept"
git push origin v0.1-poc
```

Then on GitHub:
1. Go to your repo → Releases → "Create a new release"
2. Select the v0.1-poc tag
3. Title: "v0.1-poc — Proof of Concept"
4. Upload `yourdad-0.1-poc-2025-11-28-013.zip`
5. Description:

```
First proof of concept release.

**What it does:**
- Scans Mac storage and memory
- Grades your disk health (A-F)
- Generates an interactive HTML report

**Requirements:**
- macOS (Intel or Apple Silicon)
- No Python or other dependencies needed

**Known limitations:**
- Not code-signed (macOS will show a security warning — right-click → Open)
- macOS only
- Storage scan can be slow on large disks

**How to run:**
1. Download and extract the ZIP
2. Open Terminal
3. `cd ~/Downloads/yourdad && chmod +x yourdad && ./yourdad`
```

A GitHub Releases link looks trustworthy. A Google Drive link does not.

---

## Screenshot Strategy

Take 2-3 screenshots to include in Reddit posts and the GitHub release:

1. **The HTML report card** — the grades section with letter grades and the dad comment. This is the hook. Crop it tight.
2. **The terminal output** — a few lines showing the scan running with the branded header. Shows it's a real CLI tool.
3. **The storage breakdown** — the folder chart or top files section from the HTML report. Shows the actual value.

Save these in the repo as `docs/screenshots/` and reference them in the GitHub release.

---

## What Feedback to Listen For

**Signals that matter:**
- "The grades don't match my experience" → grading thresholds need tuning
- "I don't know what to do with this information" → need clearer actionable advice
- "It took too long" → scan performance needs work
- "I couldn't get past the security warning" → need code signing or Homebrew
- "I'd use this if it could [X]" → feature ideas from real users

**Signals to ignore:**
- "Why not just use ncdu/htop" → different audience, different problem
- "Real dads don't use the terminal" → the dad theme is a hook, not a target demographic
- "You should rewrite this in Rust" → no

---

## Success Metrics for POC

You're not launching a product. You're validating whether anyone cares. Success at this stage is:

- **5+ people outside your family run it successfully** — the executable works on other Macs
- **Someone says the report helped them find something to clean up** — the tool is actually useful
- **You learn what breaks** — macOS versions, permissions, disk configs you didn't test
- **You get 1-2 feature requests that surprise you** — tells you what people actually want vs what you assumed

That's enough to decide whether to keep building or move on.
