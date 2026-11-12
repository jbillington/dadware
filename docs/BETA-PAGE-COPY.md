# Beta page copy: justaskdad.app

Copy for the landing page during the beta. It is the content brief for the design work: the design decides the layout, this file decides the words. The page has one job: **get the right people to download the DMG, install it, and send feedback.**

Items in `[CHECK: ...]` are facts to confirm before launch. Do not publish a claim that the build does not support.

## Copy rules

1. **One action.** Every section leads to the download. There is one primary button, shown twice: at the top and at the bottom. No other button looks like it.
2. **Say what the button does.** "Download Ask Dad for Mac", not "Get started" or "Try it".
3. **Answer the doubts beside the button.** Size, macOS version, price and "beta" go directly under the button, in small text. People decide there.
4. **Short words, short sentences.** Readers include kids and adults who are not technical. One idea per sentence.
5. **Dad's voice, lightly.** One joke per section at most. Facts first, then the joke.
6. **Never promise more than the build does.** If a step opens Terminal, say so. A surprise at install time loses more testers than an honest sentence on the page.
7. **Plain text for the email address**, next to every `mailto:` link. Some browsers have no mail app set up.

---

## 1. Hero (above the fold)

**Eyebrow:** Free beta for Mac

**Headline:** Mac full? Just ask Dad.

**Subhead:** Ask Dad checks your Mac, grades your storage from A to F, and shows you what is using the space, in plain English.

**Primary button:** Download Ask Dad for Mac

**Under the button (small text):**
Free beta · Version 1.0 beta · macOS 11 or later · [CHECK: size] MB
[CHECK: chip support, for example "Apple silicon and Intel" or "Apple silicon only"]

**Trust line (one line, below the details):**
Read-only. It never deletes anything, and nothing leaves your Mac.

**Visual:** a screenshot of a real report card with a grade. Alt text: "An Ask Dad report card showing a B grade for storage, with the largest folders listed below."

### Download link best practice

- **Link straight to the DMG file.** Do not link to the GitHub Releases page; most people do not know what to click there.
- **Use a URL that does not change.** Upload the DMG to each GitHub release with a fixed file name, `AskDad.dmg`, as well as the versioned name. Then the button can always use:
  `https://github.com/jbillington/dadware/releases/latest/download/AskDad.dmg`
  `make_dmg.sh` writes `AskDad-<version>.dmg`, so the fixed-name copy is a release step. Without it, the page must change on every release.
- **Add the `download` attribute** to the link so that browsers save the file and do not try to open it.
- **On phones and tablets**, the button cannot install anything. Show this instead:
  - **Button:** Email me the link
  - **Small text:** Ask Dad runs on a Mac. Send yourself the link and open it there.
  - The link is `mailto:?subject=Ask%20Dad%20for%20Mac&body=https%3A%2F%2Fjustaskdad.app`. It opens the visitor's own mail app with the to-field empty. No data goes to us.

---

## 2. After the click: install steps

Show these right below the hero, or swap them in after the click. People need them in the moment the DMG lands in Downloads.

**Heading:** Three steps, then Dad takes it from here

1. **Open the file** `AskDad-1.0-beta.dmg` from your Downloads.
2. **Drag Ask Dad** onto the Applications folder.
3. **Double-click Ask Dad** in Applications. [CHECK: current build] A Terminal window opens and the scan runs. Your report opens in your browser when the scan is done, usually in [CHECK: typical time] minutes.

**Note under the steps:**
macOS may ask if Ask Dad can see your Desktop, Documents and Downloads folders. Click **Allow** so that Dad can measure them. If you click **Don't Allow**, the report skips those folders and tells you so.

[CHECK: notarized] If the DMG is notarized, add: "Apple has checked this app for malware, so it opens with no warnings." If it is not notarized, replace that sentence with the right-click → **Open** instructions. Do not show both.

> When the app stops opening Terminal (the app-mode work in `docs/roadmap/PERMISSIONS-PLAN.md`), change step 3 to: "Double-click Ask Dad in Applications. Your report opens in your browser."

---

## 3. What Dad tells you

**Heading:** What you get

- **A grade from A to F.** One letter that says how your storage is doing, and why.
- **The big stuff, ranked.** Your largest folders and files, including the Trash and the app caches you cannot see in Finder.
- **Advice, not orders.** Dad says what each thing is and what happens if you clear it. You decide.
- **A memory check.** See which apps use the most memory, and if you need to worry. (Run `askdad cpu` from Terminal.) [CHECK: is the CPU scan reachable from the app?]

---

## 4. Safe by design

**Heading:** Dad looks. He doesn't touch.

Ask Dad only reads. It never deletes, moves or changes a file. It makes no network calls: no account, no tracking, no uploads. Your report is a file on your Mac, and you choose who sees it.

**Link:** Read the source code on GitHub →

---

## 5. Full Disk Access (optional)

**Heading:** Want the full picture?

Ask Dad works without any setup. To see the Trash and your Photos, Mail and Messages libraries, macOS needs you to turn on Full Disk Access. No app can turn this on for you; that is Apple's rule.

1. Open **System Settings** → **Privacy & Security** → **Full Disk Access**.
2. Turn on **[CHECK: Terminal, for the current build; Ask Dad, after app mode]**.
3. Run Ask Dad again.

**Small text:** Skip this, and the report says what it could not see. It never shows a zero for something it did not measure.

---

## 6. Beta feedback

**Heading:** You're a beta tester. Tell Dad what broke.

This is a beta, so some things will be rough. Every email gets read by John, the dad who built it.

**Button (secondary style):** Email feedback
**Plain text beside it:** john@dadware.net

Link:
`mailto:john@dadware.net?subject=Ask%20Dad%20beta%20feedback%20(1.0-beta)`

**What helps most:**
- What you expected, and what happened instead
- Your Mac model and macOS version (Apple menu → About This Mac)
- A screenshot, if something looks wrong

**Privacy note (small text):** Please don't attach your report. It lists your file and folder names. A screenshot of the part that looks wrong is enough.

---

## 7. Short FAQ

**Is it really free?**
Yes, during the beta. [CHECK: plans after the beta]

**Will it delete my files?**
No. Ask Dad only reads. You make every cleanup decision yourself.

**Does it send my data anywhere?**
No. It makes no network calls. The report stays on your Mac.

**Why does it ask for access to my folders?**
macOS asks for every app that reads your Desktop, Documents and Downloads. Ask Dad needs this to measure those folders. That's all it does with the access.

**I'm comfortable in Terminal. Is there a command-line version?**
Yes. [CHECK: tap published] `brew install jbillington/tap/askdad`

---

## 8. Closing call to action

**Heading:** Find out what's filling your Mac.

**Primary button:** Download Ask Dad for Mac
**Under the button:** Free beta · macOS 11 or later · [CHECK: size] MB

---

## 9. Footer

Ask Dad is made by DadWare. · Feedback: john@dadware.net · Source code on GitHub · MIT License

---

## Before launch: checklist

- [ ] DMG uploaded to a GitHub release, with a fixed-name copy `AskDad.dmg`
- [ ] Download button tested from Safari and Chrome on a Mac that has never run Ask Dad
- [ ] File size and chip support filled in from the real DMG
- [ ] Notarization status confirmed, and section 2 matches it
- [ ] Install steps match the build (Terminal window or not)
- [ ] Both `mailto:` links tested in Apple Mail and in a browser with no mail app
- [ ] Phone view shows "Email me the link", not the download button
- [ ] Report screenshot uses a test account, with no real names in paths
- [ ] `<title>` and meta description in `site/index.html` still match the hero
