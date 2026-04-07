# Testing & Launch Plan

## What You Have

- A working Mac-only CLI that scans storage and memory
- Gives letter grades, dad-style commentary, HTML reports
- Standalone executable (no Python needed, ~8.5MB)
- Landing page at dadware.vercel.app (or whatever domain)
- GitHub repo with source code

## Distribution

- **Family/friends:** AirDrop or iMessage the binary, text them the landing page URL
- **Reddit/public:** Landing page link + GitHub Releases link
- **Future:** Homebrew tap (`brew install jbillington/tap/yourdad`)

## Testing Phases

### Phase 1: Family (This Week)

**Goal:** Does it work on someone else's Mac without you there?

Just text them the landing page URL. The page has instructions for both Finder and Terminal users.

**What to watch for:**
- Do they get stuck on the security warning?
- Does the executable run on their macOS version?
- Does the HTML report open correctly?
- Do the grades make sense for their machine?

**Ask them:**
1. Did anything confuse you?
2. Did the grades match how your Mac feels?
3. Would you run this again?

### Phase 2: Friends / Colleagues (Week 2)

**Goal:** Does it work on Macs you've never seen?

Same link, but now you can't walk them through it. The landing page has to do the work.

**Expand the test surface:**
- Different macOS versions (Monterey, Ventura, Sonoma, Sequoia)
- Different hardware (Intel vs Apple Silicon)
- Different disk states (full, empty, external drives)

### Phase 3: Reddit (Week 3+)

**Goal:** Does anyone besides people who know you care?

**Where to post:**
- r/macapps -- the primary audience
- r/mac -- broader, good for "I built a thing" posts
- r/commandline -- appreciates CLI tools
- r/opensource -- if repo is public

**Do NOT post to:**
- r/apple -- they'll remove it
- r/programming -- too generic

## Reddit Post Strategy

### Title (pick one)

- "I built a free CLI tool that grades your Mac's storage health (A-F)"
- "yourdad -- a Mac cleanup scanner that gives your disk a report card"
- "Made a tool that finds what's eating your Mac's storage and gives it a letter grade"

### Post Body

```
I built a free, open-source tool for Mac that scans your storage and
memory, then gives you a report card with letter grades (A-F) and an
HTML report showing exactly what's taking up space.

It's read-only -- it never deletes anything. Just tells you what's there.

What it does:
- Finds your biggest files and folders, grades your free space
- Shows what apps are hogging RAM, groups Chrome/Safari processes
- Generates an interactive HTML report you can browse

Landing page: [dadware.vercel.app link]
GitHub: [repo link]

No Python or dependencies needed. One file, runs on any Mac.
macOS will show a security warning on first run (not code-signed yet).

Built this because my daughter called me when her Mac said the disk
was full and she didn't know what to do. So I made a tool that
explains it.

MIT licensed / free / no tracking / no data leaves your machine.
Looking for feedback on whether the grades make sense.
```

### Tips

- Include a screenshot of the HTML report card. Reddit is visual.
- Reply to every comment in the first 2 hours.
- Be honest: "POC", "looking for feedback", "built this for fun".
- Don't call it "AI-powered". r/macapps will roast you.
- Don't post to 5 subreddits the same day. Looks like spam.

## GitHub Release Setup

```bash
git tag -a v0.1-poc -m "v0.1-poc: Initial proof of concept"
git push origin v0.1-poc
```

Then on GitHub: Releases > Create new release > select tag > upload the binary > paste description.

## Screenshot Strategy

Take 2-3 screenshots:

1. The HTML report card with letter grades and dad comment (the hook)
2. The terminal output showing the scan running
3. The storage breakdown from the HTML report

Save in `docs/screenshots/` and use on the landing page and GitHub release.

## What Feedback to Listen For

**Signals that matter:**
- "The grades don't match my experience" -- grading needs tuning
- "I don't know what to do with this" -- need clearer advice
- "I couldn't get past the security warning" -- need code signing or Homebrew
- "I'd use this if it could [X]" -- real feature requests

**Signals to ignore:**
- "Why not just use ncdu" -- different audience
- "You should rewrite this in Rust" -- no

## Success Metrics

- 5+ people outside your family run it successfully
- Someone says the report helped them find something to clean up
- You learn what breaks on machines you've never seen
- 1-2 feature requests that surprise you
