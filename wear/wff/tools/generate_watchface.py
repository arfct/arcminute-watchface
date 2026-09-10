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
# Dimmer than the interactive minor marks (0xAA). These are the marks that can
# afford to recede at night, and fewer lit subpixels is the point.
AMBIENT_MINOR = "#66FFFFFF"

# ---- Ambient transitions (Watch Face Format 4) ----
# duration and startOffset are fractions of the window the system allows for a
# mode change, and the runtime discards BOTH if they sum past 1.0. Each
# Variant carries one curve that serves both directions, so this cascade runs
# forward on wake and in reverse going idle:
#
#   the whole face draws back 10%, and under that:
#   ground drains -> dials cross -> complication returns
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
COMPLICATION_FADE = 'startOffset="0.5" duration="0.5" interpolation="EASE_OUT"'
# The core move: the whole composition draws back 10% when the screen idles.
# It runs the full window under everything else, so the fades read as detail
# on top of one gesture rather than as separate events.
#
# The hand deliberately has no Variant of its own. It keeps full color and
# full length in ambient -- an earlier version scaled it about its own group
# pivot, which is the dial center, so it retracted from the rim and left a
# gap. Scaling the composition instead moves the hand with the dial, so the
# tip stays on the marks.
CORE_SCALE = 'startOffset="0" duration="0.75" interpolation="EASE_OUT"'
AMBIENT_SCALE = 0.9
# Screen center expressed as a fraction of the dial group's own box, so the
# group scales about the middle of the screen rather than the dial's center
# (which sits ~513px off-screen, and would swing the rim away instead of
# shrinking it). pivotX/pivotY are transformable, so this tracks the hour.
PIVOT_X = f"(({DC:.1f} + {DIST:.1f} * sin(rad({ANGLE}))) / {DIAL_SIZE:.1f})"
PIVOT_Y = f"(({DC:.1f} - {DIST:.1f} * cos(rad({ANGLE}))) / {DIAL_SIZE:.1f})"
# Complications ride the band just outside the rim, which the face disc
# overshoots, so they follow the face too.
TEXT_COLOR = FACE_TEXT
MINOR_COLOR = FACE_MINOR

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


def user_configurations():
    out = []
    out.append('  <UserConfigurations>')
    out.append('    <ColorConfiguration id="backColor" displayName="back_label"'
               ' screenReaderText="back_label" defaultValue="match">')
    for cid, _, bg in BACK_PALETTE:
        out.append(f'      <ColorOption id="{cid}" displayName="back_{cid}_label"'
                   f' colors="{bg}" />')
    out.append('    </ColorConfiguration>')
    out.append('    <ColorConfiguration id="faceColor" displayName="face_label"'
               ' screenReaderText="face_label" defaultValue="black">')
    for cid, _, fill in FACE_PALETTE:
        text, minor = theme_colors(fill)
        out.append(f'      <ColorOption id="{cid}" displayName="face_{cid}_label"'
                   f' colors="{fill} {text} {minor}" />')
    out.append('    </ColorConfiguration>')
    out.append('    <ColorConfiguration id="handColor" displayName="hand_label"'
               ' screenReaderText="hand_label" defaultValue="red">')
    for cid, _, hex_color in HAND_PALETTE:
        out.append(f'      <ColorOption id="{cid}" displayName="hand_{cid}_label"'
                   f' colors="{hex_color}" />')
    out.append('    </ColorConfiguration>')
    # Toggles last: the editor lists configurations in declaration order, and
    # appends its own complications page after them.
    out.append('    <BooleanConfiguration id="largeNumerals"'
               ' displayName="large_numerals_label"'
               ' screenReaderText="large_numerals_label" defaultValue="TRUE" />')
    out.append('    <BooleanConfiguration id="hour24" displayName="hour24_label"'
               ' screenReaderText="hour24_label" defaultValue="FALSE" />')
    out.append('  </UserConfigurations>')
    return "\n".join(out)


def config_strings():
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<!-- GENERATED by tools/generate_watchface.py - do not edit by hand. -->',
             '<resources>',
             '    <string name="back_label">Background</string>',
             '    <string name="face_label">Dial face</string>',
             '    <string name="hand_label">Hand</string>',
             '    <string name="large_numerals_label">Large numerals</string>',
             '    <string name="hour24_label">24-hour time</string>']
    lines.append('    <string name="back_match_label">Back: Match face</string>')
    for prefix, word in PREFIXES.items():
        for cid, label, _ in BLACK_WHITE + TAILWIND:
            lines.append(f'    <string name="{prefix}_{cid}_label">'
                         f'{word}: {label}</string>')
    lines.append('</resources>')
    return "\n".join(lines) + "\n"


# ---- Event complication slot (experimental; no companion provider yet) ----
# RANGED_VALUE min/max are read as minutes-of-day; on the 12-hour dial one
# minute is half a degree. The arc sits in the free band between the tick
# ring (which ends exactly at DIAL_R) and the screen edge.
ARC_STROKE = 6 * SCALE                              # matches large hour ticks
EVENT_GAP = 5 * SCALE                               # one tick-gap of separation
ARC_R = DIAL_R + EVENT_GAP + ARC_STROKE / 2         # arc centerline
EVENT_FONT = 15 * SCALE
# TextCircular draws glyphs inset from its circle; measured on the Wear OS 5
# emulator the glyph bottoms sit ~12 gabbro px inside the circle radius.
GLYPH_DROP = 12 * SCALE
# SHORT_TEXT has no arc: baseline one tick-gap off the tick ring.
TEXT_R_ST = DIAL_R + EVENT_GAP + GLYPH_DROP
# RANGED_VALUE text clears its arc by the same gap.
TEXT_R_RV = ARC_R + ARC_STROKE / 2 + EVENT_GAP + GLYPH_DROP
# When the hour angle points into the lower half (3..9 o'clock) the visible
# rim is the BOTTOM of the giant dial circle, so tangent-following text
# renders upside down unless the direction is flipped.
FLIP = "([HOUR_0_11_MINUTE] &gt;= 3) &amp;&amp; ([HOUR_0_11_MINUTE] &lt; 9)"
# Image complications sit upright at the same rim spot the short text uses:
# centered on the current hour direction, one tick-gap outside the ring.
IMG_SIZE = 20 * SCALE
IMG_K = DIAL_R + EVENT_GAP + IMG_SIZE / 2 - DIST    # rim offset from screen center
# RANGED_VALUE renders as a gauge riding with the hand: a quiet track
# centered on the current hour, filled proportionally. Generic system
# providers (battery %, weather temperature between today's low/high) all
# read naturally this way; a calendar companion will need its own contract.
#
# The track must not run edge-to-edge: cap the span so its endpoints (round
# caps included) stay a margin inside the screen circle at every hour. For a
# point at dial angle phi off the hour direction, the distance from screen
# center is sqrt(DIST^2 + ARC_R^2 - 2*DIST*ARC_R*cos(phi)); solve for phi at
# the allowed maximum.
GAUGE_EDGE_INSET = 5 * SCALE
_reach = CX - GAUGE_EDGE_INSET - ARC_STROKE / 2
_EDGE_LIMIT = math.degrees(math.acos(
    (DIST ** 2 + ARC_R ** 2 - _reach ** 2) / (2 * DIST * ARC_R)))
# A third of the edge-limited span reads as a meter, not a band.
GAUGE_HALF = _EDGE_LIMIT / 3
RV_FRAC = ("([COMPLICATION.RANGED_VALUE_MAX] == [COMPLICATION.RANGED_VALUE_MIN]"
           " ? 0 : clamp(([COMPLICATION.RANGED_VALUE_VALUE] -"
           " [COMPLICATION.RANGED_VALUE_MIN]) / ([COMPLICATION.RANGED_VALUE_MAX]"
           " - [COMPLICATION.RANGED_VALUE_MIN]), 0, 1))")
GAUGE_START = f"({ANGLE} - {GAUGE_HALF:.2f})"
GAUGE_FILL_END = f"({GAUGE_START} + {2 * GAUGE_HALF:.2f} * {RV_FRAC})"
GAUGE_TRACK_END = f"({ANGLE} + {GAUGE_HALF:.2f})"


def event_text_variant(direction, mid_expr, text_r):
    """Curved [COMPLICATION.TEXT] centered on mid_expr along the dial rim.

    COUNTER_CLOCKWISE traverses its angles the other way, so start/end swap
    to keep the same visual span.
    """
    sign = 1 if direction == "CLOCKWISE" else -1
    start = f"({mid_expr} - {40 * sign})"
    end = f"({mid_expr} + {40 * sign})"
    d = 2 * text_r
    # Providers are inconsistent about which of TITLE/TEXT carries the label
    # (Date: TITLE="Fri" TEXT="21"; Battery: TEXT only; agenda-style sources
    # often TITLE only), so render both. Extra whitespace collapses visually.
    return (
        f'        <PartText x="0" y="0" width="{CANVAS}" height="{CANVAS}">\n'
        f'          <TextCircular centerX="0" centerY="0" width="{d:.1f}" height="{d:.1f}"'
        f' startAngle="{-40 * sign}" endAngle="{40 * sign}" direction="{direction}" align="CENTER" ellipsis="TRUE">\n'
        f'            <Transform target="centerX" value="{DIAL_CX}" />\n'
        f'            <Transform target="centerY" value="{DIAL_CY}" />\n'
        f'            <Transform target="startAngle" value="{start}" />\n'
        f'            <Transform target="endAngle" value="{end}" />\n'
        f'            <Font family="SYNC_TO_DEVICE" size="{EVENT_FONT:.0f}" color="{TEXT_COLOR}">'
        f'<Template>%s %s<Parameter expression="[COMPLICATION.TITLE]" />'
        f'<Parameter expression="[COMPLICATION.TEXT]" /></Template></Font>\n'
        f'          </TextCircular>\n'
        f'        </PartText>'
    )


def event_text(flip_name, mid_expr, text_r):
    return "\n".join([
        '        <Condition>',
        '          <Expressions>',
        f'            <Expression name="{flip_name}">{FLIP}</Expression>',
        '          </Expressions>',
        f'          <Compare expression="{flip_name}">',
        event_text_variant("COUNTER_CLOCKWISE", mid_expr, text_r),
        '          </Compare>',
        '          <Default>',
        event_text_variant("CLOCKWISE", mid_expr, text_r),
        '          </Default>',
        '        </Condition>',
    ])


def gauge_arc(end_expr, color):
    d = 2 * ARC_R
    return (
        f'          <Arc centerX="0" centerY="0" width="{d:.1f}" height="{d:.1f}"'
        f' startAngle="{-GAUGE_HALF:.2f}" endAngle="{GAUGE_HALF:.2f}">\n'
        f'            <Transform target="centerX" value="{DIAL_CX}" />\n'
        f'            <Transform target="centerY" value="{DIAL_CY}" />\n'
        f'            <Transform target="startAngle" value="{GAUGE_START}" />\n'
        f'            <Transform target="endAngle" value="{end_expr}" />\n'
        f'            <Stroke color="{color}" thickness="{ARC_STROKE:.1f}" cap="ROUND" />\n'
        f'          </Arc>'
    )


def event_gauge():
    return "\n".join([
        f'        <PartDraw x="0" y="0" width="{CANVAS}" height="{CANVAS}">',
        gauge_arc(GAUGE_TRACK_END, MINOR_COLOR),
        gauge_arc(GAUGE_FILL_END, HAND_COLOR),
        '        </PartDraw>',
    ])


def event_image(resource, tint):
    """Icon centered on the current hour direction, one tick-gap off the
    ring. Icons stay upright, so no direction flip is needed."""
    half = IMG_SIZE / 2
    x = f"({CX:.1f} + {IMG_K:.1f} * sin(rad({ANGLE})) - {half:.1f})"
    y = f"({CX:.1f} - {IMG_K:.1f} * cos(rad({ANGLE})) - {half:.1f})"
    tint_attr = f' tintColor="{tint}"' if tint else ""
    return (
        f'        <PartImage x="{CX - half:.0f}" y="{CX - IMG_K - half:.0f}"'
        f' width="{IMG_SIZE:.0f}" height="{IMG_SIZE:.0f}"{tint_attr}>\n'
        f'          <Transform target="x" value="{x}" />\n'
        f'          <Transform target="y" value="{y}" />\n'
        f'          <Image resource="{resource}" />\n'
        f'        </PartImage>'
    )


def complication_slot():
    # Content orbits the screen center: a point at radius R from the dial
    # center lands at R - DIST from the screen center, along the hour
    # direction. So every complication shape lives in one ring, and a
    # BoundingArc over that ring gives the editor a tap outline that actually
    # marks the spot (a full-screen oval outlined nothing useful). The ring
    # also clips content, so it is padded past the extremes:
    #   gauge      ARC_R +/- stroke/2  -> 133..144
    #   short text TEXT_R_ST, glyphs inward by the font size -> 128..154
    #   gauge text TEXT_R_RV, same     -> 147..173
    #   icon       IMG_K +/- IMG_SIZE/2 -> 133..168
    inner = min(ARC_R - ARC_STROKE / 2, TEXT_R_ST - EVENT_FONT) - DIST - 8
    outer = max(TEXT_R_RV, ARC_R + ARC_STROKE / 2,
                DIST + IMG_K + IMG_SIZE / 2) - DIST + 8
    mid = (inner + outer) / 2
    return "\n".join([
        f'    <ComplicationSlot slotId="0"'
        f' supportedTypes="RANGED_VALUE SHORT_TEXT MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY"'
        f' x="0" y="0" width="{CANVAS}" height="{CANVAS}">',
        f'      <BoundingArc centerX="{CX:.1f}" centerY="{CX:.1f}"'
        f' width="{2 * mid:.1f}" height="{2 * mid:.1f}"'
        f' thickness="{outer - inner:.1f}" startAngle="0" endAngle="360"'
        f' outlinePadding="2" />',
        '      <Complication type="RANGED_VALUE">',
        event_gauge(),
        event_text("evflip_rv", ANGLE, TEXT_R_RV),
        '      </Complication>',
        '      <Complication type="SHORT_TEXT">',
        event_text("evflip_st", ANGLE, TEXT_R_ST),
        '      </Complication>',
        '      <Complication type="MONOCHROMATIC_IMAGE">',
        event_image("[COMPLICATION.MONOCHROMATIC_IMAGE]", TEXT_COLOR),
        '      </Complication>',
        '      <Complication type="SMALL_IMAGE">',
        event_image("[COMPLICATION.SMALL_IMAGE]", None),
        '      </Complication>',
        # Complication content is drawn in face colors, which are chosen for
        # contrast against the disc -- against the ambient black a light face
        # would render it invisible anyway. Dropping it in ambient costs
        # nothing readable and saves the lit pixels. Variant goes last: the
        # element's optional children follow its required Bounding and
        # Complication ones.
        f'      <Variant mode="AMBIENT" target="alpha" value="0"'
        f' {COMPLICATION_FADE} />',
        '    </ComplicationSlot>',
    ])


def unit(angle_deg):
    a = math.radians(angle_deg)
    return math.sin(a), -math.cos(a)


def polar(radius, angle_deg):
    ux, uy = unit(angle_deg)
    return DC + radius * ux, DC + radius * uy


def label24_expression(i):
    """Absolute hour (1-24) nearest the current time for tick i.

    floor() where the C code truncates toward zero; differs only at the exact
    6-hour tie point. n+24 is always positive, so % semantics don't matter.
    """
    n = f"({i} + 12 * floor(([HOUR_0_23_MINUTE] - {i}) / 12 + 0.5))"
    w = f"(({n} + 24) % 24)"
    return f"{w} == 0 ? 24 : {w}"


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
    hour24 toggle."""
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
    # A BooleanOption holds exactly one child, so each numeral set is grouped.
    out.append('        <BooleanConfiguration id="hour24">')
    out.append('          <BooleanOption id="TRUE">')
    out.append(f'            <Group x="0" y="0" width="{DIAL_SIZE:.0f}"'
               f' height="{DIAL_SIZE:.0f}" name="num24_{tag}">')
    out.extend(h24)
    out.append('            </Group>')
    out.append('          </BooleanOption>')
    out.append('          <BooleanOption id="FALSE">')
    out.append(f'            <Group x="0" y="0" width="{DIAL_SIZE:.0f}"'
               f' height="{DIAL_SIZE:.0f}" name="num12_{tag}">')
    out.extend(h12)
    out.append('            </Group>')
    out.append('          </BooleanOption>')
    out.append('        </BooleanConfiguration>')


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


def dial_variant(style_name, option_id, ambient=False):
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
    out.append(f'    <BooleanOption id="{option_id}">')
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
    out.append('    </BooleanOption>')
    return "\n".join(out)


def dial_layer(ambient=False):
    """Both dial styles under the toggle; only the selected one is built."""
    return "\n".join([
        '    <BooleanConfiguration id="largeNumerals">',
        dial_variant("large", "TRUE", ambient),
        dial_variant("classic", "FALSE", ambient),
        '    </BooleanConfiguration>',
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
{complication_slot()}
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
