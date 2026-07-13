#!/usr/bin/env python3
"""Generate the animated hero banner (dark.svg / light.svg) for the profile README.

Both files share one layout and one set of SMIL animations; only the palette differs.
Pure SVG + SMIL, no JavaScript, GitHub-safe.
"""

import os
from xml.sax.saxutils import escape

W, H = 1180, 610

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Helvetica, Arial, sans-serif"

# ---------------------------------------------------------------- content ----

NAME = "Dmitrii Gorovoi"

ROLES = [
    "iOS Engineer",
    "Mobile Developer",
    "Full-Stack Developer",
    "AI / ML Enthusiast",
    "Math & CS Student",
]

INFO = [
    ("Location", "Helsinki, Finland"),
    ("Education", "BSc Mathematics & CS, University of Helsinki"),
    ("Focus", "Mobile Development / AI"),
    ("Portfolio", "github.com/d-m-g"),
    ("Email", "gorovoi.dmitrii@gmail.com"),
]

SKILLS = [
    "Swift", "SwiftUI", "Python", "C++", "JavaScript", "React",
    "Capacitor.js", "scikit-learn", "NumPy", "Pandas", "SQL", "Git", "Linux",
]

# ASCII portrait, derived from the real photo by tools/photo_to_ascii.swift:
#   swift tools/photo_to_ascii.swift ~/Pictures/avatar.jpeg 66 0.52 > tools/portrait.txt
_PORTRAIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portrait.txt")
if os.path.exists(_PORTRAIT):
    with open(_PORTRAIT, encoding="utf-8") as _f:
        ASCII_ART = _f.read().strip("\n").split("\n")
else:
    ASCII_ART = r"""
.:^~!7?JJ?7!~^:.
.^~7J5PGB#####BGP5J7~^.
.^7J5GB#&&&&&&&&&&&&&#BG5J7^.
.~?5GB#&&&&&&&&&&&&&&&&&&&#BG5?~.
.^?PB#&&&&&&&&&&&&&&&&&&&&&&&&&#BP?^.
!5B#&&&&&&&&&#BGP555PGB#&&&&&&&&&#B5!
?G#&&&&&&&&#G5?!^:...:^!?5G#&&&&&&&&#G?
~G#&&&&&&&#P7:            :7P#&&&&&&&#G~
5#&&&&&&&#J:  .~!!~.  .~!!~.  :J#&&&&&&&#5
G#&&&&&&&#!  :JG##GJ: :JG##GJ:  !#&&&&&&&#G
G#&&&&&&&#!  ^P&@@&P^ ^P&@@&P^  !#&&&&&&&#G
P#&&&&&&&#J.  :~??~:   :~??~:  .J#&&&&&&&#P
~G#&&&&&&&#7      .:^^:.      7#&&&&&&&#G~
?G#&&&&&&&#Y~     ~JJ~     ~Y#&&&&&&&#G?
!5B#&&&&&&&#5!.   ..   .!5#&&&&&&&B5!
.^?PB#&&&&&&&BY7~^^~7YB&&&&&&&BP?^.
.~?5GB#&&&&&&&#####&&&&&&#BG5?~.
.^7J5GB#&&&&&&&&&&&&&#BG5J7^.
.^~7J5PGB#####BGP5J7~^.
.:^~!7?JJ?7!~^:.
!!!!!!!!
.:^~!7?JY55YJ?7!~^:.
.:^~7?J5PGB#&&&&&&&#BGP5J?7~^:.
.:^~7?J5PGB#&&&&&&&&&&&&&&&&&#BGP5J?7~^:.
""".strip("\n").split("\n")

# ---------------------------------------------------------------- palettes ---

DARK = dict(
    name="dark",
    bg="#030712",
    panel="#0F172A",
    border="rgba(255,255,255,.08)",
    border_hi="rgba(255,255,255,.18)",
    text="#F8FAFC",
    muted="#94A3B8",
    a1="#7C3AED", a2="#22D3EE", a3="#10B981",
    ascii1="#22D3EE", ascii2="#7C3AED", ascii3="#22D3EE",
    glow1="#22D3EE", glow2="#7C3AED",
    glow_o=0.55,
    blob1="#2563EB", blob2="#7C3AED", blob3="#10B981",
    blob_o=0.22,
    pill_bg="rgba(255,255,255,.04)",
    glass="#FFFFFF", glass_o=0.06,
    scan="#FFFFFF", scan_o=0.05,
    noise_o=0.045,
    particle="#22D3EE",
    shadow_o=0.55,
)

LIGHT = dict(
    name="light",
    bg="#FFFFFF",
    panel="#F8FAFC",
    border="rgba(15,23,42,.08)",
    border_hi="rgba(15,23,42,.16)",
    text="#0F172A",
    muted="#475569",
    a1="#2563EB", a2="#06B6D4", a3="#10B981",
    ascii1="#2563EB", ascii2="#06B6D4", ascii3="#2563EB",
    glow1="#06B6D4", glow2="#2563EB",
    glow_o=0.28,
    blob1="#2563EB", blob2="#06B6D4", blob3="#10B981",
    blob_o=0.10,
    pill_bg="rgba(15,23,42,.03)",
    glass="#FFFFFF", glass_o=0.55,
    scan="#0F172A", scan_o=0.03,
    noise_o=0.03,
    particle="#06B6D4",
    shadow_o=0.10,
)

# ------------------------------------------------------------------ layout ---

PAD = 24
LEFT_X, LEFT_W = PAD, 420                      # ~38% of the canvas
RIGHT_X = LEFT_X + LEFT_W + 16
RIGHT_W = W - RIGHT_X - PAD
PANEL_Y = PAD
PANEL_H = H - 2 * PAD

EPS = 0.01                                     # stand-in for a zero-width clip rect
CW, FS, LH = 5.8, 9.6, 11.15                   # ASCII cell metrics (66-col portrait)
PCW, PFS = 6.3, 11.0                           # pill cell metrics

TX = RIGHT_X + 32                              # terminal text left edge
TERM_INNER_W = RIGHT_W - 64

ROLE_SLOT = 3.0                                # seconds per typed role
ROLE_CYCLE = ROLE_SLOT * len(ROLES)
ROLE_START = 1.6


def e(s):
    return escape(str(s))


def role_keys(i, width):
    """Type-in / hold / erase envelope for role i, as one indefinite cycle.

    keyTimes must be strictly increasing: a duplicate entry invalidates the whole
    animation, and an invalid animation inside a <clipPath> makes WebKit drop the
    clip entirely rather than clip to nothing.
    """
    t0 = (i * ROLE_SLOT) / ROLE_CYCLE
    raw = [
        (0.0, 0.0),
        (t0, 0.0),
        (t0 + 0.075, width),
        (t0 + 0.155, width),
        (t0 + 0.198, 0.0),
        (1.0, 0.0),
    ]
    kt, vals = [], []
    for t, v in raw:
        t = min(max(t, 0.0), 1.0)
        if kt and t <= kt[-1]:
            continue
        kt.append(t)
        vals.append(v)
    return ";".join(f"{t:.4f}" for t in kt), vals


def build(p):
    # Leading spaces in the art are meaningful (they position the head within the
    # sampling grid), so pad on the right only — centring each line individually
    # would shear the columns. The block as a whole is centred via art_x.
    N = max(len(l) for l in ASCII_ART)
    art = [l.ljust(N) for l in ASCII_ART]
    art_w = N * CW
    art_x = LEFT_X + (LEFT_W - art_w) / 2
    art_y = PANEL_Y + (PANEL_H - len(art) * LH) / 2 + 14

    o = []
    a = o.append

    a(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
      f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" role="img" '
      f'aria-label="{e(NAME)} — {e(", ".join(ROLES))}">')

    # ------------------------------------------------------------- defs -----
    a("<defs>")

    # accent gradient, slowly drifting
    a(f'<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0" stop-color="{p["a1"]}">'
      f'<animate attributeName="stop-color" dur="9s" repeatCount="indefinite" '
      f'values="{p["a1"]};{p["a2"]};{p["a3"]};{p["a1"]}"/></stop>'
      f'<stop offset="0.5" stop-color="{p["a2"]}">'
      f'<animate attributeName="stop-color" dur="9s" repeatCount="indefinite" '
      f'values="{p["a2"]};{p["a3"]};{p["a1"]};{p["a2"]}"/></stop>'
      f'<stop offset="1" stop-color="{p["a3"]}">'
      f'<animate attributeName="stop-color" dur="9s" repeatCount="indefinite" '
      f'values="{p["a3"]};{p["a1"]};{p["a2"]};{p["a3"]}"/></stop>'
      f'</linearGradient>')

    # ASCII gradient — travels across the portrait and shifts hue.
    # The text lives inside the translated art group, so userSpaceOnUse coordinates
    # here are group-local (0,0 = top-left of the art block), not root coordinates.
    a(f'<linearGradient id="asciiGrad" gradientUnits="userSpaceOnUse" '
      f'x1="0" y1="{-FS:.1f}" x2="{art_w:.1f}" y2="{len(art) * LH:.1f}">'
      f'<stop offset="0" stop-color="{p["ascii1"]}">'
      f'<animate attributeName="stop-color" dur="11s" repeatCount="indefinite" '
      f'values="{p["ascii1"]};{p["ascii2"]};{p["a3"]};{p["ascii1"]}"/></stop>'
      f'<stop offset="0.5" stop-color="{p["ascii2"]}">'
      f'<animate attributeName="stop-color" dur="11s" repeatCount="indefinite" '
      f'values="{p["ascii2"]};{p["a3"]};{p["ascii1"]};{p["ascii2"]}"/></stop>'
      f'<stop offset="1" stop-color="{p["ascii3"]}">'
      f'<animate attributeName="stop-color" dur="11s" repeatCount="indefinite" '
      f'values="{p["ascii3"]};{p["ascii1"]};{p["ascii2"]};{p["ascii3"]}"/></stop>'
      f'<animateTransform attributeName="gradientTransform" type="translate" '
      f'dur="7s" repeatCount="indefinite" values="-90 0; 90 0; -90 0"/>'
      f'</linearGradient>')

    # border shimmer
    a(f'<linearGradient id="shimmer" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="360" y2="0">'
      f'<stop offset="0" stop-color="{p["border_hi"]}" stop-opacity="0"/>'
      f'<stop offset="0.5" stop-color="{p["a2"]}" stop-opacity="0.75"/>'
      f'<stop offset="1" stop-color="{p["border_hi"]}" stop-opacity="0"/>'
      f'<animateTransform attributeName="gradientTransform" type="translate" '
      f'dur="6s" repeatCount="indefinite" values="-420 0; {W + 60} 0"/>'
      f'</linearGradient>')

    # glass sheen across the panels
    a(f'<linearGradient id="glass" x1="0" y1="0" x2="0.6" y2="1">'
      f'<stop offset="0" stop-color="{p["glass"]}" stop-opacity="{p["glass_o"]}"/>'
      f'<stop offset="0.45" stop-color="{p["glass"]}" stop-opacity="0"/>'
      f'</linearGradient>')

    a(f'<linearGradient id="sheen" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="200" y2="0">'
      f'<stop offset="0" stop-color="{p["glass"]}" stop-opacity="0"/>'
      f'<stop offset="0.5" stop-color="{p["glass"]}" stop-opacity="{p["glass_o"] * 1.6:.3f}"/>'
      f'<stop offset="1" stop-color="{p["glass"]}" stop-opacity="0"/>'
      f'<animateTransform attributeName="gradientTransform" type="translate" '
      f'dur="9s" repeatCount="indefinite" values="-260 0; {W + 200} 0"/>'
      f'</linearGradient>')

    # scanline band
    a(f'<linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">'
      f'<stop offset="0" stop-color="{p["scan"]}" stop-opacity="0"/>'
      f'<stop offset="0.5" stop-color="{p["scan"]}" stop-opacity="{p["scan_o"]}"/>'
      f'<stop offset="1" stop-color="{p["scan"]}" stop-opacity="0"/>'
      f'</linearGradient>')

    # background glow blobs
    for i, (c, cx, cy, r) in enumerate([
        (p["blob2"], 210, 130, 340),
        (p["blob1"], 900, 470, 400),
        (p["blob3"], 660, 90, 300),
    ]):
        a(f'<radialGradient id="blob{i}" cx="0.5" cy="0.5" r="0.5">'
          f'<stop offset="0" stop-color="{c}" stop-opacity="{p["blob_o"]}"/>'
          f'<stop offset="1" stop-color="{c}" stop-opacity="0"/>'
          f'</radialGradient>')

    # glows
    a(f'<filter id="asciiGlow" x="-25%" y="-25%" width="150%" height="150%">'
      f'<feGaussianBlur stdDeviation="4" result="b"/>'
      f'<feColorMatrix in="b" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 {p["glow_o"]} 0" result="g"/>'
      f'<feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>'
      f'</filter>')

    a(f'<filter id="softGlow" x="-40%" y="-40%" width="180%" height="180%">'
      f'<feGaussianBlur stdDeviation="3" result="b"/>'
      f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
      f'</filter>')

    a(f'<filter id="blur40" x="-30%" y="-30%" width="160%" height="160%">'
      f'<feGaussianBlur stdDeviation="40"/></filter>')

    a(f'<filter id="cardShadow" x="-10%" y="-10%" width="120%" height="130%">'
      f'<feDropShadow dx="0" dy="18" stdDeviation="26" flood-color="#000000" '
      f'flood-opacity="{p["shadow_o"]}"/></filter>')

    a('<filter id="noise" x="0" y="0" width="100%" height="100%">'
      '<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch"/>'
      '<feColorMatrix type="saturate" values="0"/>'
      '</filter>')

    # clips
    a(f'<clipPath id="card"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24"/></clipPath>')
    a(f'<clipPath id="leftClip"><rect x="{LEFT_X}" y="{PANEL_Y}" width="{LEFT_W}" height="{PANEL_H}" rx="18"/></clipPath>')

    # Per-line typing clips for the ASCII portrait (local coords of the art group).
    # EPS, not 0: WebKit treats a zero-width rect in a <clipPath> as an *empty* clip
    # and renders the referencing element unclipped instead of clipping it away.
    for i, line in enumerate(art):
        end = len(line.rstrip()) * CW
        y = i * LH - FS
        a(f'<clipPath id="al{i}"><rect x="0" y="{y:.1f}" width="{EPS}" height="{LH:.1f}">'
          f'<animate attributeName="width" from="{EPS}" to="{end:.1f}" dur="0.42s" '
          f'begin="{0.25 + i * 0.065:.2f}s" fill="freeze"/></rect></clipPath>')

    role_x = TX + 26

    # styles (hover affordances when the SVG is viewed directly)
    a('<style>'
      '.pill{transform-box:fill-box;transform-origin:center;'
      'transition:transform .28s cubic-bezier(.2,.8,.2,1),filter .28s ease;}'
      '.pill:hover{transform:scale(1.07);filter:url(#softGlow);}'
      '.pill:hover .pb{stroke-opacity:.85;}'
      '.soc{transform-box:fill-box;transform-origin:center;'
      'transition:transform .28s cubic-bezier(.2,.8,.2,1),filter .28s ease;}'
      '.soc:hover{transform:scale(1.15);filter:url(#softGlow);}'
      '</style>')

    a("</defs>")

    # ---------------------------------------------------------- background --
    a(f'<g filter="url(#cardShadow)">'
      f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24" fill="{p["bg"]}"/></g>')

    a('<g clip-path="url(#card)">')

    # floating radial glows
    for i, (cx, cy, r, dx, dy, dur) in enumerate([
        (210, 130, 340, 26, 18, 17),
        (900, 470, 400, -30, -22, 21),
        (660, 90, 300, 18, 26, 14),
    ]):
        a(f'<g filter="url(#blur40)">'
          f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r * 0.8:.0f}" fill="url(#blob{i})">'
          f'<animateTransform attributeName="transform" type="translate" dur="{dur}s" '
          f'repeatCount="indefinite" values="0 0; {dx} {dy}; {-dx} {dy // 2}; 0 0"/>'
          f'</ellipse></g>')

    # animated particles
    for i in range(14):
        px = 60 + (i * 83) % (W - 120)
        py = 70 + (i * 137) % (H - 140)
        r = 1.0 + (i % 3) * 0.6
        dur = 9 + (i % 5) * 3
        amp = 14 + (i % 4) * 9
        a(f'<circle cx="{px}" cy="{py}" r="{r}" fill="{p["particle"]}" opacity="0.35">'
          f'<animateTransform attributeName="transform" type="translate" dur="{dur}s" '
          f'repeatCount="indefinite" values="0 0; {amp // 2} {-amp}; {-amp // 2} {-amp * 2}; 0 0"/>'
          f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" '
          f'values="0;0.5;0.15;0" keyTimes="0;0.3;0.7;1"/>'
          f'</circle>')

    # noise texture
    a(f'<rect x="0" y="0" width="{W}" height="{H}" filter="url(#noise)" opacity="{p["noise_o"]}"/>')

    # global scanline sweep
    a(f'<rect x="0" y="-80" width="{W}" height="80" fill="url(#scanGrad)">'
      f'<animate attributeName="y" from="-80" to="{H}" dur="7s" repeatCount="indefinite"/>'
      f'</rect>')

    # ------------------------------------------------------------ left panel -
    a(f'<rect x="{LEFT_X}" y="{PANEL_Y}" width="{LEFT_W}" height="{PANEL_H}" rx="18" '
      f'fill="{p["panel"]}" fill-opacity="0.75"/>')
    a(f'<rect x="{LEFT_X}" y="{PANEL_Y}" width="{LEFT_W}" height="{PANEL_H}" rx="18" fill="url(#glass)"/>')
    a(f'<rect x="{LEFT_X}.5" y="{PANEL_Y}.5" width="{LEFT_W - 1}" height="{PANEL_H - 1}" rx="17.5" '
      f'fill="none" stroke="{p["border"]}"/>')

    a('<g clip-path="url(#leftClip)">')
    a(f'<g transform="translate({art_x:.1f} {art_y:.1f})" filter="url(#asciiGlow)">')
    a('<animateTransform attributeName="transform" type="translate" additive="sum" '
      'dur="8s" repeatCount="indefinite" values="0 0; 0 -4; 0 2; 0 0"/>')

    for i, line in enumerate(art):
        y = i * LH
        a(f'<text x="0" y="{y:.1f}" clip-path="url(#al{i})" xml:space="preserve" '
          f'font-family="{MONO}" font-size="{FS}" letter-spacing="0" '
          f'textLength="{len(line) * CW:.1f}" lengthAdjust="spacing" '
          f'fill="url(#asciiGrad)">{e(line)}</text>')

    # per-line typing cursor
    for i, line in enumerate(art):
        lead = (len(line) - len(line.lstrip())) * CW
        end = len(line.rstrip()) * CW
        t = 0.25 + i * 0.065
        a(f'<rect x="{lead:.1f}" y="{i * LH - FS + 1.5:.1f}" width="{CW:.1f}" height="{FS:.1f}" '
          f'fill="{p["glow1"]}" opacity="0">'
          f'<animate attributeName="x" from="{lead:.1f}" to="{end:.1f}" dur="0.42s" begin="{t:.2f}s" fill="freeze"/>'
          f'<animate attributeName="opacity" values="0;0.9;0.9;0" keyTimes="0;0.05;0.95;1" '
          f'dur="0.42s" begin="{t:.2f}s" fill="remove"/>'
          f'</rect>')

    # resting cursor under the portrait
    last = len(art) - 1
    a(f'<rect x="{(len(art[last]) - len(art[last].lstrip())) * CW:.1f}" y="{(last + 1) * LH - FS + 1.5:.1f}" '
      f'width="{CW:.1f}" height="{FS:.1f}" fill="{p["glow1"]}" opacity="0">'
      f'<animate attributeName="opacity" values="0;0;1;0;1" keyTimes="0;0.32;0.34;0.67;1" '
      f'dur="3s" begin="0s" repeatCount="indefinite"/></rect>')

    a("</g>")  # art group

    # terminal scanline inside the ASCII panel
    a(f'<rect x="{LEFT_X}" y="{PANEL_Y}" width="{LEFT_W}" height="46" fill="url(#scanGrad)" opacity="0.9">'
      f'<animate attributeName="y" from="{PANEL_Y - 46}" to="{PANEL_Y + PANEL_H}" dur="4.5s" '
      f'repeatCount="indefinite"/></rect>')
    a("</g>")  # leftClip

    # ----------------------------------------------------------- right panel -
    a(f'<rect x="{RIGHT_X}" y="{PANEL_Y}" width="{RIGHT_W}" height="{PANEL_H}" rx="18" '
      f'fill="{p["panel"]}" fill-opacity="0.75"/>')
    a(f'<rect x="{RIGHT_X}" y="{PANEL_Y}" width="{RIGHT_W}" height="{PANEL_H}" rx="18" fill="url(#glass)"/>')
    a(f'<rect x="{RIGHT_X}.5" y="{PANEL_Y}.5" width="{RIGHT_W - 1}" height="{PANEL_H - 1}" rx="17.5" '
      f'fill="none" stroke="{p["border"]}"/>')

    # window chrome
    bar_b = PANEL_Y + 42
    for i, c in enumerate([p["a1"], p["a2"], p["a3"]]):
        a(f'<circle cx="{RIGHT_X + 26 + i * 18}" cy="{PANEL_Y + 21}" r="5" fill="{c}" opacity="0.9">'
          f'<animate attributeName="opacity" values="0.55;1;0.55" dur="{3 + i}s" repeatCount="indefinite"/>'
          f'</circle>')
    a(f'<text x="{RIGHT_X + RIGHT_W / 2:.0f}" y="{PANEL_Y + 25}" text-anchor="middle" '
      f'font-family="{MONO}" font-size="12" fill="{p["muted"]}" opacity="0.75">'
      f'dmitrii@helsinki: ~/profile</text>')
    a(f'<line x1="{RIGHT_X}" y1="{bar_b}" x2="{RIGHT_X + RIGHT_W}" y2="{bar_b}" stroke="{p["border"]}"/>')

    def reveal(begin, dy=8):
        return (f'<animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{begin}s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" from="0 {dy}" to="0 0" '
                f'dur="0.5s" begin="{begin}s" fill="freeze"/>')

    # $ whoami
    a(f'<g opacity="0" transform="translate(0 8)">{reveal(0.3)}'
      f'<text x="{TX}" y="{PANEL_Y + 76}" font-family="{MONO}" font-size="13" fill="{p["a2"]}">$</text>'
      f'<text x="{TX + 16}" y="{PANEL_Y + 76}" font-family="{MONO}" font-size="13" fill="{p["muted"]}">whoami</text>'
      f'</g>')

    # greeting
    a(f'<g opacity="0" transform="translate(0 8)">{reveal(0.7)}'
      f'<text x="{TX}" y="{PANEL_Y + 110}" font-family="{SANS}" font-size="19" fill="{p["muted"]}">'
      f'Hi <tspan font-size="19">\U0001F44B</tspan></text></g>')

    a(f'<g opacity="0" transform="translate(0 8)">{reveal(1.0)}'
      f'<text x="{TX}" y="{PANEL_Y + 152}" font-family="{SANS}" font-size="34" font-weight="700" '
      f'letter-spacing="-0.5" fill="url(#accent)">I\'m {e(NAME)}</text></g>')

    # typing roles
    a(f'<g opacity="0">'
      f'<animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="1.45s" fill="freeze"/>'
      f'<text x="{TX}" y="{PANEL_Y + 190}" font-family="{MONO}" font-size="16" fill="{p["a3"]}">&gt;</text>')
    # Each role lives in its own nested <svg> viewport whose width is animated; the
    # viewport clips by construction and behaves correctly at width 0 (a <clipPath>
    # does not — see EPS above).
    for i, role in enumerate(ROLES):
        rw = len(role) * 9.6
        kt, vals = role_keys(i, rw)
        vs = ";".join(f"{v:.1f}" for v in vals)
        a(f'<svg x="{role_x}" y="{PANEL_Y + 172}" width="0" height="26" overflow="hidden">'
          f'<animate attributeName="width" dur="{ROLE_CYCLE}s" begin="{ROLE_START}s" '
          f'repeatCount="indefinite" values="{vs}" keyTimes="{kt}"/>'
          f'<text x="0" y="18" font-family="{MONO}" font-size="16" textLength="{rw:.1f}" '
          f'lengthAdjust="spacing" fill="{p["text"]}">{e(role)}</text></svg>')

    # role cursor: outer group gates visibility per slot, inner rect blinks
    for i, role in enumerate(ROLES):
        rw = len(role) * 9.6
        kt, vals = role_keys(i, rw)
        # visibility: on for this role's slot, off otherwise
        vis = ";".join("1" if v else "0" for v in vals)
        # x: rides the right edge of the typed text
        xs = ";".join(f"{role_x + v:.1f}" for v in vals)
        a(f'<g opacity="0">'
          f'<animate attributeName="opacity" dur="{ROLE_CYCLE}s" begin="{ROLE_START}s" '
          f'repeatCount="indefinite" values="{vis}" keyTimes="{kt}"/>'
          f'<rect x="{role_x}" y="{PANEL_Y + 176}" width="9" height="18" fill="{p["a2"]}">'
          f'<animate attributeName="x" dur="{ROLE_CYCLE}s" begin="{ROLE_START}s" repeatCount="indefinite" '
          f'values="{xs}" keyTimes="{kt}"/>'
          f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.45;0.5;0.95;1" '
          f'dur="1.05s" repeatCount="indefinite"/>'
          f'</rect></g>')
    a("</g>")

    a(f'<line x1="{TX}" y1="{PANEL_Y + 214}" x2="{TX + TERM_INNER_W}" y2="{PANEL_Y + 214}" '
      f'stroke="{p["border"]}" opacity="0">'
      f'<animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="1.5s" fill="freeze"/></line>')

    # info rows
    for i, (k, v) in enumerate(INFO):
        y = PANEL_Y + 244 + i * 28
        a(f'<g opacity="0" transform="translate(0 8)">{reveal(1.8 + i * 0.16)}'
          f'<circle cx="{TX + 3}" cy="{y - 4}" r="2.5" fill="url(#accent)"/>'
          f'<text x="{TX + 16}" y="{y}" font-family="{MONO}" font-size="12.5" '
          f'fill="{p["muted"]}">{e(k)}</text>'
          f'<text x="{TX + 116}" y="{y}" font-family="{MONO}" font-size="12.5" '
          f'fill="{p["text"]}">{e(v)}</text>'
          f'</g>')

    # skills
    sy = PANEL_Y + 400
    a(f'<g opacity="0" transform="translate(0 8)">{reveal(2.8)}'
      f'<text x="{TX}" y="{sy}" font-family="{MONO}" font-size="13" fill="{p["a2"]}">$</text>'
      f'<text x="{TX + 16}" y="{sy}" font-family="{MONO}" font-size="13" fill="{p["muted"]}">'
      f'cat skills.json</text></g>')

    ph, gap, vgap = 26, 8, 8
    cx, cy = TX, sy + 18
    for i, s in enumerate(SKILLS):
        tw = len(s) * PCW
        pw = tw + 24
        if cx + pw > TX + TERM_INNER_W:
            cx = TX
            cy += ph + vgap
        b = 3.1 + i * 0.055
        a(f'<g class="pill" opacity="0">'
          f'<animate attributeName="opacity" from="0" to="1" dur="0.45s" begin="{b:.2f}s" fill="freeze"/>'
          f'<rect class="pb" x="{cx:.1f}" y="{cy}" width="{pw:.1f}" height="{ph}" rx="{ph / 2}" '
          f'fill="{p["pill_bg"]}" stroke="url(#accent)" stroke-opacity="0.35">'
          f'<animate attributeName="stroke-opacity" values="0.28;0.6;0.28" dur="{4 + (i % 4)}s" '
          f'begin="{b:.2f}s" repeatCount="indefinite"/></rect>'
          f'<text x="{cx + pw / 2:.1f}" y="{cy + 17}" text-anchor="middle" font-family="{MONO}" '
          f'font-size="{PFS}" textLength="{tw:.1f}" lengthAdjust="spacing" '
          f'fill="{p["text"]}" fill-opacity="0.88">{e(s)}</text>'
          f'</g>')
        cx += pw + gap

    # socials
    icons = {
        "github": ("M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577"
                   " 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7"
                   "c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998"
                   ".108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22"
                   "-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405"
                   " 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176"
                   ".765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22"
                   " 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297"
                   "c0-6.627-5.373-12-12-12Z"),
        "linkedin": ("M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5ZM3 9h4v12H3V9Zm7 0h3.8v1.7h.05c.53-.95 1.83-1.95 3.77-1.95"
                     "C21.6 8.75 23 11 23 14.6V21h-4v-5.7c0-1.36-.03-3.1-1.9-3.1-1.9 0-2.2 1.47-2.2 3v5.8h-4V9Z"),
        "instagram": ("M12 2.2c3.2 0 3.58.01 4.85.07 1.17.05 1.8.25 2.23.41.56.22.96.48 1.38.9.42.42.68.82.9 1.38"
                      ".16.42.36 1.06.41 2.23.06 1.27.07 1.65.07 4.85s-.01 3.58-.07 4.85c-.05 1.17-.25 1.8-.41 2.23"
                      "-.22.56-.48.96-.9 1.38-.42.42-.82.68-1.38.9-.42.16-1.06.36-2.23.41-1.27.06-1.65.07-4.85.07"
                      "s-3.58-.01-4.85-.07c-1.17-.05-1.8-.25-2.23-.41-.56-.22-.96-.48-1.38-.9-.42-.42-.68-.82-.9-1.38"
                      "-.16-.42-.36-1.06-.41-2.23C2.21 15.58 2.2 15.2 2.2 12s.01-3.58.07-4.85c.05-1.17.25-1.8.41-2.23"
                      ".22-.56.48-.96.9-1.38.42-.42.82-.68 1.38-.9.42-.16 1.06-.36 2.23-.41C8.42 2.21 8.8 2.2 12 2.2Zm0 1.8"
                      "c-3.14 0-3.5.01-4.74.07-.9.04-1.39.19-1.72.32-.43.17-.74.37-1.06.69-.32.32-.52.63-.69 1.06"
                      "-.13.33-.28.82-.32 1.72C3.41 8.5 3.4 8.86 3.4 12s.01 3.5.07 4.74c.04.9.19 1.39.32 1.72.17.43.37.74.69 1.06"
                      ".32.32.63.52 1.06.69.33.13.82.28 1.72.32 1.24.06 1.6.07 4.74.07s3.5-.01 4.74-.07c.9-.04 1.39-.19 1.72-.32"
                      ".43-.17.74-.37 1.06-.69.32-.32.52-.63.69-1.06.13-.33.28-.82.32-1.72.06-1.24.07-1.6.07-4.74"
                      "s-.01-3.5-.07-4.74c-.04-.9-.19-1.39-.32-1.72a2.9 2.9 0 0 0-.69-1.06 2.9 2.9 0 0 0-1.06-.69"
                      "c-.33-.13-.82-.28-1.72-.32C15.5 4.01 15.14 4 12 4Zm0 3.03a4.97 4.97 0 1 1 0 9.94 4.97 4.97 0 0 1 0-9.94Z"
                      "m0 1.8a3.17 3.17 0 1 0 0 6.34 3.17 3.17 0 0 0 0-6.34Zm5.2-3.24a1.16 1.16 0 1 1 0 2.32 1.16 1.16 0 0 1 0-2.32Z"),
        "globe": ("M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm0 1.8c1.4 0 2.9 2.35 3.4 5.7H8.6C9.1 6.15 10.6 3.8 12 3.8Z"
                  "M8.36 9.5a22 22 0 0 0 0 5H3.98a8.2 8.2 0 0 1 0-5h4.38Zm7.28 0h4.38a8.2 8.2 0 0 1 0 5h-4.38a22 22 0 0 0 0-5Z"
                  "M8.6 16.3h6.8c-.5 3.35-2 5.7-3.4 5.7s-2.9-2.35-3.4-5.7Zm-1.83 0c.33 2.05.94 3.8 1.75 5.02A8.24 8.24 0 0 1 4.9 16.3h1.87Z"
                  "m10.46 0h1.87a8.24 8.24 0 0 1-3.62 5.02c.81-1.22 1.42-2.97 1.75-5.02ZM8.52 2.68C7.71 3.9 7.1 5.65 6.77 7.7H4.9a8.24 8.24 0 0 1 3.62-5.02Z"
                  "m6.96 0A8.24 8.24 0 0 1 19.1 7.7h-1.87c-.33-2.05-.94-3.8-1.75-5.02ZM10.2 9.5h3.6a20 20 0 0 1 0 5h-3.6a20 20 0 0 1 0-5Z"),
    }
    order = ["github", "linkedin", "instagram", "globe"]
    iy = PANEL_Y + PANEL_H - 44
    for i, key in enumerate(order):
        ix = TX + i * 42
        b = 4.2 + i * 0.12
        a(f'<g class="soc" opacity="0">'
          f'<animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{b:.2f}s" fill="freeze"/>'
          f'<rect x="{ix - 6}" y="{iy - 6}" width="34" height="34" rx="10" fill="{p["pill_bg"]}" '
          f'stroke="{p["border"]}"/>'
          f'<g transform="translate({ix} {iy}) scale(0.92)">'
          f'<path d="{icons[key]}" fill="url(#accent)" fill-opacity="0.9"/>'
          f'</g>'
          f'<animate attributeName="opacity" values="1;0.72;1" dur="{5 + i}s" begin="{b + 0.6:.2f}s" '
          f'repeatCount="indefinite"/>'
          f'</g>')

    a(f'<text x="{TX + 4 * 42 + 14}" y="{iy + 22}" font-family="{MONO}" font-size="11.5" '
      f'fill="{p["muted"]}" opacity="0">'
      f'<animate attributeName="opacity" from="0" to="0.8" dur="0.6s" begin="4.8s" fill="freeze"/>'
      f'd-m-g &#183; dmitrii-gorovoi &#183; dm_g__</text>')

    # glass sheen + shimmer over everything
    a(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#sheen)" opacity="0.5"/>')
    a("</g>")  # card clip

    a(f'<rect x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" rx="23" fill="none" '
      f'stroke="{p["border"]}"/>')
    a(f'<rect x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" rx="23" fill="none" '
      f'stroke="url(#shimmer)" stroke-width="1.5"/>')

    a("</svg>")
    return "".join(o)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for pal in (DARK, LIGHT):
        path = os.path.join(root, f'{pal["name"]}.svg')
        with open(path, "w", encoding="utf-8") as f:
            f.write(build(pal))
        print(f'wrote {path} ({os.path.getsize(path)} bytes)')


if __name__ == "__main__":
    main()
