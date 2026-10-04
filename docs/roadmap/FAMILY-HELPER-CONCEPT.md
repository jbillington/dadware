# Family Helper Concept

**Status:** Concept — not scheduled. A direction for the product after the beta MVP ships, written to capture the thinking while it is fresh. Nothing here changes the current roadmap.
**Related:** `PERMISSIONS-PLAN.md` (the signed `.app` is a prerequisite), `utils/llm_prompt.py` (the seed of the AI integration), `docs/COMPETITIVE-COMPARISON.md`.

---

## The Problem

Ask Dad today answers "why is my Mac full?" That is a once-a-year problem with a known fix, and GrandPerspective, DaisyDisk, and Apple's own Storage pane answer it too. The real assets of this codebase are not the scanner. They are:

1. **Trust.** Read-only, no network, stdlib only.
2. **Translation.** Grades and the dad voice turn numbers into a decision a non-technical person can act on.
3. **The LLM prompt.** The code already turns machine state into text an AI can reason about.

A 10x product solves a problem people have every week, or one they cannot solve at all today. That problem is not a full disk. It is **the family tech person who gets the call and has no data.**

Every family, small business, and volunteer group has one person who hears "my Mac is slow" or "it says the disk is full." That person loves the caller but cannot see the screen, and the caller cannot explain what is wrong. Nothing exists between "nothing" and enterprise MDM (Jamf, Kandji, Mosyle). MDM needs device enrollment, an Apple Business Manager account, a per-device monthly fee, and it can wipe a Mac. A family helper will not install that on a parent's laptop.

## The Concept

A small helper lives on each family Mac. It checks the Mac's health once a week and gives it a letter grade. If the owner wants, it shares that report card with the family's tech person. If not, it never does. Nobody can control the Mac, delete files, or watch the screen. It only looks, and only at sizes and settings, never at photos, messages, or documents.

The helper advises. The owner acts. The dad voice stays the brand. The real dad is the user.

### On the owner's Mac

| Capability | Benefit |
|---|---|
| **Scheduled read-only scans** via a launch agent, weekly or on idle | Trends, not snapshots. "Your disk fills in 23 days" before it is full. |
| **Menu bar grade** | One letter at a glance. A child or a grandparent understands a report card. |
| **Ask on demand** | When the Mac feels slow, one click explains why in plain words. The owner learns to self-diagnose. |
| **More sensors, same read-only rule** | Days until disk full, Time Machine last success, iCloud Photos sync state, pending macOS updates and days pending, battery cycle count and health, login items and launch agents, last restart, FileVault, Find My, OS support status, disk health from `diskutil`, recent app crash count. Each is a stdlib or shell read. |
| **One-time setup wizard** | Full Disk Access needs a manual click. The wizard shows the exact screen, and the helper can send a pre-filled setup link. |
| **Local forever, free forever** | With no account and no network, everything above works. The product earns trust before it asks for anything. |

### Sharing, with the network optional

The owner picks a level and can change it any time.

- **Level 0, local only.** Reports stay in the owner's home folder. Nothing leaves the Mac. This is the default.
- **Level 1, share by hand.** The owner clicks "Send to Jane," sees exactly what the bundle contains, and sends it by AirDrop, Messages, Mail, or as a file. Zero infrastructure. This is the family case most of the time.
- **Level 2, linked.** The owner scans a QR code from the helper once. After each scan the agent drops a summary into a shared iCloud Drive folder, or later a hosted relay. The owner sees a log of every bundle sent and can unlink with one click.

The bundle is one file: the JSON manifest the tool already writes plus the self-contained HTML report. Three redaction levels: full paths, folder names only, or counts and sizes only. File contents, documents, messages, and browser data are never in it.

### For the helper

| Capability | Benefit |
|---|---|
| **Fleet view** — one row per Mac: owner, grade, trend, last seen, free space, days until full, backup age, update age | A Sunday glance replaces five phone calls. |
| **Alerts on change only** — grade drops, backup older than 14 days, disk under 10%, update pending over 30 days, battery health under 80% | No noise. The helper acts only when something moved. |
| **History per Mac** | "It got slow after the OS update" becomes visible instead of a guess. |
| **What changed** — diff between the last two reports | Finds the cause, not just the symptom. |
| **Advice the helper sends, the owner performs** — a plain-language numbered note with a Finder "show me" link | The helper never touches the Mac. The owner stays in charge and learns. Read-only stays intact on both ends. |
| **Notes and reminders per Mac** | "Dad's photos are on the silver drive." The helper's memory lives in the tool. |
| **Weekly digest** in the dad voice | The helper stays informed without opening the app. |
| **Works offline** — opens any bundle from a folder | Level 1 sharing needs no server. |

### What it never does

- Never deletes a file, changes a setting, or runs a command for the user.
- Never reads the inside of files, messages, browser history, or photos.
- Never sends anything without a click. Never calls AI by itself.
- Never requires an account. The free local version is the whole product for most families.

## AI Integration: Sign in with ChatGPT

OpenAI's Sign in with ChatGPT lets open-source and locally-run apps let a person sign in with their own ChatGPT Plus or Pro account and use that plan's allowance, with no API key and no developer billing. The person clicks "Sign in with ChatGPT," picks their account in the browser, and approves the app. Plan usage is open to open-source and personal local projects, which is exactly what this tool is.

- **The "Ask ChatGPT" button.** The report already contains a ready-made question about the Mac (`utils/llm_prompt.py`). One click sends it to the person's own ChatGPT and the answer comes back in plain words.
- **The helper can use it too.** In the fleet view, the helper signs in once and can ask "which family Mac needs attention first this month?"
- **Nothing is sent unless the user clicks.** The weekly scan never talks to the internet. Only the button does, and it shows the exact text before sending. The "no AI calls at runtime" promise becomes "no AI calls unless you press the button," and the button says so.
- **No cost to the maker and none extra to the family.** The person uses the plan they already pay for.
- **Sign in once, everywhere.** Sign-in also gives identity, so the same account can tie a family's Macs together for linked sharing with no separate login.

**Constraints to verify before building:** plan-backed usage is for open-source and locally-run projects. A hosted commercial version needs OpenAI's partner program or API billing. The feature is new and the rules will move. Source: https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt

### An agent that acts

Sign in with ChatGPT would also power a local agent that archives or moves files, and Codex CLI is the proof: it is OpenAI's own open-source local agent on the same sign-in. It is possible. It also cuts against the one promise the product stands on. If it is ever built:

- **Two apps, not one mode.** The scanner stays read-only forever. The agent is a separate install with a separate name.
- **Archive, never delete.** Move to a dated folder, an external drive, or the Trash. Never `rm`. Deletion stays a human act in Finder.
- **Plan, show, confirm, undo.** A plain-words plan the owner approves on their own screen, each step logged with one-click undo, nothing while the owner is absent.
- **Narrow scope by default.** Downloads, Caches, Logs, Trash, old installers. Never Documents, Desktop, Photos, Mail.
- **The helper proposes, the owner disposes.** No remote "run" button, ever.

Decision: build the read-only product first. Add the agent only when real helpers ask for it.

## Monetization Without AI

Open-source core plus a paid Mac app is a proven model (Rectangle / Rectangle Pro, AlDente / AlDente Pro, Maccy).

**Legal shape**

- The scanner stays MIT. It is the trust story.
- The menu-bar app and the helper fleet app can be closed source or source-available (PolyForm Noncommercial, Fair Source). This is "open core."
- The existing trademark clause does the heavy lifting: anyone can fork the scanner, nobody can call it Ask Dad or DadWare.
- Charging for the signed, notarized DMG is fine under any open license. The source is free; the double-click convenience is paid.

**What people pay for**

Free: the scanner CLI and the one-Mac menu-bar app with the weekly grade. Paid: the parts that matter once you care for more than one Mac or more than one week.

- More than one Mac (the fleet view).
- History: trends, days until full, what changed.
- Alerts and the Sunday digest.
- Linked sharing (hand sharing stays free; automatic sync is paid; a hosted relay is the recurring tier).
- Notes, reminders, and the advice-sending flow.
- PDF and shareable report export.

**Starting prices**

| Tier | Price | Includes |
|---|---|---|
| Free | $0 | One Mac, scan today, share by hand. |
| Family | ~$30 once, one year of updates | Up to five Macs, history, alerts, notes, advice flow. |
| Family Plus | ~$20/year | Hosted relay and email digest, once one exists. |
| Small business / consultant | per Mac per month | Ten Macs and up. Same app, different checkout. |

Sell direct (Paddle, Lemon Squeezy). The Mac App Store is out because its sandbox blocks Full Disk Access. Setapp is a second channel later.

**Two rules**

- Never gate the scan itself or the single-Mac grade. The free tier must be the whole promise for a person who cares for one Mac.
- Keep the Homebrew CLI fully free and fully capable. Technical users are the reviewers and the word of mouth. Charge the helper, never the owner.

## What Exists and What Is New

Already built and reusable without a rewrite: the scanners, grading, the dad voice, the HTML renderer, the JSON manifest, and the LLM prompt.

New work, in order:

1. A signed menu-bar app that owns the schedule and the Full Disk Access flow (the Swift wrapper in the roadmap becomes required, not optional).
2. A bundle format with redaction levels.
3. The helper app with the fleet view and offline bundle import.
4. Level 1 transport (share sheet).
5. Level 2 with iCloud Drive as the first relay, so it ships with no server.
6. Sign in with ChatGPT behind an explicit button.

## Risks to Test First

- Will a relative accept Full Disk Access on a stranger's advice? Test the wizard with real people over 60.
- Will helpers install it? Pitch five of them. The sign to look for: "I would put this on my parents' Mac next visit."
- Apple's notarization and TCC rules change. Signing has to be right before any of this ships.
- Sign in with ChatGPT eligibility and rate limits are new and may change.
