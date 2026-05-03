from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import os

WIDTH, HEIGHT = 1280, 720
FPS = 24
OUTFILE = "STRUMER.mp4"

FADE_SECONDS = 0.28
SAFE_TOP = 80
SAFE_BOTTOM = 560

BG = (7, 11, 18)
WHITE = (244, 247, 251)
GOLD = (255, 209, 102)
ACCENT = (142, 230, 201)
BLUE = (120, 170, 255)
LINE = (55, 72, 100)


def font(size, bold=False):
    try:
        if os.name == "nt":
            path = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
        else:
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


FONT_BIG = font(48, True)
FONT_MED = font(30, True)
FONT_SMALL = font(24)
FONT_CODE = font(22)
FONT_FOOTER = font(20)


def canvas():
    return Image.new("RGB", (WIDTH, HEIGHT), BG)


def text_len(text):
    return len(text.replace("\n", " ").strip())


def read_duration(text, kind="normal"):
    n = text_len(text)
    if kind == "code":
        return 5.8 if n < 80 else 7.2
    if kind == "live":
        return 7.5
    if kind == "final":
        return 5.8
    if n < 22:
        return 2.25
    if n < 45:
        return 2.8
    if n < 75:
        return 3.6
    if n < 120:
        return 4.6
    return 5.8


def center_line(draw, text, y, f, color):
    bbox = draw.textbbox((0, 0), text, font=f)
    x = (WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, font=f, fill=color)


def draw_multiline_center(draw, text, y, f, color, gap=10):
    lines = text.split("\n")
    total_h = len(lines) * (f.size + gap)
    if y + total_h > SAFE_BOTTOM:
        y = SAFE_BOTTOM - total_h
    for line in lines:
        if line.strip():
            center_line(draw, line, y, f, color)
        y += f.size + gap


def slide(title, body="", kind="normal"):
    img = canvas()
    draw = ImageDraw.Draw(img)
    draw_multiline_center(draw, title, SAFE_TOP, FONT_BIG, GOLD)
    if body:
        draw_multiline_center(draw, body, SAFE_TOP + 140, FONT_MED, WHITE)
    return img, read_duration(title + "\n" + body, kind)


def code_slide(code, title=""):
    img = canvas()
    draw = ImageDraw.Draw(img)
    if title:
        draw_multiline_center(draw, title, SAFE_TOP, FONT_BIG, GOLD)
        y = SAFE_TOP + 145
    else:
        y = SAFE_TOP + 120
    draw_multiline_center(draw, code, y, FONT_CODE, ACCENT, gap=8)
    return img, read_duration(code, "code")


def live_example_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    draw_multiline_center(draw, "Live Example", SAFE_TOP, FONT_BIG, GOLD)

    code = 'def build_slides():\n    return [\n        slide("Did this video come from editing",\n              "or from structure")\n    ]'

    draw.rectangle((95, 185, 1185, 455), outline=ACCENT, width=3)
    center_line(draw, "Exact structure for the third slide of this video", 205, FONT_SMALL, GOLD)
    draw.multiline_text((165, 265), code, font=FONT_CODE, fill=ACCENT, spacing=8)
    center_line(draw, "This structure created that visible slide.", 505, FONT_FOOTER, BLUE)
    return img, read_duration(code, "live")


def structural_diagram_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    draw_multiline_center(draw, "Structure Reveals", SAFE_TOP, FONT_BIG, GOLD)

    nodes = [
        (WIDTH // 2, 215, "Structure", 210),
        (WIDTH // 2, 350, "Complete + Consistent", 390),
        (WIDTH // 2, 485, "Visible Video", 240),
    ]

    for i in range(len(nodes) - 1):
        x1, y1, _, _ = nodes[i]
        x2, y2, _, _ = nodes[i + 1]
        draw.line((x1, y1 + 34, x2, y2 - 34), fill=LINE, width=4)

    for x, y, label, w in nodes:
        h = 64
        draw.rounded_rectangle(
            (x - w // 2, y - h // 2, x + w // 2, y + h // 2),
            radius=30,
            outline=ACCENT,
            width=3
        )
        center_line(draw, label, y - 12, FONT_FOOTER, WHITE)

    center_line(draw, "Output becomes visible when structure is complete.", 545, FONT_FOOTER, BLUE)

    return img, read_duration("Structure Complete Consistent Visible Video", "live")


def strumer_identity_slide():
    img = canvas()
    draw = ImageDraw.Draw(img)
    draw_multiline_center(draw, "STRUMER", SAFE_TOP, FONT_BIG, GOLD)
    draw_multiline_center(draw, "Structural Media Resolution", SAFE_TOP + 145, FONT_MED, WHITE)
    center_line(draw, "Part of the Shunyaya Framework", 500, FONT_FOOTER, ACCENT)
    return img, read_duration("STRUMER Structural Media Resolution Part of the Shunyaya Framework", "final")


def build_slides():
    slides = []

    def add(item):
        slides.append(item)

    add(slide("A tiny script created this entire video"))
    add(slide("~11 KB script", "generated this ~25 MB video"))
    add(slide("Did this video come from editing", "or from structure"))
    add(slide("No editor\nNo timeline\nNo manual composition"))
    add(slide("By the end of this video", "you will know how to create\nthis exact video"))

    add(slide("How do you normally create a video"))
    add(slide("Open a video editor"))
    add(slide("Create slides or scenes"))
    add(slide("Type text"))
    add(slide("Move things around"))
    add(slide("Adjust position\nspacing\ncolors"))
    add(slide("Set timing"))
    add(slide("Preview\nfix\npreview again"))
    add(slide("Repeat until it looks right"))
    add(slide("Export video"))
    add(slide("This process depends on", "trial and error\nmanual adjustment\nguesswork"))

    add(slide("What if you didn’t edit the video"))
    add(slide("What if you defined it"))
    add(code_slide('slide("Hello")'))
    add(slide("This creates one slide"))
    add(slide("Add your content"))
    add(code_slide('slide("Your title",\n      "Your message")'))
    add(slide("The slide changes", "when your content changes"))
    add(slide("No dragging\nNo adjusting"))
    add(slide("Just one structure"))

    add(slide("Add more slides"))
    add(code_slide('slides = [\n    slide("Hello"),\n    slide("World")\n]'))
    add(slide("Now you have multiple slides"))
    add(slide("Turn it into a video"))
    add(code_slide('build_video(slides)'))
    add(slide("You just created a video"))

    add(live_example_slide())

    add(slide("Before", "You adjusted the video"))
    add(slide("Now", "You define the video"))
    add(slide("Before", "Move\ncheck\nfix"))
    add(slide("Now", "Change one line\nEverything updates"))
    add(slide("Before", "Trial and error"))
    add(slide("Now", "Deterministic output"))

    add(slide("You do not write the full system"))
    add(slide("You only define the structure"))
    add(code_slide('slides = [\n    slide("Your idea"),\n    slide("Your message")\n]'))
    add(slide("This is your part"))
    add(slide("The system does the rest"))

    add(slide("Regular scripts describe process"))
    add(slide("Structural scripts define outcome"))
    add(slide("Regular scripting is execution"))
    add(slide("Structural scripting is resolution"))
    add(slide("Editing creates output"))
    add(slide("Structure resolves output"))

    add(slide("video_visible iff video_structure_complete", kind="final"))
    add(slide("You don’t edit videos"))
    add(slide("You define them"))

    add(slide("This is only the beginning"))
    add(slide("In regular thinking", "you build things step by step"))
    add(slide("In structure", "the full form already exists"))
    add(structural_diagram_slide())
    add(slide("When structure is complete", "it becomes visible"))
    add(slide("You don’t assemble"))
    add(slide("You reveal"))
    add(slide("output_visible iff structure_complete", kind="final"))
    add(slide("This video works the same way"))

    add(slide("The video you are watching", "was generated\nfrom a script"))
    add(slide("Run the script", "(provided in the description link)"))
    add(slide("You get this video"))

    add(slide("Now change one line"))
    add(code_slide('slide("Your new message")'))
    add(slide("Run again"))
    add(slide("You get a new video"))
    add(slide("No editing\nNo rework"))
    add(slide("The structure remains"))
    add(slide("Only your content changes"))
    add(slide("Create many videos"))
    add(slide("Change only the structure"))
    add(slide("Everything else stays the same"))
    add(slide("You don’t rebuild videos"))
    add(slide("You regenerate them"))

    add(slide("AI tools and STRUMER", "solve different problems"))
    add(slide("AI tools", "interpret your script"))
    add(slide("STRUMER", "resolves your structure"))
    add(slide("AI output", "can change"))
    add(slide("STRUMER output", "is always the same"))
    add(slide("AI tools", "generate possibilities"))
    add(slide("STRUMER", "guarantees outcomes"))
    add(slide("AI tools", "hide the logic"))
    add(slide("STRUMER", "shows the structure"))
    add(slide("AI tools", "recreate the video"))
    add(slide("STRUMER", "regenerates from structure"))
    add(slide("AI tools", "need adjustment"))
    add(slide("STRUMER", "needs definition"))
    add(slide("AI tools", "change with context"))
    add(slide("STRUMER", "stays consistent"))
    add(slide("AI tools", "optimize creativity"))
    add(slide("STRUMER", "optimizes control"))
    add(slide("AI tools generate videos"))
    add(slide("STRUMER defines them"))
    add(slide("AI interprets what you mean"))
    add(slide("STRUMER does exactly what you define", kind="final"))

    add(slide("For learning and exploration", "Structure defines correctness\nUse responsibly"))

    add(slide("The video was not edited", kind="final"))
    add(slide("It was resolved from structure", kind="final"))
    add(slide("This is not AI video generation", kind="final"))
    add(slide("This is structural media resolution", kind="final"))
    add(strumer_identity_slide())
    add(slide("Tiny structure\nLarge media\nDeterministic outcome", kind="final"))
    add(slide("Remove dependency\nPreserve structure", "Join the Structural Revolution", kind="final"))

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
        raise RuntimeError("Video writer could not be opened. Check OpenCV MP4 support.")

    prev = None
    for img, duration in slides:
        if prev is not None:
            write_fade(out, prev, img)
        write_hold(out, img, duration)
        prev = img

    out.release()
    print("Created:", OUTFILE)
    print("Slides:", len(slides))


if __name__ == "__main__":
    build()
