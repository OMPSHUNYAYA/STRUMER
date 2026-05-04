from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import os

WIDTH, HEIGHT = 1280, 720
FPS = 24
OUTFILE = "STRUMER_v2_7.mp4"
FADE_SECONDS = 0.32
SAFE_TOP = 70
SAFE_BOTTOM = 520

BG = (5, 8, 15)
WHITE = (250, 252, 255)
GOLD = (255, 215, 120)
ACCENT = (100, 255, 180)
LINE = (70, 85, 115)
CODE_BG = (12, 18, 32)
CODE_COLOR = (250, 252, 255)

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
FONT_BIG = font(54, True)
FONT_MED = font(32, True)
FONT_SMALL = font(24, True)
FONT_CODE = font(30, True)
FONT_FOOTER = font(22, True)
FONT_LINE_NUM = font(18, True)

def canvas():
    return Image.new("RGB", (WIDTH, HEIGHT), BG)

def text_len(text):
    return len(text.replace("\n", " ").strip())

def read_duration(text, kind="normal"):
    n = text_len(text)
    if kind == "code":
        return 6.8 if n < 90 else 8.2
    if kind == "live":
        return 8.0
    if kind == "final":
        return 6.2
    if n < 25:
        return 2.8
    if n < 55:
        return 3.6
    if n < 95:
        return 4.6
    return 5.8

def text_size(draw, text, f):
    bbox = draw.textbbox((0, 0), text, font=f)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def center_line(draw, text, y, f, color):
    w, _ = text_size(draw, text, f)
    x = (WIDTH - w) // 2
    draw.text((x, y), text, font=f, fill=color)

def draw_multiline_center(draw, text, y, f, color, gap=12):
    lines = text.split("\n")
    total_h = len(lines) * f.size + max(0, len(lines) - 1) * gap
    if y + total_h > SAFE_BOTTOM:
        y = SAFE_BOTTOM - total_h
    y = max(SAFE_TOP, y)
    for line in lines:
        if line.strip():
            center_line(draw, line, y, f, color)
        y += f.size + gap

def draw_panel(draw, x1, y1, x2, y2, outline=ACCENT, fill=CODE_BG, width=4):
    draw.rounded_rectangle((x1, y1, x2, y2), radius=24, fill=fill, outline=outline, width=width)

def slide(title, body="", kind="normal"):
    img = canvas()
    draw = ImageDraw.Draw(img)

    title_font = FONT_HERO if kind == "final" and "\n" not in title and len(title) < 28 else FONT_BIG
    title_gap = 12
    title_y = SAFE_TOP

    draw_multiline_center(draw, title, title_y, title_font, GOLD, gap=title_gap)

    if body:
        title_lines = title.split("\n")
        title_height = len(title_lines) * title_font.size + max(0, len(title_lines) - 1) * title_gap
        body_y = title_y + title_height + 48
        draw_multiline_center(draw, body, body_y, FONT_MED, WHITE, gap=12)

    return img, read_duration(title + "\n" + body, kind)

def code_slide(code, title=""):
    img = canvas()
    draw = ImageDraw.Draw(img)

    if title:
        draw_multiline_center(draw, title, SAFE_TOP, FONT_BIG, GOLD, gap=12)
        y_start = SAFE_TOP + 135
    else:
        y_start = SAFE_TOP + 105

    lines = code.strip().split("\n")
    line_height = FONT_CODE.size + 14
    box_height = len(lines) * line_height + 64
    box_top = y_start - 15
    box_bottom = min(SAFE_BOTTOM, box_top + box_height)
    box_left = 90
    box_right = WIDTH - 90

    draw_panel(draw, box_left, box_top, box_right, box_bottom, outline=GOLD, fill=CODE_BG, width=4)

    code_y = box_top + 26
    for i, line in enumerate(lines, 1):
        if code_y + FONT_CODE.size > box_bottom - 18:
            break
        draw.text((box_left + 18, code_y), f"{i:2d}", font=FONT_LINE_NUM, fill=GOLD)
        draw.text((box_left + 62, code_y), line, font=FONT_CODE, fill=CODE_COLOR)
        code_y += line_height

    return img, read_duration(code, "code")

def live_example_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)

    draw_multiline_center(draw, "LIVE PROOF", SAFE_TOP, FONT_HERO, GOLD, gap=12)
    center_line(draw, 'The slide containing "Did this video come from editing..."', 150, FONT_SMALL, WHITE)
    center_line(draw, "is generated from the structure below", 182, FONT_SMALL, WHITE)

    code = '''slides = [
    slide("Did this video come from editing",
          "or from structure")
]'''

    box_top = 225
    box_bottom = 470
    box_left = 85
    box_right = 1195

    draw_panel(draw, box_left, box_top, box_right, box_bottom, outline=GOLD, fill=CODE_BG, width=4)

    lines = code.strip().split("\n")
    y = box_top + 28
    for i, line in enumerate(lines, 1):
        draw.text((box_left + 20, y), f"{i:2d}", font=FONT_LINE_NUM, fill=GOLD)
        draw.text((box_left + 65, y), line, font=FONT_CODE, fill=CODE_COLOR)
        y += FONT_CODE.size + 14

    center_line(draw, "Structure resolves the visible media output", 500, FONT_FOOTER, ACCENT)
    return img, read_duration(code, "live")

def structural_diagram_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)

    draw_multiline_center(draw, "Structure Reveals Video", SAFE_TOP, FONT_BIG, GOLD, gap=12)

    nodes = [
        (WIDTH // 2, 220, "STRUCTURE", 260),
        (WIDTH // 2, 340, "Complete + Consistent", 410),
        (WIDTH // 2, 460, "VISIBLE VIDEO", 300),
    ]

    for i in range(len(nodes) - 1):
        x1, y1, _, _ = nodes[i]
        x2, y2, _, _ = nodes[i + 1]
        draw.line((x1, y1 + 36, x2, y2 - 48), fill=ACCENT, width=5)
        draw.polygon([(x2 - 12, y2 - 48), (x2 + 12, y2 - 48), (x2, y2 - 32)], fill=ACCENT)

    for x, y, label, w in nodes:
        h = 58
        draw.rounded_rectangle((x - w // 2, y - h // 2, x + w // 2, y + h // 2), radius=28, outline=ACCENT, width=4)
        center_line(draw, label, y - 14, FONT_MED, WHITE)

    center_line(draw, "video_visible iff video_structure_complete AND video_structure_consistent", 505, FONT_FOOTER, GOLD)
    return img, read_duration("Structure Complete Consistent Visible Video", "live")

def strumer_identity_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    draw_multiline_center(draw, "STRUMER", SAFE_TOP, FONT_HERO, GOLD, gap=12)
    draw_multiline_center(draw, "Structural Media Resolution", SAFE_TOP + 130, FONT_MED, WHITE, gap=12)
    center_line(draw, "Part of the Shunyaya Dependency Elimination Framework", 430, FONT_FOOTER, ACCENT)
    center_line(draw, "video = resolve(structure)", 485, FONT_MED, GOLD)
    return img, read_duration("STRUMER Structural Media Resolution", "final")

def build_slides():
    slides = []

    def add(item):
        slides.append(item)

    add(slide("This entire video", "Was generated\nwithout editing", "final"))
    add(slide("No editor\nNo timeline\nNo manual composition", "Yet you are watching\na complete video", "final"))
    add(slide("Did this video come from editing", "or from structure", "final"))
    add(slide("A tiny script", "generated this entire video"))

    add(slide("How videos are normally created", "Open editor\nCreate slides\nType text\nAdjust layout\nSet timing\nPreview and fix"))
    add(slide("This process depends on", "Trial and error\nManual adjustment\nGuesswork\nTool-dependent workflow"))

    add(slide("What if you did not edit the video", "What if you defined it", "final"))

    add(code_slide('slide("Hello")'))
    add(slide("This creates one slide", "Change content -> Slide changes\nNo dragging\nNo adjusting"))
    add(code_slide('slide("Your title",\n      "Your message")'))
    add(slide("One structure defines output", "No manual control needed"))

    add(code_slide('slides = [\n    slide("Hello"),\n    slide("World")\n]'))
    add(code_slide('build_video(slides)'))
    add(slide("You just created a video", "Structure -> Output", "final"))

    add(live_example_slide())
    add(slide("Let us test the claim", "Same structure\nRun multiple times"))
    add(slide("Same structure", "Same video\nEvery time", "final"))
    add(slide("Now change one line", "Modify structure"))
    add(code_slide('slide("Different message")'))
    add(slide("Run again", "New structure -> New video\nNo editing involved"))

    add(slide("Before", "Move\nAdjust\nFix\nPreview\nTrial and error"))
    add(slide("Now", "Define once\nDeterministic output\nNo adjustment\nSame structure -> same video"))

    add(slide("You do not write the full system", "You only define the structure\nThe system resolves the rest"))
    add(code_slide('slides = [\n    slide("Your idea"),\n    slide("Your message")\n]'))
    add(slide("Regular scripts describe process", "Structural scripts define outcome\nExecution vs Resolution"))

    add(slide("video != editing", kind="final"))
    add(slide("video = resolve(structure)", kind="final"))
    add(slide("video_visible iff video_structure_complete", kind="final"))

    add(slide("In regular thinking", "You build things step by step"))
    add(slide("In structure", "The full form already exists"))
    add(structural_diagram_slide())
    add(slide("When structure is complete", "Output becomes visible\nYou do not assemble\nYou reveal"))
    add(slide("output_visible iff structure_complete", kind="final"))

    add(slide("The video works the same way", "Run the script provided\nin the description\nYou get this video"))
    add(slide("Change one line", "Run again\nYou get a new video"))
    add(slide("No editing\nNo rework", "The structure remains\nOnly your content changes"))
    add(slide("Create many videos", "Change only the structure\nEverything else stays the same"))
    add(slide("You do not rebuild videos", "You regenerate them\nStructure remains\nContent evolves"))

    add(slide("AI tools and STRUMER", "Solve different problems"))
    add(slide("AI tools", "Interpret your script\nOutput can change\nGenerate possibilities"))
    add(slide("STRUMER", "Resolves your structure\nOutput stays consistent\nGuarantees outcomes"))
    add(slide("AI tools", "Hide the logic\nNeed adjustment\nChange with context"))
    add(slide("STRUMER", "Shows the structure\nNeeds definition\nStays consistent"))
    add(slide("AI tools optimize creativity", "STRUMER optimizes control"))
    add(slide("AI interprets what you mean", "STRUMER does exactly what you define", "final"))

    add(slide("Why this matters", "No trial and error\nNo manual adjustment\nNo tool dependency\nDeterministic creation"))
    add(slide("This is not just video", "Structure-based creation\nMedia\nSystems\nAutomation"))
    add(slide("Remove editing", "Video still exists\nEditing was never fundamental"))

    add(slide("For learning and exploration", "Structure defines correctness\nUse responsibly"))
    add(slide("The video was not edited", kind="final"))
    add(slide("It was resolved from structure", kind="final"))
    add(slide("This is not AI video generation", kind="final"))
    add(slide("This is structural media resolution", kind="final"))
    add(strumer_identity_slide())
    add(slide("Tiny structure\nLarge media\nDeterministic outcome", kind="final"))
    add(slide("Remove dependency\nPreserve structure", "Join the Structural Revolution", "final"))

    return slides

def to_bgr(img):
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def write_hold(writer, img, seconds):
    frame = to_bgr(img)
    frame_count = max(1, int(seconds * FPS))
    for _ in range(frame_count):
        writer.write(frame)

def write_fade(writer, a_img, b_img):
    a = to_bgr(a_img).astype(np.float32)
    b = to_bgr(b_img).astype(np.float32)
    total = max(1, int(FADE_SECONDS * FPS))
    for i in range(total):
        t = i / max(total - 1, 1)
        frame = ((1 - t) * a + t * b).astype(np.uint8)
        writer.write(frame)

def build():
    slides = build_slides()
    out = cv2.VideoWriter(OUTFILE, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (WIDTH, HEIGHT))

    if not out.isOpened():
        raise RuntimeError("Video writer failed. Check OpenCV MP4 support.")

    prev = None
    for img, duration in slides:
        if prev is not None:
            write_fade(out, prev, img)
        write_hold(out, img, duration)
        prev = img

    out.release()
    total_seconds = sum(duration for _, duration in slides) + max(0, len(slides) - 1) * FADE_SECONDS
    print("Created:", OUTFILE)
    print("Total slides:", len(slides))
    print("Estimated duration:", f"{total_seconds / 60:.1f} minutes")

if __name__ == "__main__":
    build()
