from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import os
import math
import hashlib
import wave
import struct
from copy import deepcopy

WIDTH, HEIGHT = 1280, 720
FPS = 24
VERSION = "1.9"
OUT_VIDEO = "STRUMER_A_video_v1_9.mp4"

SAMPLE_RATE = 44100
MAX_AMPLITUDE = 32767

FADE_SECONDS = 0.28
SAFE_TOP = 48
SAFE_BOTTOM = 555

BG = (5, 8, 15)
PANEL = (11, 17, 31)
WHITE = (250, 252, 255)
GOLD = (255, 215, 120)
ACCENT = (100, 255, 180)
BLUE = (120, 170, 255)
RED = (255, 105, 125)
ORANGE = (255, 175, 70)
PURPLE = (196, 150, 255)
LINE = (95, 108, 135)
CODE_BG = (10, 15, 28)


def font(size, bold=True):
    try:
        if os.name == "nt":
            path = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
        else:
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


FONT_HERO = font(66)
FONT_TITLE = font(54)
FONT_BIG = font(46)
FONT_MED = font(38)
FONT_BODY = font(32)
FONT_SMALL = font(27)
FONT_TINY = font(23)


def canvas():
    return Image.new("RGB", (WIDTH, HEIGHT), BG)


def text_size(draw, text, f):
    box = draw.textbbox((0, 0), text, font=f)
    return box[2] - box[0], box[3] - box[1]


def fit_font(draw, text, start, max_width, min_size=22):
    size = start
    while size >= min_size:
        f = font(size)
        if text_size(draw, text, f)[0] <= max_width:
            return f
        size -= 2
    return font(min_size)


def center(draw, text, y, f, color=WHITE):
    w, _ = text_size(draw, text, f)
    draw.text(((WIDTH - w) // 2, y), text, font=f, fill=color)


def panel(draw, box, outline=ACCENT, fill=PANEL, width=3, radius=22):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def title_slide(title, subtitle="", note="", duration=4.2, title_color=GOLD):
    img = canvas()
    draw = ImageDraw.Draw(img)

    title_font = fit_font(draw, title, 66, WIDTH - 120, 40)
    center(draw, title, 92, title_font, title_color)

    if subtitle:
        sub_font = fit_font(draw, subtitle, 42, WIDTH - 160, 26)
        center(draw, subtitle, 205, sub_font, WHITE)

    if note:
        note_font = fit_font(draw, note, 34, WIDTH - 180, 24)
        center(draw, note, 330, note_font, ACCENT)

    return img, duration


def statement_slide(line1, line2="", line3="", duration=4.2, color1=GOLD, color2=ACCENT, color3=WHITE):
    img = canvas()
    draw = ImageDraw.Draw(img)

    y = 110
    if line1:
        f = fit_font(draw, line1, 62, WIDTH - 150, 34)
        center(draw, line1, y, f, color1)
        y += 115

    if line2:
        f = fit_font(draw, line2, 56, WIDTH - 150, 32)
        center(draw, line2, y, f, color2)
        y += 105

    if line3:
        f = fit_font(draw, line3, 46, WIDTH - 150, 30)
        center(draw, line3, y, f, color3)

    return img, duration


def bullets_slide(title, bullets, duration=5.4, accent=ACCENT):
    img = canvas()
    draw = ImageDraw.Draw(img)

    ftitle = fit_font(draw, title, 54, WIDTH - 150, 34)
    center(draw, title, 56, ftitle, GOLD)

    y = 165
    for item in bullets[:5]:
        f = fit_font(draw, item, 36, WIDTH - 230, 24)
        draw.text((155, y), "•", font=f, fill=accent)
        draw.text((205, y), item, font=f, fill=WHITE)
        y += 70

    return img, duration


def code_slide(title, code_lines, footer="", duration=6.0):
    img = canvas()
    draw = ImageDraw.Draw(img)

    ftitle = fit_font(draw, title, 52, WIDTH - 150, 34)
    center(draw, title, 45, ftitle, GOLD)

    box = (115, 140, 1165, 455)
    panel(draw, box, outline=GOLD, fill=CODE_BG, width=4, radius=20)

    y = 180
    for line in code_lines[:7]:
        f = fit_font(draw, line, 30, 950, 20)
        draw.text((160, y), line, font=f, fill=WHITE)
        y += 42

    if footer:
        f = fit_font(draw, footer, 34, WIDTH - 160, 24)
        center(draw, footer, 493, f, ACCENT)

    return img, duration



def draw_centered_in_box(draw, text, box, f, color):
    x1, y1, x2, y2 = box
    w, h = text_size(draw, text, f)
    draw.text((x1 + (x2 - x1 - w) // 2, y1 + (y2 - y1 - h) // 2 - 2), text, font=f, fill=color)


def dependency_chain_slide(duration=5.8):
    img = canvas()
    draw = ImageDraw.Draw(img)

    center(draw, "Dependency Removed", 52, FONT_TITLE, GOLD)

    top_items = [
        ("editing", ORANGE),
        ("tuning", ORANGE),
        ("sequencing", ORANGE),
    ]

    boxes = [
        (115, 155, 405, 238),
        (495, 155, 785, 238),
        (875, 155, 1165, 238),
    ]

    for i, ((label, color), box) in enumerate(zip(top_items, boxes)):
        panel(draw, box, outline=color, fill=PANEL, width=3, radius=18)
        f = fit_font(draw, label, 34, box[2] - box[0] - 35, 24)
        draw_centered_in_box(draw, label, box, f, WHITE)

        if i < len(boxes) - 1:
            x1 = box[2] + 24
            y1 = (box[1] + box[3]) // 2
            x2 = boxes[i + 1][0] - 24
            draw.line((x1, y1, x2, y1), fill=LINE, width=5)
            draw.polygon([(x2, y1), (x2 - 15, y1 - 10), (x2 - 15, y1 + 10)], fill=LINE)

    draw.line((120, 292, 1160, 292), fill=RED, width=7)
    draw.line((120, 312, 1160, 312), fill=RED, width=7)

    panel(draw, (260, 370, 1020, 462), outline=ACCENT, fill=PANEL, width=4, radius=22)
    draw_centered_in_box(draw, "structure -> resolution -> audio", (260, 370, 1020, 462), FONT_MED, ACCENT)

    center(draw, "remove dependency -> preserve outcome", 512, FONT_SMALL, GOLD)

    return img, duration


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


def structure_signature(structure):
    return sha256_hex(canonical_text(structure))


def structure_certificate(structure):
    return structure_signature(structure)[:16]


def base_structure():
    return {
        "title": "STRUMER-A Structural Audio Identity",
        "sample_rate": SAMPLE_RATE,
        "events": [
            {"kind": "tone", "frequency": 440.0, "duration": 0.28, "amplitude": 0.45},
            {"kind": "silence", "duration": 0.08},
            {"kind": "tone", "frequency": 660.0, "duration": 0.28, "amplitude": 0.42},
            {"kind": "silence", "duration": 0.08},
            {"kind": "tone", "frequency": 880.0, "duration": 0.36, "amplitude": 0.38},
            {"kind": "silence", "duration": 0.12},
            {"kind": "tone", "frequency": 660.0, "duration": 0.22, "amplitude": 0.35},
            {"kind": "silence", "duration": 0.06},
            {"kind": "tone", "frequency": 440.0, "duration": 0.45, "amplitude": 0.40}
        ]
    }


def changed_structure():
    s = deepcopy(base_structure())
    s["events"][2]["frequency"] = 990.0
    return s


def envelope(position, total):
    if total <= 1:
        return 1.0

    attack = max(1, int(total * 0.08))
    release = max(1, int(total * 0.10))

    if position < attack:
        return position / attack
    if position > total - release:
        return max(0.0, (total - position) / release)
    return 1.0


def tone_samples(frequency, duration, amplitude):
    count = int(round(duration * SAMPLE_RATE))
    out = []
    for i in range(count):
        t = i / SAMPLE_RATE
        env = envelope(i, count)
        value = math.sin(2.0 * math.pi * frequency * t)
        out.append(int(MAX_AMPLITUDE * amplitude * env * value))
    return out


def silence_samples(seconds):
    return [0] * int(round(seconds * SAMPLE_RATE))


def synthesize_audio(structure):
    samples = []
    for event in structure["events"]:
        if event["kind"] == "tone":
            samples.extend(tone_samples(event["frequency"], event["duration"], event["amplitude"]))
        elif event["kind"] == "silence":
            samples.extend(silence_samples(event["duration"]))
    return samples


def read_wav_samples(path):
    samples = []
    if not os.path.exists(path):
        return None
    with wave.open(path, "rb") as src:
        channels = src.getnchannels()
        width = src.getsampwidth()
        frames = src.readframes(src.getnframes())

    if width != 2:
        return None

    values = struct.unpack("<" + "h" * (len(frames) // 2), frames)
    if channels == 1:
        samples = list(values)
    else:
        samples = list(values[0::channels])
    return samples


def load_actual_samples():
    original = read_wav_samples("STRUMER_A_v1_3.wav")
    repeat = read_wav_samples("STRUMER_A_v1_3_repeat.wav")
    changed = read_wav_samples("STRUMER_A_v1_3_changed.wav")

    if original is not None and repeat is not None and changed is not None:
        return original, repeat, changed, "actual GitHub output WAV files"

    base = base_structure()
    changed_structure_value = changed_structure()
    return (
        synthesize_audio(base),
        synthesize_audio(base),
        synthesize_audio(changed_structure_value),
        "deterministic fallback from STRUMER-A structure"
    )


def draw_wave(draw, samples, box, color):
    x1, y1, x2, y2 = box
    mid = (y1 + y2) // 2
    height = (y2 - y1) // 2 - 4
    draw.line((x1, mid, x2, mid), fill=LINE, width=2)

    usable = x2 - x1
    step = max(1, len(samples) // usable)
    points = []

    for px in range(usable):
        start = px * step
        end = min(len(samples), start + step)
        segment = samples[start:end]
        amp = max(segment, key=abs) if segment else 0
        y = mid - int((amp / MAX_AMPLITUDE) * height)
        points.append((x1 + px, y))

    if len(points) >= 2:
        draw.line(points, fill=color, width=3)


def waveform_slide(title, label1, label2, samples1, samples2, duration=5.8):
    img = canvas()
    draw = ImageDraw.Draw(img)

    ftitle = fit_font(draw, title, 50, WIDTH - 150, 32)
    center(draw, title, 44, ftitle, GOLD)

    panel(draw, (70, 140, 1210, 285), outline=ACCENT, fill=PANEL, width=3, radius=18)
    draw.text((95, 160), label1, font=FONT_SMALL, fill=ACCENT)
    draw_wave(draw, samples1, (95, 215, 1185, 260), ACCENT)

    panel(draw, (70, 335, 1210, 480), outline=BLUE, fill=PANEL, width=3, radius=18)
    draw.text((95, 355), label2, font=FONT_SMALL, fill=BLUE)
    draw_wave(draw, samples2, (95, 410, 1185, 455), BLUE)

    f = fit_font(draw, "same structure -> same waveform", 36, WIDTH - 150, 24)
    center(draw, "same structure -> same waveform", 520, f, GOLD)

    return img, duration


def changed_waveform_slide(samples1, samples_changed, duration=5.8):
    img = canvas()
    draw = ImageDraw.Draw(img)

    center(draw, "Changed Structure", 45, FONT_TITLE, GOLD)

    panel(draw, (80, 135, 1200, 255), outline=ACCENT, fill=PANEL, width=3, radius=18)
    draw.text((105, 150), "Original structure", font=FONT_SMALL, fill=ACCENT)
    draw_wave(draw, samples1, (105, 205, 1175, 238), ACCENT)

    panel(draw, (80, 315, 1200, 435), outline=RED, fill=PANEL, width=3, radius=18)
    draw.text((105, 330), "Changed structure output", font=FONT_SMALL, fill=RED)
    draw_wave(draw, samples_changed, (105, 385, 1175, 418), RED)

    f = fit_font(draw, "changed structure -> changed waveform", 36, WIDTH - 140, 24)
    center(draw, "changed structure -> changed waveform", 500, f, GOLD)

    return img, duration



def difference_zoom_slide(samples1, samples_changed, duration=6.0):
    img = canvas()
    draw = ImageDraw.Draw(img)

    center(draw, "Actual Difference View", 45, FONT_TITLE, GOLD)

    n = min(len(samples1), len(samples_changed))
    if n <= 0:
        return img, duration

    window = max(1024, n // 8)
    best_start = 0
    best_score = -1

    step = max(256, window // 8)
    for start in range(0, max(1, n - window), step):
        end = min(n, start + window)
        score = sum(abs(samples1[i] - samples_changed[i]) for i in range(start, end))
        if score > best_score:
            best_score = score
            best_start = start

    best_end = min(n, best_start + window)

    original_zoom = samples1[best_start:best_end]
    changed_zoom = samples_changed[best_start:best_end]
    diff_zoom = [max(-32768, min(32767, changed_zoom[i] - original_zoom[i])) for i in range(min(len(original_zoom), len(changed_zoom)))]

    panel(draw, (80, 125, 1200, 230), outline=ACCENT, fill=PANEL, width=3, radius=18)
    draw.text((105, 140), "Original output zoom", font=FONT_SMALL, fill=ACCENT)
    draw_wave(draw, original_zoom, (105, 185, 1175, 215), ACCENT)

    panel(draw, (80, 275, 1200, 380), outline=RED, fill=PANEL, width=3, radius=18)
    draw.text((105, 290), "Changed output zoom", font=FONT_SMALL, fill=RED)
    draw_wave(draw, changed_zoom, (105, 335, 1175, 365), RED)

    panel(draw, (80, 425, 1200, 530), outline=GOLD, fill=PANEL, width=3, radius=18)
    draw.text((105, 440), "Actual difference signal", font=FONT_SMALL, fill=GOLD)
    draw_wave(draw, diff_zoom, (105, 485, 1175, 515), GOLD)

    return img, duration



def actual_waveform_artifact_slide(duration=6.8):
    img = canvas()
    draw = ImageDraw.Draw(img)

    center(draw, "Actual Published Waveform", 36, FONT_TITLE, GOLD)

    path = "STRUMER_A_v1_3_waveform.png"

    if os.path.exists(path):
        artifact = Image.open(path).convert("RGB")
        max_w = 1160
        max_h = 475
        scale = min(max_w / artifact.width, max_h / artifact.height)
        new_w = int(artifact.width * scale)
        new_h = int(artifact.height * scale)
        artifact = artifact.resize((new_w, new_h), Image.LANCZOS)

        x = (WIDTH - new_w) // 2
        y = 112
        img.paste(artifact, (x, y))

        center(draw, "Exactly as published on GitHub — no editing", 610, FONT_TINY, ACCENT)
    else:
        panel(draw, (95, 165, 1185, 455), outline=RED, fill=PANEL, width=4, radius=20)
        center(draw, "STRUMER_A_v1_3_waveform.png not found", 250, FONT_MED, RED)
        center(draw, "place the published artifact in this folder", 330, FONT_SMALL, WHITE)

    return img, duration


def artifact_slide(duration=5.6):
    img = canvas()
    draw = ImageDraw.Draw(img)

    center(draw, "Generated Artifacts", 52, FONT_TITLE, GOLD)

    items = [
        "STRUMER_A_v1_3.wav",
        "STRUMER_A_v1_3_repeat.wav",
        "STRUMER_A_v1_3_changed.wav",
        "STRUMER_A_v1_3_waveform.png",
        "STRUMER_A_v1_3_VERIFY.txt",
    ]

    y = 150
    for item in items:
        f = fit_font(draw, item, 34, WIDTH - 260, 24)
        draw.text((165, y), "•", font=f, fill=ACCENT)
        draw.text((215, y), item, font=f, fill=WHITE)
        y += 66

    return img, duration


def proof_cards_slide(duration=6.4):
    img = canvas()
    draw = ImageDraw.Draw(img)

    center(draw, "Verification Proof", 45, FONT_TITLE, GOLD)

    cards = [
        ("same structure", "same audio_sha256", ACCENT),
        ("same structure", "same final_certificate", BLUE),
        ("changed structure", "changed audio_sha256", RED),
        ("incomplete", "ABSTAIN", ORANGE),
        ("conflict", "BLOCKED", RED),
        ("cross-machine", "reproducible", PURPLE),
    ]

    positions = [
        (70, 130, 590, 215),
        (690, 130, 1210, 215),
        (70, 255, 590, 340),
        (690, 255, 1210, 340),
        (70, 380, 590, 465),
        (690, 380, 1210, 465),
    ]

    for (top, bottom, color), box in zip(cards, positions):
        panel(draw, box, outline=color, fill=PANEL, width=3, radius=18)
        f1 = fit_font(draw, top, 30, box[2] - box[0] - 50, 20)
        f2 = fit_font(draw, bottom, 30, box[2] - box[0] - 50, 20)
        draw.text((box[0] + 28, box[1] + 14), top, font=f1, fill=WHITE)
        draw.text((box[0] + 28, box[1] + 48), bottom, font=f2, fill=color)

    center(draw, "same structure -> same audio -> same proof", 525, FONT_SMALL, GOLD)

    return img, duration


def challenge_slide(duration=6.0):
    img = canvas()
    draw = ImageDraw.Draw(img)

    center(draw, "Can You Break It?", 54, FONT_TITLE, GOLD)

    bullets = [
        "different audio from same structure",
        "different waveform from same structure",
        "output from incomplete structure",
        "arbitrary output from conflict",
    ]

    y = 165
    for item in bullets:
        f = fit_font(draw, item, 35, WIDTH - 230, 23)
        draw.text((150, y), "•", font=f, fill=RED)
        draw.text((205, y), item, font=f, fill=WHITE)
        y += 72

    center(draw, "If you cannot, editing was never fundamental.", 500, FONT_SMALL, ACCENT)

    return img, duration


def use_cases_slide(duration=5.8):
    img = canvas()
    draw = ImageDraw.Draw(img)

    center(draw, "Where This Matters", 55, FONT_TITLE, GOLD)

    items = [
        "scientific sonification",
        "reproducible research",
        "deterministic alerts",
        "structural UI sounds",
        "AI + structure workflows",
    ]

    y = 165
    for item in items:
        f = fit_font(draw, item, 36, WIDTH - 230, 24)
        draw.text((165, y), "•", font=f, fill=ACCENT)
        draw.text((215, y), item, font=f, fill=WHITE)
        y += 66

    return img, duration


def phase_scope_slide(duration=5.8):
    img = canvas()
    draw = ImageDraw.Draw(img)

    center(draw, "Phase I Scope", 55, FONT_TITLE, GOLD)

    panel(draw, (120, 145, 1160, 330), outline=ACCENT, fill=PANEL, width=3, radius=20)
    center(draw, "deterministic structural reference proof", 185, FONT_MED, ACCENT)
    center(draw, "not a professional DAW replacement", 255, FONT_MED, WHITE)

    panel(draw, (120, 370, 1160, 510), outline=GOLD, fill=PANEL, width=3, radius=20)
    center(draw, "run the script in the description", 405, FONT_SMALL, GOLD)
    center(draw, "verify the generated audio artifacts", 455, FONT_SMALL, WHITE)

    return img, duration


def lineage_slide(duration=5.8):
    img = canvas()
    draw = ImageDraw.Draw(img)

    center(draw, "STRUMER Family", 48, FONT_TITLE, GOLD)

    items = [
        ("STRUMER", "video", ACCENT),
        ("STRUMER-D", "diagrams", PURPLE),
        ("STRUMER-A", "audio", BLUE),
    ]

    y = 165
    for name, label, color in items:
        panel(draw, (205, y, 1075, y + 75), outline=color, fill=PANEL, width=3, radius=18)
        draw.text((245, y + 18), name, font=FONT_BODY, fill=color)
        draw.text((650, y + 18), label, font=FONT_BODY, fill=WHITE)
        y += 105

    center(draw, "Different media. Same principle.", 500, FONT_MED, GOLD)
    return img, duration


def meta_proof_slide(duration=6.0):
    img = canvas()
    draw = ImageDraw.Draw(img)

    center(draw, "Did you know?", 62, FONT_TITLE, GOLD)
    center(draw, "This video was created", 165, FONT_BIG, WHITE)
    center(draw, "from structure.", 245, FONT_BIG, ACCENT)

    center(draw, "Run the script again.", 355, FONT_MED, GOLD)
    center(draw, "same structure -> same video", 430, FONT_MED, WHITE)

    return img, duration


def final_slide(duration=6.4):
    img = canvas()
    draw = ImageDraw.Draw(img)

    center(draw, "Remove dependency", 78, FONT_BIG, WHITE)
    center(draw, "Preserve structure", 164, FONT_BIG, ACCENT)
    center(draw, "Same outcome", 250, FONT_BIG, BLUE)

    center(draw, "Join the Structural Revolution", 370, FONT_TITLE, GOLD)

    f = fit_font(draw, "https://github.com/OMPSHUNYAYA", 30, WIDTH - 220, 20)
    center(draw, "https://github.com/OMPSHUNYAYA", 505, f, WHITE)

    return img, duration


def build_slides():
    base = base_structure()

    base_samples, repeat_samples, changed_samples, source_label = load_actual_samples()

    cert_base = structure_certificate(base)

    slides = []

    slides.append(title_slide("Can audio be generated", "without editing, tuning,", "or manual sequencing?", 5.0))
    slides.append(statement_slide("A tiny script", "proves audio can", "emerge from structure", 5.0))
    slides.append(statement_slide("same structure", "same audio", "same proof", 4.8))
    slides.append(statement_slide("incomplete structure", "no audio", "", 4.4, ORANGE, WHITE, WHITE))
    slides.append(statement_slide("conflicting structure", "no arbitrary audio", "", 4.4, RED, WHITE, WHITE))

    slides.append(statement_slide("audio_output", "= resolve(structure)", "", 4.4))
    slides.append(statement_slide("audio_visible iff", "audio_structure_complete AND", "audio_structure_consistent", 6.0))

    slides.append(bullets_slide(
        "Traditional Audio Workflow",
        ["open editor", "adjust waveform", "set timing", "preview and fix", "export again"],
        5.8,
        ORANGE
    ))

    slides.append(dependency_chain_slide(5.8))
    slides.append(statement_slide("What if audio", "was not edited", "but revealed?", 5.0))

    slides.append(code_slide(
        "Tiny Structure",
        [
            "events = [",
            "  tone(440, 0.28),",
            "  silence(0.08),",
            "  tone(660, 0.28),",
            "  tone(880, 0.36)",
            "]"
        ],
        "resolve(structure) -> audio",
        6.2
    ))

    slides.append(statement_slide("The script generates", "3 audio files", "and one waveform proof", 5.0, GOLD, ACCENT, WHITE))
    slides.append(statement_slide("Waveforms shown here", "come from the actual", "generated WAV outputs", 5.2, GOLD, WHITE, ACCENT))
    slides.append(artifact_slide(5.8))

    slides.append(actual_waveform_artifact_slide(7.0))
    slides.append(statement_slide("Original and repeat", "resolve identically", "changed structure resolves differently", 6.0, ACCENT, BLUE, RED))
    slides.append(proof_cards_slide(6.0))

    slides.append(statement_slide("Tools may render audio", "Structure determines it", "", 5.0, WHITE, ACCENT, WHITE))
    slides.append(statement_slide("Editing did not create", "the audio", "Structure did", 5.2, GOLD, WHITE, ACCENT))
    slides.append(statement_slide("This is not optimization", "This is", "dependency elimination", 5.2, WHITE, GOLD, ACCENT))

    slides.append(statement_slide("Audio is not edited", "It is revealed", "by structure", 5.2))
    slides.append(statement_slide("The waveform is not", "manually shaped", "It resolves", 5.2, GOLD, WHITE, ACCENT))

    slides.append(use_cases_slide(5.8))
    slides.append(challenge_slide(6.0))
    slides.append(phase_scope_slide(5.8))
    slides.append(lineage_slide(5.8))

    slides.append(statement_slide("If output remains", "after removing dependency", "dependency was not fundamental", 6.0, WHITE, GOLD, ACCENT))
    slides.append(statement_slide("Tiny structure", "Audible reality", "Deterministic outcome", 5.8))
    slides.append(meta_proof_slide(6.0))
    slides.append(final_slide(6.4))

    return slides


def to_bgr(img):
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def write_hold(writer, img, seconds):
    frame = to_bgr(img)
    count = max(1, int(round(seconds * FPS)))
    for _ in range(count):
        writer.write(frame)


def write_fade(writer, img_a, img_b):
    frames = max(1, int(round(FADE_SECONDS * FPS)))
    a = np.array(img_a).astype(np.float32)
    b = np.array(img_b).astype(np.float32)

    for i in range(frames):
        t = (i + 1) / frames
        mixed = (a * (1.0 - t) + b * t).astype(np.uint8)
        writer.write(cv2.cvtColor(mixed, cv2.COLOR_RGB2BGR))


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build():
    slides = build_slides()

    writer = cv2.VideoWriter(
        OUT_VIDEO,
        cv2.VideoWriter_fourcc(*"mp4v"),
        FPS,
        (WIDTH, HEIGHT)
    )

    total_video_seconds = 0.0

    for i, (img, duration) in enumerate(slides):
        hold = max(0.1, duration - (FADE_SECONDS if i < len(slides) - 1 else 0))
        write_hold(writer, img, hold)
        total_video_seconds += hold

        if i < len(slides) - 1:
            write_fade(writer, img, slides[i + 1][0])
            total_video_seconds += FADE_SECONDS

    writer.release()

    print("STRUMER-A Video v" + VERSION)
    print("Created:", OUT_VIDEO)
    print("Duration seconds:", round(total_video_seconds, 2))
    print("Final SHA256:", file_sha256(OUT_VIDEO))
    print("Principle: audio_output = resolve(structure)")
    print("Final law: audio_visible iff audio_structure_complete AND audio_structure_consistent")


if __name__ == "__main__":
    build()
