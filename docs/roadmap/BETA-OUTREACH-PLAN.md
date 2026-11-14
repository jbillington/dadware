# Beta Outreach Plan

**Status:** Notes, opened Nov 14, 2026. Not scheduled. Use it when the signed DMG is ready for testers outside the family.
**Goal:** Find 10 to 20 beta testers outside friends and family. Confirm that Ask Dad works on Macs we have not seen. Then start the Swift app.
**Related:** `docs/TESTING-AND-LAUNCH.md` (phases and the Reddit post draft), `docs/COMPETITIVE-COMPARISON.md`, `FAMILY-HELPER-CONCEPT.md`.

---

## Why this plan exists

The plan in `TESTING-AND-LAUNCH.md` lists r/commandline as a place to post. Do not post there. On Oct 28, 2026 a top post in that subreddit ("This sub is now an endless parade of slop projects and I'm unsubbing", 443 upvotes) complained about AI-built projects. The writer said they are "not anti AI usage". They objected to four things:

1. AI use that is not labelled.
2. Recreations of popular tools that already exist.
3. Authors who "don't know how to program".
4. Projects that nobody will maintain.

That subreddit is also the wrong audience. Ask Dad is mainly a double-click app for non-technical people. Command-line users are not those people.

## How to answer the four complaints

Answer them on the landing page, in the "Why I made this" section (`site/index.html:271`). John writes this copy by hand, so that it reads as a person.

| Complaint | Answer |
|---|---|
| AI use is not labelled | Say plainly that AI wrote most of the code. Do not lead with it, and do not hide it. |
| The author can't program | John learned BASIC, Fortran and Pascal as a kid, then moved to the business side of software. He knows how computers, file systems, Unix, macOS and Windows work. He made every design decision and tested on real Macs. |
| A copy of an existing tool | DaisyDisk, GrandPerspective, OmniDiskSweeper, `du` and `ncdu` show what is big. Ask Dad explains what it is and whether it matters, for people who don't know. Have this one-line answer ready. |
| Nobody will maintain it | Promise to keep it working. Give the feedback email. |

**Lead with facts a skeptic can check:** read-only, never deletes anything, no network calls, signed and notarized by Apple, has a test suite. Most people who distrust AI code are afraid of code that does damage. The read-only design answers that fear.

**Proof is stronger than a résumé.** Use real findings from testing:
- A real Mac's Trash held 14.3 GB. No folder list showed it, because the scan skipped dotfiles.
- Claude Desktop's `rootfs.img` showed 10 GB but used 8.5 GB on disk. John found the cause (`.img` was missing from the virtual-disk list) and fixed it.

## Where to find testers

In order of value:

1. **The family tech-support person.** In most families one person fixes everyone's Mac. That person is the best tester and the best way to reach more. Ask each tester: "Send this to the person who always asks you why their Mac is full." Each tester can bring 2 or 3 more. This also tests the idea in `FAMILY-HELPER-CONCEPT.md`.
2. **Help threads.** r/mac, r/MacOS and r/applehelp get "my Mac is full" posts every day. Give a real answer first. Mention Ask Dad only where it helps. Read each subreddit's self-promotion rules first.
3. **Communities where "built with AI" is a good story.** r/SideProject, r/ClaudeAI, r/ChatGPTCoding, Indie Hackers. Good feedback on the product and the launch, but most of these people are not end users.
4. **Founder communities.** Good for the landing page, onboarding and pricing. Not good for learning whether a parent understands the report.
5. **Offline groups.** Mac user groups (MUGs), library and senior-center tech help, school tech teachers and STEM clubs, parent and homeschool groups, Nextdoor.
6. **Beta directories.** BetaList, Product Hunt "upcoming". Small return.

## Articles: tutorials that also find testers

**Idea (John, Nov 14):** Write tutorials on how to find big files with the tools that already exist, then say what Ask Dad does differently. Possible articles:

- How to find your biggest files with Finder (and the Storage pane in System Settings).
- How to use `du` to see what is taking up space.
- How to use GrandPerspective.
- Where the hidden space goes: Trash, caches, Photos and Messages libraries, iPhone backups.

**Why this is good:**
- It helps the reader first, so it does not read as an ad. A link to a helpful article is welcome in a help thread, where a link to a product often is not.
- It shows that John knows the subject, which answers complaints 2 and 3.
- It is honest about the other tools. The difference is clear without a sales pitch: Ask Dad is easier to install, is not only for the Terminal, and explains what it finds.
- It builds search traffic for justaskdad.app over time.

**Limits:**
- Search traffic takes months. It will not find beta testers quickly. Its quick value is as a link in help threads.
- Finder and `du` tutorials already exist in large numbers. Make each one different with real numbers and screenshots from real scans.
- Keep the site rule: no third-party requests. Host the articles on justaskdad.app (for example `/guides/`), with the site's own fonts and images.

**Suggested first step:** Write one article, "Where did my Mac's storage go?", built from real findings (the 14.3 GB Trash, hidden caches). Use it as the link in help-thread answers. Write more only if that one brings testers.

## Target and feedback

- 10 to 20 good testers is enough. We do not need hundreds.
- Give each one a short feedback form. The main question: "Did the report tell you what to do?"
- Record each tester's Mac (Intel or Apple Silicon, macOS version). This fills the clean-machine matrix in `BACKLOG.md`, Milestone 3.
