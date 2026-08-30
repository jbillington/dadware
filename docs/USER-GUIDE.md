# Dad Ware User Guide

## Why This Exists

My daughter called me because her Mac said the disk was full and everything was slow. She didn't know what was taking up space or what was safe to delete. I tried to explain it over the phone. That went about as well as you'd expect.

So I built this. It scans your Mac, figures out what's using all the space and memory, and gives you a report card. Like school, but for your computer. And like school, you probably won't love the grades.

## What It Does

Dad Ware looks at two things: **storage** (what's filling up your hard drive) and **memory** (what's slowing your computer down right now). It doesn't delete anything. It doesn't change anything. It just looks around, takes notes, and tells you what it found.

Think of it like opening the hood of your car. You're not fixing anything yet. You're just seeing what's in there.

## The Report Card

After a scan, you get letter grades from A to F:

- **A** means you're good. Don't touch anything.
- **B** means fine, maybe tidy up when you get a chance.
- **C** means it's getting cluttered. Time to deal with it.
- **D** means it's bad. Your Mac is probably complaining.
- **F** means we need to talk.

You get separate grades for things like free space, how messy your Downloads folder is, how big your Photos library has gotten, and an overall grade that puts it all together.

## Storage Scan

This is the main one. Run it when your Mac says the disk is full or you're getting those annoying "your startup disk is almost full" warnings.

```
./askdad
```

That's it. One command.

It finds your biggest files and folders, checks your Downloads and Desktop for clutter, looks at your Photos, Music, Mail, and Messages libraries, and tells you where all your space went.

**Things it checks:**

- **Free space.** How much room you have left. Under 10% is bad. Under 5% and your Mac starts acting weird.
- **Downloads folder.** This is where files go to be forgotten. If yours is over 10GB, you've been downloading stuff and never cleaning up. We've all been there.
- **Desktop.** Your desktop is not a filing cabinet. If you've got gigabytes of stuff on it, that's a problem.
- **Photos library.** Years of photos and videos add up. This is often the biggest thing on your drive and most people don't realize it.
- **Music library.** If you downloaded your whole iTunes library back in 2009, it's still sitting there.
- **Messages.** Every photo and video anyone ever texted you. All of it. Sitting in a database. For years.
- **Mail.** Attachments. So many attachments.
- **Top files and folders.** The biggest things on your drive, ranked by size. Sometimes you'll find a 40GB iPhone backup you forgot about. That's the point.

## CPU and Memory Scan

Run this when your Mac feels slow, the fans are loud, or you're getting the spinning rainbow wheel.

```
./askdad cpu
```

It checks what's using your memory (RAM) and CPU right now.

**Things it checks:**

- **Memory pressure.** Is your Mac running out of memory? Low pressure is fine. High pressure means something needs to close.
- **Memory hogs.** Which apps are using the most memory. It groups things together, so instead of seeing 47 separate "Google Chrome Helper" processes, it shows you "Chrome: 4.2 GB across 47 processes." Because Chrome does that.
- **Browser tabs.** Every tab is a separate process that uses memory. If you have 30 tabs open, that's 30 little programs running. Close some. Bookmark the rest.
- **Process count.** How many things are running at once. Hundreds of small processes can add up.

## The HTML Report

After every scan, a report opens in your browser automatically. This is the good stuff. It has:

- Your report card with all the grades
- Bar charts showing what's using your space
- Sortable tables of your biggest files and folders
- Expandable sections where you can drill into specific folders
- A button to reveal files in Finder so you can go look at them
- Tips for what to clean up

You can save this report or send it to someone. It's a single HTML file that works on its own. If you're calling your dad for help, send him the report. He'll appreciate not having to guess.

## The Dad Commentary

The tool has opinions. If your Downloads folder is 15GB, it's going to say something about it. If Chrome is eating 4GB of RAM, it's going to mention that. The tone is "dad who's seen this before and is trying to help without lecturing." Whether it succeeds at that is debatable.

The status indicators:

- 🟢 means you're fine. Good job.
- 🟡 means it's not urgent but you should deal with it.
- 🔴 means deal with it now.

## What To Do With The Results

The report tells you what's big. It doesn't tell you what to delete. That's on you. But here are the usual suspects:

1. **Downloads folder.** Go through it. Delete the installers, the duplicate files, the PDFs you downloaded once and never opened. If you haven't touched it in a year, you don't need it.

2. **Old iPhone backups.** These live in `~/Library/Application Support/MobileSync/Backup/`. They can be 20-50GB each. If you back up to iCloud now, you don't need the local ones.

3. **Cache files.** Apps store temporary files that build up over time. Restarting your Mac clears some of these.

4. **Browser tabs.** Close them. If you need them later, that's what bookmarks are for. Your Mac will immediately feel faster.

5. **Apps you don't use.** Check your Applications folder. If you downloaded something two years ago and used it once, drag it to the trash.

## Running Both Scans

If you want the full picture:

```
./askdad all
```

This runs the storage scan and the memory scan together and opens both reports.

## Options

You don't need any of these. But if you like knobs:

```
./askdad --volume /Volumes/External
```
Scan a different drive. By default it asks you which one (and if there's only one, it just picks it).

The picker only lists actual storage devices. If you have a .dmg installer mounted, a network share connected, or a read-only volume attached, they're left out — there's nothing to clean up on those — and it tells you what it left out.

```
./askdad --all-volumes
```
Put those back in the list. You can also point `--volume` straight at one of them if you really want to scan it.

```
./askdad --top 100
```
How many of your biggest files to report. Default is 500, which is plenty of bad news for anyone.

```
./askdad --min-size 500MB
```
Ignore anything smaller than this. Useful on huge drives when you only care about the big stuff.

```
./askdad --terminal
```
Skip the HTML report and just print to the terminal. For people who like it old school.

```
./askdad --no-color
```
Plain text output, no colors. For scripts, logs, or terminals stuck in 1985.

```
./askdad --skip-protected
```
Skip the protected libraries (Photos, Messages, Mail) entirely instead of showing 0 bytes when access is denied.

```
./askdad --no-mac-libraries
```
Skip app library scanning altogether. Faster, but you lose the Photos/Music/Messages/Mail numbers.

```
./askdad cpu --export-memory mem.csv
```
Export every running process and its memory use to a CSV you can open in a spreadsheet. For when you want to see all of it.

```
./askdad export memory report.json
```
Already ran a CPU scan? Export the CSV from the saved report without scanning again. The JSON files live next to the HTML reports.

## It's Safe

This tool is read-only. It never deletes files, moves files, or changes anything on your computer. It only looks. The worst thing that can happen is you learn something you didn't want to know about your Downloads folder.

No data leaves your computer. Nothing is uploaded anywhere. There's no account, no tracking, no analytics. It runs, it scans, it shows you a report. That's all it does.

## FAQ

**Q: My Mac says this is from an unidentified developer.**
A: Right-click the file and choose Open. Click Open again in the dialog. You only have to do this once. This happens because I haven't paid Apple $99/year to sign the app. The source code is on GitHub if you want to verify it's not doing anything sketchy.

**Q: The scan is taking a long time.**
A: Storage scans can take a minute or two on large drives. It's looking at every file. Let it run.

**Q: Some libraries show 0 bytes.**
A: You need to grant Terminal "Full Disk Access" in System Settings > Privacy & Security for it to see your Photos, Messages, and Mail. The scan still works without it, you just won't get those numbers.

**Q: Do I need to install Python?**
A: No. The executable bundles everything it needs.

**Q: Can this break my Mac?**
A: No. It only reads. It can't break anything any more than opening Finder and looking at your files can.

**Q: My grades are bad. Should I panic?**
A: No. The grades are meant to give you a sense of where things stand. A C doesn't mean your Mac is broken. It means there's room to clean up. Start with the biggest thing on the list and work your way down. Even clearing out Downloads will probably bump you up a grade.
