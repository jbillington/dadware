# Ask Dad FAQ: how the report works

How Ask Dad gets every grade, number and comment in its reports, in plain terms. The full
technical version, with every edge case, is [`GRADING.md`](GRADING.md).

Ask Dad only reads your Mac. It never deletes, moves or changes anything, and it makes no
network calls. Everything below is worked out on your Mac from what it can see.

---

## The storage report

### What does the big letter at the top mean?

It is a weighted average of four smaller grades, each scored from 0 to 100:

| What it grades | Share of the letter |
|---|---|
| Free space on the disk | 50% |
| Clutter in Downloads and Desktop | 20% |
| How much of the used space is your home folder | 15% |
| Mac app libraries (Photos, Music, Messages, Mail) | 15% |

```
overall score = 0.50 × free space
              + 0.20 × clutter
              + 0.15 × home folder share
              + 0.15 × app libraries
```

Every score, the four parts and the total, turns into a letter the same way:

| Score | Letter | Comment beside the overall letter |
|---|---|---|
| 90 or more | A | Excellent! |
| 80 to 89 | B | Good job! |
| 70 to 79 | C | Room for improvement |
| 60 to 69 | D | Needs work |
| under 60 | F | Critical issues |

Free space carries half the grade because a nearly full disk is the thing that actually
slows a Mac down.

### How is free space graded?

Free space is the share of the disk that is free: `free ÷ total × 100`. The score rises
with it and tops out at 40% free.

| Free space | Letter |
|---|---|
| 32.5% or more | A |
| 25% to 32.5% | B |
| 20% to 25% | C |
| 15% to 20% | D |
| under 15% | F |

The score is a set of straight lines joined together:

```
40% free or more    score = 100
25% to 40%          score = 80 + (free% − 25) × 1.33
15% to 25%          score = 60 + (free% − 15) × 2
10% to 15%          score = 40 + (free% − 10) × 4
under 10%           score = free% × 4
```

For example, 19% free scores 60 + 4 × 2 = 68, a D.

### Why does Finder show more free space than Ask Dad?

Finder's "Available" figure includes *purgeable* space: files macOS could remove on its own
if it needed room, such as iCloud copies, caches and local Time Machine snapshots. Ask Dad
counts only space that is free right now. Both numbers are right; they answer different
questions.

### How is clutter graded?

Ask Dad looks at only two folders, Downloads and Desktop, because they fill up fastest and
are the quickest to clear. Each folder adds problem points:

- over 5 GB: 1 point
- over 10 GB: 2 points

| Points | Score | Letter | What that looks like |
|---|---|---|---|
| 0 | 100 | A | both under 5 GB |
| 1 | 85 | B | one between 5 and 10 GB |
| 2 | 72 | C | one over 10 GB, or both over 5 GB |
| 3 | 62 | D | one over 10 GB and the other over 5 GB |
| 4 | 40 | F | both over 10 GB |

### What is the home folder share?

It is how much of the used space on the disk is in your home folder (the folder with your
name: Documents, Downloads, Desktop, Pictures, the Trash and anything else you keep there):

```
home folder share = home folder size ÷ used space × 100
```

A low share scores well. It means most of the used space belongs to macOS and your apps,
and your own files are not crowding the disk.

| Home folder share | Letter |
|---|---|
| up to 40% | A |
| 40% to 50% | B |
| 50% to 60% | C |
| 60% to 70% | D |
| 70% or more | F |

Hidden files (names starting with a dot) and app caches are left out of the folder sizes.
The Trash is the exception: it is counted, because it is often one of the biggest folders
on the Mac.

### How are Photos, Music, Messages and Mail graded?

Each library is graded against limits for its own kind, because 50 GB of photos is ordinary
and 50 GB of email is not. The library grade is the average of the libraries Ask Dad found.

| Library | A | B | C | D | F |
|---|---|---|---|---|---|
| Photos | up to 75 GB | 75 to 100 GB | 100 to 150 GB | 150 to 200 GB | over 200 GB |
| Music, creative apps | up to 35 GB | 35 to 50 GB | 50 to 75 GB | 75 to 100 GB | over 100 GB |
| Messages, Mail | up to 7.5 GB | 7.5 to 10 GB | 10 to 15 GB | 15 to 20 GB | over 20 GB |

A library that is a large share of everything on the disk loses extra points:

| Library's share of used space | Points taken off |
|---|---|
| over 20% | 5 |
| over 30% | 10 |
| over 50% | 20 |

Creative apps (GarageBand, Logic and Final Cut media) appear only if you have them.

### Why does the libraries row say "not scored"?

If Ask Dad could not measure every library, it leaves that row out of the grade instead of
guessing. That happens when a library needs Full Disk Access, took too long to measure, or
gave an error. The other three parts then share the whole grade:

```
overall score = (0.50 × free space + 0.20 × clutter + 0.15 × home folder share) ÷ 0.85
```

Ask Dad never grades something it did not measure. If it could not read something, the
report says so instead of counting it as zero.

### A worked example

A 250 GB disk with 19% free, tidy Downloads and Desktop, and a 30 GB Messages library:

```
free space         19% free                  68   D
clutter            nothing over 5 GB        100   A
home folder share  22% of used space        100   A
app libraries      average of four           88   B
   Photos 1.1 GB → 100,  Music 3.7 GB → 100,  Messages 29.9 GB → 53,  Mail 1.5 GB → 100

overall = 0.50 × 68 + 0.20 × 100 + 0.15 × 100 + 0.15 × 88
        = 34 + 20 + 15 + 13.2
        = 82.2  →  B, "Good job!"
```

### Why does Dad say something different from the grade?

Dad's comments and the letter are worked out separately. The letter averages four things;
Dad points at the most pressing one. In the example above the grade is a B, while Dad says
the disk is "getting tight", because free space is under 20%. Both are true.

Dad's colour (green, yellow or red) comes from these checks:

| What Dad sees | Colour |
|---|---|
| free space under 10% | red: needs attention |
| free space under 20% | yellow: stable but cluttered |
| Downloads over 5 GB, or Desktop over 5 GB | yellow |
| none of the above | green: all good |

The colour only ever goes up, from green to yellow to red, and never back down within one
report.

### What do "Top 10 Folders", "Top 25 Files" and "In the Trash" add up?

- **Top 10 Folders** and **Top 25 Files** are the total size of the biggest folders and
  files the scan found. They show where the space is, not what to delete: the list can
  include apps and system files you need.
- **In the Trash** is everything already in your Trash. That space comes back only when you
  empty it. The Trash has no grade of its own, because its size already counts against free
  space.

### Why are app caches and snapshots not graded?

Caches are apps doing their job, and they fill back up after you clear them. Local Time
Machine snapshots are managed by macOS, and macOS does not report how much space each one
uses. Ask Dad mentions both so you know where space went, but they don't change the grade.

### What does a GB mean here?

For disk sizes, 1 GB is 1,000,000,000 bytes. That is how Finder and About This Mac count, so
the numbers match what you see on your Mac. (Some tools count 1 GB as 1,073,741,824 bytes,
which makes the same file look about 7% smaller.)

Some files are measured by the space they really take on the disk, not the size they claim.
Virtual machine disks and Docker images can claim 64 GB while using only 9 GB; Ask Dad
reports the 9 GB.

### What about a scan of an external drive?

A drive that isn't your Mac's startup disk gets a shorter report with no letter grade: free
space, folder totals and the biggest files. The grades measure your home folder and Apple's
libraries, which are not on that drive.

---

## The CPU and memory report (`askdad cpu`)

### Does the memory report have a grade?

No. It shows a colour (green, yellow or red) and Dad's comments. A memory grade is planned
but not built yet.

### What is memory pressure, and where does it come from?

Memory pressure is macOS's own answer to "is this Mac short of memory right now?" Ask Dad
reads the setting macOS keeps for this (the same measure behind the pressure graph in
Activity Monitor) and reports it as is:

| macOS says | Ask Dad shows | Dad says |
|---|---|---|
| normal | 🟢 low | "memory looks fine. macOS is just using what it has." |
| warning | 🟡 medium | "memory's getting busy. quit what you're not using before it complains." |
| critical | 🔴 high | "memory's maxed out. macOS says it's under real pressure." |
| no answer | ⚪ unknown | "couldn't get a memory pressure reading from macOS, so i'm not guessing." |

If macOS doesn't give an answer, Ask Dad says it doesn't know. It never guesses "high".

### Why does "Free" look so small when the Mac is fine?

macOS keeps spare memory busy, for example holding recently closed apps and files so they
open faster. So memory that is completely unused is usually small on a healthy Mac. That is
why the report shows several numbers:

| Number | What it means | How it is worked out |
|---|---|---|
| **Free** | memory nothing is using at all | free pages |
| **Available** (approximate) | memory macOS could hand to an app quickly | free + inactive + purgeable pages |
| **Used** | memory in use, counted the way Activity Monitor does | active + wired + compressed pages |
| **Memory used by apps** (approximate) | every running process's memory, added up | sum of each process's resident memory |
| **Swap in use** | memory macOS has moved out to the disk right now | macOS's swap usage figure |

Look at the pressure colour first. A high "Used" figure with green pressure is normal.

"Available" is an estimate. Some purgeable memory is also counted as inactive, so it can
read a little high.

The HTML report, the terminal and the AI prompt all show the same figures.

### Why do the apps add up to more memory than the Mac is using?

Apps share memory. When several processes use the same shared piece, each one counts it as
its own, so the per-app totals count shared memory more than once. That makes them useful
for seeing which apps are biggest, not for adding up. For the same reason, quitting an app
"may free up to about" its total, not exactly that much.

### When does Dad suggest quitting apps, closing tabs or restarting?

Only when macOS reports warning or critical pressure. With normal pressure, a big browser or
a large Messages app is just a Mac using its memory, and closing things won't make it
faster.

| What Dad sees | Colour |
|---|---|
| pressure critical | red: needs attention |
| pressure warning | yellow: stable but cluttered |
| Chrome using over 50% of the CPU, or Photos analysing your library hard | yellow |
| a large Chrome, Safari or Messages, *while pressure is warning or critical* | yellow |
| none of the above | green: all good |

### Is RAM counted the same way as disk space?

No. RAM uses 1 GB = 1,073,741,824 bytes, because that is how Apple labels memory. A Mac with
"16 GB" of memory shows 16.0 GB here and in Activity Monitor. Counting it like disk space
would show 17.2 GB.

### Is the report just one moment?

Yes. The CPU and memory figures are one reading, taken in under a second. Run `askdad cpu`
again later to see whether something is steady or was a brief spike.

---

## Privacy

### What is in the AI prompt, and what is left out?

The report includes a prompt you can copy into an AI chat. Ask Dad never sends it anywhere
itself.

- **Storage prompt:** your home folder appears as `~`, so your account name isn't in it.
  Untick the checkbox to leave out file names too.
- **Memory prompt:** shows each app's name, memory and CPU. It leaves out the full command
  that started each process, because those can include your user name and folder paths.

### What is the .json file next to the report?

It is the full scan data, saved so a report can be redrawn later. For the memory scan it
holds every process's full command line, which can include your user name and folder paths.
Keep it to yourself; share the HTML report or the AI prompt instead.
