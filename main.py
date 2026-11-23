#!/usr/bin/env python3
"""Draw one 1024x1024 newspaper front page: the world's news of Monday 23 November 2026.

Fifty sourced stories in one image: a giant date masthead, a BY THE NUMBERS strip,
a six-slot UTC timeline, four big illustrated headlines (each with a WHY IT MATTERS
line and a UTC clock), twelve secondary stories, a 34-line ALSO ON list with a region
tag on every line, a schematic world map with numbered pins, a DATE CHECK strip
naming the near-miss stories we left out, and a footer with the source statement.

Every story is drawn from the STORIES data below, researched on 23 November 2026
from live news pages (One Turn day page, Al Jazeera, Reuters, CNN, Arab News, WION,
SCMP, Dawn, Economic Times). CLAIM marks one side's account, REPORTED a single-source
report, CONFIRMED the rest. Flat vector-style drawings only: no photographs of real
people anywhere in the image.

Run: python3 main.py  ->  writes entry.png (to $MAKEFUN_OUTPUT_DIR, or /output,
or the current directory). Deterministic: same bytes on every run.
"""
import hashlib
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (248, 243, 230)
INK = (25, 25, 25)
MUTED = (90, 86, 72)
RULE = (178, 39, 30)
FAINT = (214, 206, 188)
MAP_FILL = (216, 222, 230)
MAP_LINE = (154, 165, 177)
REGION_COLORS = {
    "EUROPE": (35, 64, 107),
    "MIDEAST": (178, 39, 30),
    "ASIA": (15, 107, 92),
    "AMERICAS": (122, 74, 18),
    "AFRICA": (107, 78, 158),
    "OCEANIA": (46, 125, 138),
    "GLOBAL": (85, 85, 85),
}
FIELD_ICONS = ("ship", "flame", "ballot", "shield", "chip", "scale", "cross",
               "star", "bolt", "bars", "globe", "arrow")

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    except OSError:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            return ImageFont.load_default()


def wrap(draw, text, fnt, width):
    """Greedy word wrap; returns a list of lines that fit `width` pixels."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            if draw.textlength(word, font=fnt) <= width:
                cur = word
            else:  # one very long word: split it by characters
                part = ""
                for ch in word:
                    if draw.textlength(part + ch, font=fnt) <= width:
                        part += ch
                    else:
                        lines.append(part)
                        part = ch
                cur = part
    if cur:
        lines.append(cur)
    return lines


def fit_lines(draw, text, fnt, width, max_lines):
    """Wrap text, shrinking the font until it fits in max_lines; returns (lines, font)."""
    size = fnt.size
    while size > 7:
        lines = wrap(draw, text, fnt, width)
        if len(lines) <= max_lines:
            return lines, fnt
        size -= 1
        fnt = font(size, bold=(fnt is not None and "Bold" in getattr(fnt, "path", "")))
    return wrap(draw, text, fnt, width), fnt


def truncate(draw, text, fnt, width):
    """Shorten text to fit `width`, cutting at a word boundary where possible."""
    if draw.textlength(text, font=fnt) <= width:
        return text
    cut = text
    while cut and draw.textlength(cut + "\u2026", font=fnt) > width:
        cut = cut[:-1]
    space = cut.rfind(" ")
    if space > len(cut) // 2:
        cut = cut[:space]
    return cut + "\u2026"


# ---------------------------------------------------------------- stories
HEADLINES = [
    dict(n=1, region="CLIMATE \u00b7 TURKEY", utc="SUN NIGHT",
         title="COP31 collapses with no deal",
         body="EU and ~130 nations reject a text with no fossil-fuel language; the longest COP ever.",
         why="Why it matters: the first COP collapse in 17 years.",
         tag="CONFIRMED", source="CNN", icon="globe"),
    dict(n=2, region="CONFLICT \u00b7 LIBYA", utc="MONDAY",
         title="Ukraine sinks Russian corvette off Libya",
         body="Seven sea drones hit the Merkury as it took on fuel at Benghazi; a second ship was hit and ten people hurt.",
         why="Why it matters: the Black Sea war reaches the Med.",
         tag="CONFIRMED", source="BBC", icon="ship"),
    dict(n=3, region="EUROPE \u00b7 UKRAINE", utc="OVERNIGHT",
         title="Russian strike kills 15 near Kyiv",
         body="A five-storey block collapses in Dymer; 11 dead, a boy of 7 pulled alive; a supermarket strike kills 3 more.",
         why="Why it matters: nightly barrages grind into a fifth winter.",
         tag="CONFIRMED", source="REUTERS", icon="flame"),
    dict(n=4, region="ECONOMY \u00b7 GLOBAL", utc="MONDAY",
         title="AI rout sinks world markets",
         body="Nikkei \u22125.06%, S&P 500 \u22123.7% as AI valuations wobble; gold jumps 3.14% as investors flee.",
         why="Why it matters: the year's sharpest tech sell-off.",
         tag="CONFIRMED", source="ONE TURN", icon="bars"),
]

SECONDARIES = [
    dict(n=5, region="MIDEAST", title="Iran vows \u2018all means\u2019 against US blockade",
         body="Tehran says Hormuz can reopen within hours.",
         tag="CONFIRMED", source="ARAB NEWS", icon="shield"),
    dict(n=6, region="AMERICAS", title="Trump: blockade-runners \u2018at the bottom of the sea\u2019",
         body="He may resume Iran strikes after New Year without a deal.",
         tag="REPORTED", source="FOX NEWS", icon="ship"),
    dict(n=7, region="AMERICAS", title="Democrats take biggest House majority since 1992",
         body="At least 258 seats after a North Carolina recount win.",
         tag="CONFIRMED", source="ONE TURN", icon="ballot"),
    dict(n=8, region="EUROPE", title="Zelenskyy urges NATO to bolster air defence",
         body="Kyiv asks the US to release Patriot interceptors.",
         tag="CONFIRMED", source="AL JAZEERA", icon="shield"),
    dict(n=9, region="AMERICAS", title="Nvidia probed as Huang quits as CEO",
         body="US probes chip sales to China; Bessent seeks answers.",
         tag="REPORTED", source="SCMP", icon="chip"),
    dict(n=10, region="MIDEAST", title="Houthis claim Saudi refinery hit",
         body="Saudi strike hits Hodeida in reply.",
         tag="CLAIM", source="ONE TURN", icon="flame"),
    dict(n=11, region="AMERICAS", title="FBI most-wanted \u2018El Chapo Isidro\u2019 captured",
         body="Mexican forces seize the cartel fugitive in Sinaloa.",
         tag="CONFIRMED", source="ONE TURN", icon="scale"),
    dict(n=12, region="AFRICA", title="Paramilitary attack kills 24 in South Sudan",
         body="SPLA-IO forces blamed for the civilian deaths.",
         tag="CONFIRMED", source="ARAB NEWS", icon="flame"),
    dict(n=13, region="AFRICA", title="Drone strikes kill five children in Khartoum",
         body="Homes and a UN building hit in Khartoum and Omdurman.",
         tag="REPORTED", source="ONE TURN", icon="flame"),
    dict(n=14, region="ASIA", title="Nepal PM Balen Shah meets Modi in Delhi",
         body="India pledges aid on the two-day visit.",
         tag="CONFIRMED", source="WION", icon="globe"),
    dict(n=15, region="EUROPE", title="Belgian airports shut in austerity strike",
         body="Flights grounded as workers walk out.",
         tag="CONFIRMED", source="ONE TURN", icon="bolt"),
    dict(n=16, region="ASIA", title="Banten factory-fire toll rises to 24",
         body="More remains found; dozens still missing.",
         tag="CONFIRMED", source="ARAB NEWS", icon="flame"),
]

ALSO_ON = [
    (17, "Eisenkot condemns settler arson in West Bank villages", "MIDEAST", "OT"),
    (18, "Netanyahu\u2013Eisenkot coalition talks end with no deal", "MIDEAST", "OT"),
    (19, "Gaza war left widespread contamination, experts say", "MIDEAST", "OT"),
    (20, "Five EU states accept Rwanda deportation centres", "EUROPE", "OT"),
    (21, "Kremlin warns of Baltic escalation after cargo-ship hit", "EUROPE", "WION"),
    (22, "Sparta II freighter towed to Russian waters", "EUROPE", "DAWN"),
    (23, "NATO fears Russia may launch nuclear-armed satellite", "EUROPE", "ET"),
    (24, "Bomb threats emailed to 450 schools in German state", "EUROPE", "WION"),
    (25, "Sanchez vows tax on \u20ac100m+ fortunes before snap vote", "EUROPE", "WION"),
    (26, "Burnham: EU deal could make next decade \u2018much better\u2019", "EUROPE", "OT"),
    (27, "Denmark plans school phone ban from 2027", "EUROPE", "REUTERS"),
    (28, "UK digs new reservoirs to fight persistent drought", "EUROPE", "ARAB NEWS"),
    (29, "Lead found in fish near Saipan lagoon", "OCEANIA", "OT"),
    (30, "ConocoPhillips exits Norway in $4.4bn deal", "EUROPE", "OT"),
    (31, "US intel chief backs Trump calling Putin \u2018friend\u2019", "AMERICAS", "AP"),
    (32, "DoJ admits US citizen was deported to Mexico", "AMERICAS", "OT"),
    (33, "ICE video sparks Seattle protests", "AMERICAS", "OT"),
    (34, "US Army to detonate unstable Iowa explosives despite court order", "AMERICAS", "OT"),
    (35, "Nine shot at California concert; one critical", "AMERICAS", "ARAB NEWS"),
    (36, "Delta fault delays Thanksgiving flights", "AMERICAS", "ARAB NEWS"),
    (37, "Trump to host gala for investors in plunging meme coin", "AMERICAS", "ARAB NEWS"),
    (38, "Tata Steel buys $1.67bn stake in APL Apollo", "ASIA", "OT"),
    (39, "Bangladesh vows to arrest Hasina if she returns", "ASIA", "ET"),
    (40, "Armenia proposes new constitution in peace step", "ASIA", "ARAB NEWS"),
    (41, "Kim: North Korea seeks security, not supremacy", "ASIA", "ET"),
    (42, "India tests JWALA anti-drone missile", "ASIA", "ET"),
    (43, "Marquez equals Agostini with eighth MotoGP title", "SPORT", "OT"),
    (44, "Fighting near Ebola area disrupts DR Congo response", "AFRICA", "OT"),
    (45, "Kenya and DR Congo agree to restore ties", "AFRICA", "OT"),
    (46, "Storm kills five, displaces thousands in Brazil town", "AMERICAS", "OT"),
    (47, "Bolsonaro in intensive care with intestinal blockage", "AMERICAS", "OT"),
    (48, "Robot sub finds volcanic activity in Mariana Trench", "SCIENCE", "OT"),
    (49, "FDA-approved drug may cure hormone-driven hypertension", "HEALTH", "OT"),
    (50, "Alcaraz wins first ATP Finals title", "SPORT", "OT"),
]

NUMBERS = [
    ("258", "DEM HOUSE SEATS"),
    ("15", "KILLED NEAR KYIV"),
    ("7", "DRONES AT MERKURY"),
    ("\u22125.06%", "NIKKEI FALL"),
    ("\u22123.7%", "S&P 500 FALL"),
    ("24", "DEAD IN BANTEN FIRE"),
    ("450", "SCHOOLS THREATENED"),
    ("$4.4bn", "CONOCOPHILLIPS DEAL"),
]

TIMELINE = [
    ("OVERNIGHT", "Dymer block hit; 11 killed"),
    ("~06:00", "Nikkei opens down 5%"),
    ("~09:30", "COP31 collapse confirmed"),
    ("MIDDAY", "Iran vows \u2018all means\u2019"),
    ("AFTERNOON", "Merkury sinking confirmed"),
    ("EVENING", "Democrats pass 258 seats"),
]

DATE_CHECK = [
    "COP31 itself ran 9\u201320 Nov \u2014 only its collapse is today\u2019s news. Shenzhen summit (19 Nov): only today\u2019s echo counts, the intel chief backing \u2018friend\u2019.",
    "Left out: Seoul exam-cheating minister quits (22 Nov) \u00b7 BepiColombo Mercury orbit (21 Nov) \u00b7 Pugh Hormuz swim (pre-22 Nov) \u00b7 GTA VI $3.79bn (20 Nov) \u00b7 Kryvyi Rih strike (21 Nov).",
]

REGION_COUNTS = "EUROPE 14 \u00b7 AMERICAS 13 \u00b7 ASIA 7 \u00b7 AFRICA 6 \u00b7 MIDEAST 5 \u00b7 GLOBAL 4 \u00b7 OCEANIA 1"

CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70), (-75, 62),
     (-60, 55), (-55, 47), (-70, 42), (-75, 35), (-80, 26), (-85, 30), (-95, 29),
     (-100, 25), (-105, 20), (-110, 23), (-120, 34), (-125, 40), (-125, 49),
     (-140, 60), (-155, 58), (-165, 60)],
    [(-80, 10), (-75, 5), (-80, -5), (-85, -15), (-75, -25), (-70, -35), (-65, -45),
     (-60, -55), (-55, -40), (-50, -30), (-40, -20), (-35, -10), (-45, -2),
     (-55, 5), (-65, 10), (-75, 10)],
    [(-10, 35), (0, 36), (10, 37), (20, 32), (30, 31), (35, 28), (40, 20), (45, 12),
     (50, 10), (45, 0), (40, -10), (35, -20), (30, -30), (20, -35), (15, -25),
     (12, -15), (10, -5), (5, 5), (-5, 5), (-15, 10), (-17, 20), (-15, 30)],
    [(-10, 36), (-5, 44), (0, 46), (5, 50), (10, 55), (15, 58), (20, 60), (25, 65),
     (30, 70), (35, 68), (40, 60), (35, 55), (30, 50), (25, 45), (20, 40),
     (15, 38), (10, 38), (5, 40), (0, 38), (-5, 36)],
    [(35, 70), (50, 72), (70, 73), (90, 75), (110, 76), (130, 72), (150, 70),
     (170, 66), (180, 65), (170, 60), (160, 55), (150, 50), (140, 40), (130, 35),
     (120, 30), (110, 20), (105, 10), (100, 8), (95, 15), (90, 22), (85, 20),
     (80, 10), (75, 8), (70, 15), (65, 25), (60, 25), (55, 28), (50, 30),
     (45, 30), (40, 35), (35, 40)],
    [(113, -22), (122, -14), (132, -12), (142, -11), (150, -22), (153, -32),
     (150, -37), (140, -38), (130, -32), (120, -34), (113, -26)],
]
MAP_PINS = [(1, 30.7, 36.9, "ANTALYA"), (2, 20.1, 32.1, "BENGHAZI"),
            (3, 30.5, 50.5, "DYMER"), (4, 56.5, 26.5, "HORMUZ")]


# ---------------------------------------------------------------- drawing
def draw_icon(d, kind, x, y, s, color):
    """A tiny flat glyph inside a square of side s at (x, y)."""
    if kind == "globe":
        d.ellipse([x + 2, y + 2, x + s - 2, y + s - 2], outline=color, width=2)
        d.arc([x + s // 2 - 4, y + 2, x + s // 2 + 4, y + s - 2], 270, 90, fill=color, width=1)
        d.arc([x + s // 2 - 4, y + 2, x + s // 2 + 4, y + s - 2], 90, 270, fill=color, width=1)
        d.line([x + 2, y + s // 2, x + s - 2, y + s // 2], fill=color, width=1)
    elif kind == "ship":
        d.polygon([(x + 2, y + s - 7), (x + s - 2, y + s - 7), (x + s - 6, y + s - 2),
                   (x + 6, y + s - 2)], fill=color)
        d.rectangle([x + s // 2 - 1, y + 3, x + s // 2 + 1, y + s - 8], fill=color)
        d.polygon([(x + s // 2 + 1, y + 4), (x + s - 4, y + 10), (x + s // 2 + 1, y + 10)], fill=color)
        d.line([x + 1, y + s - 1, x + s - 1, y + s - 1], fill=color, width=1)
    elif kind == "flame":
        d.polygon([(x + s // 2, y + 2), (x + s - 3, y + s // 2 + 2), (x + s // 2 + 3, y + s - 3),
                   (x + 3, y + s // 2 + 2)], fill=color)
    elif kind == "ballot":
        d.rectangle([x + 2, y + 7, x + s - 2, y + s - 2], outline=color, width=2)
        d.line([x + 4, y + 4, x + s // 2, y + 1, x + s - 3, y + 6], fill=color, width=2)
    elif kind == "shield":
        d.polygon([(x + 2, y + 4), (x + s // 2, y + 2), (x + s - 2, y + 4),
                   (x + s - 2, y + s // 2 + 2), (x + s // 2, y + s - 2),
                   (x + 2, y + s // 2 + 2)], outline=color, width=2)
    elif kind == "chip":
        d.rectangle([x + 4, y + 4, x + s - 4, y + s - 4], outline=color, width=2)
        for px in (x + 7, x + s // 2, x + s - 7):
            d.line([px, y + 1, px, y + 4], fill=color, width=1)
            d.line([px, y + s - 4, px, y + s - 1], fill=color, width=1)
    elif kind == "scale":
        d.line([x + s // 2, y + 2, x + s // 2, y + s - 3], fill=color, width=2)
        d.line([x + 3, y + 5, x + s - 3, y + 5], fill=color, width=2)
        d.line([x + 2, y + s - 3, x + s - 2, y + s - 3], fill=color, width=2)
    elif kind == "cross":
        d.rectangle([x + s // 2 - 2, y + 2, x + s // 2 + 2, y + s - 2], fill=color)
        d.rectangle([x + 2, y + s // 2 - 2, x + s - 2, y + s // 2 + 2], fill=color)
    elif kind == "star":
        cx, cy, r = x + s // 2, y + s // 2, s // 2 - 2
        pts = []
        for i in range(10):
            ang = -90 + i * 36
            rr = r if i % 2 == 0 else r // 2
            import math
            pts.append((cx + rr * math.cos(math.radians(ang)),
                        cy + rr * math.sin(math.radians(ang))))
        d.polygon(pts, fill=color)
    elif kind == "bolt":
        d.polygon([(x + s // 2 + 2, y + 1), (x + 4, y + s // 2 + 1), (x + s // 2, y + s // 2 + 1),
                   (x + s // 2 - 2, y + s - 1), (x + s - 4, y + s // 2 - 1),
                   (x + s // 2, y + s // 2 - 1)], fill=color)
    elif kind == "bars":
        d.line([x + 2, y + s - 3, x + s - 2, y + s - 3], fill=color, width=1)
        for i, hgt in enumerate((5, 9, 13)):
            bx = x + 4 + i * 6
            d.rectangle([bx, y + s - 3 - hgt, bx + 3, y + s - 3], fill=color)
    elif kind == "arrow":
        d.line([x + 3, y + s - 4, x + s - 4, y + 4], fill=color, width=2)
        d.polygon([(x + s - 4, y + 3), (x + s - 4, y + 9), (x + s - 9, y + 3)], fill=color)


def draw_headline_art(d, kind, x, y, s, color):
    """A flat vector illustration, side s, for one of the four headlines."""
    d.rectangle([x, y, x + s, y + s], fill=(233, 226, 205), outline=FAINT)
    pad = 12
    if kind == "globe":  # climate: globe with a rising red arrow
        cx, cy, r = x + s // 2 - 6, y + s // 2, s // 2 - pad
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(35, 64, 107), width=3)
        d.ellipse([cx - r // 2, cy - r, cx + r // 2, cy + r], outline=(35, 64, 107), width=1)
        d.line([cx - r, cy, cx + r, cy], fill=(35, 64, 107), width=1)
        d.line([x + s - 26, y + s - 16, x + s - 26, y + 14], fill=RULE, width=3)
        d.polygon([(x + s - 32, y + 20), (x + s - 20, y + 20), (x + s - 26, y + 10)], fill=RULE)
        d.ellipse([x + s - 30, y + s - 22, x + s - 22, y + s - 14], fill=RULE)
    elif kind == "ship":  # warship hit at sea
        d.polygon([(x + 10, y + s - 34), (x + s - 10, y + s - 34), (x + s - 22, y + s - 18),
                   (x + 22, y + s - 18)], fill=(25, 25, 25))
        d.rectangle([x + s // 2 - 2, y + 18, x + s // 2 + 2, y + s - 34], fill=(25, 25, 25))
        d.polygon([(x + s // 2 + 2, y + 20), (x + s - 16, y + 34), (x + s // 2 + 2, y + 34)],
                  fill=(25, 25, 25))
        for wy in (s - 12, s - 6):
            d.line([x + 6, y + wy, x + s - 6, y + wy], fill=(35, 64, 107), width=2)
        d.ellipse([x + 12, y + 10, x + 18, y + 16], fill=RULE)
        d.ellipse([x + s - 24, y + 14, x + s - 18, y + 20], fill=RULE)
    elif kind == "flame":  # apartment block struck, rescue below
        for i, bx in enumerate((x + 12, x + 40, x + 68)):
            d.rectangle([bx, y + 22, bx + 22, y + s - 20], fill=(120, 116, 100))
            for wy in (30, 44, 58):
                d.rectangle([bx + 4, y + wy, bx + 10, y + wy + 6], fill=PAPER)
                d.rectangle([bx + 13, y + wy, bx + 19, y + wy + 6], fill=PAPER)
        d.line([x + 40, y + 22, x + 52, y + 40, x + 44, y + 52, x + 56, y + 66],
               fill=RULE, width=3)
        d.line([x + 14, y + s - 12, x + s - 14, y + s - 12], fill=(15, 107, 92), width=2)
    else:  # bars: falling market chart
        d.line([x + 12, y + 14, x + 12, y + s - 14], fill=INK, width=2)
        d.line([x + 12, y + s - 14, x + s - 12, y + s - 14], fill=INK, width=2)
        pts = [(x + 16, y + 26), (x + 34, y + 34), (x + 50, y + 30), (x + 66, y + 52),
               (x + 82, y + 66)]
        d.line(pts, fill=RULE, width=3)
        d.polygon([(x + 82, y + 58), (x + 82, y + 74), (x + 74, y + 66)], fill=RULE)
        for bx, bh in ((20, 14), (38, 22), (56, 10)):
            d.rectangle([x + bx, y + s - 14 - bh, x + bx + 10, y + s - 14],
                        fill=(35, 64, 107))


def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    mx = 28  # side margin
    right = W - mx

    # ---- masthead
    d.rectangle([0, 0, W, 6], fill=RULE)
    f_title = font(52, bold=True)
    d.text((mx, 14), "MONDAY 23 NOVEMBER 2026", font=f_title, fill=INK)
    f_sub = font(15, bold=True)
    d.text((mx, 74), "ONE DAY OF WORLD NEWS \u2014 ONE PICTURE", font=f_sub, fill=RULE)
    f_count = font(14, bold=True)
    counts = "50 STORIES \u00b7 7 REGIONS \u00b7 12 OUTLETS"
    d.text((right - d.textlength(counts, font=f_count), 76), counts, font=f_count, fill=INK)
    d.line([mx, 96, right, 96], fill=INK, width=2)

    # ---- BY THE NUMBERS strip
    y0, y1 = 100, 130
    cell_w = (right - mx) / len(NUMBERS)
    for i, (num, label) in enumerate(NUMBERS):
        cx = mx + i * cell_w
        f_num = font(19, bold=True)
        d.text((cx + (cell_w - d.textlength(num, font=f_num)) / 2, y0 + 1), num,
               font=f_num, fill=RULE)
        f_lab = font(8, bold=True)
        lab = truncate(d, label, f_lab, cell_w - 4)
        d.text((cx + (cell_w - d.textlength(lab, font=f_lab)) / 2, y0 + 21), lab,
               font=f_lab, fill=MUTED)
        if i:
            d.line([cx, y0 + 3, cx, y1 - 3], fill=FAINT, width=1)
    d.line([mx, y1, right, y1], fill=INK, width=1)

    # ---- UTC timeline
    y0, y1 = 134, 174
    f_tl_head = font(11, bold=True)
    d.text((mx, y0), "THE DAY IN UTC", font=f_tl_head, fill=INK)
    d.line([mx, y0 + 14, right, y0 + 14], fill=FAINT, width=1)
    cell_w = (right - mx) / len(TIMELINE)
    for i, (when, what) in enumerate(TIMELINE):
        cx = mx + i * cell_w
        d.text((cx + 2, y0 + 17), when, font=font(10, bold=True), fill=RULE)
        lines = wrap(d, what, font(9), cell_w - 8)
        for j, ln in enumerate(lines[:1]):
            d.text((cx + 2, y0 + 29 + j * 11), ln, font=font(9), fill=INK)
        if i:
            d.line([cx, y0 + 17, cx, y1 - 2], fill=FAINT, width=1)
    d.line([mx, y1, right, y1], fill=INK, width=1)

    # ---- four headlines, 2 x 2
    y0 = 178
    cell_w, cell_h = 480, 110
    for idx, st in enumerate(HEADLINES):
        col, row = idx % 2, idx // 2
        x = mx + col * (cell_w + 8)
        y = y0 + row * (cell_h + 4)
        d.rectangle([x, y, x + cell_w, y + cell_h], outline=FAINT, width=1)
        d.rectangle([x, y, x + 5, y + cell_h], fill=REGION_COLORS["GLOBAL"])
        draw_headline_art(d, st["icon"], x + 12, y + 7, 96,
                          REGION_COLORS["GLOBAL"])
        tx = x + 116
        tw = cell_w - 124
        tagline = "%s \u2014 %s \u00b7 %s" % (st["region"], st["tag"], st["source"])
        d.text((tx, y + 6), tagline, font=font(10, bold=True),
               fill=REGION_COLORS["GLOBAL"])
        d.text((tx + tw - d.textlength(st["utc"], font=font(10, bold=True)), y + 6),
               st["utc"], font=font(10, bold=True), fill=RULE)
        title_lines, f_title2 = fit_lines(d, st["title"], font(19, bold=True), tw, 2)
        for j, ln in enumerate(title_lines):
            d.text((tx, y + 20 + j * 22), ln, font=f_title2, fill=INK)
        body_lines = wrap(d, st["body"], font(11), tw)
        for j, ln in enumerate(body_lines[:2]):
            d.text((tx, y + 66 + j * 13), ln, font=font(11), fill=INK)
        d.text((tx, y + 92), truncate(d, st["why"], font(10), tw),
               font=font(10), fill=MUTED)

    # ---- secondaries header + 12 rows
    y0 = 406
    d.text((mx, y0), "THE DAY IN BRIEF \u2014 12 MORE STORIES", font=font(12, bold=True), fill=INK)
    d.line([mx, y0 + 16, right, y0 + 16], fill=INK, width=1)
    y0 += 20
    row_h = 33
    for idx, st in enumerate(SECONDARIES):
        col, row = idx % 2, idx // 2
        x = mx + col * 484
        y = y0 + row * row_h
        color = REGION_COLORS[st["region"]]
        d.rectangle([x, y + 4, x + 20, y + 24], fill=color)
        d.text((x + 5, y + 7), str(st["n"]), font=font(11, bold=True), fill=(255, 255, 255))
        draw_icon(d, st["icon"], x + 26, y + 5, 18, color)
        tx = x + 50
        tw = 484 - 58
        d.text((tx, y + 2), truncate(d, st["title"], font(12, bold=True), tw),
               font=font(12, bold=True), fill=INK)
        tag = "%s \u00b7 %s" % (st["tag"], st["source"])
        f_tag = font(9, bold=True)
        tag_w = d.textlength(tag, font=f_tag)
        d.text((tx, y + 17), truncate(d, st["body"], font(10), tw - tag_w - 8),
               font=font(10), fill=MUTED)
        d.text((tx + tw - tag_w, y + 17), tag, font=f_tag, fill=color)
        if row < 5:
            d.line([x, y + row_h - 2, x + 476, y + row_h - 2], fill=FAINT, width=1)

    # ---- ALSO ON list
    y0 = 628
    d.text((mx, y0), "ALSO ON MONDAY 23 NOVEMBER", font=font(12, bold=True), fill=INK)
    d.line([mx, y0 + 16, right, y0 + 16], fill=INK, width=1)
    y0 += 20
    row_h = 12
    for idx, (n, text, region, src) in enumerate(ALSO_ON):
        col, row = idx % 2, idx // 2
        x = mx + col * 484
        y = y0 + row * row_h
        line = "%d. %s \u2014 %s \u00b7 %s" % (n, text, region, src)
        d.text((x, y), truncate(d, line, font(9), 476), font=font(9), fill=INK)

    # ---- world map band
    y0 = 856
    d.text((mx, y0), "WHERE IT HAPPENED", font=font(12, bold=True), fill=INK)
    d.line([mx, y0 + 16, right, y0 + 16], fill=INK, width=1)
    map_x, map_y, map_w, map_h = mx, y0 + 22, 640, 66
    d.rectangle([map_x, map_y, map_x + map_w, map_y + map_h], fill=(238, 233, 218),
                outline=FAINT)
    for gx in range(-150, 181, 30):
        px = map_x + (gx + 170) / 360.0 * map_w
        d.line([px, map_y, px, map_y + map_h], fill=(228, 222, 204), width=1)
    for gy in (-30, 0, 30, 60):
        py = map_y + (75 - gy) / 130.0 * map_h
        d.line([map_x, py, map_x + map_w, py], fill=(228, 222, 204), width=1)

    def proj(lon, lat):
        return (map_x + (lon + 170) / 360.0 * map_w,
                map_y + (75 - lat) / 130.0 * map_h)

    for cont in CONTINENTS:
        d.polygon([proj(lon, lat) for lon, lat in cont], fill=MAP_FILL, outline=MAP_LINE)
    pin_xy = {}
    for n, lon, lat, name in MAP_PINS:
        px, py = proj(lon, lat)
        pin_xy[n] = (px, py)
        d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RULE, outline=(255, 255, 255), width=1)
        f_pin = font(9, bold=True)
        d.text((px - d.textlength(str(n), font=f_pin) / 2, py - 6), str(n),
               font=f_pin, fill=(255, 255, 255))
    lx = map_x + map_w + 16
    d.text((lx, map_y + 2), "1 ANTALYA \u2014 COP31 collapses", font=font(10, bold=True), fill=INK)
    d.text((lx, map_y + 18), "2 BENGHAZI \u2014 Merkury sunk", font=font(10, bold=True), fill=INK)
    d.text((lx, map_y + 34), "3 DYMER \u2014 strike kills 15", font=font(10, bold=True), fill=INK)
    d.text((lx, map_y + 50), "4 HORMUZ \u2014 blockade stand-off", font=font(10, bold=True), fill=INK)

    # ---- DATE CHECK
    y0 = 948
    d.rectangle([mx, y0, right, y0 + 34], fill=(233, 226, 205))
    d.text((mx + 6, y0 + 3), "DATE CHECK \u2014 NOT TODAY\u2019S NEWS, LEFT OUT:",
           font=font(10, bold=True), fill=RULE)
    d.text((mx + 6, y0 + 14), truncate(d, DATE_CHECK[0], font(9), right - mx - 12),
           font=font(9), fill=INK)
    d.text((mx + 6, y0 + 24), truncate(d, DATE_CHECK[1], font(9), right - mx - 12),
           font=font(9), fill=INK)

    # ---- footer
    y0 = 986
    d.line([mx, y0, right, y0], fill=INK, width=1)
    f_foot = font(9)
    d.text((mx, y0 + 5),
           "Every story here happened or was first reported on Monday 23 November 2026. "
           "CLAIM = one side\u2019s account, not independently confirmed; REPORTED = single-source report.",
           font=f_foot, fill=MUTED)
    d.text((mx, y0 + 17),
           "Sources: AP, Arab News, BBC, CNN, Dawn, ET, Fox News, One Turn, Reuters, SCMP, WION. "
           "Original flat drawings; no photographs.",
           font=f_foot, fill=MUTED)
    d.text((mx, y0 + 29), REGION_COUNTS, font=font(9, bold=True), fill=INK)
    d.text((right - d.textlength("23 NOV 2026", font=font(9, bold=True)), y0 + 29),
           "23 NOV 2026", font=font(9, bold=True), fill=RULE)
    return img


def main():
    img = build()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not outdir:
        outdir = "/output" if os.path.isdir("/output") else "."
    path = os.path.join(outdir, "entry.png")
    img.save(path, format="PNG")
    data = open(path, "rb").read()
    print("wrote %s %d bytes %s sha256=%s" % (
        path, len(data), img.size, hashlib.sha256(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
