# DadWare brand

The starting point for any DadWare or Ask Dad design: the website, the logo, the report, the app icon. **To see it all, open `brand-guide.html` in a browser.** This file is the same guide in words.

- **DadWare** is the company. **Ask Dad** is the product. Keep "Ask Dad" in page titles.
- **Style:** 1980s PC games. Speed stripes, pixel art, chunky shadows. Retro, but easy to read: the audience includes kids and adults who aren't technical.
- **Source of truth:** `brand-picks.json` in this folder. To change the brand, open `brand-lab.html` in a browser, click **Load picks from a file**, choose `brand-picks.json`, make your changes, then **Save picks to a file** and replace `brand-picks.json` with the new file. The page also exports ready-to-use CSS (`dadware-brand.css`), tokens (`dadware-tokens.json`) and SVG assets in these colors.
- `dadware design ideas.png` (not committed) is the early mockup. Don't copy its Ask Dad icon: it looks like Apple's Finder face.

## Colors (Box Art palette)

| Name | Hex | Use |
|---|---|---|
| Background | `#f5eedb` | Page background (cream, like an old game box) |
| Surface | `#fffaf0` | Cards and panels |
| Text | `#1d1a16` | Main text and headings |
| Muted text | `#5c554a` | Captions and secondary text |
| Primary | `#c8102e` | Buttons, step numbers. White text on it |
| Link / Accent | `#1446a0` | Text links, small labels, bullets |
| Stripe 1 | `#f7b801` | Wordmark top band |
| Stripe 2 | `#f18701` | Wordmark band 2 |
| Stripe 3 | `#e0301e` | Wordmark band 3 |
| Stripe 4 | `#7a1fa2` | Wordmark bottom band |
| Terminal background | `#1d1a16` | Command-line boxes |
| Terminal text | `#f7b801` | Text in command-line boxes |
| Good (A, B) | `#1f8a4c` | Good grades, checkmarks |
| Caution (C) | `#b86e00` | Middle grade |
| Alert (D, F) | `#c8102e` | Bad grades |

Every text color passes the readability check against its background: 4.5:1 for text, 3:1 for big text and badges. Check again with the brand lab if you change a color.

## Fonts

All are free Google Fonts (SIL Open Font License, which allows use in logos). The new website serves its own copies from `site-next/fonts` (Latin subset, with the license files), so it makes no requests to Google.

| Role | Font | Where |
|---|---|---|
| Headlines and wordmark | **Saira Black Italic** (weight 900, italic) | DADWARE wordmark, headings, grade letters |
| Body | **Atkinson Hyperlegible** | Paragraphs and buttons. Designed for easy reading |
| Terminal | **IBM Plex Mono** | Commands, small uppercase labels |

## Wordmark and logo

Files are in `logo/`. The letters are outlines (SVG paths), so they display without the font.

| File | Use |
|---|---|
| `dadware-logo.svg` | The main logo: DADWARE in Saira Black Italic, cut into four stripes (Stripe 1 to 4, top to bottom). The gaps are transparent, so it works on cream, white or near-black. |
| `dadware-logo-ink.svg` | One color, for print or anywhere color isn't possible. |
| `dadware-logo-white.svg` | White, for red, dark colors and photos. |
| `dadware-mark.svg` | The striped D on its own, when DADWARE won't fit. |
| `dadware-tile.svg` | The D on a dark rounded square: profile pictures, avatars. |
| `favicon.svg` | Three stripes and one gap, so it reads at 16 pixels. Copied to `site-next/favicon.svg`. |
| `askdad-icon-concept-*.svg` | Three Ask Dad app icon directions (speech bubble, glasses and mustache, striped question mark). **Not decided yet.** |
| `make_logo.py` | Rebuilds every file above from the font. Setup is in the script's first lines. |

- No "SOFTWARE" line and no tagline under the wordmark, for now.
- Clear space: at least the height of the yellow top stripe on every side. Minimum size: 16 pixels tall on screen; below that, use the D mark or the tile.
- Don't stretch, recolor, re-slant or add effects. Don't retype it in the font; use the files.
- **The stripe gaps are placed by measurement.** A gap edge that lands near a letter's horizontal edge leaves a hairline sliver, so the gaps sit at 58–63.5% and 79.7–85.2% of the cap height, clear of Saira's bar edges. `make_logo.py` explains the numbers; re-measure if the font ever changes.
- The Ask Dad app icon must be original: nothing like Apple's Finder face.

## Website style

The new landing page is staged in `site-next/`, not `site/`, so merging it does not publish it: Netlify publishes `site/`. BACKLOG.md has the launch steps.

**Preview it through a local server, not by double-clicking.** Safari won't load all of a page's own fonts when it's opened as a file, so the text comes out bold. From the repo root run `python3 -m http.server 8000`, then open http://localhost:8000/site-next/ or http://localhost:8000/assets/dadware/brand-guide.html. Netlify serves the page the same way the local server does, so this is what visitors will see.

- **Hero background:** Disk map (blocks of used and free space around the edges, clear in the middle).
- **Cards:** thin outline. **Buttons:** solid, with a hard offset shadow. **Corners:** 4px.
- **Section dividers:** the four stripe colors as staggered speed stripes.
- No CRT scanlines.

## Voice

The site and the report should sound like John, a dad who built this for his daughter, not like a marketing team.

- First person, plain and short. Fragments are fine ("the works", "hogging RAM").
- Lead with the real story: built to help his daughter understand her Mac and learn the terminal.
- Honest about the beta: "Stuff will break." If people like it, a native Mac app comes next.
- Position against scammy cleaner apps by saying what Ask Dad *doesn't* do. Never name another company.

## Claims that must stay true

The page makes these promises. If the product changes, change the page.

- **Free and open source** (MIT). Nothing to buy: no trial, no subscription, no upgrade.
- **Never deletes anything.** Read-only.
- **Private, secure:** doesn't connect to the internet or use AI to scan your computer. (The report *offers* a prompt you can paste into an AI yourself; Ask Dad never sends it.)
- **Pure Python code**, open to read on GitHub.
- The install steps match the current build (today: the app opens a Terminal window).
