# Dad Ware vs ncdu vs htop — Comparison & Agent Strategy

## Do They Solve the Same Problem?

**Short answer: No.** There's overlap in the data they collect, but the problems they solve are different.

| | ncdu | htop | Dad Ware |
|---|---|---|---|
| **Problem it solves** | "Where is my disk space going?" | "What's using CPU/RAM right now?" | "Is my Mac healthy, and what should I do about it?" |
| **User** | Developer who knows what to delete | Developer debugging a performance issue | Anyone with a Mac who wants guidance |
| **Output** | Interactive file browser | Interactive process list | Report card with grades, advice, and a personality |
| **Requires knowledge** | You need to know what's safe to delete | You need to know which processes matter | It tells you what matters |
| **Interaction model** | Navigate and drill down in real-time | Watch and kill processes in real-time | Run scan, read report, take action offline |

### ncdu

ncdu is a disk usage explorer. You navigate a tree of folders sorted by size. It's extremely good at what it does, but it assumes you know what you're looking at. If someone sees `/Users/dad/Library/Application Support/MobileSync/Backup` taking 40GB, ncdu shows you the number — it doesn't tell you "those are your old iPhone backups, and here's how to manage them."

**What ncdu does that Dad Ware doesn't:**
- Real-time interactive navigation (drill into any folder)
- Delete files directly from the UI
- Works on Linux/any Unix system

**What Dad Ware does that ncdu doesn't:**
- Grades your storage health (A-F letter grades)
- Identifies Mac-specific libraries (Photos, Mail, Music, Messages, Time Machine)
- Explains what things are and whether they're safe to clean up
- Generates a shareable HTML report
- Provides personality-driven advice that makes it approachable
- Scans memory/CPU in addition to storage

### htop

htop is a real-time process viewer. It shows CPU and RAM usage per process with sorting, filtering, and the ability to send signals (kill, nice, etc.). It's a power tool for people who already understand processes.

**What htop does that Dad Ware doesn't:**
- Real-time updating display
- Kill/renice processes directly
- Filter and search processes
- CPU core visualization
- Works on Linux/any Unix system

**What Dad Ware does that htop doesn't:**
- Groups processes by app (shows Chrome's total across 47 helper processes)
- Grades your memory situation and tells you if you should worry
- Provides specific advice ("Chrome is using 4.2 GB across 47 tabs — consider closing some")
- Combines memory analysis with storage analysis in one report
- Generates a shareable report you can send to someone for help

### The Real Difference

ncdu and htop are **instruments** — they show you raw data and assume you can interpret it.

Dad Ware is an **advisor** — it interprets the data for you, grades it, and tells you what to do. The target user isn't someone who lives in the terminal; it's someone whose Mac is running slow and they don't know why.

The overlap is in data collection. The differentiation is in interpretation and presentation.

---

## Agent Integration — Is It Dumb?

**No, it's actually the most natural evolution of what you've already started.**

You already have `llm_prompt.py` generating structured prompts with system specs, scan results, and pre-written questions. The HTML report has a "Consult AI" section where users copy/paste that prompt into ChatGPT or Claude. That's a manual agent workflow — the user is acting as the glue between Dad Ware and an LLM.

### What Agent-Friendly Dad Ware Could Look Like

**Tier 1: Structured output (low effort, high value)**
Add a `--json` flag that outputs scan results as clean JSON to stdout. Any agent or MCP tool can call `yourdad scan storage --json`, parse the results, and reason about them. This is the simplest useful thing.

```bash
# Agent runs this, gets structured data back
yourdad storage --json | agent_reads_this
```

**Tier 2: MCP tool (medium effort, very high value)**
Dad Ware becomes an MCP server that agents like Claude Code can call directly. An agent helping someone with a slow Mac could call the `scan_storage` tool, get structured results, and give personalized advice — no copy/paste required.

```
User: "My Mac is really slow and I'm running out of space"
Agent: [calls dadware.scan_storage] → gets structured results
Agent: "Your disk is 94% full. The biggest thing is 38GB of old iPhone backups in..."
```

**Tier 3: The prompt is the product**
The LLM prompt you already generate is genuinely useful context for any agent helping with Mac issues. Instead of the user copying it, an agent could request it directly:

```bash
yourdad storage --prompt  # outputs just the LLM-ready prompt
```

Any AI agent that needs to understand a user's Mac health can run this single command and get rich, pre-interpreted context.

### Why This Isn't Dumb

1. **You already built the hard part** — the scanning, grading, and interpretation logic. The LLM prompt generator proves the concept works.

2. **The "dad advisor" personality differentiates from raw tools** — an agent calling ncdu gets raw numbers. An agent calling Dad Ware gets graded, interpreted, Mac-specific analysis with actionable recommendations already attached.

3. **The use case is real** — "help me fix my slow Mac" is one of the most common requests people bring to AI assistants. Right now those assistants are guessing blind. Dad Ware gives them eyes.

4. **It inverts the current flow** — instead of Dad Ware generating a prompt for the user to paste into an agent, the agent calls Dad Ware as a tool. Same data, no friction.

### What to Build First

`--json` output on scan commands. It's a few hours of work, it makes everything else possible, and it doesn't change the existing UX at all. The MCP server and `--prompt` flag can come later once you validate that agents actually use the structured output.
