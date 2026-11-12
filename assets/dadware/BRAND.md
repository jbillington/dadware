# DadWare brand

The starting point for any DadWare or Ask Dad design: the website, the logo, the report, the app icon.

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

All are free Google Fonts (SIL Open Font License, which allows use in logos).

| Role | Font | Where |
|---|---|---|
| Headlines and wordmark | **Saira Black Italic** (weight 900, italic) | DADWARE wordmark, headings, grade letters |
| Body | **Atkinson Hyperlegible** | Paragraphs and buttons. Designed for easy reading |
| Terminal | **IBM Plex Mono** | Commands, small uppercase labels |

## Wordmark and logo

- **Wordmark:** "DADWARE" in capitals, Saira Black Italic, no extra letter spacing, filled with the four stripe colors in horizontal bands (top to bottom: Stripe 1 to 4) with thin gaps between the lower bands.
- No "SOFTWARE" line and no tagline under it, for now.
- **The final logo isn't made yet.** When it is, the letters will be converted to outlines (SVG paths) so it doesn't depend on the font being installed. Planned files: full color, one color, white for dark backgrounds, and a small square mark. The Ask Dad app icon is designed separately and must be original.

## Website style

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
