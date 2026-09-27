#!/usr/bin/env python3
"""Generates res/raw/watchface.xml for the Arcminute Watch Face Format port.

The geometry is the same orbiting-dial design as pebble/src/c/arcminute.c: a
dial three screen-sizes wide whose center sits opposite the current hour
angle, so the rim (numerals + ticks) sweeps through the visible screen, plus
a hand from the dial center to the current-hour rim point.

Targets Watch Face Format 4 (Wear OS 6, API 36), for the ambient transition
attributes on Variant. Version 5 adds nothing this face uses and would cost
every watch below Wear OS 7.

Edit THIS file and re-run it; never hand-edit watchface.xml.

    python3 wear/wff/tools/generate_watchface.py
"""

import math
import os

# ---- Reference geometry: gabbro (260 px) constants scaled to a 450 canvas ----
CANVAS = 450
SCALE = CANVAS / 260.0          # 1.7308
CX = CANVAS / 2                 # 225
ORBIT = 188 * SCALE             # 325.4
DIST = CX + ORBIT               # dial-center distance from screen center
DIAL_R = 1.5 * CANVAS           # 675
# The face disc is filled 8 gabbro px past the marker ring, as in
# arcminute.c's my_face_draw (`bounds.size.w / 2 + 8`), so its edge reads as
# a rim just outside the ticks rather than slicing through them. The dial
# group is grown by the same amount at every edge so the disc is not clipped;
# every interior coordinate is measured from DC, so widening the group and
# recentering DC shifts the whole dial with it.
FACE_OVERSHOOT = 8 * SCALE      # 13.8
FACE_R = DIAL_R + FACE_OVERSHOOT
DIAL_SIZE = 3 * CANVAS + 2 * FACE_OVERSHOOT
DC = DIAL_SIZE / 2              # dial local center

HAND_STROKE = 7 * SCALE         # 12.1 (Pebble uses 9; thinned per user preference)

# Hour angle in degrees, updated each minute
ANGLE = "(30 * [HOUR_0_11_MINUTE])"
# Dial group top-left corner so the dial center lands at C - DIST*u(angle)
GROUP_X = f"({CX - DC:.1f} - {DIST:.1f} * sin(rad({ANGLE})))"
GROUP_Y = f"({CX - DC:.1f} + {DIST:.1f} * cos(rad({ANGLE})))"
# Dial center in screen coordinates, for elements whose center attribute is
# transformable (Arc, TextCircular) and so need no oversized wrapper group
DIAL_CX = f"({CX:.1f} - {DIST:.1f} * sin(rad({ANGLE})))"
DIAL_CY = f"({CX:.1f} + {DIST:.1f} * cos(rad({ANGLE})))"

STYLES = {
    "large": dict(
        font_size=95 * SCALE,        # 164.4
        hour_inset=27.7 * SCALE,     # 47.9
        hour_stroke=6 * SCALE,       # 10.4
        minor_stroke=6 * SCALE,      # 10.4 - matches hour_stroke per user preference
        # Tight glyph half-dimensions for Helvetica digits at this size:
        # cap height ~0.72em, digit advance ~0.556em
        half_h=0.36 * 95 * SCALE,    # 59
        half_w1=0.278 * 95 * SCALE,  # 46 (one digit)
        half_w2=0.556 * 95 * SCALE,  # 91 (two digits)
    ),
    "classic": dict(
        font_size=42 * SCALE,        # 72.7
        hour_inset=13.8 * SCALE,     # 23.9
        hour_stroke=3 * SCALE,       # 5.2
        minor_stroke=3 * SCALE,      # 5.2 - matches hour_stroke per user preference
        half_h=0.36 * 42 * SCALE,
        half_w1=0.278 * 42 * SCALE,
        half_w2=0.556 * 42 * SCALE,
    ),
}

# The face is the single source of color: it fills the dial disc and every
# mark drawn on it. The background sits behind the disc and defaults to a
# fully transparent "Match face" option, so the face color shows through and
# the screen reads as one surface -- pebble's FACE_CLEAR, without needing a
# toggle. Picking a real background color paints over that, and the disc
# edge becomes visible. Nothing is color-conditional, so the dial is emitted
# once (colors accept a single reference or literal, never an expression).
BG_COLOR = "[CONFIGURATION.backColor.0]"
FACE_COLOR = "[CONFIGURATION.faceColor.0]"
FACE_TEXT = "[CONFIGURATION.faceColor.1]"
FACE_MINOR = "[CONFIGURATION.faceColor.2]"
HAND_COLOR = "[CONFIGURATION.handColor.0]"
# Ambient is always dark, and is not a user choice. Everything colored -- the
# ground, the face disc, the marks on it, the complication -- fades out, and a
# light copy of the dial fades in on black. A copy is needed because Variant
# only carries numeric values (it can swap alpha, never a color), so marks
# drawn in a light face's dark text would vanish against the black. Leaving
# the disc lit would put a non-black face over Play's 15% illuminated-pixel
# guidance for ambient, since the disc covers the whole screen.
AMBIENT_TEXT = "#FFFFFF"
# Same weight as the interactive minor marks. An earlier version dropped
# these to 0x66 to shave lit subpixels; the tick ring is the dial's
# character and reading it as faded at night was not worth the pixels.
AMBIENT_MINOR = "#AAFFFFFF"

# ---- Ambient transitions (Watch Face Format 4) ----
# duration and startOffset are fractions of the window the system allows for a
# mode change, and the runtime discards BOTH if they sum past 1.0. Each
# Variant carries one curve that serves both directions, so this cascade runs
# forward on wake and in reverse going idle:
#
#   the whole face draws back 5%, and under that:
#   ground drains -> dials cross
#
# The staggering is the point. A single shared window cross-fades every layer
# through a muddy half-lit midpoint; offsetting them means the dark lifts
# before the color arrives, and each stage reads as its own move.
GROUND_FADE = 'startOffset="0" duration="0.5" interpolation="EASE_OUT"'
# Named for the object, not a direction: each of these fades out going idle
# and in again on wake, on the same curve. The color dial moves first at
# both ends, so waking, the face has color under the marks before the light
# copy has finished dissolving off the top of it.
COLOR_DIAL_FADE = 'startOffset="0.1" duration="0.5" interpolation="EASE_OUT"'
LIGHT_DIAL_FADE = 'startOffset="0.25" duration="0.6" interpolation="EASE_IN_OUT"'
# The core move: the whole composition draws back 5% when the screen idles.
# It runs the full window under everything else, so the fades read as detail
# on top of one gesture rather than as separate events.
#
# The hand deliberately has no Variant of its own. It keeps full color and
# full length in ambient -- an earlier version scaled it about its own group
# pivot, which is the dial center, so it retracted from the rim and left a
# gap. Scaling the composition instead moves the hand with the dial, so the
# tip stays on the marks.
CORE_SCALE = 'startOffset="0" duration="0.75" interpolation="EASE_OUT"'
AMBIENT_SCALE = 0.95
# Screen center expressed as a fraction of the dial group's own box, so the
# group scales about the middle of the screen rather than the dial's center
# (which sits ~513px off-screen, and would swing the rim away instead of
# shrinking it). pivotX/pivotY are transformable, so this tracks the hour.
# Ambient rim vignette: the outermost few pixels ramp to pure black, so the
# dial does not end on a hard lit edge against the bezel at night. Drawn last
# and in screen coordinates, so it stays pinned to the rim while the
# composition scales away from it.
VIGNETTE_WIDTH = 0.10
# The ramp spans this fraction of the screen WIDTH, so twice that of the
# radius. Stops are laid out to be evenly spaced BY CONSTRUCTION and
# `positions` is emitted to match, because the two runtimes disagree about
# it: Wear OS 7 ignores `positions` and distributes stops evenly, while the
# Wear OS 6 emulator honors them. The same four-stop file rendered a 10px
# rim on the emulator and a 75px wash across a third of the radius on a
# Pixel Watch 5. Even spacing is the one layout both agree on.
#
# For the last gap to be the ramp, N stops evenly spaced need the
# second-to-last at 1 - 2*width, which gives N = 1/(2*width) + 1.
PIVOT_X = f"(({DC:.1f} + {DIST:.1f} * sin(rad({ANGLE}))) / {DIAL_SIZE:.1f})"
PIVOT_Y = f"(({DC:.1f} - {DIST:.1f} * cos(rad({ANGLE}))) / {DIAL_SIZE:.1f})"
# The complication rides the band just outside the rim, which the face disc
# overshoots, so it follows the face too.
TEXT_COLOR = FACE_TEXT

# Tailwind CSS 500-series palette
TAILWIND = [
    ("red", "Red", "#EF4444"),
    ("orange", "Orange", "#F97316"),
    ("amber", "Amber", "#F59E0B"),
    ("yellow", "Yellow", "#EAB308"),
    ("lime", "Lime", "#84CC16"),
    ("olive", "Olive", "#708238"),
    ("green", "Green", "#22C55E"),
    ("emerald", "Emerald", "#10B981"),
    ("teal", "Teal", "#14B8A6"),
    ("cyan", "Cyan", "#06B6D4"),
    ("sky", "Sky", "#0EA5E9"),
    ("blue", "Blue", "#3B82F6"),
    ("indigo", "Indigo", "#6366F1"),
    ("violet", "Violet", "#8B5CF6"),
    ("purple", "Purple", "#A855F7"),
    ("fuchsia", "Fuchsia", "#D946EF"),
    ("pink", "Pink", "#EC4899"),
    ("rose", "Rose", "#F43F5E"),
]
BLACK_WHITE = [("black", "Black", "#000000"), ("white", "White", "#FFFFFF")]


def luminance(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def theme_colors(bg_hex):
    """bg -> (text, minor) so numerals stay readable on any background.

    Minor marks are the text color at 67% alpha (0xAA) rather than a solid
    gray, so they tint with the background. Over pure black/white this blends
    to the same #AAAAAA / #555555 the solid grays used to be.
    """
    if luminance(bg_hex) >= 140:
        return "#000000", "#AA000000"
    return "#FFFFFF", "#AAFFFFFF"


# Option labels carry their configuration's name ("Hand: Red"), because the
# editor shows one option label at a time with no indication of which setting
# is being turned.
MATCH_FACE = ("match", "Match face", "#00000000")
BACK_PALETTE = [MATCH_FACE] + BLACK_WHITE + TAILWIND
FACE_PALETTE = BLACK_WHITE + TAILWIND
HAND_PALETTE = TAILWIND + BLACK_WHITE
PREFIXES = {"back": "Back", "face": "Face", "hand": "Hand"}
# id -> (string prefix, label word, {option id: label}, default option), in
# editor page order. Option labels carry the setting's word, as colors do.
LIST_SETTINGS = {
    "numerals": ("numerals", "Numerals",
                 {"large": "Large", "classic": "Classic"}, "large"),
    "hours": ("hours", "Hours",
              {"h12": "12-hour", "h24": "24-hour"}, "h12"),
    # Last, so it sits next to the editor's own complications page.
    "iconPosition": ("icon_position", "Complication",
                     {"tip": "Tip", "base": "Base"}, "tip"),
}


def user_configurations():
    out = []
    out.append('  <UserConfigurations>')
    # Face before background: the face is the one that actually changes the
    # watch, and the background defaults to matching it, so it reads as the
    # exception you reach for second.
    out.append('    <ColorConfiguration id="faceColor" displayName="face_label"'
               ' screenReaderText="face_label" defaultValue="black">')
    for cid, _, fill in FACE_PALETTE:
        text, minor = theme_colors(fill)
        out.append(f'      <ColorOption id="{cid}" displayName="face_{cid}_label"'
                   f' colors="{fill} {text} {minor}" />')
    out.append('    </ColorConfiguration>')
    out.append('    <ColorConfiguration id="backColor" displayName="back_label"'
               ' screenReaderText="back_label" defaultValue="match">')
    for cid, _, bg in BACK_PALETTE:
        out.append(f'      <ColorOption id="{cid}" displayName="back_{cid}_label"'
                   f' colors="{bg}" />')
    out.append('    </ColorConfiguration>')
    out.append('    <ColorConfiguration id="handColor" displayName="hand_label"'
               ' screenReaderText="hand_label" defaultValue="red">')
    for cid, _, hex_color in HAND_PALETTE:
        out.append(f'      <ColorOption id="{cid}" displayName="hand_{cid}_label"'
                   f' colors="{hex_color}" />')
    out.append('    </ColorConfiguration>')
    # Lists rather than toggles: each gets its own editor page, whereas the
    # Wear OS 7 editor draws its shared toggles page with every switch cut
    # off at the right edge of the round screen.
    for config_id, (prefix, _, options, default) in LIST_SETTINGS.items():
        out.append(f'    <ListConfiguration id="{config_id}"'
                   f' displayName="{prefix}_label"'
                   f' screenReaderText="{prefix}_label" defaultValue="{default}">')
        for option_id in options:
            out.append(f'      <ListOption id="{option_id}"'
                       f' displayName="{prefix}_{option_id}_label" />')
        out.append('    </ListConfiguration>')
    out.append('  </UserConfigurations>')
    return "\n".join(out)


def config_strings():
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<!-- GENERATED by tools/generate_watchface.py - do not edit by hand. -->',
             '<resources>',
             '    <string name="back_label">Background</string>',
             '    <string name="face_label">Dial face</string>',
             '    <string name="hand_label">Hand</string>']
    for prefix, word, options, _ in LIST_SETTINGS.values():
        lines.append(f'    <string name="{prefix}_label">{word}</string>')
        for option_id, label in options.items():
            lines.append(f'    <string name="{prefix}_{option_id}_label">'
                         f'{word}: {label}</string>')
    lines.append('    <string name="back_match_label">Back: Match face</string>')
    for prefix, word in PREFIXES.items():
        for cid, label, _ in BLACK_WHITE + TAILWIND:
            lines.append(f'    <string name="{prefix}_{cid}_label">'
                         f'{word}: {label}</string>')
    lines.append('</resources>')
    return "\n".join(lines) + "\n"


# ---- Icon complication at the tip or base of the hand ----
# A circle on the hand line, one tick-gap outside the tick ring at its inner
# edge and one tick-gap inside the bezel at its outer edge. The iconPosition
# setting moves it from past the tip to the same distance on the far side,
# where the hand starts; both positions share one ring, so one slot bound
# covers either.
ICON_GAP = 5 * SCALE
ICON_INNER = DIAL_R - DIST + ICON_GAP
ICON_OUTER = CX - ICON_GAP
ICON_SIZE = ICON_OUTER - ICON_INNER
ICON_K = (ICON_INNER + ICON_OUTER) / 2      # circle center from screen center
# At the base nothing else is drawn nearby, so the circle grows about the
# same center until it touches the bezel.
BASE_SIZE = 2 * (CX - ICON_K)


def orbit_xy(k, half):
    """Top-left of a box of half-size `half` centered k px from the screen
    center along the hour direction (negative k points away from it)."""
    toward, away = ("+", "-") if k >= 0 else ("-", "+")
    x = f"({CX:.1f} {toward} {abs(k):.1f} * sin(rad({ANGLE})) - {half:.1f})"
    y = f"({CX:.1f} {away} {abs(k):.1f} * cos(rad({ANGLE})) - {half:.1f})"
    return x, y


def ambient_fade(value, timing):
    return (f'              <Variant mode="AMBIENT" target="alpha"'
            f' value="{value}" {timing} />\n')


# Interactive copies fade out with the color dial, ambient copies fade in
# with the light one.
INTERACTIVE = (255, ambient_fade("0", COLOR_DIAL_FADE))
AMBIENT = (0, ambient_fade("255", LIGHT_DIAL_FADE))


def icon_image(k, size, resource, tint, phase=(255, "")):
    """Icon centered on the hand line. Icons stay upright, so no direction
    flip is needed."""
    half = size / 2
    x, y = orbit_xy(k, half)
    alpha, variant = phase
    tint_attr = f' tintColor="{tint}"' if tint else ""
    return (
        f'            <PartImage x="{CX - half:.0f}" y="{CX - k - half:.0f}"'
        f' width="{size:.0f}" height="{size:.0f}"'
        f' alpha="{alpha}"{tint_attr}>\n'
        f'{variant}'
        f'              <Transform target="x" value="{x}" />\n'
        f'              <Transform target="y" value="{y}" />\n'
        f'              <Image resource="{resource}" />\n'
        f'            </PartImage>'
    )


def hub(k, size, color, phase):
    """Disc under the base icon, so the hand reads as starting from it."""
    half = size / 2
    x, y = orbit_xy(k, half)
    alpha, variant = phase
    return (
        f'            <PartDraw x="{CX - half:.0f}" y="{CX - k - half:.0f}"'
        f' width="{size:.0f}" height="{size:.0f}" alpha="{alpha}">\n'
        f'{variant}'
        f'              <Transform target="x" value="{x}" />\n'
        f'              <Transform target="y" value="{y}" />\n'
        f'              <Ellipse x="0" y="0" width="{size:.1f}" height="{size:.1f}">\n'
        f'                <Fill color="{color}" />\n'
        f'              </Ellipse>\n'
        f'            </PartDraw>'
    )


def icon_parts(complication_type, k, size):
    """A monochrome icon is tinted with the face text color, which can be
    black, so like the dial it crossfades to a white copy in ambient. A
    full-color icon has no tint to swap and stays as it is."""
    resource = f"[COMPLICATION.{complication_type}]"
    if complication_type == "MONOCHROMATIC_IMAGE":
        return [icon_image(k, size, resource, TEXT_COLOR, INTERACTIVE),
                icon_image(k, size, resource, AMBIENT_TEXT, AMBIENT)]
    return [icon_image(k, size, resource, None)]


def icon_position(option_id, complication_type, k, size, with_hub):
    # The hub is face-colored while awake and black in ambient, where a
    # light face color would light the disc all night.
    backing = ([hub(k, size, FACE_COLOR, INTERACTIVE),
                hub(k, size, "#000000", AMBIENT)] if with_hub else [])
    return "\n".join([
        f'          <ListOption id="{option_id}">',
        f'            <Group x="0" y="0" width="{CANVAS}" height="{CANVAS}"'
        f' name="icon_{complication_type.lower()}_{option_id.lower()}">',
        *backing,
        *icon_parts(complication_type, k, size),
        '            </Group>',
        '          </ListOption>',
    ])


def icon_complication(complication_type):
    """The icon stays up in ambient and draws back with the dial: a
    canvas-sized group pivots on the screen center, so the same 5% scale
    keeps the icon on the hand line. A ComplicationSlot cannot sit inside a
    configuration, so the position setting lives in here instead."""
    return "\n".join([
        f'      <Complication type="{complication_type}">',
        f'        <Group x="0" y="0" width="{CANVAS}" height="{CANVAS}"'
        f' name="icon_{complication_type.lower()}"'
        f' pivotX="0.5" pivotY="0.5" scaleX="1" scaleY="1">',
        f'          <Variant mode="AMBIENT" target="scaleX"'
        f' value="{AMBIENT_SCALE}" {CORE_SCALE} />',
        f'          <Variant mode="AMBIENT" target="scaleY"'
        f' value="{AMBIENT_SCALE}" {CORE_SCALE} />',
        '          <ListConfiguration id="iconPosition">',
        icon_position("tip", complication_type, ICON_K, ICON_SIZE,
                      with_hub=False),
        icon_position("base", complication_type, -ICON_K, BASE_SIZE,
                      with_hub=True),
        '          </ListConfiguration>',
        '        </Group>',
        '      </Complication>',
    ])


def ring_bounds(inner, outer):
    """Full-circle BoundingArc from inner to outer radius.

    A ComplicationSlot must be a direct child of Scene and takes no
    Transform, so a slot whose content orbits can only be bounded by the
    whole ring it travels. The bound also clips content.

    Measured on the Wear OS 6 emulator via dumpsys complicationSlotBounds:
    width/height are the OUTER diameter, with thickness growing inward, and
    endAngle="360" collapses the bounds to a wrong rect in the upper left
    that clips most content. 359.9 leaves a 0.3 px gap at the bezel.
    """
    return (
        f'      <BoundingArc centerX="{CX:.1f}" centerY="{CX:.1f}"'
        f' width="{2 * outer:.1f}" height="{2 * outer:.1f}"'
        f' thickness="{outer - inner:.1f}" startAngle="0" endAngle="359.9"'
        f' outlinePadding="2" />'
    )


def complication_slot():
    # One slot only: the editor hit-tests each slot's bounding RECT and the
    # last-declared containing rect wins, so a second orbiting slot at a
    # similar radius could never be selected for editing.
    return "\n".join([
        f'    <ComplicationSlot slotId="0"'
        f' supportedTypes="MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY"'
        f' x="0" y="0" width="{CANVAS}" height="{CANVAS}">',
        # Covers both positions, the base circle reaching the bezel, and the
        # inner edge at its ambient scale, where it sits closer to the center.
        ring_bounds(AMBIENT_SCALE * min(ICON_INNER, ICON_K - BASE_SIZE / 2) - 2,
                    CX),
        icon_complication("MONOCHROMATIC_IMAGE"),
        icon_complication("SMALL_IMAGE"),
        '    </ComplicationSlot>',
    ])


def unit(angle_deg):
    a = math.radians(angle_deg)
    return math.sin(a), -math.cos(a)


def polar(radius, angle_deg):
    ux, uy = unit(angle_deg)
    return DC + radius * ux, DC + radius * uy


def label24_expression(i):
    """Absolute hour (0-23) nearest the current time for tick i.

    Midnight reads 0, not 24, matching how a 24h clock is written and keeping
    this port in step with the Pebble one (per ericmigi, #4).

    floor() where the C code truncates toward zero; differs only at the exact
    6-hour tie point. n+24 is always positive, so % semantics don't matter.
    """
    n = f"({i} + 12 * floor(([HOUR_0_23_MINUTE] - {i}) / 12 + 0.5))"
    return f"(({n} + 24) % 24)"


def hour_tick(s, angle_deg, out, text_color):
    # Round caps extend half the stroke past the endpoint; pull the outer
    # endpoint in so every mark's outermost pixel lands exactly on DIAL_R.
    x1, y1 = polar(DIAL_R - s["hour_inset"], angle_deg)
    x2, y2 = polar(DIAL_R - s["hour_stroke"] / 2, angle_deg)
    out.append(
        f'        <Line startX="{x1:.1f}" startY="{y1:.1f}" endX="{x2:.1f}" endY="{y2:.1f}">\n'
        f'          <Stroke color="{text_color}" thickness="{s["hour_stroke"]:.1f}" cap="ROUND" />\n'
        f'        </Line>'
    )


def minor_marks(s, base_angle, out, minor_color):
    for j in range(1, 12):
        a = base_angle + 2.5 * j
        if j % 3 == 0:
            inset = s["hour_inset"] if j == 6 else s["hour_inset"] / 2
            x1, y1 = polar(DIAL_R - inset, a)
            x2, y2 = polar(DIAL_R - s["minor_stroke"] / 2, a)
            out.append(
                f'        <Line startX="{x1:.1f}" startY="{y1:.1f}" endX="{x2:.1f}" endY="{y2:.1f}">\n'
                f'          <Stroke color="{minor_color}" thickness="{s["minor_stroke"]:.1f}" cap="ROUND" />\n'
                f'        </Line>'
            )
        else:
            # Dots match the minor tick width and end at the same outer radius
            r = s["minor_stroke"] / 2
            px, py = polar(DIAL_R - r, a)
            out.append(
                f'        <Ellipse x="{px - r:.1f}" y="{py - r:.1f}" width="{2 * r:.1f}" height="{2 * r:.1f}">\n'
                f'          <Fill color="{minor_color}" />\n'
                f'        </Ellipse>'
            )


def numeral_center(s, i, two_digits):
    """Pebble radial-box placement: glyph box sits inward of the tick's inner
    end, keeping a gap of hour_inset/2 along the radial direction."""
    angle = i * 30.0
    ux, uy = unit(angle)
    half_w = s["half_w2"] if two_digits else s["half_w1"]
    half_h = s["half_h"]
    tx = half_w / abs(ux) if abs(ux) > 1e-6 else float("inf")
    ty = half_h / abs(uy) if abs(uy) > 1e-6 else float("inf")
    d_edge = min(tx, ty)
    gap = s["hour_inset"] / 2
    ix, iy = polar(DIAL_R - s["hour_inset"], angle)
    return ix - (gap + d_edge) * ux, iy - (gap + d_edge) * uy


def part_text(s, name, cx, cy, content, text_color):
    w = 2 * s["half_w2"] + 24
    h = s["font_size"] * 1.3
    # The runtime renders Font text content verbatim: leading whitespace or a
    # newline becomes an empty first line and the digits get clipped away, so
    # the Font element must stay on ONE line with no padding around content.
    return (
        f'          <PartText x="{cx - w / 2:.0f}" y="{cy - h / 2:.0f}" width="{w:.0f}" height="{h:.0f}" name="{name}">\n'
        f'            <Text align="CENTER">'
        f'<Font family="helvetica_digits" size="{s["font_size"]:.0f}" color="{text_color}">{content}</Font>'
        f'</Text>\n'
        f'          </PartText>'
    )


def numerals(s, out, tag, text_color):
    """12h numerals statically, 24h numerals via Template, switched on the
    hours setting."""
    h24 = []
    h12 = []
    for i in range(12):
        cx, cy = numeral_center(s, i, two_digits=True)
        expr = label24_expression(i)
        h24.append(part_text(s, f'num24_{tag}_{i}', cx, cy,
                             f'<Template>%d<Parameter expression="{expr}" /></Template>',
                             text_color))
        label = 12 if i == 0 else i
        cx, cy = numeral_center(s, i, two_digits=label >= 10)
        h12.append(part_text(s, f'num12_{tag}_{i}', cx, cy, str(label),
                             text_color))
    # A ListOption holds exactly one child, so each numeral set is grouped.
    out.append('        <ListConfiguration id="hours">')
    out.append('          <ListOption id="h24">')
    out.append(f'            <Group x="0" y="0" width="{DIAL_SIZE:.0f}"'
               f' height="{DIAL_SIZE:.0f}" name="num24_{tag}">')
    out.extend(h24)
    out.append('            </Group>')
    out.append('          </ListOption>')
    out.append('          <ListOption id="h12">')
    out.append(f'            <Group x="0" y="0" width="{DIAL_SIZE:.0f}"'
               f' height="{DIAL_SIZE:.0f}" name="num12_{tag}">')
    out.extend(h12)
    out.append('            </Group>')
    out.append('          </ListOption>')
    out.append('        </ListConfiguration>')


def dial_body(style_name, tag, text_color, minor_color, disc):
    """One dial: optional face disc, then marks and numerals in the colors of
    whatever they sit on."""
    s = STYLES[style_name]
    out = []
    out.append(f'        <Group x="0" y="0" width="{DIAL_SIZE:.0f}"'
               f' height="{DIAL_SIZE:.0f}" name="dial_{tag}">')
    out.append(f'          <PartDraw x="0" y="0" width="{DIAL_SIZE:.0f}"'
               f' height="{DIAL_SIZE:.0f}">')
    if disc:
        # First, so the marks land on top of it. Its radius clears the marker
        # ring by FACE_OVERSHOOT, exactly filling the widened group.
        out.append(f'            <Ellipse x="{DC - FACE_R:.1f}" y="{DC - FACE_R:.1f}"'
                   f' width="{2 * FACE_R:.1f}" height="{2 * FACE_R:.1f}">\n'
                   f'              <Fill color="{FACE_COLOR}" />\n'
                   f'            </Ellipse>')
    marks = []
    for i in range(12):
        hour_tick(s, i * 30.0, marks, text_color)
        minor_marks(s, i * 30.0, marks, minor_color)
    out.extend(marks)
    out.append('          </PartDraw>')
    numerals(s, out, tag, text_color)
    out.append('        </Group>')
    return out


def dial_variant(style_name, ambient=False):
    """The dial, positioned on the orbiting center.

    One alpha Variant on the position group carries the entire subtree in and
    out of ambient, so none of the ~170 parts below it needs one of its own.
    The ambient copy drops the face disc and is drawn in fixed light colors,
    because a Variant can animate alpha but cannot swap a color.
    """
    tag = f'{style_name}_amb' if ambient else style_name
    text = AMBIENT_TEXT if ambient else FACE_TEXT
    minor = AMBIENT_MINOR if ambient else FACE_MINOR
    base_alpha = 0 if ambient else 255
    value, timing = (("255", LIGHT_DIAL_FADE) if ambient
                     else ("0", COLOR_DIAL_FADE))
    out = []
    out.append(f'    <ListOption id="{style_name}">')
    out.append(f'      <Group x="0" y="0" width="{DIAL_SIZE:.0f}"'
               f' height="{DIAL_SIZE:.0f}" name="dialpos_{tag}"'
               f' alpha="{base_alpha}" pivotX="0.5" pivotY="0.5"'
               f' scaleX="1" scaleY="1">')
    out.append(f'        <Variant mode="AMBIENT" target="alpha"'
               f' value="{value}" {timing} />')
    out.append(f'        <Variant mode="AMBIENT" target="scaleX"'
               f' value="{AMBIENT_SCALE}" {CORE_SCALE} />')
    out.append(f'        <Variant mode="AMBIENT" target="scaleY"'
               f' value="{AMBIENT_SCALE}" {CORE_SCALE} />')
    out.append(f'        <Transform target="x" value="{GROUP_X}" />')
    out.append(f'        <Transform target="y" value="{GROUP_Y}" />')
    out.append(f'        <Transform target="pivotX" value="{PIVOT_X}" />')
    out.append(f'        <Transform target="pivotY" value="{PIVOT_Y}" />')
    out.extend(dial_body(style_name, tag, text, minor, disc=not ambient))
    out.append('      </Group>')
    out.append('    </ListOption>')
    return "\n".join(out)


def dial_layer(ambient=False):
    """Both dial styles under the setting; only the selected one is built."""
    return "\n".join([
        '    <ListConfiguration id="numerals">',
        dial_variant("large", ambient),
        dial_variant("classic", ambient),
        '    </ListConfiguration>',
    ])


def ambient_vignette():
    """Transparent until the last stop gap, then ramping to pure black.

    RadialGradient lives inside a Fill and takes ARGB, so the ramp is done
    with alpha rather than a second layer. The middle stops hold full
    transparency right up to the ramp, otherwise the fade would start at the
    center and dim the whole face.

    The Fill's own color must be OPAQUE. A transparent one (#00000000)
    suppresses the entire fill, gradient included -- it renders nothing at
    all, silently, and the validator accepts it. The transparency belongs in
    the gradient stops, not the Fill.
    """
    stops = 1 / (2 * VIGNETTE_WIDTH) + 1
    assert abs(stops - round(stops)) < 1e-9, (
        f"VIGNETTE_WIDTH {VIGNETTE_WIDTH} needs {stops} evenly spaced stops; "
        "pick a width of the form 1/(2*(n-1))")
    stops = round(stops)
    colors = " ".join(["#00000000"] * (stops - 1) + ["#FF000000"])
    positions = " ".join(f"{i / (stops - 1):.4f}" for i in range(stops))
    return "\n".join([
        f'    <PartDraw x="0" y="0" width="{CANVAS}" height="{CANVAS}" alpha="0">',
        f'      <Variant mode="AMBIENT" target="alpha" value="255" {LIGHT_DIAL_FADE} />',
        f'      <Ellipse x="0" y="0" width="{CANVAS}" height="{CANVAS}">',
        f'        <Fill color="#FF000000">',
        f'          <RadialGradient centerX="{CX:.1f}" centerY="{CX:.1f}"'
        f' radius="{CX:.1f}" colors="{colors}" positions="{positions}" />',
        '        </Fill>',
        '      </Ellipse>',
        '    </PartDraw>',
    ])


def ground():
    """Every colored surface behind the dial, in one part so a single Variant
    clears the lot for ambient.

    The Scene's own backgroundColor is not transformable, so it stays black
    and the face color is painted here instead. Left on the Scene it would
    keep lighting the crescent of screen the dial disc does not reach, all
    night. The background option is painted over it and defaults to fully
    transparent, which leaves the face color showing.
    """
    return "\n".join([
        f'    <PartDraw x="0" y="0" width="{CANVAS}" height="{CANVAS}" alpha="255">',
        f'      <Variant mode="AMBIENT" target="alpha" value="0" {GROUND_FADE} />',
        f'      <Rectangle x="0" y="0" width="{CANVAS}" height="{CANVAS}">',
        f'        <Fill color="{FACE_COLOR}" />',
        '      </Rectangle>',
        f'      <Rectangle x="0" y="0" width="{CANVAS}" height="{CANVAS}">',
        f'        <Fill color="{BG_COLOR}" />',
        '      </Rectangle>',
        '    </PartDraw>',
    ])


def watchface():
    hand_x1 = DC
    hand_y1 = DC
    hand_x2 = DC
    # Round cap extends half the stroke; pull the tip in so it ends on the
    # same outer radius as the ticks and dots
    hand_y2 = DC - (DIAL_R - HAND_STROKE / 2)
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!-- GENERATED by wear/wff/tools/generate_watchface.py - do not edit by hand. -->
<WatchFace width="{CANVAS}" height="{CANVAS}" clipShape="CIRCLE">
  <Metadata key="CLOCK_TYPE" value="ANALOG" />
  <Metadata key="PREVIEW_TIME" value="07:07:00" />
{user_configurations()}
  <Scene backgroundColor="#000000">
{ground()}
{dial_layer()}
{dial_layer(ambient=True)}
    <Group x="0" y="0" width="{DIAL_SIZE:.0f}" height="{DIAL_SIZE:.0f}" name="handscale" pivotX="0.5" pivotY="0.5" scaleX="1" scaleY="1">
      <Variant mode="AMBIENT" target="scaleX" value="{AMBIENT_SCALE}" {CORE_SCALE} />
      <Variant mode="AMBIENT" target="scaleY" value="{AMBIENT_SCALE}" {CORE_SCALE} />
      <Transform target="x" value="{GROUP_X}" />
      <Transform target="y" value="{GROUP_Y}" />
      <Transform target="pivotX" value="{PIVOT_X}" />
      <Transform target="pivotY" value="{PIVOT_Y}" />
      <Group x="0" y="0" width="{DIAL_SIZE:.0f}" height="{DIAL_SIZE:.0f}" name="hand" angle="0" pivotX="0.5" pivotY="0.5">
        <Transform target="angle" value="{ANGLE}" />
        <PartDraw x="0" y="0" width="{DIAL_SIZE:.0f}" height="{DIAL_SIZE:.0f}">
          <Line startX="{hand_x1:.1f}" startY="{hand_y1:.1f}" endX="{hand_x2:.1f}" endY="{hand_y2:.1f}">
            <Stroke color="{HAND_COLOR}" thickness="{HAND_STROKE:.1f}" cap="ROUND" />
          </Line>
        </PartDraw>
      </Group>
    </Group>
{complication_slot()}
{ambient_vignette()}
  </Scene>
</WatchFace>
'''


if __name__ == "__main__":
    res = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "src", "main", "res"))
    out_path = os.path.join(res, "raw", "watchface.xml")
    with open(out_path, "w") as f:
        f.write(watchface())
    print(f"wrote {out_path}")
    strings_path = os.path.join(res, "values", "config_strings.xml")
    with open(strings_path, "w") as f:
        f.write(config_strings())
    print(f"wrote {strings_path}")
