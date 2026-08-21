#!/usr/bin/env python3
"""Generates res/raw/watchface.xml for the Chronology Watch Face Format port.

The geometry is the same orbiting-dial design as pebble/src/c/chronology.c and
wear/app's ChronologyRenderer.kt: a dial three screen-sizes wide whose center
sits opposite the current hour angle, so the rim (numerals + ticks) sweeps
through the visible screen, plus a hand from the dial center to the
current-hour rim point.

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
DIAL_SIZE = 3 * CANVAS          # 1350
DC = DIAL_SIZE / 2              # dial local center 675

HAND_STROKE = 7 * SCALE         # 12.1 (Pebble uses 9; thinned per user preference)

# Hour angle in degrees, updated each minute
ANGLE = "(30 * [HOUR_0_11_MINUTE])"
# Dial group top-left corner so the dial center lands at C - DIST*u(angle)
GROUP_X = f"({CX - DC:.1f} - {DIST:.1f} * sin(rad({ANGLE})))"
GROUP_Y = f"({CX - DC:.1f} + {DIST:.1f} * cos(rad({ANGLE})))"

STYLES = {
    "large": dict(
        font_size=95 * SCALE,        # 164.4
        hour_inset=27.7 * SCALE,     # 47.9
        hour_stroke=6 * SCALE,       # 10.4
        minor_stroke=4 * SCALE,      # 6.9
        dot_r=3 * SCALE,             # 5.2
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
        minor_stroke=2 * SCALE,      # 3.5
        dot_r=2 * SCALE,             # 3.5
        half_h=0.36 * 42 * SCALE,
        half_w1=0.278 * 42 * SCALE,
        half_w2=0.556 * 42 * SCALE,
    ),
}

TEXT_COLOR = "[CONFIGURATION.themeColor.1]"
MINOR_COLOR = "[CONFIGURATION.themeColor.2]"
BG_COLOR = "[CONFIGURATION.themeColor.0]"
HAND_COLOR = "[CONFIGURATION.handColor.0]"


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


def hour_tick(s, angle_deg, out):
    x1, y1 = polar(DIAL_R - s["hour_inset"], angle_deg)
    x2, y2 = polar(DIAL_R, angle_deg)
    out.append(
        f'        <Line startX="{x1:.1f}" startY="{y1:.1f}" endX="{x2:.1f}" endY="{y2:.1f}">\n'
        f'          <Stroke color="{TEXT_COLOR}" thickness="{s["hour_stroke"]:.1f}" cap="ROUND" />\n'
        f'        </Line>'
    )


def minor_marks(s, base_angle, out):
    for j in range(1, 12):
        a = base_angle + 2.5 * j
        if j % 3 == 0:
            inset = s["hour_inset"] if j == 6 else s["hour_inset"] / 2
            x1, y1 = polar(DIAL_R - inset, a)
            x2, y2 = polar(DIAL_R, a)
            out.append(
                f'        <Line startX="{x1:.1f}" startY="{y1:.1f}" endX="{x2:.1f}" endY="{y2:.1f}">\n'
                f'          <Stroke color="{MINOR_COLOR}" thickness="{s["minor_stroke"]:.1f}" cap="ROUND" />\n'
                f'        </Line>'
            )
        else:
            px, py = polar(DIAL_R, a)
            r = s["dot_r"]
            out.append(
                f'        <Ellipse x="{px - r:.1f}" y="{py - r:.1f}" width="{2 * r:.1f}" height="{2 * r:.1f}">\n'
                f'          <Fill color="{MINOR_COLOR}" />\n'
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


def part_text(s, name, cx, cy, content):
    w = 2 * s["half_w2"] + 24
    h = s["font_size"] * 1.3
    # The runtime renders Font text content verbatim: leading whitespace or a
    # newline becomes an empty first line and the digits get clipped away, so
    # the Font element must stay on ONE line with no padding around content.
    return (
        f'          <PartText x="{cx - w / 2:.0f}" y="{cy - h / 2:.0f}" width="{w:.0f}" height="{h:.0f}" name="{name}">\n'
        f'            <Text align="CENTER">'
        f'<Font family="helvetica_digits" size="{s["font_size"]:.0f}" color="{TEXT_COLOR}">{content}</Font>'
        f'</Text>\n'
        f'          </PartText>'
    )


def numerals(s, out, tag):
    """12h numerals statically, 24h numerals via Template, switched on
    [IS_24_HOUR_MODE]."""
    h24 = []
    h12 = []
    for i in range(12):
        cx, cy = numeral_center(s, i, two_digits=True)
        expr = label24_expression(i)
        h24.append(part_text(s, f'num24_{tag}_{i}', cx, cy,
                             f'<Template>%d<Parameter expression="{expr}" /></Template>'))
        label = 12 if i == 0 else i
        cx, cy = numeral_center(s, i, two_digits=label >= 10)
        h12.append(part_text(s, f'num12_{tag}_{i}', cx, cy, str(label)))
    out.append('        <Condition>')
    out.append('          <Expressions>')
    out.append(f'            <Expression name="h24_{tag}">[IS_24_HOUR_MODE]</Expression>')
    out.append('          </Expressions>')
    out.append(f'          <Compare expression="h24_{tag}">')
    out.extend(h24)
    out.append('          </Compare>')
    out.append('          <Default>')
    out.extend(h12)
    out.append('          </Default>')
    out.append('        </Condition>')


def dial_variant(style_name):
    s = STYLES[style_name]
    out = []
    out.append(f'    <ListOption id="{style_name}">')
    out.append(f'      <Group x="0" y="0" width="{DIAL_SIZE:.0f}" height="{DIAL_SIZE:.0f}" name="dial_{style_name}">')
    out.append(f'        <Transform target="x" value="{GROUP_X}" />')
    out.append(f'        <Transform target="y" value="{GROUP_Y}" />')
    out.append(f'        <PartDraw x="0" y="0" width="{DIAL_SIZE:.0f}" height="{DIAL_SIZE:.0f}">')
    marks = []
    for i in range(12):
        hour_tick(s, i * 30.0, marks)
        minor_marks(s, i * 30.0, marks)
    out.extend(marks)
    out.append('        </PartDraw>')
    numerals(s, out, style_name)
    out.append('      </Group>')
    out.append('    </ListOption>')
    return "\n".join(out)


def watchface():
    hand_x1 = DC
    hand_y1 = DC
    hand_x2 = DC
    hand_y2 = DC - DIAL_R
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!-- GENERATED by wear/wff/tools/generate_watchface.py - do not edit by hand. -->
<WatchFace width="{CANVAS}" height="{CANVAS}" clipShape="CIRCLE">
  <Metadata key="CLOCK_TYPE" value="ANALOG" />
  <Metadata key="PREVIEW_TIME" value="07:07:00" />
  <UserConfigurations>
    <ListConfiguration id="dialStyle" displayName="Dial style" defaultValue="large">
      <ListOption id="large" displayName="Large numerals" />
      <ListOption id="classic" displayName="Classic" />
    </ListConfiguration>
    <ColorConfiguration id="themeColor" displayName="Background" defaultValue="black">
      <ColorOption id="black" displayName="Black" colors="#000000 #FFFFFF #AAAAAA" />
      <ColorOption id="white" displayName="White" colors="#FFFFFF #000000 #555555" />
      <ColorOption id="blue" displayName="Blue" colors="#0000FF #FFFFFF #AAAAAA" />
      <ColorOption id="green" displayName="Green" colors="#00AA00 #FFFFFF #AAAAAA" />
    </ColorConfiguration>
    <ColorConfiguration id="handColor" displayName="Hand color" defaultValue="red">
      <ColorOption id="red" displayName="Red" colors="#FF0000" />
      <ColorOption id="white" displayName="White" colors="#FFFFFF" />
      <ColorOption id="black" displayName="Black" colors="#000000" />
      <ColorOption id="yellow" displayName="Yellow" colors="#FFFF00" />
      <ColorOption id="blue" displayName="Blue" colors="#0000FF" />
    </ColorConfiguration>
  </UserConfigurations>
  <Scene backgroundColor="{BG_COLOR}">
    <ListConfiguration id="dialStyle">
{dial_variant("large")}
{dial_variant("classic")}
    </ListConfiguration>
    <Group x="0" y="0" width="{DIAL_SIZE:.0f}" height="{DIAL_SIZE:.0f}" name="hand" angle="0" pivotX="0.5" pivotY="0.5">
      <Transform target="x" value="{GROUP_X}" />
      <Transform target="y" value="{GROUP_Y}" />
      <Transform target="angle" value="{ANGLE}" />
      <PartDraw x="0" y="0" width="{DIAL_SIZE:.0f}" height="{DIAL_SIZE:.0f}">
        <Line startX="{hand_x1:.1f}" startY="{hand_y1:.1f}" endX="{hand_x2:.1f}" endY="{hand_y2:.1f}">
          <Stroke color="{HAND_COLOR}" thickness="{HAND_STROKE:.1f}" cap="ROUND" />
        </Line>
      </PartDraw>
    </Group>
  </Scene>
</WatchFace>
'''


if __name__ == "__main__":
    out_path = os.path.join(os.path.dirname(__file__), "..", "src", "main", "res", "raw", "watchface.xml")
    with open(os.path.normpath(out_path), "w") as f:
        f.write(watchface())
    print(f"wrote {os.path.normpath(out_path)}")
