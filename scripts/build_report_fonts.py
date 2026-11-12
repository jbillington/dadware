#!/usr/bin/env python3
"""Regenerate renderers/report_fonts.py from the brand's woff2 files.

The HTML report is one self-contained file that makes no network requests,
and the app ships as a PyInstaller binary, so the report cannot load fonts
from disk or from Google at runtime. Instead the fonts are embedded in the
report's CSS as base64 data URIs, held in a generated Python module.

Usage:
    ./venv/bin/python scripts/build_report_fonts.py site-next/fonts

Embeds only the faces the report uses (see FACES). Adding a face adds its
size again, plus a third, to every report: check the report CSS really
uses it first. Dev tool only: not part of the build.
"""
import base64
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(REPO_ROOT, 'renderers', 'report_fonts.py')

# (family, style, weight, woff2 file)
FACES = [
    ('Saira', 'italic', 900, 'saira-black-italic.woff2'),
    ('Atkinson Hyperlegible', 'normal', 400, 'atkinson-regular.woff2'),
    ('Atkinson Hyperlegible', 'normal', 700, 'atkinson-bold.woff2'),
    ('Atkinson Hyperlegible', 'italic', 400, 'atkinson-italic.woff2'),
    ('IBM Plex Mono', 'normal', 400, 'ibm-plex-mono-regular.woff2'),
]

LICENSE_COMMENT = """/* Fonts embedded under the SIL Open Font License, Version 1.1
   (https://openfontlicense.org), Latin subsets, unmodified:
   - Saira Black Italic: Copyright 2020 The Saira Project Authors
     (https://github.com/Omnibus-Type/Saira)
   - Atkinson Hyperlegible: Copyright 2020 Braille Institute of America, Inc.
   - IBM Plex Mono: Copyright 2017 IBM Corp., with Reserved Font Name "Plex"
   License texts: site-next/fonts/OFL-*.txt in the Ask Dad source. */
"""

HEADER = '''"""Embedded @font-face CSS for the HTML report. GENERATED - do not edit.

Regenerate with:
    ./venv/bin/python scripts/build_report_fonts.py site-next/fonts

The fonts are base64 data URIs so the report stays one self-contained file
with no network requests, and nothing is read from disk at runtime.
"""

'''


def build(fonts_dir):
    rules = [LICENSE_COMMENT]
    raw_total = 0
    for family, style, weight, filename in FACES:
        with open(os.path.join(fonts_dir, filename), 'rb') as fh:
            data = fh.read()
        raw_total += len(data)
        b64 = base64.b64encode(data).decode('ascii')
        rules.append(
            f'@font-face {{ font-family: "{family}"; font-style: {style}; '
            f'font-weight: {weight}; font-display: swap; '
            f'src: url(data:font/woff2;base64,{b64}) format("woff2"); }}\n'
        )
    css = ''.join(rules)
    with open(OUTPUT, 'w', encoding='utf-8') as fh:
        fh.write(HEADER)
        fh.write('REPORT_FONTS_CSS = """\n')
        fh.write(css)
        fh.write('"""\n')
    print(f'Wrote {os.path.relpath(OUTPUT, REPO_ROOT)}: {len(FACES)} faces, '
          f'{raw_total:,} bytes of woff2, {len(css):,} bytes of CSS per report')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    build(sys.argv[1])
