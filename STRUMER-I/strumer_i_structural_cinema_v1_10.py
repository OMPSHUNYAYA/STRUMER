#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2
import numpy as np
import hashlib
import math
import os
from copy import deepcopy

VERSION = "1.10"
WIDTH = 1600
HEIGHT = 900
FPS = 24

OUT_VIDEO = "STRUMER_I_Structural_Cinema_v1_10.mp4"
OUT_POSTER = "STRUMER_I_Structural_Cinema_Poster_v1_10.png"
OUT_VERIFY = "STRUMER_I_Structural_Cinema_VERIFY_v1_10.txt"

WHITE = (248, 251, 255)
MUTED = (184, 204, 230)
GOLD = (255, 212, 102)
ACCENT = (86, 244, 216)
BLUE = (94, 158, 255)
RED = (255, 86, 108)
ORANGE = (255, 170, 70)
GREEN = (80, 226, 142)
PURPLE = (182, 132, 255)
LINE = (70, 94, 135)
PANEL = (8, 15, 28)
REPO_HOME = "github.com/OMPSHUNYAYA"


def load_font(size, bold=False):
    try:
        if os.name == "nt":
            path = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
        else:
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def text_size(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0], b[3] - b[1]


def fit_font(draw, text, start, max_width, min_size=18, bold=True):
    size = start
    while size >= min_size:
        font = load_font(size, bold)
        if text_size(draw, text, font)[0] <= max_width:
            return font
        size -= 2
    return load_font(min_size, bold)


def center(draw, text, y, font, color=WHITE):
    w, _ = text_size(draw, text, font)
    draw.text(((WIDTH - w) // 2, y), text, font=font, fill=color)


def center_fit(draw, text, y, max_width, start_size, color=WHITE, min_size=18):
    font = fit_font(draw, text, start_size, max_width, min_size, True)
    center(draw, text, y, font, color)


def center_box(draw, text, box, y, start_size, color=WHITE, min_size=18):
    font = fit_font(draw, text, start_size, box[2] - box[0] - 48, min_size, True)
    w, _ = text_size(draw, text, font)
    draw.text((box[0] + (box[2] - box[0] - w) // 2, y), text, font=font, fill=color)


def panel(draw, box, fill=PANEL, outline=LINE, width=2, radius=28):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def gradient(top=(3, 7, 14), mid=(8, 22, 42), bottom=(12, 36, 60)):
    img = Image.new("RGB", (WIDTH, HEIGHT), top)
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        if t < 0.56:
            p = t / 0.56
            c = tuple(int(top[i] + (mid[i] - top[i]) * p) for i in range(3))
        else:
            p = (t - 0.56) / 0.44
            c = tuple(int(mid[i] + (bottom[i] - mid[i]) * p) for i in range(3))
        draw.line((0, y, WIDTH, y), fill=c)
    return img


def add_vignette(img, strength=80):
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for i in range(14):
        a = int(strength * (i / 14) ** 2)
        draw.rectangle((i * 18, i * 12, WIDTH - i * 18, HEIGHT - i * 12), outline=(0, 0, 0, a), width=24)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def particles(img, t, count=20, color=ACCENT):
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    rng = np.random.default_rng(18001 + int(t * 4000) + color[0] * 7)
    for _ in range(count):
        x = int(rng.integers(90, WIDTH - 90))
        y = int(rng.integers(90, 660))
        r = int(rng.integers(2, 5))
        a = int(rng.integers(35, 110))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(color[0], color[1], color[2], a))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def sweep(img, t, color=ACCENT):
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x = int(-300 + (WIDTH + 600) * t)
    for i in range(60):
        a = max(0, 24 - i // 3)
        draw.line((x + i * 6, 0, x - 260 + i * 6, 700), fill=(color[0], color[1], color[2], a), width=2)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def subtle_problem_motion(img, t, box):
    x1, y1, x2, y2 = box
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    phase = (math.sin(t * math.pi * 2.0) + 1) / 2
    dx = int(-18 + phase * 36)
    dy = int(8 * math.sin(t * math.pi * 4.0))

    ghost = (x1 + 170 + dx, y1 + 115 + dy, x1 + 370 + dx, y1 + 170 + dy)
    draw.rounded_rectangle(ghost, radius=14, outline=(255, 170, 70, 150), width=3)
    draw.line((ghost[0] - 35, ghost[1] + 26, ghost[0] - 5, ghost[1] + 26), fill=(255, 86, 108, 130), width=3)
    draw.line((ghost[2] + 5, ghost[1] + 26, ghost[2] + 35, ghost[1] + 26), fill=(255, 86, 108, 130), width=3)

    for i, yy in enumerate([360, 400, 440, 480]):
        p = (t * 1.1 + i * 0.22) % 1.0
        alpha = int(40 + 90 * (1 - abs(p - 0.5) * 2))
        draw.rounded_rectangle((x1 + 64, yy - 6, x2 - 64, yy + 32), radius=10, outline=(255, 86, 108, alpha), width=2)

    layer = layer.filter(ImageFilter.GaussianBlur(0.4))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def pulse_ring(draw, x, y, t, color=ACCENT):
    for i in range(4):
        r = int(26 + i * 18 + 10 * math.sin(t * math.pi * 2 + i))
        draw.ellipse((x - r, y - r, x + r, y + r), outline=color, width=2)


def scan_beam(draw, box, t, color=ACCENT):
    x1, y1, x2, y2 = box
    if t <= 0.08 or t >= 0.94:
        return
    p = (t - 0.08) / 0.86
    x = int(x1 + (x2 - x1) * p)
    for i in range(9):
        a = max(25, 135 - i * 14)
        draw.line((x - i * 6, y1 + 16, x - i * 6, y2 - 16), fill=(color[0], color[1], color[2], a), width=2)
    draw.line((x, y1 + 14, x, y2 - 14), fill=color, width=3)


def arrow(draw, x1, y1, x2, y2, color=GOLD, progress=1.0):
    mx = int(x1 + (x2 - x1) * progress)
    my = int(y1 + (y2 - y1) * progress)
    draw.line((x1, y1, mx, my), fill=color, width=7)
    if progress > 0.92:
        ang = math.atan2(y2 - y1, x2 - x1)
        p1 = (x2, y2)
        p2 = (int(x2 - 30 * math.cos(ang - 0.45)), int(y2 - 30 * math.sin(ang - 0.45)))
        p3 = (int(x2 - 30 * math.cos(ang + 0.45)), int(y2 - 30 * math.sin(ang + 0.45)))
        draw.polygon([p1, p2, p3], fill=color)


def title(draw, main, sub=None, size=68):
    center_fit(draw, main, 54, 1450, size, GOLD, 34)
    if sub:
        center_fit(draw, sub, 148, 1400, 48, WHITE, 26)


def punch(draw, text, y, color=ACCENT):
    box = (275, y - 24, 1325, y + 48)
    panel(draw, box, fill=(6, 12, 24), outline=color, width=3, radius=18)
    center_box(draw, text, box, y - 1, 30, WHITE, 18)


def canonical_text(v):
    if isinstance(v, dict):
        return "{" + "|".join(str(k) + "=" + canonical_text(v[k]) for k in sorted(v)) + "}"
    if isinstance(v, list):
        return "[" + "|".join(canonical_text(x) for x in v) + "]"
    return str(v)


def sha256_hex(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def structure_base():
    return {
        "title": "New Product Launch",
        "panel_width": 680,
        "left_x": 520,
        "right_x": 1080,
        "complete": True,
        "consistent": True,
    }


def structure_changed():
    s = deepcopy(structure_base())
    s["title"] = "Launch Visual Updated"
    s["panel_width"] = 830
    s["left_x"] = 470
    s["right_x"] = 1130
    return s


def structure_incomplete():
    s = deepcopy(structure_base())
    s["complete"] = False
    return s


def structure_conflict():
    s = deepcopy(structure_base())
    s["consistent"] = False
    s["left_x"] = 800
    s["right_x"] = 800
    return s


def state(s):
    if not s.get("complete"):
        return "INCOMPLETE"
    if not s.get("consistent"):
        return "CONFLICT"
    return "RESOLVED"


def cert(s):
    return sha256_hex(canonical_text(s))[:16]


def draw_mini_image(draw, s, box, reveal=1.0, label=False):
    x1, y1, x2, y2 = box
    st = state(s)

    if st != "RESOLVED":
        c = ORANGE if st == "INCOMPLETE" else RED
        panel(draw, box, fill=(8, 13, 26), outline=c, width=4, radius=26)
        center_box(draw, "NO IMAGE", box, y1 + 70, 38, RED, 24)
        center_box(draw, st, box, y1 + 140, 32, c, 20)
        return

    panel(draw, box, fill=(7, 14, 27), outline=ACCENT, width=4, radius=26)

    if reveal > 0.12:
        center_box(draw, s["title"], box, y1 + 32, 28, GOLD, 18)

    if reveal > 0.28:
        cx = (x1 + x2) // 2
        py = y1 + 160
        pw = min(int(s["panel_width"] * 0.50), x2 - x1 - 110)
        panel(draw, (cx - pw // 2, py - 44, cx + pw // 2, py + 44), fill=(14, 31, 56), outline=BLUE, width=3, radius=18)

    if reveal > 0.46:
        for px0, c in [(s["left_x"], GOLD), (s["right_x"], ACCENT)]:
            px = int(x1 + (px0 - 360) * (x2 - x1) / 880)
            for rr in [42, 34, 26]:
                draw.ellipse((px - rr, y1 + 160 - rr, px + rr, y1 + 160 + rr), outline=c, width=1)
            draw.ellipse((px - 23, y1 + 160 - 23, px + 23, y1 + 160 + 23), fill=c, outline=WHITE, width=3)

    if label and reveal > 0.72:
        center_box(draw, "same image", box, y2 - 48, 24, WHITE, 16)


def draw_structure_panel(draw, box, lines, reveal=1.0):
    panel(draw, box, fill=(7, 14, 27), outline=ACCENT, width=4, radius=28)
    center_box(draw, "STRUCTURE", box, box[1] + 34, 34, ACCENT, 20)
    max_lines = int(len(lines) * reveal + 0.999)
    y = box[1] + 118
    for line in lines[:max_lines]:
        row = (box[0] + 55, y - 8, box[2] - 55, y + 42)
        panel(draw, row, fill=(10, 20, 36), outline=(48, 72, 106), width=1, radius=10)
        center_box(draw, line, row, y + 3, 24, WHITE, 16)
        y += 66


def slide_1(t):
    img = gradient((4, 6, 12), (9, 19, 36), (14, 30, 50))
    draw = ImageDraw.Draw(img)
    title(draw, "THE EVERYDAY PROBLEM", "One small change restarts the work.", 68)

    left = (150, 260, 715, 535)
    right = (885, 260, 1450, 535)
    panel(draw, left, fill=(26, 12, 24), outline=RED, width=4, radius=32)
    panel(draw, right, fill=(8, 28, 27), outline=ACCENT, width=4, radius=32)

    center_box(draw, "USUAL WAY", left, 305, 38, RED, 22)
    for i, word in enumerate(["Move", "Resize", "Fix", "Export again"]):
        center_box(draw, word, left, 370 + i * 40, 28, WHITE if i < 3 else ORANGE, 18)

    center_box(draw, "STRUMER-I", right, 305, 38, ACCENT, 22)
    for i, word in enumerate(["Change structure", "Run again", "Same rules", "New image"]):
        center_box(draw, word, right, 370 + i * 40, 28, WHITE if i < 3 else GOLD, 18)

    punch(draw, "Why rebuild from scratch when structure can evolve?", 650, ACCENT)

    img = subtle_problem_motion(img, t, left)
    return add_vignette(particles(sweep(img, t, GOLD), t, 20, ORANGE), 76)


def slide_2(t):
    img = gradient((7, 5, 13), (22, 14, 32), (38, 18, 40))
    draw = ImageDraw.Draw(img)
    title(draw, "THE SHIFT", "Images Without Manual Construction", 72)

    center_fit(draw, "The image is not assembled.", 255, 1380, 58, ACCENT, 32)
    center_fit(draw, "It is revealed.", 355, 1380, 76, GOLD, 40)
    center_fit(draw, "when the structure is complete and consistent.", 485, 1320, 34, WHITE, 20)
    punch(draw, "Complete structure -> visible image", 650, ACCENT)
    return add_vignette(particles(sweep(img, t, ORANGE), t, 20, ORANGE), 94)


def slide_3(t):
    img = gradient((3, 7, 14), (7, 24, 42), (8, 44, 58))
    draw = ImageDraw.Draw(img)
    title(draw, "THE LAW", "One rule across structural media.", 70)

    box = (260, 285, 1340, 465)
    panel(draw, box, fill=(7, 18, 31), outline=ACCENT, width=5, radius=32)
    center_box(draw, "image_output = resolve(structure)", box, 350, 48, ACCENT, 26)

    center_fit(draw, "Rendering shows it.", 535, 1400, 38, WHITE, 24)
    center_fit(draw, "Structure determines it.", 595, 1400, 42, GOLD, 24)
    return add_vignette(particles(sweep(img, t, ACCENT), t, 24, ACCENT), 82)


def slide_4(t):
    img = gradient((3, 7, 14), (8, 18, 38), (10, 30, 54))
    draw = ImageDraw.Draw(img)
    title(draw, "THE STRUMER FAMILY", "Video. Diagrams. Audio. Images.", 64)

    steps = [("VIDEO", BLUE), ("DIAGRAMS", ACCENT), ("AUDIO", GOLD), ("IMAGES", GREEN)]
    x = 150
    y = 315
    for i, (step, col) in enumerate(steps):
        box = (x, y, x + 265, y + 120)
        panel(draw, box, fill=(8, 16, 30), outline=col, width=4, radius=24)
        center_box(draw, step, box, y + 45, 32, col, 18)
        if i < len(steps) - 1:
            arrow(draw, x + 280, y + 60, x + 340, y + 60, LINE, min(1, t * 1.3))
        x += 330

    punch(draw, "Different outputs. Same structural principle.", 640, GOLD)
    return add_vignette(particles(sweep(img, t, PURPLE), t, 24, GOLD), 80)


def slide_5(t):
    img = gradient()
    draw = ImageDraw.Draw(img)
    title(draw, "WATCH IT WORK", "Structure enters. Image appears.", 62)

    rows = ["title", "panel", "badges", "visibility"]
    draw_structure_panel(draw, (120, 225, 670, 605), rows, reveal=max(0.2, t))
    arrow(draw, 720, 415, 880, 415, GOLD, min(1, t * 1.25))
    draw_mini_image(draw, structure_base(), (930, 225, 1480, 605), reveal=t, label=False)
    scan_beam(draw, (930, 225, 1480, 605), t, ACCENT)
    pulse_ring(draw, 800, 415, t, GOLD)

    punch(draw, "No manual layout loop.", 660, ACCENT)
    return add_vignette(particles(sweep(img, t, ACCENT), t, 20, ACCENT), 82)


def slide_6(t):
    img = gradient((3, 7, 14), (10, 25, 45), (12, 38, 56))
    draw = ImageDraw.Draw(img)
    title(draw, "REPLAY IT", "Same structure. Same image.", 66)

    draw_mini_image(draw, structure_base(), (125, 235, 690, 560), reveal=1.0, label=False)
    draw_mini_image(draw, deepcopy(structure_base()), (910, 235, 1475, 560), reveal=1.0, label=False)
    arrow(draw, 725, 398, 875, 398, ACCENT, min(1, t * 1.3))
    scan_beam(draw, (125, 235, 690, 560), t, ACCENT)
    scan_beam(draw, (910, 235, 1475, 560), t, ACCENT)

    center_fit(draw, "certificate: " + cert(structure_base()), 595, 1360, 26, WHITE, 16)
    punch(draw, "Same structure -> same proof.", 670, GOLD)
    return add_vignette(particles(sweep(img, t, BLUE), t, 20, BLUE), 82)


def slide_7(t):
    img = gradient((4, 7, 14), (18, 18, 42), (26, 22, 50))
    draw = ImageDraw.Draw(img)
    title(draw, "CHANGE IT", "Only the structure changes.", 66)

    draw_mini_image(draw, structure_base(), (110, 235, 690, 560), reveal=1.0, label=False)
    draw_mini_image(draw, structure_changed(), (910, 235, 1490, 560), reveal=min(1, 0.35 + t), label=False)
    arrow(draw, 725, 398, 875, 398, PURPLE, min(1, t * 1.3))

    center_fit(draw, "Old image", 340, 590, 28, WHITE, 16)
    center_fit(draw, "Updated image", 1080, 590, 28, PURPLE, 16)
    punch(draw, "Small structural change -> new deterministic image.", 670, PURPLE)
    return add_vignette(particles(sweep(img, t, PURPLE), t, 22, PURPLE), 88)


def slide_8(t):
    img = gradient((7, 5, 12), (22, 12, 28), (38, 14, 34))
    draw = ImageDraw.Draw(img)
    title(draw, "NO FORCED IMAGE", "If structure is not ready, visibility is blocked.", 60)

    draw_mini_image(draw, structure_incomplete(), (165, 255, 720, 545), reveal=1.0, label=False)
    draw_mini_image(draw, structure_conflict(), (880, 255, 1435, 545), reveal=1.0, label=False)

    scan_beam(draw, (165, 255, 720, 545), t, ORANGE)
    scan_beam(draw, (880, 255, 1435, 545), t, RED)
    pulse_ring(draw, 800, 400, t, RED)

    punch(draw, "No arbitrary output.", 660, RED)
    return add_vignette(particles(sweep(img, t, RED), t, 22, RED), 96)


def slide_9(t):
    img = gradient((3, 7, 14), (8, 23, 42), (9, 42, 52))
    draw = ImageDraw.Draw(img)
    title(draw, "WHY THIS MATTERS", "For creators, builders, and teams.", 64)

    items = [("Create", BLUE), ("Reuse", ACCENT), ("Change", GOLD), ("Verify", GREEN)]
    x = 210
    y = 300
    for i, (label, color) in enumerate(items):
        box = (x, y, x + 235, y + 135)
        panel(draw, box, fill=(8, 16, 30), outline=color, width=4, radius=24)
        center_box(draw, label, box, y + 48, 32, WHITE, 18)
        if i < len(items) - 1:
            arrow(draw, x + 250, y + 68, x + 305, y + 68, LINE, min(1, t * 1.5))
        x += 315

    center_fit(draw, "Templates become reusable structural assets.", 515, 1350, 38, WHITE, 20)
    punch(draw, "Speed from reuse. Trust from replay.", 665, ACCENT)
    return add_vignette(particles(sweep(img, t, ACCENT), t, 22, ACCENT), 82)


def slide_10(t):
    img = gradient((3, 7, 14), (7, 18, 36), (9, 28, 52))
    draw = ImageDraw.Draw(img)
    title(draw, "SHUNYAYA CONNECTION", "Dependency removed. Correctness preserved.", 58)

    box = (280, 285, 1320, 470)
    panel(draw, box, fill=(6, 14, 32), outline=GOLD, width=4, radius=28)
    center_box(draw, "Remove manual construction", box, 332, 38, WHITE, 22)
    center_box(draw, "Preserve structural correctness", box, 398, 42, GOLD, 24)

    punch(draw, "If correctness survives removal, the dependency was not fundamental.", 640, ACCENT)
    return add_vignette(particles(sweep(img, t, GOLD), t, 22, ACCENT), 82)


def slide_11(t):
    img = gradient((4, 7, 14), (8, 20, 40), (10, 34, 58))
    draw = ImageDraw.Draw(img)
    title(draw, "PROOF TRAVELS WITH THE IMAGE", "Replay-verifiable image creation.", 62)

    box = (320, 250, 1280, 515)
    panel(draw, box, fill=(7, 14, 27), outline=ACCENT, width=5, radius=30)
    center_box(draw, "image certificate", box, 295, 38, ACCENT, 22)
    center_box(draw, cert(structure_base()), box, 372, 64, WHITE, 32)
    center_box(draw, "same structure. same image. same proof.", box, 470, 30, WHITE, 18)

    punch(draw, "Structure carries the proof.", 660, GOLD)
    return add_vignette(particles(sweep(img, t, ACCENT), t, 26, ACCENT), 82)


def slide_12(t):
    img = gradient((2, 5, 12), (8, 18, 38), (16, 32, 58))
    draw = ImageDraw.Draw(img)

    center_fit(draw, "DID YOU KNOW?", 78, 1400, 78, GOLD, 40)

    box = (250, 265, 1350, 520)
    panel(draw, box, fill=(7, 14, 27), outline=ACCENT, width=5, radius=36)
    center_box(draw, "This video was generated", box, 325, 54, WHITE, 30)
    center_box(draw, "by a tiny script.", box, 405, 64, GOLD, 34)

    center_fit(draw, "The same structure recreates the same output.", 580, 1380, 38, WHITE, 22)
    center_fit(draw, "No editor. No timeline. No manual reconstruction.", 640, 1380, 32, WHITE, 18)
    center_fit(draw, "See the description for the full script.", 705, 1380, 30, GOLD, 18)

    pulse_ring(draw, 800, 395, t, GOLD)
    return add_vignette(particles(sweep(img, t, GOLD), t, 30, ACCENT), 76)


def slide_13(t):
    img = gradient((2, 5, 12), (6, 16, 34), (10, 28, 52))
    draw = ImageDraw.Draw(img)

    center_fit(draw, "STRUMER-I", 58, 1400, 92, GOLD, 46)
    center_fit(draw, "Images Without Manual Construction", 148, 1400, 48, WHITE, 26)

    box = (250, 285, 1350, 555)
    panel(draw, box, fill=(7, 14, 27), outline=ACCENT, width=5, radius=34)
    center_box(draw, "image_output = resolve(structure)", box, 350, 48, ACCENT, 24)
    center_box(draw, "visible iff complete AND consistent", box, 415, 30, GOLD, 18)
    center_box(draw, "Create by structure. Reuse with confidence.", box, 500, 32, WHITE, 18)

    center_fit(draw, "Join the Structural Revolution", 625, 1400, 50, GOLD, 28)
    center_fit(draw, REPO_HOME, 705, 1400, 28, WHITE, 16)

    return add_vignette(particles(sweep(img, t, GOLD), t, 28, ACCENT), 76)


def poster_frame():
    img = gradient((2, 5, 12), (8, 22, 42), (12, 40, 62))
    draw = ImageDraw.Draw(img)

    center_fit(draw, "STRUMER-I", 64, 1400, 88, GOLD, 46)
    center_fit(draw, "Images Without Manual Construction", 158, 1450, 50, WHITE, 28)
    draw_mini_image(draw, structure_base(), (460, 290, 1140, 610), reveal=1.0, label=True)
    center_fit(draw, "same structure -> same image -> same certificate", 655, 1450, 32, WHITE, 18)
    center_fit(draw, "Join the Structural Revolution", 720, 1450, 40, GOLD, 22)
    center_fit(draw, REPO_HOME, 765, 1450, 26, WHITE, 16)

    return add_vignette(particles(img, 0.5, 28, ACCENT), 82)


def render_segment(fn, seconds):
    frames = []
    n = int(round(seconds * FPS))
    for i in range(n):
        t = 0 if n <= 1 else i / (n - 1)
        frames.append(fn(t))
    return frames


def fade(a, b, count):
    out = []
    aa = np.array(a).astype(np.float32)
    bb = np.array(b).astype(np.float32)
    for i in range(count):
        p = (i + 1) / count
        arr = (aa * (1 - p) + bb * p).clip(0, 255).astype(np.uint8)
        out.append(Image.fromarray(arr))
    return out


def build_video():
    timeline = [
        (slide_1, 7.0),
        (slide_2, 6.5),
        (slide_3, 6.4),
        (slide_4, 6.6),
        (slide_5, 7.0),
        (slide_6, 6.6),
        (slide_7, 6.6),
        (slide_8, 6.5),
        (slide_9, 6.5),
        (slide_10, 6.4),
        (slide_11, 6.4),
        (slide_12, 6.8),
        (slide_13, 7.2),
    ]

    writer = cv2.VideoWriter(OUT_VIDEO, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (WIDTH, HEIGHT))
    prev = None
    total = 0
    fade_frames = int(0.30 * FPS)

    for fn, seconds in timeline:
        frames = render_segment(fn, seconds)
        if prev is not None:
            for frame in fade(prev, frames[0], fade_frames):
                writer.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR))
                total += 1
        for frame in frames:
            writer.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR))
            total += 1
        prev = frames[-1]

    writer.release()
    return total


def write_verify(total):
    poster = poster_frame()
    poster.save(OUT_POSTER)

    b = structure_base()
    r = deepcopy(structure_base())
    c = structure_changed()
    inc = structure_incomplete()
    con = structure_conflict()

    with open(OUT_VERIFY, "w", encoding="utf-8") as f:
        f.write("STRUMER-I Structural Cinema v1.10 VERIFY\n")
        f.write("Images Without Manual Construction\n\n")
        f.write("Principle: image_output = resolve(structure)\n")
        f.write("Law: image_visible iff image_structure_complete AND image_structure_consistent\n")
        f.write("Generated by a tiny deterministic script.\n")
        f.write("Repository home: " + REPO_HOME + "\n\n")
        f.write("Video: " + OUT_VIDEO + "\n")
        f.write("Poster: " + OUT_POSTER + "\n")
        f.write("Frames: " + str(total) + "\n")
        f.write("FPS: " + str(FPS) + "\n")
        f.write("Resolution: " + str(WIDTH) + "x" + str(HEIGHT) + "\n")
        f.write("video_sha256: " + file_sha256(OUT_VIDEO) + "\n")
        f.write("poster_sha256: " + file_sha256(OUT_POSTER) + "\n\n")
        f.write("canonical_state: " + state(b) + "\n")
        f.write("repeat_state: " + state(r) + "\n")
        f.write("changed_state: " + state(c) + "\n")
        f.write("incomplete_state: " + state(inc) + "\n")
        f.write("conflict_state: " + state(con) + "\n\n")
        f.write("canonical_certificate: " + cert(b) + "\n")
        f.write("repeat_certificate: " + cert(r) + "\n")
        f.write("changed_certificate: " + cert(c) + "\n")
        f.write("incomplete_certificate: " + cert(inc) + "\n")
        f.write("conflict_certificate: " + cert(con) + "\n\n")
        f.write("same structure -> same certificate: " + str(cert(b) == cert(r)) + "\n")
        f.write("changed structure -> changed certificate: " + str(cert(b) != cert(c)) + "\n")
        f.write("incomplete structure -> visibility blocked: " + str(state(inc) == "INCOMPLETE") + "\n")
        f.write("conflicting structure -> no arbitrary visibility: " + str(state(con) == "CONFLICT") + "\n\n")
        f.write("Final line: Join the Structural Revolution\n")


def main():
    total = build_video()
    write_verify(total)

    print("STRUMER-I Structural Cinema v1.10")
    print("Created: " + OUT_VIDEO)
    print("Created: " + OUT_POSTER)
    print("Created: " + OUT_VERIFY)
    print("Principle: image_output = resolve(structure)")
    print("Law: image_visible iff image_structure_complete AND image_structure_consistent")
    print("same structure -> same image -> same certificate")
    print("Generated by a tiny deterministic script.")
    print("Join the Structural Revolution")


if __name__ == "__main__":
    main()
