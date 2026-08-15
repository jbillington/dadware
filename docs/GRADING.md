# Dad Ware — Grading & Personality Reference

*How the letter grades and the "Dad says" comment are computed, and why they
sometimes tell you different things about the same report. No code changes
accompany this document — it is a reference, derived by reading the source
and verifying every number against the running functions.*

There is no single "scoring system." There are two independent systems that
both read the same scan data and both end up on the report:

1. **The grading system** (`scanners/grading.py` + weights/bands in
   `renderers/html.py`) — produces the big letter grade and the `X/100`
   score.
2. **The personality system** (`personality/yourdad.py`) — produces the
   "Dad says" line, the tips, and the ok/warn/critical status color, by
   walking the raw scan data with its own thresholds. It never looks at any
   grade the first system computed.

Section 6 covers why that split causes visible disagreements.

---

## 1. The letter scale

Every numeric score (0–100) maps to a letter the same way, everywhere in the
codebase, via `score_to_letter()`:

| Score range | Letter |
|---|---|
| ≥ 90 | A |
| 80–89.99 | B |
| 70–79.99 | C |
| 60–69.99 | D |
| < 60 | F |

`scanners/grading.py:38-49`

Keep this table next to you — several of the component functions below have
docstrings that *describe* nicer round-number bands (e.g. "A: >40% free")
than what actually comes out once their score formula is run through this
scale. Where that happens it's called out explicitly, because it's the crux
of the user's complaint.

---

## 2. Component grades

### 2.1 Free space — `grade_free_space(free_percent)`

`scanners/grading.py:52-77`

The docstring claims A>40%, B 25–40%, C 15–25%, D 10–15%, F<10%. The actual
score formula is piecewise linear, and running it through `score_to_letter`
gives **different** cutoffs than the docstring states:

| `free_percent` | Score formula | Score at boundary | Actual letter |
|---|---|---|---|
| < 10% | `free_percent * 4` | 0–40 | F |
| 10–15% | `40 + (fp-10) * 4` | 40–60 | **F** (docstring says D) |
| 15–20% | `60 + (fp-15) * 2` | 60–70 | **D** (docstring says C) |
| 20–25% | (same formula, continued) | 70–80 | **C** |
| 25–32.5% | `80 + (fp-25) * (20/15)` | 80–90 | **B** (docstring says B up to 40%) |
| ≥ 32.5% | (same formula, continued) / capped at 100 for fp≥40 | 90–100 | **A** |

Verified directly against the function (`./venv/bin/python`):

```
grade_free_space(14.999) -> F (score 59.996)
grade_free_space(15.0)   -> D (score 60.0)
grade_free_space(19.999) -> D (score 69.998)
grade_free_space(20.0)   -> C (score 70.0)
grade_free_space(24.999) -> C (score 79.998)
grade_free_space(25.0)   -> B (score 80.0)
grade_free_space(32.499) -> B (score 89.999)
grade_free_space(32.5)   -> A (score 90.0)
```

So the real bands are **F <15%, D 15–20%, C 20–25%, B 25–32.5%, A ≥32.5%** —
not the 10/15/25/40 cutoffs the docstring names. The boundaries themselves
are continuous (no jump at 10/15/25/40), it's just that the letter each
segment lands on doesn't match the comment above it.

### 2.2 Home-folder clutter — `grade_home_folders_clutter(top_folders)`

`scanners/grading.py:80-133`

Not interpolated — a flat step function on a `problem_count`:

| Condition | `problem_count` += |
|---|---|
| Downloads > 10 GB | 2 |
| Downloads 5–10 GB | 1 |
| Desktop > 5 GB | 1 |

| `problem_count` | Score | Letter |
|---|---|---|
| 0 | 100 | A |
| 1 | 80 | B |
| 2 | 60 | **D** |
| 3 | 40 | F |
| ≥ 4 | 20 | F |

`problem_count == 2` (e.g. Downloads >10 GB alone) lands on score 60, which
`score_to_letter` maps to **D**, not C — the letter scale simply has no C
slot at that score. Verified: `score_to_letter(60) == 'D'`. There is no way
to score a C on this component at all; the step sizes (100/80/60/40/20)
skip straight over the 70–79 C band.

**This grade is computed and shown in the report, but it is excluded from
the composite score** (see §3) — it only appears as its own row.

### 2.3 Home-folder ratio — `grade_home_folders_ratio(home_folders_bytes, total_used_bytes)`

`scanners/grading.py:136-173`

Same pattern as §2.1: the docstring's bands (A<30%, B30-50%, C50-70%,
D70-85%, F>85%) don't match what the formula actually produces once run
through `score_to_letter`. Verified by scanning the function across its
input range:

| `ratio_percent` (home folders ÷ total used) | Actual letter |
|---|---|
| ≤ 40% | A |
| 40–50% | B |
| 50–60% | C |
| 60–<70% | D (very narrow — see note) |
| ≥ 70% | F |

Note a genuine discontinuity at exactly 70%: the segment for `ratio < 70`
evaluates to score 60.00 in the limit (D), but the next segment
(`70 ≤ ratio < 85`) starts at score **59.95** at `ratio = 70` — landing in F
by 0.05 points. So there's a hairline jump from D to F right at the 70%
boundary:

```
ratio=69.99 -> score=60.01 (D)
ratio=70.0  -> score=59.95 (F)
```

This looks like a formula rounding artifact rather than an intentional
cliff, but it's below the threshold anyone would notice in practice (0.05
points, one input value in a thousand).

### 2.4 Library size — `grade_library_size(library_size_bytes, library_type, total_used_bytes)`

`scanners/grading.py:176-224`

Per-type GB thresholds (`scanners/grading.py:187-194`):

| Library type | A (GB) | B (GB) | C (GB) | D (GB) |
|---|---|---|---|---|
| photos | 50 | 100 | 200 | 300 |
| music | 20 | 50 | 100 | 200 |
| messages | 5 | 10 | 20 | 50 |
| mail | 5 | 10 | 20 | 50 |
| time_machine | 100 | 200 | 500 | 1000 |
| creative | 20 | 50 | 100 | 200 |

**These four numbers per type are not the actual letter-grade cutoffs.**
The score is linearly interpolated between each pair of thresholds across a
*fixed 20-point score range* (100→80 between A and B, 80→60 between B and C,
60→40 between C and D), and because each interpolation zone spans two
10-point letter bands, the real A/B and C/D transitions fall at the
**midpoint** between the stated thresholds, not at the threshold itself.
Concretely, for photos (A=50, B=100, C=200, D=300), verified directly:

```
gb=74.99  -> A (score 90.0)
gb=75.0   -> A (score 90.0)
gb=75.01  -> B (score 90.0-)
gb=100.0  -> B (score 80.0)
gb=150.0  -> C (score 70.0)
gb=150.01 -> D
gb=200.0  -> D (score 60.0)
gb=200.01 -> F
gb=300.0  -> F (score 40.0)
```

So the actual bands are **A ≤ 75 GB, B 75–100 GB, C 100–150 GB,
D 150–200 GB, F > 200 GB** — derived from `(A+B)/2`, `B`, `(B+C)/2`, `C` —
not the 50/100/200/300 the dict implies. The **D threshold value in the
dict is cosmetically unused for the letter cutoff**: F starts at the C
threshold (200 GB for photos), regardless of what D says; D only changes
how negative the score gets past that point (`max(0, 40 - (gb - D)/10)`),
which no longer affects the letter (already F). Verified against a second
type (messages/mail, A=5,B=10,C=20,D=50) and a third (time_machine,
A=100,B=200,C=500,D=1000) — same pattern holds exactly:

| Type | Actual A | Actual B | Actual C | Actual D | Actual F |
|---|---|---|---|---|---|
| photos | ≤75 GB | 75–100 GB | 100–150 GB | 150–200 GB | >200 GB |
| music / creative | ≤35 GB | 35–50 GB | 50–75 GB | 75–100 GB | >100 GB |
| messages / mail | ≤7.5 GB | 7.5–10 GB | 10–15 GB | 15–20 GB | >20 GB |
| time_machine | ≤150 GB | 150–200 GB | 200–350 GB | 350–500 GB | >500 GB |

After the size score is computed, a separate penalty applies if the
library is a large share of total used space (`scanners/grading.py:210-216`):

| `library_percent` (library ÷ total used) | Penalty |
|---|---|
| > 50% | −20 |
| > 30% | −10 |
| > 20% | −5 |
| else | 0 |

This penalty is a flat subtraction after the size-based score, so it can
drop a library by a full letter or more independent of its absolute size.
Verified: a 60 GB photo library in a 100 GB-used volume (60% share) scores
96 on size alone (B-range) but 76 after the −20 penalty (C).

---

## 3. The composite storage grade

The composite is **not** computed in `scanners/grading.py` — it's assembled
in the renderer, `renderers/html.py:935-946`, inside `render_report_card()`:

```python
component_grades = {
    'free_space': free_space_grade,
    'home_folders_ratio': home_folders_ratio_grade,
    'mac_libraries': avg_library_grade,
}
weights = {
    'free_space': 0.6,
    'home_folders_ratio': 0.2,
    'mac_libraries': 0.2,
}
composite_grade = calculate_composite_storage_grade(component_grades, weights)
```

`avg_library_grade` is the mean `score` across all libraries that were
actually scanned and non-zero (`renderers/html.py:928-933`), then converted
back to a letter with `score_to_letter`.

**`grade_home_folders_clutter` (the Downloads/Desktop grade, §2.2) is
computed and displayed as its own row on the report card, but it is
explicitly excluded from the composite** — the comment right above the
dict says so (`renderers/html.py:935`: "excluding home folders clutter -
shown separately"). A user can have an F-grade clutter row and it will not
move the big letter grade at the top of the report by a single point.

Formula:

```
composite_score = 0.6 * free_space_score
                 + 0.2 * home_folders_ratio_score
                 + 0.2 * avg_library_score

composite_letter = score_to_letter(composite_score)
```

`calculate_composite_storage_grade()` itself (`scanners/grading.py:268-295`)
is generic — if called with `weights=None` it falls back to equal weighting
across whatever keys are in `grades`, but that fallback path is never
exercised in this codebase; the renderer always passes the 0.6/0.2/0.2
weights above.

---

## 4. Overall comment bands

Also in the renderer, immediately after the composite is computed
(`renderers/html.py:949-953`):

| `composite_grade['score']` | `overall_comment` |
|---|---|
| ≥ 90 | "Excellent!" |
| ≥ 80 | "Good job!" |
| ≥ 70 | "Room for improvement" |
| ≥ 60 | "Needs work" |
| < 60 | "Critical issues" |

These cutoffs are identical to `score_to_letter`'s (90/80/70/60), so the
comment always agrees with the composite letter — an A is always
"Excellent!", never "Needs work". This part of the system is internally
consistent. The disagreement users notice is between this comment/letter
pair and the separately-computed "Dad says" line (§6).

---

## 5. The "Dad says" personality rules — `add_personality()`

`personality/yourdad.py:8-224`

This function reads raw `scan_data` directly — it does not receive or
consult any grade computed in §2–4. For `scan_type == 'storage'`, checks run
in this fixed order and mutate a shared `comments` list and `status` string:

| Order | Check | Comment | Status effect |
|---|---|---|---|
| 1 | Downloads > 10 GB | "downloads looks like a garage shelf. time to label a box." | `status = 'warn'` (unconditional) |
| 2 | Downloads 5–10 GB | "downloads is getting crowded. regular cleanup day?" | `status = 'warn'` (unconditional) |
| 3 | Desktop > 5 GB | "desktop isn't meant to be storage. it's a desk, not a box of junk." | `status = 'warn'` only if currently `'ok'` |
| 4 | free_percent < 10% | "living on the edge. let's back away from the cliff." | `status = 'critical'` (unconditional) |
| 5 | free_percent 10–20% | "getting tight. time to make some room." **only appended if `comments` is still empty** | `status = 'warn'` only if currently `'ok'` |
| 6 | largest top file > 5 GB | no comment text — only adds a tip, **only if `comments` is still empty** | none |
| 7 | (fallback) nothing matched and `status == 'ok'` | "looks fine. don't mess with success." | none |

`personality/yourdad.py:25-74`

**Control flow that matters:**
- Checks 1–4 always append their comment text when triggered — they are
  never suppressed.
- Checks 5 and 6 are guarded by `if not comments:` — **first match wins**.
  If Downloads or Desktop already fired, the free-space "getting tight"
  message (check 5) and the large-file tip (check 6) are silently dropped
  entirely, even though the status may still be bumped up by check 5's
  separate `status` line, which runs regardless of the comment guard.
  **This means a Downloads finding can hide the free-space message —** the
  user sees only "downloads looks like a garage shelf," with no mention
  that free space is also tight, even if `status` did quietly escalate to
  `'warn'` because of it.
- `status` only ever escalates (`ok → warn → critical`), and only checks 1,
  2, and 4 set it unconditionally; checks 3 and 5 use
  `if status == 'ok': status = 'warn'`, i.e. they escalate but never
  downgrade a status set earlier by a stronger check.
- Final output is capped: `comments[:2]` (at most two lines shown),
  `tips[:5]` (`personality/yourdad.py:218-224`).

### CPU/memory rules (`scan_type == 'cpu'`)

`personality/yourdad.py:76-215`. Checked in this order:

| Trigger | Comment | Status |
|---|---|---|
| `photoanalysisd` CPU > 20% | "photoanalysisd is doing its thing..." | `warn` (unconditional) |
| any chrome/chromium process CPU > 50% | "lots of tabs. lots of fans..." | `warn` (unconditional) |
| `pressure_level == 'high'` or `used_percent > 95` | "memory's maxed out..." | `critical` (unconditional) |
| `pressure_level == 'medium'` or `used_percent > 85` | "memory's getting tight..." | `warn` if `ok` |
| Chrome total RSS > 3 GB | "chrome's using N GB across..." | `warn` if `ok` |
| Safari total RSS > 2 GB | "safari's using N GB..." | `warn` if `ok` |
| Messages total RSS > 1 GB | "messages is using N GB..." | `warn` if `ok` |
| >400 small processes AND >5 GB in them AND pressure is medium/high | "N small processes using N GB..." | `warn` if `ok` |
| ≥3 memory hogs AND pressure medium/high AND no chrome/safari/messages/small-process comment fired yet | generic "X, Y, Z are all fighting for memory" | (none) |
| nothing matched | "cpu and memory look reasonable. nothing to worry about." | — |

`used_percent` here is `total_used_gb / total_memory_gb * 100` from the CPU
scan, a different quantity from storage's `used_percent`.

Memory `pressure_level` itself comes from `get_memory_pressure()` in
`scanners/cpu.py:98-104`, based on **available memory** (free + inactive
pages, not just free pages) and swap-out activity:

| Condition | `pressure` |
|---|---|
| `available_gb < 1.0` OR `swapouts > 1000` | `high` |
| `available_gb < 2.0` OR `swapouts > 100` | `medium` |
| else | `low` |

`scanners/cpu.py:100-104`

---

## 6. Why the grade and Dad's comment can disagree

This is the user's actual question, so: **the letter grade and "Dad says"
are two separate calculations over two different slices of the same scan,
with different cutoffs, and neither one looks at the other's output.**

- The **letter grade** is `0.6 × free_space + 0.2 × home_folders_ratio +
  0.2 × avg_library_score` (§3). It never reads Downloads/Desktop size
  directly (that's a different, excluded grade) and it has no concept of
  CPU/memory at all.
- **Dad's comment** (storage scan) reads Downloads size, Desktop size,
  `free_percent`, and the single largest file — and nothing else. **It
  never looks at the home-folder ratio or any library size**, both of
  which can dominate the letter grade's other 40%.
- Even on the one input they share — free space — the cutoffs don't line
  up. Dad only has two thresholds (critical <10%, warn <20%); the grade
  has five (§2.1: F<15, D 15–20, C 20–25, B 25–32.5, A≥32.5). Between 10%
  and 15% free, Dad still only says "warn," while the free-space component
  grade is already **F** — the worst possible score on that axis.

### Worked example: 81% used / 19% free

Verified with `./venv/bin/python`:

```python
>>> from scanners.grading import grade_free_space
>>> grade_free_space(19)
{'letter': 'D', 'score': 68, 'max': 100}
```

19% lands in the 15–20% band (§2.1): score `60 + (19-15)*2 = 68` → **D**.

Now assume the rest of the report is in decent shape — home-folder ratio
graded A (score 100) and the average library grade is B (score 85), a
realistic "everything else is fine, it's just free space that's tight"
scenario:

```python
>>> from scanners.grading import calculate_composite_storage_grade
>>> calculate_composite_storage_grade(
...     {'free_space': {'score': 68}, 'home_folders_ratio': {'score': 100},
...      'mac_libraries': {'score': 85}},
...     {'free_space': 0.6, 'home_folders_ratio': 0.2, 'mac_libraries': 0.2})
{'letter': 'C', 'score': 77.8, 'max': 100}
```

`0.6×68 + 0.2×100 + 0.2×85 = 40.8 + 20 + 17 = 77.8` → **C**, "Room for
improvement" (§4).

Meanwhile, `add_personality()` on the same 19%-free scan data: since
`free_percent (19) < 20`, check 5 fires — **if** no Downloads/Desktop
comment already fired, the user sees "getting tight. time to make some
room." and status flips from `ok` to `warn`.

So the report shows, side by side: a big **C — 77.8/100 — "Room for
improvement"**, and Dad saying **"getting tight. time to make some room"**
with a warn-colored status. Two believable but independently-sourced
readings of the same 19% free space — one folded into an 78-point blend
that calls it "room for improvement," the other a standalone threshold
check that calls it "tight" — neither wrong, but nothing ties them
together. And if Downloads had also tripped (a very common combination),
the free-space comment above would be dropped entirely by the `if not
comments:` guard (§5) — the user would see only a Downloads comment next
to that same C/77.8, with no text at all mentioning that free space (a
D-grade component) contributed to the score.

---

## 7. Recommendation

*This is a proposal, not something implemented — changing any of this
changes what every existing user sees on their report, so it should be a
deliberate product decision with its own review, not a drive-by fix.*

Options, roughly in order of how much they change existing report text:

1. **Derive Dad's `status` (and by extension which comment tier fires) from
   the composite score band** (e.g. `ok` if composite ≥80, `warn` 60–80,
   `critical` <60) instead of Dad's own independent threshold walk, keeping
   the specific per-finding comments (Downloads, Desktop, free space, CPU)
   as supporting detail/tips rather than status-setters. This directly
   fixes "the grade and the status disagree" because there would be one
   status, derived once.
2. **Leave the two systems independent but align the free-space cutoffs** —
   change Dad's 10%/20% thresholds to match `grade_free_space`'s actual
   15/20/25/32.5 bands, so at least the shared input produces consistent
   language. Composite could still diverge from Dad's overall tone because
   of the other two weighted components (home-folder ratio, libraries) that
   Dad never reads at all.
3. **Fix the suppression order** in `add_personality()` so a Downloads/
   Desktop finding can't silently hide a genuine free-space or large-file
   finding — e.g. show the worst (not merely the first) applicable comment,
   or stop capping at `comments[:2]` when more than one distinct problem
   area is active.

(1) is the most direct fix for what the user actually observed. (2) and (3)
are smaller, more surgical changes that reduce the frequency of visible
disagreement without unifying the two systems.
