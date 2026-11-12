"""Build the DadWare logo SVGs from Saira Black Italic outlines.

Not part of Ask Dad: a one-off design script. It needs two packages the app
does not use, so run it from its own throwaway venv, not the project's:

    python3 -m venv /tmp/fontenv && /tmp/fontenv/bin/pip install fonttools uharfbuzz
    curl -o /tmp/Saira-BlackItalic.ttf "$(curl -s 'https://fonts.googleapis.com/css2?family=Saira:ital,wght@1,900' | grep -o 'https://[^)]*\.ttf')"
    /tmp/fontenv/bin/python assets/dadware/logo/make_logo.py /tmp/Saira-BlackItalic.ttf assets/dadware/logo

The letters become SVG paths, so the files need no font to display. Stripe
bands are clipped to the letters and the gaps between them are transparent,
so every version works on any background. Copy favicon.svg and
dadware-logo.svg into the website (site/favicon.svg and
site/img/dadware-logo.svg) after regenerating.
"""
import os
import sys

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

INK, CREAM, WHITE = '#1d1a16', '#f5eedb', '#ffffff'
S1, S2, S3, S4 = '#f7b801', '#f18701', '#e0301e', '#7a1fa2'
PRIMARY = '#c8102e'

tt = TTFont(FONT)
gs = tt.getGlyphSet()
order = tt.getGlyphOrder()
CAP = tt['OS/2'].sCapHeight            # 688 for Saira
hbfont = hb.Font(hb.Face(hb.Blob.from_file_path(FONT)))


def shape(text):
    """Return [(glyph_name, x, y)] in font units, with the font's own kerning."""
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, {'kern': True, 'liga': True})
    out, x = [], 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((order[info.codepoint], x + pos.x_offset, pos.y_offset))
        x += pos.x_advance
    return out


def text_path(text, baseline):
    """SVG path d for text with its baseline at y=baseline (y grows down). Returns (d, xmin, xmax)."""
    d, xmin, xmax = [], 1e9, -1e9
    for name, x, y in shape(text):
        sp = SVGPathPen(gs)
        gs[name].draw(TransformPen(sp, (1, 0, 0, -1, x, baseline - y)))
        d.append(sp.getCommands())
        bp = BoundsPen(gs)
        gs[name].draw(bp)
        if bp.bounds:
            xmin, xmax = min(xmin, x + bp.bounds[0]), max(xmax, x + bp.bounds[2])
    return ' '.join(d), xmin, xmax


# Bands as fractions of cap height, top (0) to baseline (1). Gaps are left empty.
# Gap positions come from measuring Saira's horizontal edges in D A W R E ?:
# bar edges at 0.24, E middle arm 0.38-0.61, bar bottoms 0.75-0.76, A crossbar 0.85.
# A gap edge within ~0.02 of a letter edge leaves a hairline sliver, so the gaps
# sit at 0.58-0.635 (cuts through the E's arm) and 0.797-0.852 (ends past the A crossbar).
BANDS = [(-0.15, 0.40), (0.40, 0.58), (0.635, 0.797), (0.852, 1.15)]
SIMPLE_BANDS = [(-0.15, 0.48), (0.48, 0.70), (0.78, 1.15)]   # for tiny sizes: one gap


def bands_svg(top, colors, x0, x1, bands=BANDS):
    # Bands that touch overlap by a hair, or the edge between them shows a faint line.
    out = []
    for i, ((a, b), c) in enumerate(zip(bands, colors)):
        touches_next = i + 1 < len(bands) and abs(bands[i + 1][0] - b) < 1e-9
        h = (b - a) * CAP + (4 if touches_next else 0)
        out.append(f'<rect x="{x0:.0f}" y="{top + a * CAP:.1f}" width="{x1 - x0:.0f}" height="{h:.1f}" fill="{c}"/>')
    return ''.join(out)


def lettering(text, colors, uid, pad=40, bands=BANDS):
    """Return (svg_body, width, height) for striped text on a transparent background."""
    top = pad
    baseline = top + CAP
    d, xmin, xmax = text_path(text, baseline)
    shift = pad - xmin
    w, h = xmax - xmin + 2 * pad, CAP + 2 * pad
    body = (f'<defs><clipPath id="{uid}"><path transform="translate({shift:.1f} 0)" d="{d}"/></clipPath></defs>'
            f'<g clip-path="url(#{uid})">{bands_svg(top, colors, 0, w, bands)}</g>')
    return body, w, h


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{body}</svg>\n')


def write(name, content):
    with open(os.path.join(OUT, name), 'w') as f:
        f.write(content)
    print('wrote', name)


# ---------- Wordmark ----------
for name, colors in [('dadware-logo.svg', [S1, S2, S3, S4]),
                     ('dadware-logo-ink.svg', [INK] * 4),
                     ('dadware-logo-white.svg', [WHITE] * 4)]:
    body, w, h = lettering('DADWARE', colors, 'dw')
    write(name, svg(w, h, body, 'DadWare'))

# ---------- Mark: the D on its own ----------
body, w, h = lettering('D', [S1, S2, S3, S4], 'dm')
side = max(w, h)
write('dadware-mark.svg', svg(side, side, f'<g transform="translate({(side - w) / 2:.1f} {(side - h) / 2:.1f})">{body}</g>', 'DadWare'))

# ---------- Tile: the D on a dark rounded square (avatar, favicon) ----------
def tile(colors, bg, uid, bands=BANDS):
    body, w, h = lettering('D', colors, uid, pad=0, bands=bands)
    side = 1000
    scale = 620 / h
    tx, ty = (side - w * scale) / 2, (side - h * scale) / 2
    return svg(side, side, f'<rect width="{side}" height="{side}" rx="200" fill="{bg}"/>'
               f'<g transform="translate({tx:.1f} {ty:.1f}) scale({scale:.4f})">{body}</g>', 'DadWare')

write('dadware-tile.svg', tile([S1, S2, S3, S4], INK, 'dt'))
write('favicon.svg', tile([S1, S2, S3], INK, 'fv', bands=SIMPLE_BANDS))

# ---------- Ask Dad icon concepts (macOS grid: 1024 canvas, 824 body) ----------
def px(rows, cmap, scale, ox, oy):
    out = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            ch, run = row[x], 1
            while x + run < len(row) and row[x + run] == ch:
                run += 1
            if ch in cmap:
                out.append(f'<rect x="{ox + x * scale}" y="{oy + y * scale}" width="{run * scale}" height="{scale}" fill="{cmap[ch]}"/>')
            x += run
    return '<g shape-rendering="crispEdges">' + ''.join(out) + '</g>'


def icon(inner, bg=CREAM, stripes=True):
    s = ('<defs><clipPath id="body"><rect x="100" y="100" width="824" height="824" rx="185"/></clipPath></defs>'
         f'<g clip-path="url(#body)"><rect x="100" y="100" width="824" height="824" fill="{bg}"/>')
    if stripes:
        for i, c in enumerate([S1, S2, S3, S4]):
            s += f'<rect x="100" y="{772 + i * 38}" width="824" height="28" fill="{c}"/>'
    return svg(1024, 1024, s + inner + '</g>', 'Ask Dad')

BUBBLE = [
    '..##############..',
    '.#wwwwwwwwwwwwww#.',
    '#wwwwwwwwwwwwwwww#',
    '#wwwwwwwwwwwwwwww#',
    '#wwwwwwwwwwwwwwww#',
    '#wwwwwwwwwwwwwwww#',
    '#wwwwwwwwwwwwwwww#',
    '#wwwwwwwwwwwwwwww#',
    '#wwwwwwwwwwwwwwww#',
    '#wwwwwwwwwwwwwwww#',
    '#wwwwwwwwwwwwwwww#',
    '.#wwwwwwwwwwwwww#.',
    '..#ww###########..',
    '..#w#.............',
    '..##..............',
]
QMARK = ['.qqqq.', 'qq..qq', '....qq', '...qq.', '..qq..', '..qq..', '......', '..qq..']
bubble = [list(r) for r in BUBBLE]
for y, r in enumerate(QMARK):
    for x, ch in enumerate(r):
        if ch == 'q':
            bubble[2 + y][6 + x] = 'q'
bubble = [''.join(r) for r in bubble]
shadow = [''.join('s' if ch != '.' else '.' for ch in r) for r in bubble]
sc = 32
ox, oy = (1024 - 18 * sc) // 2 - 16, 190
write('askdad-icon-concept-bubble.svg', icon(
    px(shadow, {"s": INK}, sc, ox + sc, oy + sc) + px(bubble, {'#': INK, 'w': WHITE, 'q': PRIMARY}, sc, ox, oy)))

DAD = [
    '..######....######..',
    '.#llglll####lglll#..',
    '##llllll#..#llllll##',
    '.#llllll#..#llllll#.',
    '.#llllll#..#llllll#.',
    '..######....######..',
    '....................',
    '....................',
    '....mmmmmmmmmmmm....',
    '..mmmmmmmmmmmmmmmm..',
    '.mmmmmmmm..mmmmmmmm.',
    '.mmmmmmm....mmmmmmm.',
    '..mmmm........mmmm..',
]
sc = 32
ox, oy = (1024 - 20 * sc) // 2, 250
write('askdad-icon-concept-dad.svg', icon(px(DAD, {'#': INK, 'l': '#cfdcf5', 'g': WHITE, 'm': '#6b4423'}, sc, ox, oy)))

# Concept C: a striped question mark in the brand lettering, on a dark tile
body, w, h = lettering('?', [S1, S2, S3, S4], 'qm', pad=0)
scale = 560 / h
tx, ty = (1024 - w * scale) / 2, (1024 - h * scale) / 2
write('askdad-icon-concept-question.svg', icon(
    f'<g transform="translate({tx:.1f} {ty:.1f}) scale({scale:.4f})">{body}</g>', bg=INK, stripes=False))
