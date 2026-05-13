#!/usr/bin/env python3

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2
import numpy as np
import hashlib
import math
import os

VERSION = "2.1"
WIDTH = 1600
HEIGHT = 900
OUTPUT_WIDTH = 1920
OUTPUT_HEIGHT = 1080
FPS = 24

OUT_VIDEO  = "STRUMER-Deterministic_v2_1.mp4"
OUT_POSTER = "STRUMER-Deterministic_v2_1_Poster.png"
OUT_VERIFY = "STRUMER-Deterministic_v2_1_VERIFY.txt"

WHITE  = (248, 251, 255)
MUTED  = (182, 198, 222)
GOLD   = (255, 204,  35)
CYAN   = ( 35, 214, 255)
BLUE   = ( 79, 168, 255)
GREEN  = (102, 255,  60)
RED    = (255,  64,  48)
ORANGE = (255, 128,  35)
PURPLE = (196, 105, 255)
YELLOW = (255, 215,  40)
AMBER  = (255, 160,  20)
BLACK  = (  2,   5,  12)
PANEL  = (  7,  12,  24)
LINE   = ( 80, 100, 130)

SLIDE_DURATIONS = [5.4, 5.0, 5.2, 5.0, 5.6, 5.2, 5.0, 5.8, 5.8, 5.8, 6.6]
TRANSITION_FRAMES = int(FPS * 0.38)

UI_LINE_Y = 820

def load_font(size, bold=True):
    try:
        if os.name == "nt":
            path = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
        else:
            path = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
                    else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def text_size(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0], b[3] - b[1]


def fit_font(draw, text, start, max_width, min_size=18, bold=True):
    size = start
    while size >= min_size:
        f = load_font(size, bold)
        if text_size(draw, text, f)[0] <= max_width:
            return f
        size -= 2
    return load_font(min_size, bold)


def draw_text(draw, xy, text, size, color=WHITE, bold=True, max_width=None, min_size=18):
    f = load_font(size, bold)
    if max_width is not None:
        f = fit_font(draw, text, size, max_width, min_size, bold)
    draw.text(xy, text, font=f, fill=color)
    return f


def center_text(draw, text, y, size, color=WHITE, bold=True, max_width=None, min_size=18):
    f = load_font(size, bold)
    if max_width is not None:
        f = fit_font(draw, text, size, max_width, min_size, bold)
    w, _ = text_size(draw, text, f)
    draw.text(((WIDTH - w) // 2, y), text, font=f, fill=color)
    return f


def center_in_box(draw, text, box, y, size, color=WHITE, bold=True, min_size=18):
    x1, _, x2, _ = box
    f = fit_font(draw, text, size, x2 - x1 - 40, min_size, bold)
    w, _ = text_size(draw, text, f)
    draw.text((x1 + (x2 - x1 - w) // 2, y), text, font=f, fill=color)
    return f

def panel(draw, box, fill=PANEL, outline=LINE, width=3, radius=28):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def gradient_bg(seed=1, primary=BLUE, secondary=CYAN, energy=0.45):
    img = Image.new("RGB", (WIDTH, HEIGHT), BLACK)
    pix = img.load()
    for y in range(HEIGHT):
        t = y / max(1, HEIGHT - 1)
        for x in range(WIDTH):
            u = x / max(1, WIDTH - 1)
            base = int(6 + 13 * (1 - t) + 8 * math.sin((u * 2.0 + t * 1.4 + seed) * math.pi) * energy)
            r = max(0, min(255, base + int(primary[0] * 0.05 * (1 - t)) + int(secondary[0] * 0.03 * u)))
            g = max(0, min(255, base + int(primary[1] * 0.05 * (1 - t)) + int(secondary[1] * 0.03 * u)))
            b = max(0, min(255, base + int(primary[2] * 0.07 * (1 - t)) + int(secondary[2] * 0.04 * u)))
            pix[x, y] = (r, g, b)
    return img


def add_vignette(img, strength=100):
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(26):
        alpha = int(strength * (i / 25) ** 2)
        draw.rectangle((i * 14, i * 10, WIDTH - i * 14, HEIGHT - i * 10),
                        outline=(0, 0, 0, alpha), width=22)
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def cinematic_bg(seed=1, primary=BLUE, secondary=CYAN, streaks=120, storm=False):
    img = gradient_bg(seed, primary, secondary, 0.36)
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    rng = np.random.default_rng(seed)
    cx = int(rng.integers(260, WIDTH - 260))
    cy = int(rng.integers(150, 500))
    for _ in range(streaks):
        a = int(rng.integers(18, 85))
        length = int(rng.integers(90, 410))
        x = int(rng.integers(-120, WIDTH + 120))
        y = int(rng.integers(40, 780))
        ang = math.atan2(y - cy, x - cx) + float(rng.normal(0, 0.10))
        x2 = int(x + math.cos(ang) * length)
        y2 = int(y + math.sin(ang) * length)
        col = primary if rng.random() > 0.36 else secondary
        draw.line((x, y, x2, y2), fill=(col[0], col[1], col[2], a),
                  width=int(rng.integers(1, 4)))
    if storm:
        for _ in range(14):
            x = int(rng.integers(820, 1510))
            y = int(rng.integers(80, 520))
            pts = [(x, y)]
            for _ in range(5):
                x += int(rng.integers(-70, 60))
                y += int(rng.integers(30, 72))
                pts.append((x, y))
            draw.line(pts, fill=(primary[0], primary[1], primary[2], 130), width=4)
            draw.line(pts, fill=(255, 255, 255, 60), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    return add_vignette(img, 115)

def glow_shape(base, draw_func, color, blur=18, repeat=2):
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    draw_func(d, (*color, 180))
    for _ in range(repeat):
        blurred = layer.filter(ImageFilter.GaussianBlur(blur))
        base = Image.alpha_composite(base.convert("RGBA"), blurred).convert("RGB")
    layer2 = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(layer2)
    draw_func(d2, (*color, 255))
    return Image.alpha_composite(base.convert("RGBA"), layer2).convert("RGB")


def simple_glow_icon(img, center, kind, color):
    cx, cy = center
    def f(d, rgba):
        if kind == "file":
            d.rounded_rectangle((cx-70, cy-95, cx+70, cy+95), radius=10, outline=rgba, width=6)
            d.line((cx+35, cy-95, cx+70, cy-60, cx+70, cy-95), fill=rgba, width=5)
            for yy in [-30, 12, 54]:
                d.line((cx-38, cy+yy, cx+42, cy+yy), fill=rgba, width=4)
        elif kind == "refresh":
            d.arc((cx-80, cy-80, cx+80, cy+80), 25, 310, fill=rgba, width=8)
            d.polygon([(cx+72, cy-56), (cx+106, cy-54), (cx+87, cy-25)], fill=rgba)
            d.arc((cx-80, cy-80, cx+80, cy+80), 205, 130, fill=rgba, width=8)
            d.polygon([(cx-72, cy+56), (cx-106, cy+54), (cx-87, cy+25)], fill=rgba)
        elif kind == "play":
            d.ellipse((cx-92, cy-92, cx+92, cy+92), outline=rgba, width=7)
            d.line((cx-30, cy-52, cx-30, cy+52, cx+56, cy, cx-30, cy-52), fill=rgba, width=7)
        elif kind == "growth":
            d.line((cx-74, cy+64, cx+82, cy+64), fill=rgba, width=5)
            for i, h in enumerate([40, 70, 105]):
                x = cx - 62 + i * 55
                d.rectangle((x, cy+62-h, x+28, cy+62), outline=rgba, width=6)
            d.line((cx-65, cy+8, cx+74, cy-104), fill=rgba, width=6)
            d.polygon([(cx+74, cy-104), (cx+48, cy-98), (cx+68, cy-76)], fill=rgba)
        elif kind == "code":
            d.rounded_rectangle((cx-82, cy-60, cx+82, cy+60), radius=16, outline=rgba, width=6)
            d.line((cx-44, cy-16, cx-82, cy+10, cx-44, cy+36), fill=rgba, width=5)
            d.line((cx+44, cy-16, cx+82, cy+10, cx+44, cy+36), fill=rgba, width=5)
            d.line((cx-12, cy+40, cx+24, cy-38), fill=rgba, width=5)
        elif kind == "shield":
            pts = [(cx, cy-90), (cx+80, cy-50), (cx+60, cy+50), (cx, cy+90),
                   (cx-60, cy+50), (cx-80, cy-50)]
            d.line(pts + [pts[0]], fill=rgba, width=7, joint="curve")
            d.line((cx-30, cy, cx-5, cy+28, cx+38, cy-28), fill=rgba, width=9)
        elif kind == "stack":
            for i, yoff in enumerate([-48, 0, 48]):
                d.rounded_rectangle((cx-72, cy+yoff-18, cx+72, cy+yoff+18),
                                     radius=8, outline=rgba, width=5)
        elif kind == "hash":
            d.line((cx-50, cy-28, cx+50, cy-28), fill=rgba, width=6)
            d.line((cx-50, cy+28, cx+50, cy+28), fill=rgba, width=6)
            d.line((cx-20, cy-52, cx-20, cy+52), fill=rgba, width=6)
            d.line((cx+20, cy-52, cx+20, cy+52), fill=rgba, width=6)
    return glow_shape(img, f, color, 14, 2)

def draw_number(draw, n, total=11):
    box = (26, 28, 82, 84)
    draw.rounded_rectangle(box, radius=8, fill=GOLD)
    f = load_font(36, True)
    w, h = text_size(draw, str(n), f)
    draw.text((box[0] + (box[2]-box[0]-w)//2, box[1] + (box[3]-box[1]-h)//2 - 3),
              str(n), font=f, fill=(10, 10, 12))
    label = f"{n} / {total}"
    fl = load_font(18, False)
    wl, _ = text_size(draw, label, fl)
    draw.text((WIDTH - wl - 36, 48), label, font=fl, fill=MUTED)


def draw_ui(draw, progress=0.2, duration="1:00:00"):
    y = UI_LINE_Y
    draw.line((34, y, WIDTH - 48, y), fill=(168, 176, 190), width=2)
    draw.line((34, y, 34 + int((WIDTH - 82) * progress), y), fill=RED, width=5)
    knob_x = 34 + int((WIDTH - 82) * progress)
    draw.ellipse((knob_x - 8, y - 8, knob_x + 8, y + 8), fill=RED)
    f = load_font(22, True)
    draw.polygon([(42, 858), (42, 828), (69, 843)], fill=WHITE)
    draw.polygon([(112, 858), (112, 828), (135, 843)], fill=WHITE)
    draw.rectangle((137, 828, 144, 858), fill=WHITE)
    draw.arc((196, 831, 232, 867), -35, 35, fill=WHITE, width=4)
    draw.polygon([(165, 840), (182, 828), (182, 858)], fill=WHITE)
    draw.text((260, 832), duration, font=f, fill=WHITE)
    for i, x in enumerate([1370, 1450, 1530]):
        if i == 0:
            draw.ellipse((x-12, 830, x+12, 854), outline=WHITE, width=4)
            draw.line((x-18, 842, x+18, 842), fill=WHITE, width=4)
            draw.line((x, 824, x, 860), fill=WHITE, width=4)
        elif i == 1:
            draw.rectangle((x-22, 826, x+22, 858), outline=WHITE, width=4)
        else:
            for sx, ex in [(x-24, x-5), (x+5, x+24)]:
                draw.line((sx, 826, ex, 826), fill=WHITE, width=4)
            draw.line((x-24, 826, x-24, 845), fill=WHITE, width=4)
            draw.line((x+24, 826, x+24, 845), fill=WHITE, width=4)
            for sx, ex in [(x-24, x-5), (x+5, x+24)]:
                draw.line((sx, 858, ex, 858), fill=WHITE, width=4)
            draw.line((x-24, 858, x-24, 839), fill=WHITE, width=4)
            draw.line((x+24, 858, x+24, 839), fill=WHITE, width=4)


def draw_play_icon(img, center=(1190, 305), scale=1.0, color=BLUE, text=None):
    cx, cy = center
    s = int(165 * scale)
    pts = [(cx - int(s * 0.48), cy - int(s * 0.70)),
           (cx - int(s * 0.48), cy + int(s * 0.70)),
           (cx + int(s * 0.66), cy)]
    def f(d, rgba):
        d.line([pts[0], pts[1], pts[2], pts[0]], fill=rgba,
               width=max(5, int(9 * scale)), joint="curve")
    img = glow_shape(img, f, color, 20, 2)
    draw = ImageDraw.Draw(img)
    if text:
        lines = text.split("\n")
        y = cy - int(40 * scale)
        for line in lines:
            font = fit_font(draw, line, int(42 * scale), int(s * 0.75), int(19 * scale), True)
            w, h = text_size(draw, line, font)
            draw.text((cx - w // 2 - int(8 * scale), y), line, font=font, fill=YELLOW)
            y += h + int(8 * scale)
    return img


def draw_bullet(draw, x, y, text, color=GREEN, size=34):
    f = load_font(size, True)
    draw.ellipse((x, y+6, x+28, y+34), outline=color, width=4)
    draw.line((x+7, y+21, x+13, y+29, x+23, y+11), fill=color, width=4)
    draw.text((x+48, y), text, font=f, fill=WHITE)


def draw_cross_bullet(draw, x, y, text, color=RED, size=34):
    f = load_font(size, True)
    draw.ellipse((x, y+6, x+28, y+34), outline=color, width=4)
    draw.line((x+8, y+14, x+21, y+27), fill=color, width=4)
    draw.line((x+21, y+14, x+8, y+27), fill=color, width=4)
    draw.text((x+48, y), text, font=f, fill=WHITE)


def draw_clock(img, center=(1160, 330), radius=150, color=RED):
    cx, cy = center
    def f(d, rgba):
        d.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline=rgba, width=8)
        d.line((cx, cy, cx, cy-radius+44), fill=rgba, width=9)
        d.line((cx, cy, cx+78, cy+74), fill=rgba, width=9)
        for i in range(12):
            a = math.pi * 2 * i / 12
            r1, r2 = radius - 25, radius - 9
            d.line((cx + math.sin(a)*r1, cy - math.cos(a)*r1,
                    cx + math.sin(a)*r2, cy - math.cos(a)*r2), fill=rgba, width=4)
    return glow_shape(img, f, color, 16, 2)


def draw_lightning(img, box=(1150, 125, 1480, 560), color=GREEN):
    x1, y1, x2, y2 = box
    pts = [(x1+150, y1), (x1+44, y1+205), (x1+142, y1+205), (x1+84, y2),
           (x2-34, y1+152), (x2-136, y1+152), (x2-72, y1)]
    def f(d, rgba):
        d.line(pts + [pts[0]], fill=rgba, width=10, joint="curve")
    return glow_shape(img, f, color, 22, 2)


def draw_shield(img, box=(1040, 210, 1390, 610), color=BLUE):
    x1, y1, x2, y2 = box
    pts = [(x1+160, y1), (x2, y1+60), (x2-40, y2-120),
           (x1+160, y2), (x1+40, y2-120), (x1, y1+60)]
    def f(d, rgba):
        d.line(pts + [pts[0]], fill=rgba, width=8, joint="curve")
        d.line((x1+100, y1+210, x1+155, y1+265, x2-75, y1+130), fill=rgba, width=14)
    return glow_shape(img, f, color, 18, 2)


def draw_globe(img, center=(1200, 410), r=180, color=BLUE):
    cx, cy = center
    def f(d, rgba):
        d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=rgba, width=5)
        for off in [-90, -45, 0, 45, 90]:
            d.arc((cx-r, cy-r+abs(off), cx+r, cy+r-abs(off)), 0, 360, fill=rgba, width=3)
        for off in [-95, -45, 0, 45, 95]:
            d.arc((cx-r+abs(off), cy-r, cx+r-abs(off), cy+r), 90, 270, fill=rgba, width=3)
            d.arc((cx-r+abs(off), cy-r, cx+r-abs(off), cy+r), -90, 90, fill=rgba, width=3)
    return glow_shape(img, f, color, 18, 2)


def draw_code_window(img, box=(1000, 210, 1420, 620), color=BLUE):
    x1, y1, x2, y2 = box
    def f(d, rgba):
        d.rounded_rectangle(box, radius=22, outline=rgba, width=6)
        d.line((x1, y1+62, x2, y1+62), fill=rgba, width=4)
        d.ellipse((x1+24, y1+24, x1+39, y1+39), fill=rgba)
        d.ellipse((x1+52, y1+24, x1+67, y1+39), fill=rgba)
        d.ellipse((x1+80, y1+24, x1+95, y1+39), fill=rgba)
        d.line((x1+120, y1+145, x1+65, y1+205, x1+120, y1+265), fill=rgba, width=7)
        d.line((x1+172, y1+145, x1+228, y1+205, x1+172, y1+265), fill=rgba, width=7)
        d.line((x1+260, y1+130, x1+365, y1+190, x1+260, y1+250, x1+260, y1+130), fill=rgba, width=7)
        d.line((x1+90, y2-95, x2-70, y2-95), fill=rgba, width=5)
        d.line((x1+90, y2-55, x2-120, y2-55), fill=rgba, width=5)
    return glow_shape(img, f, color, 17, 2)


def slide1():
    img = cinematic_bg(11, BLUE, CYAN, 180)
    draw = ImageDraw.Draw(img)
    draw_number(draw, 1)

    draw_text(draw, (155, 52), "DEFINE STRUCTURE.", 82, WHITE, True, max_width=880)
    draw_text(draw, (155, 150), "GET YOUR VIDEO.", 82, GOLD, True, max_width=880)
    draw_text(draw, (155, 248), "EVERY TIME.", 82, GOLD, True, max_width=880)

    draw.line((1135, 145, 1135, 455), fill=CYAN, width=3)

    draw.line((1190, 190, 1205, 205), fill=GREEN, width=6)
    draw.line((1205, 205, 1235, 170), fill=GREEN, width=6)
    draw_text(draw, (1250, 165), "Deterministic", 42, WHITE, True)

    draw.line((1190, 280, 1205, 295), fill=GREEN, width=6)
    draw.line((1205, 295, 1235, 260), fill=GREEN, width=6)
    draw_text(draw, (1250, 255), "Structural", 42, WHITE, True)

    draw.line((1190, 370, 1205, 385), fill=GREEN, width=6)
    draw.line((1205, 385, 1235, 350), fill=GREEN, width=6)
    draw_text(draw, (1250, 345), "Replayable", 42, WHITE, True)

    panel(draw, (90, 455, 1080, 690), fill=(7, 13, 25), outline=CYAN, width=4, radius=18)
    draw_text(draw, (130, 480), "video_output = resolve(structure)", 38, CYAN, False, max_width=900)
    draw.line((130, 535, 1030, 535), fill=LINE, width=1)
    draw_text(draw, (130, 555), "Same structure.", 50, WHITE, True, max_width=900)
    draw_text(draw, (130, 625), "Same output. Always.", 46, MUTED, True, max_width=900)

    draw_ui(draw, 0.09)
    return img


def slide2():
    img = cinematic_bg(21, RED, ORANGE, 120)
    img = draw_clock(img, (1160, 330), 150, RED)
    draw = ImageDraw.Draw(img)
    draw_number(draw, 2)

    draw_text(draw, (190, 52), "THE", 64, WHITE, True)
    draw_text(draw, (352, 52), "TRADITIONAL", 64, RED, True)
    draw_text(draw, (820, 52), "WAY", 64, WHITE, True)

    y = 190
    for item in [
        "MANUAL EDITING REQUIRED",
        "REPEATED ADJUSTMENTS",
        "VERSION CONFUSION",
        "HARD TO REPRODUCE",
        "TOOL-DEPENDENT OUTPUT",
    ]:
        draw_cross_bullet(draw, 190, y, item, RED, 34)
        y += 86

    draw_text(draw, (1040, 530), "Output depends", 30, MUTED, True)
    draw_text(draw, (1040, 568), "on editing process,", 30, MUTED, True)
    draw_text(draw, (1040, 606), "not on structure.", 30, RED, True)

    draw_ui(draw, 0.18)
    return img


def slide3():
    img = cinematic_bg(31, GREEN, CYAN, 130, True)
    img = draw_lightning(img, (1150, 125, 1480, 560), GREEN)
    draw = ImageDraw.Draw(img)
    draw_number(draw, 3)

    draw_text(draw, (190, 52), "THE", 64, WHITE, True)
    draw_text(draw, (355, 52), "STRUMER", 64, GREEN, True)
    draw_text(draw, (735, 52), "WAY", 64, WHITE, True)

    y = 178
    for item in [
        "DEFINE STRUCTURE ONCE",
        "REGENERATE DETERMINISTICALLY",
        "SAME STRUCTURE = SAME OUTPUT",
        "INSTANT REPLAY, ANY TIME",
        "REUSE ACROSS VERSIONS",
        "NO EDITING DEPENDENCY",
    ]:
        draw_bullet(draw, 190, y, item, GREEN, 33)
        y += 76

    draw_ui(draw, 0.27)
    return img


def slide4():
    img = cinematic_bg(41, BLUE, GREEN, 150)
    img = simple_glow_icon(img, (300, 330), "file", BLUE)
    img = simple_glow_icon(img, (800, 330), "refresh", YELLOW)
    img = simple_glow_icon(img, (1300, 330), "play", GREEN)
    draw = ImageDraw.Draw(img)
    draw_number(draw, 4)

    center_text(draw, "HOW IT WORKS", 62, 72, WHITE, True)

    draw.line((430, 330, 655, 330), fill=WHITE, width=5)
    draw.polygon([(655, 330), (620, 312), (620, 348)], fill=WHITE)
    draw.line((932, 330, 1157, 330), fill=WHITE, width=5)
    draw.polygon([(1157, 330), (1122, 312), (1122, 348)], fill=WHITE)

    for x, lines in [(178, ["1. DEFINE", "STRUCTURE"]),
                     (640, ["2. RESOLVE", "(REGENERATE)"]),
                     (1110, ["3. VIDEO", "BECOMES VISIBLE"])]:
        for i, line in enumerate(lines):
            draw_text(draw, (x, 520 + i * 48), line, 36, WHITE if i == 0 else MUTED, True)

    panel(draw, (110, 660, 1490, 730), fill=(4, 10, 22), outline=CYAN, width=2, radius=12)
    center_text(draw, "same structure  →  same video  →  same output signature", 676, 28, CYAN, False)

    draw_ui(draw, 0.36)
    return img


def slide5():
    img = cinematic_bg(51, PURPLE, AMBER, 110)
    draw = ImageDraw.Draw(img)
    draw_number(draw, 5)

    center_text(draw, "THREE STATES. NO SURPRISES.", 52, 58, WHITE, True)

    states = [
        ("RESOLVED", "Structure complete\n& consistent", GREEN,  (90,  150, 490, 680)),
        ("ABSTAIN",  "Structure\nincomplete",            YELLOW, (560, 150, 960, 680)),
        ("BLOCKED",  "Structure\nconflicting",           RED,    (1030, 150, 1490, 680)),
    ]
    for label, desc, color, box in states:
        x1, y1, x2, y2 = box
        cx = (x1 + x2) // 2
        panel(draw, box, fill=(8, 14, 26), outline=color, width=5, radius=22)

        fl = load_font(48, True)
        wl, _ = text_size(draw, label, fl)
        draw.text((cx - wl//2, y1 + 28), label, font=fl, fill=color)

        icon_y = y1 + 130
        if label == "RESOLVED":
            draw.line((cx-36, icon_y+28, cx-10, icon_y+58, cx+42, icon_y), fill=color, width=10)
        elif label == "ABSTAIN":
            draw.line((cx-38, icon_y+30, cx+38, icon_y+30), fill=color, width=10)
        else:
            draw.line((cx-34, icon_y, cx+34, icon_y+58), fill=color, width=10)
            draw.line((cx+34, icon_y, cx-34, icon_y+58), fill=color, width=10)

        for i, dline in enumerate(desc.split("\n")):
            fd = load_font(30, False)
            wd, _ = text_size(draw, dline, fd)
            draw.text((cx - wd//2, y1 + 230 + i * 44), dline, font=fd, fill=WHITE)

        outcomes = {"RESOLVED": "→ VIDEO GENERATED",
                    "ABSTAIN":  "→ NO OUTPUT FORCED",
                    "BLOCKED":  "→ NO OUTPUT ALLOWED"}
        fo = load_font(26, True)
        wo, _ = text_size(draw, outcomes[label], fo)
        draw.text((cx - wo//2, y2 - 72), outcomes[label], font=fo, fill=color)

    panel(draw, (110, 700, 1490, 760), fill=(4, 10, 22), outline=PURPLE, width=2, radius=10)
    center_text(draw, "incomplete → ABSTAIN    |    conflict → BLOCKED    |    complete → RESOLVED", 716, 26, MUTED, False)

    draw_ui(draw, 0.45)
    return img


def slide6():
    img = cinematic_bg(61, BLUE, CYAN, 170)
    img = draw_shield(img, (1040, 200, 1400, 620), BLUE)
    draw = ImageDraw.Draw(img)
    draw_number(draw, 6)

    draw_text(draw, (165, 58), "THE CORE GUARANTEE", 50, WHITE, True)
    draw_text(draw, (165, 168), "DETERMINISTIC", 80, CYAN, True)
    draw_text(draw, (165, 268), "REPRODUCIBILITY", 76, CYAN, True)
    draw.line((165, 400, 940, 400), fill=CYAN, width=3)

    items = [
        ("SAME STRUCTURE.", WHITE),
        ("SAME OUTPUT.", WHITE),
        ("EVERY RUN.", CYAN),
    ]
    y = 428
    for txt, col in items:
        draw_text(draw, (165, y), txt, 50, col, True)
        y += 70

    panel(draw, (165, 638, 870, 710), fill=(4, 10, 22), outline=CYAN, width=2, radius=10)
    draw_text(draw, (188, 654), "Verified by SHA-256 structure certificate.", 26, MUTED, False)

    draw_ui(draw, 0.54)
    return img


def slide7():
    img = cinematic_bg(71, PURPLE, CYAN, 130)
    icons = [
        ((220, 290), "refresh", GREEN),
        ((490, 290), "file",    BLUE),
        ((760, 290), "code",    PURPLE),
        ((1030, 290), "shield", GOLD),
        ((1340, 290), "stack",  CYAN),
    ]
    for center, kind, color in icons:
        img = simple_glow_icon(img, center, kind, color)
    draw = ImageDraw.Draw(img)
    draw_number(draw, 7)
    center_text(draw, "KEY ADVANTAGES", 58, 68, WHITE, True)

    labels = [
        ("REUSE",    "TEMPLATES"),
        ("EASY",     "UPDATES"),
        ("VERSION",  "CONTROL"),
        ("REDUCED",  "REWORK"),
        ("SCALE",    "EFFORTLESSLY"),
    ]
    xs = [220, 490, 760, 1030, 1340]
    for x, (a, b) in zip(xs, labels):
        fa = load_font(36, True);  fb = load_font(34, True)
        wa, _ = text_size(draw, a, fa);  wb, _ = text_size(draw, b, fb)
        draw.text((x - wa//2, 500), a, font=fa, fill=WHITE)
        draw.text((x - wb//2, 544), b, font=fb, fill=MUTED)

    panel(draw, (110, 620, 1490, 720), fill=(5, 10, 22), outline=PURPLE, width=2, radius=12)
    center_text(draw, "STRUMER  ·  STRUMER-D  ·  STRUMER-A  ·  STRUMER-I", 642, 34, PURPLE, True)
    center_text(draw, "Video  ·  Diagrams  ·  Audio  ·  Images — all structure-driven", 684, 24, MUTED, False)

    draw_ui(draw, 0.63)
    return img


def slide8():
    img = cinematic_bg(81, PURPLE, GREEN, 145)
    img = simple_glow_icon(img, (270, 290), "code",    PURPLE)
    img = simple_glow_icon(img, (800, 290), "refresh", GOLD)
    img = simple_glow_icon(img, (1340, 290), "growth", GREEN)
    draw = ImageDraw.Draw(img)
    draw_number(draw, 8)

    center_text(draw, "THIS VIDEO PROVES IT.", 58, 66, WHITE, True)
    draw.line((540, 178, 540, 620), fill=LINE, width=2)
    draw.line((1068, 178, 1068, 620), fill=LINE, width=2)

    col_data = [
        (270,  ["A SCRIPT",    "CREATED",      "THIS VIDEO."],   [PURPLE, WHITE, WHITE]),
        (800,  ["CHANGE",      "ONE LINE.",     "NEW VIDEO."],    [WHITE,  WHITE, GOLD]),
        (1340, ["SAME LINE.",  "SAME VIDEO.",   "EVERY TIME."],   [WHITE,  WHITE, GREEN]),
    ]
    for cx, lines, colors in col_data:
        y = 480
        for line, col in zip(lines, colors):
            f = load_font(36, True)
            w, _ = text_size(draw, line, f)
            draw.text((cx - w//2, y), line, font=f, fill=col)
            y += 52

    draw_ui(draw, 0.72)
    return img


def slide9():
    img = cinematic_bg(91, BLUE, CYAN, 160)
    img = draw_code_window(img, (1010, 160, 1460, 630), BLUE)
    draw = ImageDraw.Draw(img)
    draw_number(draw, 9)

    draw_text(draw, (150, 58),  "RUN THE",              56, WHITE, True)
    draw_text(draw, (150, 124), "SAME SCRIPT.",         56, GREEN, True)
    draw_text(draw, (150, 190), "GET THE SAME VIDEO.",  44, GREEN, True)

    draw.line((150, 286), fill=LINE, width=0)

    draw_text(draw, (150, 310), "STRUCTURE CERTIFICATE", 36, CYAN, True)
    panel(draw, (150, 358, 940, 430), fill=(4, 10, 22), outline=CYAN, width=2, radius=8)
    draw_text(draw, (174, 374),
              "SHA-256 fingerprint of the structure payload", 26, MUTED, False)

    draw_text(draw, (150, 458), "SAME SCRIPT.", 46, WHITE, True)
    draw_text(draw, (150, 516), "SAME CERTIFICATE.", 46, WHITE, True)
    draw_text(draw, (150, 574), "PROVABLY IDENTICAL.", 40, CYAN, True)

    panel(draw, (150, 646, 940, 718), fill=(4, 10, 22), outline=CYAN, width=2, radius=8)
    draw_text(draw, (174, 662),
              "video_output = resolve(structure)", 28, CYAN, False)

    draw_ui(draw, 0.81)
    return img


def slide10():
    img = cinematic_bg(101, BLUE, CYAN, 130)
    img = draw_globe(img, (1215, 370), 185, BLUE)
    draw = ImageDraw.Draw(img)
    draw_number(draw, 10)

    draw_text(draw, (148, 62),  "JOIN THE",   72, WHITE, True)
    draw_text(draw, (148, 152), "STRUCTURAL", 82, GOLD,  True)
    draw_text(draw, (148, 248), "REVOLUTION.", 80, GOLD, True)

    panel(draw, (110, 440, 950, 510), fill=(5, 13, 24), outline=CYAN, width=3, radius=10)
    draw_text(draw, (138, 456), "video_output = resolve(structure)", 30, CYAN, False)

    panel(draw, (110, 530, 950, 690), fill=(5, 13, 24), outline=CYAN, width=3, radius=10)
    draw_text(draw, (138, 548), "video_visible  iff", 28, CYAN, False)
    draw_text(draw, (138, 592), "  video_structure_complete", 28, CYAN, False)
    draw_text(draw, (138, 634), "  AND  video_structure_consistent", 28, CYAN, False)

    draw_ui(draw, 0.90)
    return img


def slide11():
    img = cinematic_bg(111, BLUE, ORANGE, 210)
    draw = ImageDraw.Draw(img)
    draw_number(draw, 11)

    center_text(draw, "STRUMER", 46, 122, WHITE, True, max_width=1100, min_size=60)
    center_text(draw, "STRUCTURAL MEDIA RESOLUTION", 192, 46, MUTED, True, max_width=1050)

    panel(draw, (500, 316, 1100, 396), fill=(5, 13, 24), outline=CYAN, width=3, radius=13)
    center_in_box(draw, "github.com/OMPSHUNYAYA/STRUMER", (500, 316, 1100, 396), 340, 34, WHITE, False, 22)

    center_text(draw, "STRUCTURE TODAY.", 450, 66, CYAN,  True)
    center_text(draw, "SCALE FOREVER.",   550, 80, GREEN, True)

    panel(draw, (120, 658, 1450, 736), fill=(4, 10, 22), outline=PURPLE, width=2, radius=10)
    center_text(draw, "STRUMER · STRUMER-D · STRUMER-A · STRUMER-I", 676, 30, PURPLE, True)

    center_text(draw,
        "Results vary by machine, runtime, and platform.",
        790, 18, MUTED, False)

    draw_ui(draw, 1.0)
    return img


SLIDE_BUILDERS = [
    slide1,   # 1  Define structure. Get your video.
    slide2,   # 2  The traditional way
    slide3,   # 3  The STRUMER way
    slide4,   # 4  How it works
    slide5,   # 5  RESOLVED / ABSTAIN / BLOCKED  (NEW)
    slide6,   # 6  Deterministic reproducibility
    slide7,   # 7  Key advantages + ecosystem
    slide8,   # 8  Self-referential proof
    slide9,   # 9  Certificate / SHA-256 verification
    slide10,  # 10 Join the structural revolution
    slide11,  # 11 CTA / outro
]

SLIDE_NAMES = [
    "Define Structure Get Your Video",
    "The Traditional Way",
    "The STRUMER Way",
    "How It Works",
    "Three States RESOLVED ABSTAIN BLOCKED",
    "Deterministic Reproducibility",
    "Key Advantages and Ecosystem",
    "Self-Referential Proof",
    "Certificate and Verification",
    "Join the Structural Revolution",
    "Structure Today Scale Forever",
]

def canonical_text(value):
    if isinstance(value, dict):
        return "{" + "|".join(str(k) + "=" + canonical_text(value[k]) for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + "|".join(canonical_text(x) for x in value) + "]"
    if isinstance(value, float):
        return format(value, ".12g")
    return str(value)


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


def structure_payload():
    return {
        "project":      "STRUMER",
        "title":        "STRUMER Structural Media Resolution",
        "version":      VERSION,
        "output_video": OUT_VIDEO,
        "width":        WIDTH,
        "height":       HEIGHT,
        "fps":          FPS,
        "slides":       SLIDE_NAMES,
        "law":          "same structure -> deterministic output",
        "principle":    "video_output = resolve(structure)",
        "admissibility": "video_visible iff video_structure_complete AND video_structure_consistent",
        "states":       ["RESOLVED", "ABSTAIN", "BLOCKED"],
    }


def structure_signature():
    return sha256_hex(canonical_text(structure_payload()))


def structure_certificate():
    return structure_signature()[:16]

def animate_slide(slide, index, t):
    img = slide.convert("RGBA")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    pulse = (math.sin(t * math.pi * 2.0) + 1) / 2

    sweep_slides = [0, 2, 5, 8, 10]
    sweep_colors = [BLUE, GREEN, CYAN, CYAN, BLUE]
    if index in sweep_slides:
        col = sweep_colors[sweep_slides.index(index)]
        x = int(-260 + (WIDTH + 520) * ((t * 0.65) % 1.0))
        for i in range(70):
            a = max(0, 26 - i // 3)
            draw.line((x + i*7, 0, x - 290 + i*7, 760),
                      fill=(col[0], col[1], col[2], a), width=2)

    particle_slides = [1, 3, 4, 6, 7, 9]
    if index in particle_slides:
        rng = np.random.default_rng(1000 + index)
        for _ in range(22):
            px = int(rng.integers(90, WIDTH - 90))
            py = int(rng.integers(80, 720))
            r = int(rng.integers(1, 4))
            a = int(35 + pulse * 45)
            draw.ellipse((px-r, py-r, px+r, py+r),
                         fill=(CYAN[0], CYAN[1], CYAN[2], a))

    if index == 4:
        alpha = int(40 + 60 * pulse)
        draw.rounded_rectangle((560, 150, 960, 680),
                                radius=22, outline=(255, 215, 40, alpha), width=4)

    final = Image.alpha_composite(img, overlay).convert("RGB")

    zoom = 1.0 + (0.018 if index in [0, 8, 10] else 0.012) * math.sin(t * math.pi)
    if abs(zoom - 1.0) > 0.001:
        nw, nh = int(WIDTH * zoom), int(HEIGHT * zoom)
        resized = final.resize((nw, nh), Image.Resampling.BICUBIC)
        ox, oy = (nw - WIDTH) // 2, (nh - HEIGHT) // 2
        final = resized.crop((ox, oy, ox + WIDTH, oy + HEIGHT))

    return final


def transition(a, b, t):
    ease = t * t * (3 - 2 * t)
    return Image.blend(a.convert("RGB"), b.convert("RGB"), ease)


def scale_for_output(img):
    if WIDTH == OUTPUT_WIDTH and HEIGHT == OUTPUT_HEIGHT:
        return img
    return img.resize((OUTPUT_WIDTH, OUTPUT_HEIGHT), Image.Resampling.LANCZOS)

def make_frames():
    print(f"  Building {len(SLIDE_BUILDERS)} slides...")
    slides = [builder() for builder in SLIDE_BUILDERS]
    scale_for_output(slides[0]).save(OUT_POSTER)
    print(f"  Poster saved: {OUT_POSTER}")

    frames = []
    for index, slide in enumerate(slides):
        frame_count = int(round(SLIDE_DURATIONS[index] * FPS))
        for i in range(frame_count):
            frames.append(animate_slide(slide, index, i / max(1, frame_count - 1)))
        if index < len(slides) - 1:
            for j in range(TRANSITION_FRAMES):
                frames.append(
                    transition(slide, slides[index + 1], j / max(1, TRANSITION_FRAMES - 1))
                )
        print(f"  Slide {index+1}/{len(slides)} rendered ({frame_count} frames)")

    return frames

def write_video(frames):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(OUT_VIDEO, fourcc, FPS, (OUTPUT_WIDTH, OUTPUT_HEIGHT))
    if not writer.isOpened():
        raise RuntimeError("Video writer could not be opened.")
    for frame in frames:
        writer.write(cv2.cvtColor(np.array(scale_for_output(frame)), cv2.COLOR_RGB2BGR))
    writer.release()

def write_verify():
    video_hash  = file_sha256(OUT_VIDEO)  if os.path.exists(OUT_VIDEO)  else "(not found)"
    poster_hash = file_sha256(OUT_POSTER) if os.path.exists(OUT_POSTER) else "(not found)"

    total_seconds = sum(SLIDE_DURATIONS) + (len(SLIDE_DURATIONS) - 1) * (TRANSITION_FRAMES / FPS)
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60

    lines = [
        "STRUMER Structural Media Resolution",
        f"Version:              {VERSION}",
        f"Output video:         {OUT_VIDEO}",
        f"Output poster:        {OUT_POSTER}",
        "",
        "CORE INVARIANTS",
        "  Principle:          video_output = resolve(structure)",
        "  Law:                same structure -> deterministic output",
        "  Visibility:         video_visible iff video_structure_complete AND video_structure_consistent",
        "  Admissibility:      RESOLVED | ABSTAIN | BLOCKED",
        "",
        "STRUCTURE CERTIFICATE",
        f"  Signature (SHA-256): {structure_signature()}",
        f"  Certificate (16):    {structure_certificate()}",
        "",
        "FILE INTEGRITY",
        f"  Video  SHA-256:     {video_hash}",
        f"  Poster SHA-256:     {poster_hash}",
        "",
        "OUTPUT METADATA",
        f"  Slides:             {len(SLIDE_BUILDERS)}",
        f"  FPS:                {FPS}",
        f"  Resolution:         {OUTPUT_WIDTH}x{OUTPUT_HEIGHT}",
        f"  Duration (approx):  {minutes}m {seconds:.1f}s",
        "",
        "SLIDE MANIFEST",
    ]
    for i, name in enumerate(SLIDE_NAMES, 1):
        lines.append(f"  {i:2d}. {name}")

    lines += [
        "",
        "REPRODUCTION NOTES",
        "  Same script + same dependencies + same fonts + same rendering environment",
        "  = byte-level reproduction of this output.",
        "  Structure governs admissible media resolution.",
        "  Operational substrates (renderers, codecs) may exist;",
        "  they do not determine the output — structure does.",
        "",
        "ECOSYSTEM",
        "  STRUMER   — Structural Video Resolution",
        "  STRUMER-D — Structural Diagram Resolution",
        "  STRUMER-A — Structural Audio Resolution",
        "  STRUMER-I — Structural Image Resolution",
        "",
        "  github.com/OMPSHUNYAYA/STRUMER",
    ]

    with open(OUT_VERIFY, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def main():
    print("=" * 60)
    print(f"STRUMER Structural Media Resolution  v{VERSION}")
    print("=" * 60)
    print(f"Principle:   video_output = resolve(structure)")
    print(f"Law:         same structure -> deterministic output")
    print(f"Slides:      {len(SLIDE_BUILDERS)}")
    print()

    frames = make_frames()
    print(f"\n  Writing video ({len(frames)} frames)...")
    write_video(frames)
    write_verify()

    print()
    print(f"  Created: {OUT_VIDEO}")
    print(f"  Created: {OUT_POSTER}")
    print(f"  Created: {OUT_VERIFY}")
    print()
    print(f"  structure_signature : {structure_signature()}")
    print(f"  certificate         : {structure_certificate()}")
    print()
    print("  RESOLVED: structure complete + consistent → video generated")
    print("  ABSTAIN:  structure incomplete            → no output forced")
    print("  BLOCKED:  structure conflicting           → no output allowed")
    print()
    print("  same structure → same video → same output signature")
    print("=" * 60)


if __name__ == "__main__":
    main()
