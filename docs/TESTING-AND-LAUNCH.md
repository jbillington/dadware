# Testing & Launch Plan

**Last updated:** Nov 14, 2026
**Status:** The signed beta is out. `v1.0-beta` is a public GitHub release with the signed, notarized, stapled `AskDad.dmg`, and justaskdad.app links to it (Nov 11, 2026). The checks left before we invite testers are in `BACKLOG.md`, "What to do next".
**Related:** `docs/roadmap/BETA-OUTREACH-PLAN.md` (where to find testers outside family and friends, and how to talk about AI use).

## What You Have

- A Mac-only scanner for storage and memory. It is read-only and makes no network calls.
- Letter grades, dad-style commentary and a self-contained HTML report.
- A signed, notarized DMG that holds `Ask Dad.app`. The app is a thin launcher: it opens Terminal, runs the scan, and opens the report in the browser. Terminal, not Ask Dad, asks for each permission and needs Full Disk Access.
- The same scanner as a command-line tool (`askdad`). The Homebrew tap is not ready and is not part of the beta.
- A landing page at justaskdad.app, with a sample report (`site/sample-report.html`).
- A feedback banner in every report: "Ask Dad is in beta, and I'd love to hear from you", with an email button for john@dadware.net.
- A public GitHub repo with the source code (MIT license).

## Distribution

- **Everyone:** send the landing page link. The Download button gets the latest `AskDad.dmg`. The tester drags the app to Applications and double-clicks it.
- **On a phone:** the landing page has an "Email yourself the link" note.
- **Technical users:** the GitHub release and the source. No Homebrew tap yet.

## Testing Phases

### Phase 1: Family

**Goal:** Does it work on someone else's Mac without you there?

Send the landing page link. The page tells them what to expect: a Terminal window opens, the scan runs, and the report opens in the browser.

**What to watch for:**
- Does the download → drag to Applications → double-click flow work without help?
- Do they accept the "are you sure?" prompt that macOS shows for every downloaded app?
- Do they understand the permission prompts, which come from Terminal and not from Ask Dad?
- Does the report open in the browser?
- Do the grades make sense for their Mac?

**Ask them:**
1. Did anything confuse you?
2. Did the report tell you what to do?
3. Did the grades match how your Mac feels?
4. Would you run it again?

### Phase 2: Friends and colleagues

**Goal:** Does it work on Macs you have never seen?

Same link, but you can't walk them through it. The landing page has to do the work. Ask each tester to send it on to one more person, such as the person in their family who always fixes the Mac.

**Widen the test surface:**
- macOS versions. The app needs macOS 11 or later. Most important: Sonoma, Sequoia and Tahoe. Tahoe failed with the old unsigned binary (`BACKLOG.md`, "Retest on Tahoe").
- Hardware: Intel and Apple Silicon.
- Disk states: nearly full, mostly empty, with an external or Time Machine drive attached.
- Permissions: a Mac where Terminal has no Full Disk Access.

Record each tester's Mac (chip and macOS version). This fills the clean-machine matrix in `BACKLOG.md`, Milestone 3.

### Phase 3: Public

**Goal:** Does anyone who doesn't know you care?

Start only when Phases 1 and 2 show the app works on unseen Macs. `docs/roadmap/BETA-OUTREACH-PLAN.md` has the full list of places. On Reddit:

**Where to post:**
- r/macapps: the main audience.
- r/mac: broader, good for "I built a thing" posts.
- r/SideProject: welcomes AI-built projects with a story.
- Help threads in r/mac, r/MacOS and r/applehelp: answer the question first, then mention Ask Dad only if it helps.

**Do NOT post to:**
- r/commandline: hostile to AI-built projects (see the outreach plan), and the wrong audience.
- r/apple: they remove it.
- r/programming: too general.

## Reddit Post Strategy

Read each subreddit's rules first. Some now require you to say if AI wrote the code. Say it either way.

### Title (pick one)

- "I built a free Mac app that grades your storage A to F and explains what's using the space"
- "My daughter's Mac was full, so I built a tool that gives the disk a report card"
- "Ask Dad: a read-only Mac scanner that tells you what's eating your storage"

### Post Body

```
I built a free tool for Mac that scans your storage and memory, then
gives you a report card with letter grades (A to F) and a report that
shows what is taking up space and what it is.

It's read-only. It never deletes anything, and it never connects to
the internet. It just tells you what's there.

What it does:
- Finds your biggest files and folders, including the Trash and
  hidden app caches, and grades your free space
- Shows which apps use the most memory (it groups Chrome's and
  Safari's helper processes)
- Writes an HTML report you can browse, with a sample on the site

Download and sample report: https://justaskdad.app
Source: [GitHub repo link]

It's signed and notarized by Apple. Right now the app opens a Terminal
window to run the scan, then opens the report in your browser. If people
find it useful, I'll make it a proper native Mac app.

Why: my daughter's Mac said the disk was full and she didn't know what
to do. I wanted a tool that explains it.

About me: I learned to program in BASIC, Fortran and Pascal, then
spent my career on the business side of software. AI wrote most of
the code. I designed it and tested it on real Macs.

Free, MIT licensed, no tracking. I'm looking for beta testers and
feedback on whether the grades make sense.
```

Replace the "About me" paragraph with John's own words when the landing page copy is written.

### Tips

- Include a screenshot of the report card. Reddit is visual.
- Reply to every comment in the first 2 hours.
- Be honest: "beta", "looking for feedback".
- Say AI wrote most of the code. Don't call it "AI-powered": it isn't, and that phrase gets roasted.
- If someone asks "why not ncdu / DaisyDisk / GrandPerspective?", answer in one line: those show what is big; Ask Dad explains what it is and whether it matters, for people who don't know.
- Don't post to 5 subreddits on the same day. It looks like spam.

## GitHub Release Setup

The release procedure is in `BACKLOG.md`, "Next — the road to a signed beta", step 1. In short:

- Build, sign and notarize with `build_executable.sh`, `sign_and_notarize.sh`, `make_app.sh` and `make_dmg.sh`.
- Attach the DMG under exactly the name `AskDad.dmg`. The site's Download button links to `releases/latest/download/AskDad.dmg`.
- Do not mark the release as a pre-release. `latest` skips pre-releases.
- Tag the commit the binary was built from.

## Screenshot Strategy

Take 2 or 3 screenshots:

1. The report card with letter grades and the dad comment (the hook).
2. The Terminal window while the scan runs.
3. The folder chart from the report.

**Take them from `tests/fixtures/storage_scan.snapshot.html` or `site/sample-report.html`, never from a real scan.** A real report shows file names (licenses, tax and medical papers) and the home path. Save landing-page images in `site/img/`.

## What Feedback to Listen For

**Signals that matter:**
- "The grades don't match my experience": grading needs tuning.
- "I don't know what to do with this": the advice needs to be clearer.
- "It asked for permissions and I said no": the permission copy needs work.
- "It didn't open" or "macOS blocked it": a Gatekeeper or signing problem. Get the macOS version and chip.
- "I'd use this if it could [X]": real feature requests.

**Signals to ignore:**
- "Why not just use ncdu": different audience.
- "You should rewrite this in Rust": no.

## Success Metrics

- 10 to 20 testers outside the family run it.
- It runs on Intel and Apple Silicon, and on Sonoma, Sequoia and Tahoe.
- Someone says the report helped them find something to clean up.
- You learn what breaks on Macs you have never seen.
- 1 or 2 feature requests that surprise you.

When these are met, start the Swift app.
