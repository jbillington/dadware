# How a scan is graded

Everything on the report card, from the scan data to the big letter at the top.
Every table here was derived by running the real functions across their input
range, not by reading their comments.

Two independent systems read the same scan and both end up on the report:

- **The grade** — the big letter and `X/100`, plus the per-component breakdown.
  Built in `scanners/grading.py`, assembled in `renderers/html.py`.
- **"Dad says"** — the comment lines, the tips, and the ok/warn/critical colour.
  Built in `personality/dad.py`, from the raw scan data.

They never read each other. §7 explains why that means they can disagree, and
when that is a bug rather than a design choice.

---

## The walkthrough

```
  scan data
      |
      +--> Free Space ............. from free %                    score 0-100
      +--> Home Folders Ratio ..... from home bytes / used bytes   score 0-100
      +--> Home Folders Clutter ... from Downloads + Desktop       score 0-100
      +--> Mac App Libraries ...... average of per-library scores  score 0-100
      |
      +--> weighted average, renormalized -----------------------> COMPOSITE
                                                                       |
                                                    score_to_letter ---+--> A-F
```

Four component scores, each 0–100. They are combined by weighted average. The
result maps to a letter through one shared table, and that letter is what the
reader sees at the top of the card.

A component that could not be measured is **dropped**, not scored as zero, and
the remaining weights renormalize (§5).

---

## 1. The letter scale

Every score in the system — components and composite alike — becomes a letter
the same way, via `score_to_letter()`:

| Score | Letter |
|---|---|
| 90 – 100 | A |
| 80 – 89.99 | B |
| 70 – 79.99 | C |
| 60 – 69.99 | D |
| below 60 | F |

Worth holding on to: several components produce scores by interpolating between
thresholds, so the *stated* threshold and the *letter* boundary are not always
the same number. Each section below gives the letter boundaries directly.

---

## 2. Free Space — 50% of the grade

**What it measures:** how much room is left on the drive, as a percentage.

**In plain terms:** the score climbs in a straight line as free space grows,
steeply at first and then more gently. Below 10% free the score falls away
fast; at 40% free or better it is pinned at 100.

**The calculation:**

```
free_percent = free_bytes / total_bytes * 100

if free_percent >= 40      score = 100
elif free_percent >= 25    score = 80 + (free_percent - 25) * (20/15)
elif free_percent >= 15    score = 60 + (free_percent - 15) * 2
elif free_percent >= 10    score = 40 + (free_percent - 10) * 4
else                       score = free_percent * 4
```

**What you get:**

| Free space | Letter |
|---|---|
| 32.5% or more | A |
| 25 – 32.49% | B |
| 20 – 24.99% | C |
| 15 – 19.99% | D |
| under 15% | F |

This carries half the grade, because it is the component that actually slows a
Mac down. A disk under 15% free is the one condition here with real consequences.

---

## 3. Home Folders Clutter — 20% of the grade

**What it measures:** Downloads and Desktop — the two folders that fill up
fastest and are the quickest to clear.

**In plain terms:** count the problems, look up the score. Not a formula — a
flat ladder. Both folders are treated identically: over 5 GB is one problem,
over 10 GB is two.

**The calculation:**

```
problem_count = 0

if Downloads > 10 GB       problem_count += 2
elif Downloads > 5 GB      problem_count += 1

if Desktop > 10 GB         problem_count += 2
elif Desktop > 5 GB        problem_count += 1
```

**What you get:**

| Problems | Score | Letter | Means |
|---|---|---|---|
| 0 | 100 | A | Both folders under 5 GB |
| 1 | 85 | B | One folder between 5 and 10 GB |
| 2 | 72 | C | One folder over 10 GB, or both over 5 |
| 3 | 62 | D | One over 10 and one over 5 |
| 4 | 40 | F | Both over 10 GB |

Sizes are decimal GB, the same units the report prints and Finder shows.

Both halves of this ladder matter together. Scores spaced 100/85/72/62/40 make
every letter *reachable*, but only because `problem_count` can reach 4 — which
needs both folders to have two tiers. Give Desktop only one tier and the maximum
becomes 3, and F becomes impossible no matter how the scores are spaced.
`TestEveryClutterLetterIsReachable` pins both halves, because changing either
one alone silently reopens the hole.

---

## 4. Home Folders Ratio — 15% of the grade

**What it measures:** how much of your used space is your own files, rather than
the system's and applications'.

**In plain terms:** a low ratio is good. If your own folders are a small share
of what is used, the rest is system overhead you cannot do much about, and
there is little for you to act on.

**The calculation:**

```
ratio_percent = home_folders_bytes / total_used_bytes * 100

if ratio_percent < 30      score = 100
elif ratio_percent < 50    score = 80 + (50 - ratio_percent)
elif ratio_percent < 70    score = 60 + (70 - ratio_percent)
elif ratio_percent < 85    score = 40 + (85 - ratio_percent) * 1.33
else                       score = max(0, 40 - (ratio_percent - 85) * 2.67)
```

Anything under 30% scores a flat 100 — below that point the split is considered
healthy and is not graded further.

**What you get:**

| Home folders as share of used | Letter |
|---|---|
| up to 40% | A |
| 40 – 50% | B |
| 50 – 60% | C |
| 60 – 70% | D |
| 70% or more | F |

There is a hairline discontinuity at exactly 70%: the segment below it reaches
60.01 (a D) and the segment at 70 starts at 59.95 (an F), so the letter jumps
by 0.06 of a point. It is a rounding artifact of the piecewise formula, not an
intended cliff, and affects roughly one input value in a thousand.

---

## 5. Mac App Libraries — 15% of the grade

**What it measures:** Photos, Music, Messages, Mail and Creative Apps, graded
individually and then averaged.

**In plain terms:** each library is scored against thresholds for its own type,
because 20 GB of Photos is ordinary and 20 GB of Mail is not. A library that is
also a large share of your whole disk takes an extra penalty on top.

**The calculation, per library:**

```
size_gb = library_bytes / 1000^3          # decimal GB, matching Finder

# interpolate between the thresholds for this library type
if size_gb < A            score = 100
elif size_gb < B          score = 80 + (B - size_gb) / (B - A) * 20   # 80-100
elif size_gb < C          score = 60 + (C - size_gb) / (C - B) * 20   # 60-80
elif size_gb < D          score = 40 + (D - size_gb) / (D - C) * 20   # 40-60
else                      score = max(0, 40 - (size_gb - D) / 10)     # 0-40

# then a penalty if this one library dominates the disk
library_percent = library_bytes / total_used_bytes * 100
if library_percent > 50   score -= 20
elif library_percent > 30 score -= 10
elif library_percent > 20 score -= 5
```

**The type thresholds** (`A`, `B`, `C`, `D` above, in GB):

| Library | A | B | C | D |
|---|---|---|---|---|
| photos | 50 | 100 | 200 | 300 |
| music | 20 | 50 | 100 | 200 |
| creative | 20 | 50 | 100 | 200 |
| messages | 5 | 10 | 20 | 50 |
| mail | 5 | 10 | 20 | 50 |

**These are not the letter boundaries.** Each interpolation zone spans a fixed
20-point score range, and each 20-point range covers two letter bands — so the
A/B and C/D boundaries land at the *midpoint* between thresholds. The actual
letters, before any share penalty:

| Library | A | B | C | D | F |
|---|---|---|---|---|---|
| photos | ≤ 75 GB | 75 – 100 | 100 – 150 | 150 – 200 | over 200 |
| music / creative | ≤ 35 GB | 35 – 50 | 50 – 75 | 75 – 100 | over 100 |
| messages / mail | ≤ 7.5 GB | 7.5 – 10 | 10 – 15 | 15 – 20 | over 20 |

The `D` column of the threshold table never moves a letter. F begins at the `C`
threshold regardless of what `D` says; `D` only controls how far below 40 the
score falls once you are already in F.

**The share penalty in practice** — a 60 GB photo library, varying only the size
of the disk it sits on:

| Library share of used space | Score | Letter |
|---|---|---|
| 20% | 96 | A |
| 30% | 91 | A |
| 50% | 86 | B |
| 60% | 76 | C |

Same library, same 60 GB, three different letters. The penalty is a flat
subtraction, so it can cost a full letter independent of absolute size.

**The component score** is the mean of the individual library scores — but only
for libraries that returned a size above zero. See §6 for when the whole
component is dropped instead.

---

## 6. The composite

Assembled in `render_report_card()` (`renderers/html.py`), not in
`scanners/grading.py`.

```
composite = 0.5  * free_space
          + 0.2  * home_folders_clutter
          + 0.15 * home_folders_ratio
          + 0.15 * mac_libraries

letter = score_to_letter(composite)
```

| Component | Weight |
|---|---|
| Free Space | 0.50 |
| Home Folders Clutter | 0.20 |
| Home Folders Ratio | 0.15 |
| Mac App Libraries | 0.15 |

### Nothing is graded that was not measured

If the library scan did not measure everything, the `mac_libraries` component is
**dropped from the composite entirely** and the remaining weights renormalize:

```
composite = (0.5 * free_space + 0.2 * clutter + 0.15 * ratio) / 0.85
```

The report card shows `-` and "not scored" on that row rather than a letter that
does not count. A component is dropped when any library:

- was **skipped** because the scan hit its time budget,
- returned an **error**, or
- came back **empty while we lack permission to read it**.

That last case is the subtle one, and it was a live bug until Aug 25, 2026. A
library blocked by Full Disk Access does not raise an error — it reports success
with zero bytes, because the scanner genuinely finds nothing at a path it cannot
read. Zero-byte libraries are excluded from the average rather than averaged in
as zeros, so a blocked library did not drag the score down; it silently shrank
the evidence. On a real Mac this produced **Mac App Libraries: A 100/100**
computed from Music alone, while Photos, Messages and Mail — including a 29.9 GB
Messages library that grades F — were invisible. Granting access and rescanning
the same machine gave B 88/100.

A genuinely empty library on a machine *with* access is a true zero and does not
block grading.

Renormalizing rather than subtracting also matters for `--no-mac-libraries`: the
component used to keep its 0.15 weight at a score of 0, so a flag meaning "don't
look here" cost the user real points.

### The overall comment

Set from the composite immediately after it is computed:

| Composite | Comment |
|---|---|
| 90+ | "Excellent!" |
| 80 – 89 | "Good job!" |
| 70 – 79 | "Room for improvement" |
| 60 – 69 | "Needs work" |
| under 60 | "Critical issues" |

These cutoffs are the same as `score_to_letter`'s, so the comment always agrees
with the letter. An A is never "Needs work".

---

## 7. "Dad says" — a separate system

`add_personality()` reads the raw scan data. It receives no grade and consults
none. For a storage scan, checks run in this order:

| # | Trigger | Status effect |
|---|---|---|
| 1 | Downloads > 10 GB | `warn`, always |
| 2 | Downloads 5 – 10 GB | `warn`, always |
| 3 | Desktop > 5 GB | `warn` only if still `ok` |
| 4 | free space < 10% | `critical`, always |
| 5 | free space 10 – 20% | `warn` only if still `ok`; **comment only if nothing has commented yet** |
| 6 | largest file > 5 GB | no status change; tip only, and **only if nothing has commented yet** |
| 7 | nothing matched and status is `ok` | "looks fine. don't mess with success." |

Then, separately and always:

| Trigger | Effect |
|---|---|
| caches over 20 GB, or over 5 GB | one informational note |
| stale local snapshots | one informational note |

**Status only ever escalates** — `ok → warn → critical`, never back.

**The informational notes never touch status and never produce a tip.** A full
cache is an app doing its job and the space returns on its own; calling it a
warning would scold someone for something they cannot permanently fix.

**The two-line cap applies to the verdict, not the notes.** Comments are capped
at two, because nobody reads more. The cache and snapshot notes are appended
*after* that cap. This is deliberate: when they were inside it, a cache note
would evict a real finding, and the snapshot note vanished from the output
entirely.

**Checks 5 and 6 are guarded by "nothing has commented yet".** A Downloads
finding therefore hides the free-space message, even while free space still
escalates the status. The user sees "downloads looks like a garage shelf", with
no mention that the disk is also nearly full.

---

## 8. Why the grade and the comment can disagree

They are two calculations over overlapping slices of the same scan, with
different cutoffs, neither reading the other.

- **The grade** weighs free space at 0.5, clutter at 0.2, ratio at 0.15 and
  libraries at 0.15. Since Aug 24, 2026 it does read Downloads and Desktop,
  through the clutter component — before that it did not, which was the single
  biggest source of disagreement.
- **Dad's comment** reads Downloads, Desktop, free space, and the largest single
  file. It never looks at the home-folder ratio or any library size, which
  together still carry 30% of the grade.
- Even on free space, which both read, the cutoffs differ: the grade turns D at
  20% free, while Dad stays quiet until 20% and only escalates below it.

So a report can carry a **C** with a cheerful "looks fine", or an **A** with
"getting tight". Both are behaving as written.

### Worked example

A disk at 19% free, tidy home folders, one large Messages library:

These are the real numbers from a scan of a 250 GB disk, 201.8 GB used, with
Full Disk Access granted:

```
free_space            19% free                 -> score  68.0   D
home_folders_clutter  nothing over 5 GB        -> score 100.0   A
home_folders_ratio    22% of used space        -> score 100.0   A   (< 30%, flat 100)
mac_libraries         mean of the four below   -> score  88.3   B

    photos      1.06 GB  ->  A (100.0)
    music       3.66 GB  ->  A (100.0)
    messages   29.91 GB  ->  F ( 53.4)     <- over the 20 GB F threshold
    mail        1.46 GB  ->  A (100.0)

composite = 0.5*68.0 + 0.2*100.0 + 0.15*100.0 + 0.15*88.3
          = 34.00   + 20.00     + 15.00      + 13.25
          = 82.25  ->  B, "Good job!"
```

Meanwhile `add_personality()` on the same scan: Downloads and Desktop are both
under 5 GB, so checks 1–3 do not fire; free space at 19% is under 20, so check 5
fires — and because nothing has commented yet, its comment is kept. The user
sees **B / "Good job!"** at the top and **"getting tight. time to make some
room."** below it, with status `warn`.

Both are right. The B is an honest average across four components, three of
which are fine. The warning is about the one that is not — and it is the one
that carries half the grade.
