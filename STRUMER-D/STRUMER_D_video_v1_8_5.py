from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import os
import textwrap
import hashlib
import math

WIDTH, HEIGHT = 1280, 720
FPS = 30
OUTFILE = "STRUMER_D_video_v1_8_5.mp4"
VERSION = "1.8.5"

FADE_SECONDS = 0.30
SAFE_TOP = 44
SAFE_BOTTOM = 560
FOOTER_Y = 656

BG = (5, 8, 15)
PANEL = (10, 16, 29)
PANEL_DARK = (8, 12, 22)
CARD = (13, 21, 38)
WHITE = (250, 252, 255)
MUTED = (218, 226, 240)
GOLD = (255, 215, 120)
ACCENT = (100, 255, 180)
PURPLE = (196, 150, 255)
TEAL = (120, 255, 225)
RED = (255, 105, 125)
ORANGE = (255, 170, 70)
LINE = (95, 108, 135)
CODE_BG = (11, 17, 31)


def font(size, bold=False):
    try:
        if os.name == "nt":
            path = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
        else:
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


FONT_HERO = font(62, True)
FONT_TITLE = font(50, True)
FONT_MED = font(34, True)
FONT_BODY = font(30, True)
FONT_SMALL = font(25, True)
FONT_TINY = font(22, True)
FONT_MICRO = font(19, True)
FONT_CODE = font(23, True)
FONT_CODE_SMALL = font(20, True)
FONT_NODE = font(25, True)
FONT_FOOTER = font(20, True)


def canvas():
    return Image.new("RGB", (WIDTH, HEIGHT), BG)


def text_size(draw, text, f):
    b = draw.textbbox((0, 0), text, font=f)
    return b[2] - b[0], b[3] - b[1]


def center(draw, text, y, f, color=WHITE):
    w, _ = text_size(draw, text, f)
    draw.text(((WIDTH - w) // 2, y), text, font=f, fill=color)


def center_in_box(draw, text, box, y, f, color=WHITE):
    max_width = box[2] - box[0] - 34
    active_font = fit_font_for_width(draw, text, f.size, max_width, True, 16)
    w, _ = text_size(draw, text, active_font)
    x = box[0] + ((box[2] - box[0] - w) // 2)
    draw.text((x, y), text, font=active_font, fill=color)


def wrap_lines(text, max_chars):
    out = []
    for raw in str(text).split("\n"):
        if not raw.strip():
            out.append("")
        else:
            out.extend(textwrap.wrap(raw, width=max_chars, break_long_words=False, replace_whitespace=False))
    return out


def fit_font_for_width(draw, text, start_size, max_width, bold=True, min_size=16):
    size = start_size
    while size >= min_size:
        f = font(size, bold)
        if text_size(draw, text, f)[0] <= max_width:
            return f
        size -= 1
    return font(min_size, bold)


def center_multiline(draw, text, y, f, color=WHITE, gap=12, max_chars=38, bottom=SAFE_BOTTOM):
    lines = wrap_lines(text, max_chars)
    total = len(lines) * f.size + max(0, len(lines) - 1) * gap
    y = min(y, bottom - total)
    y = max(SAFE_TOP, y)
    for line in lines:
        if line:
            center(draw, line, y, f, color)
        y += f.size + gap


def panel(draw, box, outline=ACCENT, fill=PANEL, width=3, radius=22):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_footer(draw, text=""):
    return


def structural_signature(payload):
    normalized = "|".join(f"{k}={payload[k]}" for k in sorted(payload))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def title_slide(title, body="", duration=4.8, title_color=GOLD, footer=True):
    img = canvas()
    draw = ImageDraw.Draw(img)
    f = FONT_HERO if len(title.replace("\n", " ")) < 24 else FONT_TITLE
    center_multiline(draw, title, 96, f, title_color, gap=14, max_chars=34, bottom=355 if body else SAFE_BOTTOM)
    if body:
        center_multiline(draw, body, 310, FONT_BODY, WHITE, gap=14, max_chars=58, bottom=590)
    if footer:
        draw_footer(draw)
    return img, duration


def two_line_slide(line1, line2, duration=4.6):
    img = canvas()
    draw = ImageDraw.Draw(img)
    f1 = fit_font_for_width(draw, line1, 62, WIDTH - 140, True, 38)
    f2 = fit_font_for_width(draw, line2, 62, WIDTH - 140, True, 38)
    center(draw, line1, 190, f1, GOLD)
    center(draw, line2, 320, f2, ACCENT)
    draw_footer(draw)
    return img, duration


def principle_slide(title, principle, duration=5.4):
    img = canvas()
    draw = ImageDraw.Draw(img)
    center_multiline(draw, title, 74, FONT_TITLE, GOLD, gap=10, max_chars=36, bottom=180)
    panel(draw, (88, 230, 1192, 430), outline=ACCENT, fill=PANEL_DARK, width=4)
    f = fit_font_for_width(draw, principle, 34, 1020, True, 22)
    center_multiline(draw, principle, 295, f, ACCENT, gap=10, max_chars=60, bottom=415)
    draw_footer(draw)
    return img, duration


def draw_code_lines(draw, code, box, start_size=23, color=WHITE, line_numbers=False):
    x1, y1, x2, y2 = box
    max_w = x2 - x1 - (78 if line_numbers else 42)
    max_h = y2 - y1 - 40
    raw_lines = code.strip("\n").split("\n")

    for size in range(start_size, 15, -1):
        f = font(size, True)
        wrapped = []
        for raw in raw_lines:
            max_chars = max(28, int(max_w / max(8, size * 0.55)))
            chunks = textwrap.wrap(raw, width=max_chars, break_long_words=False, replace_whitespace=False) or [""]
            for j, chunk in enumerate(chunks):
                wrapped.append(chunk if j == 0 else "    " + chunk)
        line_h = size + 9
        if len(wrapped) * line_h <= max_h:
            break
    else:
        f = font(16, True)
        line_h = 24
        wrapped = []
        max_chars = 72
        for raw in raw_lines:
            wrapped.extend(textwrap.wrap(raw, width=max_chars, break_long_words=False, replace_whitespace=False) or [""])

    max_lines = max(1, int(max_h // line_h))
    if len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines - 1] + ["..."]

    y = y1 + 22
    for i, line in enumerate(wrapped, 1):
        if line_numbers:
            draw.text((x1 + 18, y), f"{i:02d}", font=font(max(14, f.size - 5), True), fill=GOLD)
            draw.text((x1 + 64, y), line, font=f, fill=color)
        else:
            draw.text((x1 + 24, y), line, font=f, fill=color)
        y += line_h


def simple_code_slide(title, code, footer="", duration=6.4):
    img = canvas()
    draw = ImageDraw.Draw(img)
    center_multiline(draw, title, 48, FONT_TITLE, GOLD, gap=8, max_chars=34, bottom=140)
    box = (92, 158, 1188, 488)
    panel(draw, box, outline=GOLD, fill=CODE_BG, width=4)
    draw_code_lines(draw, code, box, start_size=24, line_numbers=False)
    if footer:
        center_multiline(draw, footer, 514, FONT_SMALL, ACCENT, gap=8, max_chars=55, bottom=640)
    draw_footer(draw)
    return img, duration


def live_diagram_proof_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "LIVE PROOF", 55, FONT_HERO, GOLD)
    center(draw, "The flowchart appears from the structure below", 148, FONT_SMALL, WHITE)
    code = '''diagram = {
  "type": "flowchart",
  "nodes": ["Request", "Gateway", "Logic", "Store"],
  "edges": ["Request->Gateway", "Gateway->Logic", "Logic->Store"],
  "layout": "horizontal"
}

resolve(diagram) -> visible diagram'''
    box = (82, 218, 1198, 508)
    panel(draw, box, outline=GOLD, fill=CODE_BG, width=4)
    draw_code_lines(draw, code, box, start_size=24, line_numbers=True)
    center(draw, "Complete structure resolves into visible diagram output.", 532, FONT_TINY, ACCENT)
    draw_footer(draw)
    return img, 7.0


def draw_node(draw, box, text, outline=ACCENT, fill=PANEL_DARK, f=FONT_NODE):
    panel(draw, box, outline=outline, fill=fill, width=4, radius=18)
    f = fit_font_for_width(draw, text, f.size, box[2] - box[0] - 20, True, 15)
    w, h = text_size(draw, text, f)
    x = (box[0] + box[2] - w) // 2
    y = (box[1] + box[3] - h) // 2 - 1
    draw.text((x, y), text, font=f, fill=WHITE)


def arrow_down(draw, x, y1, y2, color=ACCENT, width=5):
    draw.line((x, y1, x, y2), fill=color, width=width)
    draw.polygon([(x, y2 + 18), (x - 13, y2 - 2), (x + 13, y2 - 2)], fill=color)


def structure_reveals_video_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "Structure Reveals Video", 55, FONT_TITLE, GOLD)
    draw_node(draw, (500, 155, 780, 215), "STRUCTURE", ACCENT)
    arrow_down(draw, 640, 222, 275, ACCENT)
    draw_node(draw, (410, 295, 870, 360), "Complete + Consistent", ACCENT)
    arrow_down(draw, 640, 368, 425, ACCENT)
    draw_node(draw, (480, 445, 800, 505), "VISIBLE VIDEO", ACCENT)
    center(draw, "video_visible iff video_structure_complete AND video_structure_consistent", 532, FONT_TINY, GOLD)
    draw_footer(draw)
    return img, 6.0


def before_after_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "Old Workflow vs STRUMER-D", 52, FONT_TITLE, GOLD)
    panel(draw, (80, 150, 585, 510), outline=RED, fill=PANEL_DARK, width=4)
    panel(draw, (695, 150, 1200, 510), outline=ACCENT, fill=PANEL_DARK, width=4)
    center_in_box(draw, "Manual Diagramming", (80, 150, 585, 510), 180, FONT_MED, RED)
    center_in_box(draw, "Structural Resolution", (695, 150, 1200, 510), 180, FONT_MED, ACCENT)
    left = ["Open tool", "Drag shapes", "Connect arrows", "Fix alignment", "Repeat"]
    right = ["Define structure", "Resolve once", "Deterministic output", "Same result every run", "Done"]
    y = 250
    for item in left:
        draw.text((140, y), "* " + item, font=FONT_SMALL, fill=WHITE)
        y += 45
    y = 250
    for item in right:
        draw.text((755, y), "* " + item, font=FONT_SMALL, fill=WHITE)
        y += 45
    draw_footer(draw)
    return img, 7.0


def structure_to_diagram_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "STRUCTURE  ->  DIAGRAM", 40, FONT_TITLE, GOLD)
    left_box = (60, 120, 565, 515)
    panel(draw, left_box, outline=ACCENT, fill=PANEL_DARK, width=5)
    draw.text((92, 145), "INPUT STRUCTURE", font=FONT_MED, fill=ACCENT)
    lines = '''{
  "type": "flowchart",
  "nodes": [
    "Request",
    "Gateway",
    "Logic",
    "Store"
  ],
  "edges": [
    "Request -> Gateway",
    "Gateway -> Logic",
    "Logic -> Store"
  ]
}'''
    draw_code_lines(draw, lines, (78, 185, 548, 500), start_size=20, line_numbers=False)
    draw.line((610, 310, 715, 310), fill=GOLD, width=8)
    draw.polygon([(730, 310), (704, 292), (704, 328)], fill=GOLD)
    right_box = (760, 130, 1215, 500)
    panel(draw, right_box, outline=GOLD, fill=PANEL_DARK, width=5)
    center_in_box(draw, "VISIBLE DIAGRAM", right_box, 162, FONT_MED, GOLD)
    node_y = 312
    xs = [825, 940, 1055, 1155]
    labels = ["Request", "Gateway", "Logic", "Store"]
    for i in range(3):
        draw.line((xs[i] + 48, node_y, xs[i + 1] - 48, node_y), fill=ACCENT, width=4)
        draw.polygon([(xs[i + 1] - 48, node_y), (xs[i + 1] - 62, node_y - 8), (xs[i + 1] - 62, node_y + 8)], fill=ACCENT)
    for x, label in zip(xs, labels):
        draw.rounded_rectangle((x - 55, node_y - 28, x + 55, node_y + 28), radius=14, fill=(18, 28, 49), outline=ACCENT, width=3)
        f = fit_font_for_width(draw, label, 18, 96, True, 13)
        w, h = text_size(draw, label, f)
        draw.text((x - w // 2, node_y - h // 2), label, font=f, fill=WHITE)
    center(draw, "No drawing. No dragging. No layout tuning.", 525, FONT_SMALL, ACCENT)
    draw_footer(draw)
    return img, 7.0


def structure_to_diagram_reveal_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "STRUCTURE  ->  DIAGRAM", 38, FONT_TITLE, GOLD)
    left_box = (60, 115, 565, 520)
    right_box = (715, 128, 1240, 500)
    panel(draw, left_box, outline=ACCENT, fill=PANEL_DARK, width=5)
    draw.text((88, 140), "STRUCTURAL INPUT", font=FONT_SMALL, fill=ACCENT)
    structure_text = '''{
  "type": "flowchart",
  "nodes": [
    {"id": "request", "label": "Request"},
    {"id": "gateway", "label": "Gateway"},
    {"id": "logic", "label": "Logic"},
    {"id": "store", "label": "Store"}
  ],
  "edges": [
    ("request", "gateway"),
    ("gateway", "logic"),
    ("logic", "store")
  ],
  "layout": "horizontal"
}'''
    draw_code_lines(draw, structure_text, (72, 178, 553, 505), start_size=19)
    draw.line((590, 315, 685, 315), fill=GOLD, width=8)
    draw.polygon([(704, 315), (678, 296), (678, 334)], fill=GOLD)
    panel(draw, right_box, outline=GOLD, fill=PANEL_DARK, width=5)
    center_in_box(draw, "RESOLVED DIAGRAM", right_box, 158, FONT_MED, GOLD)
    node_y = 315
    xs = [795, 920, 1045, 1170]
    labels = ["Request", "Gateway", "Logic", "Store"]
    for i in range(3):
        draw.line((xs[i] + 54, node_y, xs[i + 1] - 54, node_y), fill=ACCENT, width=4)
        draw.polygon([(xs[i + 1] - 54, node_y), (xs[i + 1] - 69, node_y - 9), (xs[i + 1] - 69, node_y + 9)], fill=ACCENT)
    for x, label in zip(xs, labels):
        draw.rounded_rectangle((x - 60, node_y - 30, x + 60, node_y + 30), radius=15, fill=(18, 28, 49), outline=ACCENT, width=3)
        f = fit_font_for_width(draw, label, 19, 108, True, 13)
        w, h = text_size(draw, label, f)
        draw.text((x - w // 2, node_y - h // 2), label, font=f, fill=WHITE)
    center(draw, "One definition. Deterministic output. Zero drawing.", 530, FONT_TINY, ACCENT)
    draw_footer(draw)
    return img, 7.2


def storage_reveal_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "The Drawing Is Not Stored", 95, FONT_TITLE, GOLD)
    center(draw, "Only the structure is stored", 220, FONT_MED, WHITE)
    center(draw, "The diagram reappears when structure resolves", 300, FONT_MED, ACCENT)
    center(draw, "same structure  ->  same diagram", 420, FONT_MED, GOLD)
    draw_footer(draw)
    return img, 6.0


def determinism_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "Same Structure", 130, FONT_HERO, GOLD)
    center(draw, "Same Diagram", 240, FONT_HERO, ACCENT)
    center(draw, "Every single time", 365, FONT_HERO, WHITE)
    draw_footer(draw)
    return img, 5.4


def run_proof_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "30-Second Proof", 54, FONT_TITLE, GOLD)
    panel(draw, (125, 150, 1155, 500), outline=GOLD, fill=PANEL_DARK, width=4)
    lines = ["python strumer_d_v2_0.py", "", "Case 1 state: RESOLVED", "Case 2 state: ABSTAIN", "Case 3 state: BLOCKED", "", "Run again -> same output signature"]
    y = 200
    for line in lines:
        draw.text((175, y), line, font=FONT_CODE, fill=ACCENT if "python" in line else WHITE)
        y += 38
    center(draw, "Determinism is the proof: same structure -> same diagram.", 525, FONT_SMALL, GOLD)
    draw_footer(draw)
    return img, 7.0


def change_one_node_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "Change One Node", 70, FONT_TITLE, GOLD)
    panel(draw, (130, 175, 1150, 430), outline=PURPLE, fill=PANEL_DARK, width=4)
    center(draw, '"Request"  ->  "New Request"', 270, FONT_MED, WHITE)
    center(draw, "New structure -> new deterministic diagram", 365, FONT_SMALL, ACCENT)
    center(draw, "No drawing involved.", 500, FONT_MED, GOLD)
    draw_footer(draw)
    return img, 5.8


def simplified_flowchart_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "Flowchart From Structure", 48, FONT_TITLE, GOLD)
    y = 305
    xs = [220, 430, 640, 850, 1060]
    labels = ["Input", "Structure", "Resolve", "Signature", "Diagram"]
    for i in range(len(xs) - 1):
        draw.line((xs[i] + 80, y, xs[i + 1] - 80, y), fill=ACCENT, width=5)
        draw.polygon([(xs[i + 1] - 80, y), (xs[i + 1] - 98, y - 10), (xs[i + 1] - 98, y + 10)], fill=ACCENT)
    for x, label in zip(xs, labels):
        draw.rounded_rectangle((x - 90, y - 42, x + 90, y + 42), radius=18, fill=CARD, outline=ACCENT, width=3)
        f = fit_font_for_width(draw, label, 25, 160, True, 17)
        w, h = text_size(draw, label, f)
        draw.text((x - w // 2, y - h // 2), label, font=f, fill=WHITE)
    center(draw, "The structure defines the diagram path.", 445, FONT_SMALL, GOLD)
    draw_footer(draw)
    return img, 6.0


def simplified_mindmap_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "Mind Map From Structure", 48, FONT_TITLE, GOLD)
    cx, cy = 640, 340
    branches = [("Structure", 360, 210), ("Diagram", 640, 170), ("Resolve", 920, 210), ("Signature", 380, 470), ("Safety", 900, 470)]
    draw_node(draw, (520, 300, 760, 380), "STRUMER-D", GOLD, CARD, FONT_NODE)
    for label, x, y in branches:
        draw.line((cx, cy, x, y), fill=LINE, width=4)
        draw_node(draw, (x - 90, y - 34, x + 90, y + 34), label, ACCENT, PANEL_DARK, FONT_MICRO)
    center(draw, "Center + branches -> visible structural map", 535, FONT_SMALL, ACCENT)
    draw_footer(draw)
    return img, 6.0



def draw_artifact_flowchart(draw, box):
    x1, y1, x2, y2 = box
    title_y = y1 + 28
    center(draw, "FLOWCHART | RESOLVED", title_y, FONT_SMALL, GOLD)
    y = y1 + 230
    xs = [x1 + 165, x1 + 415, x1 + 665, x1 + 915]
    labels = ["Request", "Gateway", "Logic", "Store"]
    for i in range(3):
        source_right = xs[i] + 100
        target_left = xs[i + 1] - 100
        arrow_start = source_right + 14
        arrow_end = target_left - 14
        draw.line((arrow_start, y, arrow_end, y), fill=ACCENT, width=6)
        draw.polygon([(arrow_end, y), (arrow_end - 20, y - 12), (arrow_end - 20, y + 12)], fill=ACCENT)
    for x, label in zip(xs, labels):
        draw_node(draw, (x - 100, y - 45, x + 100, y + 45), label, ACCENT, CARD, FONT_NODE)
    center(draw, "structure: nodes + edges + layout", y1 + 385, FONT_TINY, WHITE)
    center(draw, "state: RESOLVED | signature: deterministic", y1 + 420, FONT_TINY, ACCENT)


def draw_artifact_mindmap(draw, box):
    x1, y1, x2, y2 = box
    center(draw, "MIND MAP | RESOLVED", y1 + 28, FONT_SMALL, GOLD)
    cx, cy = (x1 + x2) // 2, y1 + 245
    branches = [
        ("Structure", cx, y1 + 115),
        ("Diagram", x2 - 210, y1 + 185),
        ("Resolve", x2 - 290, y1 + 355),
        ("Signature", x1 + 290, y1 + 355),
        ("Safety", x1 + 210, y1 + 185),
    ]
    for label, x, y in branches:
        draw.line((cx, cy, x, y), fill=PURPLE, width=5)
    draw_node(draw, (cx - 120, cy - 46, cx + 120, cy + 46), "STRUMER-D", GOLD, CARD, FONT_NODE)
    for label, x, y in branches:
        draw_node(draw, (x - 100, y - 36, x + 100, y + 36), label, PURPLE, PANEL_DARK, FONT_MICRO)
    center(draw, "center + branches -> visible structural map", y1 + 430, FONT_TINY, ACCENT)


def draw_artifact_sequence(draw, box):
    x1, y1, x2, y2 = box
    center(draw, "SEQUENCE | RESOLVED", y1 + 28, FONT_SMALL, GOLD)
    participants = [("User", x1 + 210), ("Resolver", (x1 + x2) // 2), ("Diagram", x2 - 210)]
    top = y1 + 110
    bottom = y1 + 405
    for name, x in participants:
        draw_node(draw, (x - 82, top - 34, x + 82, top + 34), name, ACCENT, CARD, FONT_MICRO)
        draw.line((x, top + 44, x, bottom), fill=LINE, width=3)
    msgs = [(0, 1, "submit structure"), (1, 2, "resolve visible form"), (2, 1, "return signature"), (1, 0, "diagram visible")]
    yy = y1 + 185
    for a, b, label in msgs:
        x_start = participants[a][1]
        x_end = participants[b][1]
        draw.line((x_start, yy, x_end, yy), fill=ACCENT, width=4)
        direction = 1 if x_end > x_start else -1
        draw.polygon([(x_end, yy), (x_end - 16 * direction, yy - 9), (x_end - 16 * direction, yy + 9)], fill=ACCENT)
        f = fit_font_for_width(draw, label, 18, abs(x_end - x_start) - 28, True, 13)
        draw.text((min(x_start, x_end) + 18, yy - 28), label, font=f, fill=WHITE)
        yy += 58
    center(draw, "resolved sequence interaction", y1 + 430, FONT_TINY, ACCENT)


def draw_artifact_polygon(draw, box):
    x1, y1, x2, y2 = box
    center(draw, "POLYGON | RESOLVED", y1 + 28, FONT_SMALL, GOLD)
    cx, cy = (x1 + x2) // 2, y1 + 250
    radius = 145
    points = []
    for i in range(7):
        angle = -math.pi / 2 + i * 2 * math.pi / 7
        points.append((cx + int(math.cos(angle) * radius), cy + int(math.sin(angle) * radius)))
    draw.polygon(points, outline=ACCENT, fill=(14, 32, 45))
    for p in points:
        draw.ellipse((p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7), fill=GOLD)
    center(draw, "resolved polygon structure", y1 + 430, FONT_TINY, ACCENT)


def draw_artifact_overview(draw, box):
    x1, y1, x2, y2 = box
    center(draw, "ONE RESOLVER | MULTIPLE DIAGRAM TYPES", y1 + 28, FONT_SMALL, GOLD)
    cards = [
        ((x1 + 90, y1 + 120, x1 + 330, y1 + 205), "Flowchart", ACCENT),
        ((x1 + 450, y1 + 120, x1 + 690, y1 + 205), "Mind Map", PURPLE),
        ((x1 + 810, y1 + 120, x1 + 1050, y1 + 205), "Sequence", TEAL),
        ((x1 + 270, y1 + 300, x1 + 510, y1 + 385), "Polygon", GOLD),
        ((x1 + 630, y1 + 300, x1 + 870, y1 + 385), "Safety", ORANGE),
    ]
    for b, label, color in cards:
        draw_node(draw, b, label, color, CARD, FONT_MICRO)
    center(draw, "RESOLVED | ABSTAIN | BLOCKED", y1 + 245, FONT_MED, WHITE)
    center(draw, "handled deterministically from structure", y1 + 430, FONT_TINY, ACCENT)


def artifact_slide(title, renderer, caption="", duration=6.0):
    img = canvas()
    draw = ImageDraw.Draw(img)
    center_multiline(draw, title, 34, FONT_MED, GOLD, max_chars=48, bottom=92)
    box = (70, 96, 1210, 600)
    panel(draw, box, outline=GOLD, fill=PANEL_DARK, width=4, radius=18)
    renderer(draw, box)
    if caption:
        f = fit_font_for_width(draw, caption, 22, WIDTH - 160, True, 15)
        center(draw, caption, 615, f, ACCENT)
    draw_footer(draw)
    return img, duration

def tools_vs_resolution_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "Tools Render. Structure Resolves.", 52, FONT_TITLE, GOLD)
    panel(draw, (65, 155, 1215, 515), outline=ACCENT, fill=PANEL_DARK, width=4)
    rows = [("Drawing tools", "help create visuals"), ("STRUMER-D", "defines when a diagram may become visible"), ("Renderer", "displays resolved output"), ("Structure", "determines correctness")]
    y = 210
    for left, right in rows:
        left_font = fit_font_for_width(draw, left, 34, 300, True, 24)
        right_font = fit_font_for_width(draw, right, 32, 570, True, 23)
        draw.text((130, y), left, font=left_font, fill=GOLD)
        draw.text((475, y), "->", font=FONT_MED, fill=ACCENT)
        draw.text((545, y), right, font=right_font, fill=WHITE)
        y += 68
    draw_footer(draw)
    return img, 6.4


def failure_safety_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "Structural Safety", 52, FONT_TITLE, GOLD)
    items = [("RESOLVED", "complete + consistent -> diagram visible", ACCENT), ("ABSTAIN", "incomplete -> no forced output", ORANGE), ("BLOCKED", "conflicting -> no arbitrary diagram", RED)]
    y = 170
    for state, note, color in items:
        panel(draw, (125, y, 1155, y + 85), outline=color, fill=PANEL_DARK, width=4)
        draw.text((170, y + 24), state, font=FONT_MED, fill=color)
        draw.text((430, y + 27), note, font=FONT_SMALL, fill=WHITE)
        y += 112
    center(draw, "The system refuses invalid visibility.", 535, FONT_SMALL, GOLD)
    draw_footer(draw)
    return img, 6.4


def structural_diagram_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "Structural Resolution Model", 48, FONT_TITLE, GOLD)
    boxes = [((120, 170, 390, 245), "Structure"), ((505, 170, 775, 245), "Completeness"), ((890, 170, 1160, 245), "Consistency"), ((320, 360, 590, 435), "Resolution"), ((700, 360, 970, 435), "Visibility")]
    for box, label in boxes:
        draw_node(draw, box, label, ACCENT, PANEL_DARK, FONT_NODE)
    draw.line((390, 207, 505, 207), fill=GOLD, width=5)
    draw.polygon([(505, 207), (486, 195), (486, 219)], fill=GOLD)
    draw.line((775, 207, 890, 207), fill=GOLD, width=5)
    draw.polygon([(890, 207), (871, 195), (871, 219)], fill=GOLD)
    draw.line((640, 245, 455, 360), fill=GOLD, width=5)
    draw.line((640, 245, 835, 360), fill=GOLD, width=5)
    draw.line((590, 397, 700, 397), fill=GOLD, width=5)
    draw.polygon([(700, 397), (681, 385), (681, 409)], fill=GOLD)
    center(draw, "No manual assembly. Visibility follows structural maturity.", 520, FONT_SMALL, ACCENT)
    draw_footer(draw)
    return img, 6.6


def strumer_d_identity_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "STRUMER-D Identity", 54, FONT_TITLE, GOLD)
    panel(draw, (90, 145, 1190, 505), outline=GOLD, fill=PANEL_DARK, width=4)
    lines = [("diagram != drawing", GOLD), ("diagram = resolve(structure)", ACCENT), ("diagram_visible iff structure_complete AND structure_consistent", WHITE), ("same structure -> same diagram -> same signature", TEAL)]
    y = 205
    for text, color in lines:
        f = fit_font_for_width(draw, text, 34, 1000, True, 21)
        center(draw, text, y, f, color)
        y += 70
    draw_footer(draw)
    return img, 6.6


def lineage_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center(draw, "STRUMER Lineage", 52, FONT_TITLE, GOLD)
    panel(draw, (115, 160, 1165, 500), outline=ACCENT, fill=PANEL_DARK, width=4)
    center(draw, "STRUMER", 210, FONT_MED, GOLD)
    center(draw, "Video without editing", 260, FONT_SMALL, WHITE)
    center(draw, "->", 320, FONT_MED, ACCENT)
    center(draw, "STRUMER-D", 365, FONT_MED, GOLD)
    center(draw, "Diagrams without drawing", 415, FONT_SMALL, WHITE)
    draw_footer(draw)
    return img, 6.0


def final_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    center_multiline(draw, "Diagrams are not drawn", 72, FONT_TITLE, GOLD, gap=14, max_chars=36, bottom=155)
    center_multiline(draw, "They are resolved from structure.", 185, FONT_MED, ACCENT, gap=12, max_chars=42, bottom=260)
    panel(draw, (155, 315, 1125, 505), outline=GOLD, fill=PANEL_DARK, width=4, radius=24)
    center(draw, "Join the Structural Revolution", 350, FONT_TITLE, GOLD)
    center(draw, "STRUMER-D | Structural Diagram Resolution", 430, FONT_SMALL, ACCENT)
    center(draw, "Part of the Shunyaya Framework", 585, FONT_MED, WHITE)
    return img, 8.0


def build_slides():
    slides = []
    slides.append(title_slide("What if diagrams\ndid not require drawing?", "What if structure alone\nwas enough?", 6.0))
    slides.append(title_slide("This entire video\nwas generated from structure.", "No drawing.\nNo tools.\nNo manual placement.", 6.2))
    slides.append(two_line_slide("You are not drawing", "You are defining", 4.8))
    slides.append(title_slide("No drawing tool\nNo layout tuning\nNo manual placement", "Yet you are seeing complete diagrams.", 5.8))
    slides.append(title_slide("This video is structure-first", "The same principle that resolves diagrams\nalso resolves the video you are watching.", 6.0))
    slides.append(structure_reveals_video_slide())
    slides.append(before_after_slide())
    slides.append(title_slide("A tiny script", "Generated every diagram shown here.", 4.8))
    slides.append(simple_code_slide("Smallest visible unit", 'diagram("Hello")', "This creates one diagram unit.", 5.5))
    slides.append(simple_code_slide("One node. One relation.", 'diagram("Your node",\n        "Your relation")', "Change structure -> diagram changes.", 5.8))
    slides.append(simple_code_slide("Define the diagram", '''diagram = {
  "type": "flowchart",
  "nodes": ["Request", "Gateway", "Logic", "Store"],
  "edges": ["Request -> Gateway",
            "Gateway -> Logic",
            "Logic -> Store"]
}''', "Structure defines the visible diagram.", 7.0))
    slides.append(simple_code_slide("Resolve the structure", "resolve(diagram)", "Structure -> Output", 4.8))
    slides.append(title_slide("You just created a diagram", "Structure -> Output", 4.8))
    slides.append(live_diagram_proof_slide())
    slides.append(structure_to_diagram_slide())
    slides.append(structure_to_diagram_reveal_slide())
    slides.append(title_slide("The system does not guess", "Structure resolves only what the definition allows.", 4.8))
    slides.append(storage_reveal_slide())
    slides.append(two_line_slide("Structure remains", "Content evolves", 4.8))
    slides.append(determinism_slide())
    slides.append(run_proof_slide())
    slides.append(change_one_node_slide())
    slides.append(simplified_flowchart_slide())
    slides.append(artifact_slide("Generated Flowchart Artifact", draw_artifact_flowchart, "Artifact view: full STRUMER-D generated output", 6.0))
    slides.append(simplified_mindmap_slide())
    slides.append(artifact_slide("Generated Mind Map Artifact", draw_artifact_mindmap, "Artifact view: full STRUMER-D generated output", 6.0))
    slides.append(artifact_slide("Sequence Diagram Resolved From Structure", draw_artifact_sequence, "", 6.0))
    slides.append(artifact_slide("Polygon Resolved From Structure", draw_artifact_polygon, "", 6.0))
    slides.append(title_slide("No manual placement", "No dragging.\nNo alignment repair.\nNo repeated correction.", 5.4))
    slides.append(title_slide("Old thinking", "Build the diagram step by step.", 4.8))
    slides.append(title_slide("Structural thinking", "Define once.\nLet structure resolve the visible form.", 5.4))
    slides.append(strumer_d_identity_slide())
    slides.append(principle_slide("The Core Law", "diagram_visible iff structure_complete AND structure_consistent", 5.8))
    slides.append(structural_diagram_slide())
    slides.append(failure_safety_slide())
    slides.append(artifact_slide("One Resolver. Multiple Domains.", draw_artifact_overview, "RESOLVED | ABSTAIN | BLOCKED -- handled deterministically", 6.4))
    slides.append(tools_vs_resolution_slide())
    slides.append(title_slide("AI and STRUMER-D", "AI interprets intent.\nSTRUMER-D resolves structure.\nDifferent problems. Different layers.", 6.0))
    slides.append(title_slide("AI optimizes creativity", "STRUMER-D optimizes control.", 4.8))
    slides.append(title_slide("Structure-based creation", "Diagrams today.\nMedia, systems, and automation tomorrow.", 6.0))
    slides.append(title_slide("Diagrams are not drawn", "They are resolved from structure.", 5.2))
    slides.append(lineage_slide())
    slides.append(final_slide())
    return slides


def to_bgr(img):
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def write_hold(writer, img, duration):
    frame = to_bgr(img)
    for _ in range(max(1, int(duration * FPS))):
        writer.write(frame)


def write_fade(writer, img1, img2):
    a = np.array(img1).astype(np.float32)
    b = np.array(img2).astype(np.float32)
    steps = max(1, int(FADE_SECONDS * FPS))
    for i in range(steps):
        t = (i + 1) / steps
        frame = (a * (1 - t) + b * t).astype(np.uint8)
        writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))


def build():
    slides = build_slides()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(OUTFILE, fourcc, FPS, (WIDTH, HEIGHT))
    if not writer.isOpened():
        raise RuntimeError("Could not open video writer. Check OpenCV MP4 support.")
    prev = None
    for img, duration in slides:
        if prev is not None:
            write_fade(writer, prev, img)
        write_hold(writer, img, duration)
        prev = img
    writer.release()
    total_seconds = sum(d for _, d in slides) + max(0, len(slides) - 1) * FADE_SECONDS
    print("STRUMER-D Video v" + VERSION)
    print("Created:", OUTFILE)
    print("Total slides:", len(slides))
    print("Estimated duration:", f"{total_seconds / 60:.1f} minutes")


if __name__ == "__main__":
    build()
