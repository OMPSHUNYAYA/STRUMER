#!/usr/bin/env python3
import hashlib
import math
import wave
import struct
from copy import deepcopy
from datetime import datetime

VERSION = "1.3"
SAMPLE_RATE = 44100
OUTPUT_FILE = "STRUMER_A_v1_3.wav"
OUTPUT_FILE_REPEAT = "STRUMER_A_v1_3_repeat.wav"
OUTPUT_FILE_CHANGED = "STRUMER_A_v1_3_changed.wav"
WAVEFORM_FILE = "STRUMER_A_v1_3_waveform.png"
VERIFY_FILE = "STRUMER_A_v1_3_VERIFY.txt"
MAX_AMPLITUDE = 32767

WIDTH = 1400
HEIGHT = 720

BG = (5, 8, 15)
PANEL = (12, 18, 32)
WHITE = (245, 248, 252)
MUTED = (190, 202, 222)
GOLD = (255, 215, 120)
ACCENT = (100, 255, 180)
BLUE = (120, 170, 255)
RED = (255, 105, 125)
LINE = (70, 85, 115)


def canonical_text(value):
    if isinstance(value, dict):
        parts = []
        for key in sorted(value):
            parts.append(str(key) + "=" + canonical_text(value[key]))
        return "{" + "|".join(parts) + "}"

    if isinstance(value, list):
        return "[" + "|".join(canonical_text(item) for item in value) + "]"

    if isinstance(value, tuple):
        return "(" + "|".join(canonical_text(item) for item in value) + ")"

    if isinstance(value, float):
        return format(value, ".12g")

    return str(value)


def sha256_hex(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def short_hash(text):
    return sha256_hex(text)[:16]


def structure_signature(structure):
    return sha256_hex(canonical_text(structure))


def structure_certificate(structure):
    return structure_signature(structure)[:16]


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def result(state, reason, structure=None, payload=None):
    data = {"state": state, "reason": reason}

    if structure is not None:
        data["structure_signature"] = structure_signature(structure)
        data["structure_certificate"] = structure_certificate(structure)

    if payload:
        data.update(payload)

    data["resolution_signature"] = short_hash(canonical_text(data))
    return data


def resolve_audio(structure):
    required = ["title", "sample_rate", "events"]
    missing = [key for key in required if key not in structure]

    if missing:
        return result("ABSTAIN", "missing audio structure", structure, {"missing": ",".join(missing)})

    if structure["sample_rate"] != SAMPLE_RATE:
        return result("BLOCKED", "unsupported sample rate", structure, {"sample_rate": structure["sample_rate"]})

    events = structure["events"]

    if not events:
        return result("ABSTAIN", "no audio events supplied", structure)

    total_duration = 0.0

    for index, event in enumerate(events):
        if "kind" not in event or "duration" not in event:
            return result("ABSTAIN", "audio event incomplete", structure, {"event_index": index})

        if event["duration"] <= 0:
            return result("BLOCKED", "event duration must be positive", structure, {"event_index": index})

        if event["kind"] == "tone":
            for key in ["frequency", "amplitude"]:
                if key not in event:
                    return result("ABSTAIN", "tone event incomplete", structure, {"event_index": index, "missing": key})

            if event["frequency"] <= 0:
                return result("BLOCKED", "frequency must be positive", structure, {"event_index": index})

            if event["amplitude"] < 0 or event["amplitude"] > 1:
                return result("BLOCKED", "amplitude outside allowed range", structure, {"event_index": index})

        elif event["kind"] == "silence":
            pass

        else:
            return result("BLOCKED", "unsupported audio event kind", structure, {"event_index": index, "kind": event["kind"]})

        total_duration += event["duration"]

    return result(
        "RESOLVED",
        "complete structural audio",
        structure,
        {
            "title": structure["title"],
            "event_count": len(events),
            "duration_seconds": round(total_duration, 3),
            "sample_rate": structure["sample_rate"]
        }
    )


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
    samples = []

    for i in range(count):
        t = i / SAMPLE_RATE
        env = envelope(i, count)
        value = math.sin(2.0 * math.pi * frequency * t)
        sample = int(MAX_AMPLITUDE * amplitude * env * value)
        samples.append(sample)

    return samples


def silence_samples(duration):
    count = int(round(duration * SAMPLE_RATE))
    return [0] * count


def synthesize_audio(structure):
    samples = []

    for event in structure["events"]:
        if event["kind"] == "tone":
            samples.extend(tone_samples(event["frequency"], event["duration"], event["amplitude"]))
        elif event["kind"] == "silence":
            samples.extend(silence_samples(event["duration"]))

    return samples


def write_wav(path, samples):
    with wave.open(path, "w") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)

        frames = bytearray()
        for sample in samples:
            frames.extend(struct.pack("<h", sample))

        out.writeframes(frames)


def generate_audio(structure, output_path):
    resolved = resolve_audio(structure)

    if resolved["state"] != "RESOLVED":
        return resolved, []

    samples = synthesize_audio(structure)
    write_wav(output_path, samples)

    resolved["audio_sha256"] = file_sha256(output_path)
    resolved["sample_count"] = len(samples)
    resolved["output_file"] = output_path
    resolved["final_certificate"] = short_hash(
        resolved["structure_signature"] + "|" + resolved["audio_sha256"]
    )

    return resolved, samples


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


def incomplete_structure():
    return {
        "title": "Incomplete STRUMER-A Audio",
        "sample_rate": SAMPLE_RATE
    }


def conflicting_structure():
    return {
        "title": "Conflicting STRUMER-A Audio",
        "sample_rate": SAMPLE_RATE,
        "events": [
            {"kind": "tone", "frequency": -440.0, "duration": 0.20, "amplitude": 0.40}
        ]
    }


def changed_structure():
    structure = deepcopy(base_structure())
    structure["events"][2]["frequency"] = 990.0
    return structure


def result_lines(label, resolved):
    lines = []
    lines.append(label + " state: " + resolved["state"])
    lines.append(label + " reason: " + resolved["reason"])

    if "structure_certificate" in resolved:
        lines.append(label + " structure_certificate: " + resolved["structure_certificate"])

    if "structure_signature" in resolved:
        lines.append(label + " structure_signature: " + resolved["structure_signature"])

    lines.append(label + " resolution_signature: " + resolved["resolution_signature"])

    if "output_file" in resolved:
        lines.append(label + " output: " + resolved["output_file"])
        lines.append(label + " audio_sha256: " + resolved["audio_sha256"])
        lines.append(label + " sample_count: " + str(resolved["sample_count"]))
        lines.append(label + " final_certificate: " + resolved["final_certificate"])

    return lines


def print_result(label, resolved):
    for line in result_lines(label, resolved):
        print(line)


def load_font(size):
    try:
        from PIL import ImageFont
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        try:
            from PIL import ImageFont
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except Exception:
            from PIL import ImageFont
            return ImageFont.load_default()


def draw_text(draw, xy, text, fill, size=22):
    draw.text(xy, text, fill=fill, font=load_font(size))


def draw_center(draw, y, text, fill, size=28):
    font = load_font(size)
    try:
        box = draw.textbbox((0, 0), text, font=font)
        w = box[2] - box[0]
    except Exception:
        w = len(text) * size // 2
    draw.text(((WIDTH - w) // 2, y), text, fill=fill, font=font)


def draw_wave_panel(draw, samples, box, label, certificate, audio_hash, color):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=20, fill=PANEL, outline=LINE, width=2)

    draw_text(draw, (x1 + 22, y1 + 16), label, GOLD, 24)
    draw_text(draw, (x1 + 22, y1 + 48), "structure_certificate: " + certificate, MUTED, 18)
    draw_text(draw, (x1 + 22, y1 + 72), "audio_sha256: " + audio_hash[:32] + "...", MUTED, 18)

    wave_top = y1 + 112
    wave_bottom = y2 - 28
    mid = (wave_top + wave_bottom) // 2
    height = (wave_bottom - wave_top) // 2 - 4

    draw.line((x1 + 22, mid, x2 - 22, mid), fill=LINE, width=1)

    usable_width = x2 - x1 - 44
    if usable_width <= 0 or not samples:
        return

    step = max(1, len(samples) // usable_width)
    points = []

    for px in range(usable_width):
        start = px * step
        end = min(len(samples), start + step)
        segment = samples[start:end]

        if not segment:
            amp = 0
        else:
            amp = max(segment, key=abs)

        x = x1 + 22 + px
        y = mid - int((amp / MAX_AMPLITUDE) * height)
        points.append((x, y))

    if len(points) >= 2:
        draw.line(points, fill=color, width=2)


def create_waveform_image(samples_1, samples_2, samples_5, resolved_1, resolved_2, resolved_5):
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return None

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    draw_center(draw, 28, "STRUMER-A v" + VERSION + " Structural Audio Resolution", GOLD, 34)
    draw_center(draw, 72, "same structure -> same waveform | changed structure -> changed waveform", WHITE, 22)

    draw_wave_panel(
        draw,
        samples_1,
        (48, 120, WIDTH - 48, 285),
        "Case 1: Original",
        resolved_1["structure_certificate"],
        resolved_1["audio_sha256"],
        ACCENT
    )

    draw_wave_panel(
        draw,
        samples_2,
        (48, 305, WIDTH - 48, 470),
        "Case 2: Repeat",
        resolved_2["structure_certificate"],
        resolved_2["audio_sha256"],
        BLUE
    )

    draw_wave_panel(
        draw,
        samples_5,
        (48, 490, WIDTH - 48, 655),
        "Case 5: Changed structure",
        resolved_5["structure_certificate"],
        resolved_5["audio_sha256"],
        RED
    )

    draw_center(draw, 674, "Final law: audio_visible iff audio_structure_complete AND audio_structure_consistent", MUTED, 18)

    img.save(WAVEFORM_FILE)
    return WAVEFORM_FILE


def write_verify_report(results, checks, waveform_file):
    lines = []
    lines.append("STRUMER-A v" + VERSION + " VERIFY REPORT")
    lines.append("Structural Audio Resolution")
    lines.append("")
    lines.append("Generated: " + datetime.now().isoformat(timespec="seconds"))
    lines.append("")
    lines.append("Principle: audio_output = resolve(structure)")
    lines.append("Final law: audio_visible iff audio_structure_complete AND audio_structure_consistent")
    lines.append("")
    lines.append("Core guarantees:")
    lines.append("same structure -> same structure_signature")
    lines.append("same structure -> same audio_sha256")
    lines.append("same structure -> same final_certificate")
    lines.append("changed structure -> changed structure_signature")
    lines.append("changed structure -> changed audio_sha256")
    lines.append("incomplete structure -> ABSTAIN")
    lines.append("conflicting structure -> BLOCKED")
    lines.append("")
    lines.append("Generated files:")
    lines.append(OUTPUT_FILE)
    lines.append(OUTPUT_FILE_REPEAT)
    lines.append(OUTPUT_FILE_CHANGED)

    if waveform_file:
        lines.append(waveform_file)

    lines.append("")
    lines.append("Results:")
    lines.append("")

    for label, resolved in results:
        lines.extend(result_lines(label, resolved))
        lines.append("")

    lines.append("Verification checks:")
    for name, passed in checks:
        lines.append(name + ": " + ("PASS" if passed else "FAIL"))

    lines.append("")
    lines.append("Conclusion:")
    if all(passed for _, passed in checks):
        lines.append("PASS - STRUMER-A v" + VERSION + " deterministic structural audio proof verified.")
    else:
        lines.append("FAIL - one or more verification checks did not pass.")

    with open(VERIFY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    print("STRUMER-A v" + VERSION)
    print("Structural Audio Resolution")
    print("Principle: audio_output = resolve(structure)")
    print("Guarantee: same structure -> same structure signature -> same audio -> same SHA-256")
    print()

    resolved_1, samples_1 = generate_audio(base_structure(), OUTPUT_FILE)
    print_result("Case 1", resolved_1)
    print()

    resolved_2, samples_2 = generate_audio(base_structure(), OUTPUT_FILE_REPEAT)
    print_result("Case 2 repeat", resolved_2)
    print()

    same_structure = resolved_1.get("structure_signature") == resolved_2.get("structure_signature")
    same_audio = resolved_1.get("audio_sha256") == resolved_2.get("audio_sha256")
    same_certificate = resolved_1.get("final_certificate") == resolved_2.get("final_certificate")

    print("Structure determinism check:", "PASS" if same_structure else "FAIL")
    print("Audio determinism check:", "PASS" if same_audio else "FAIL")
    print("Final certificate check:", "PASS" if same_certificate else "FAIL")
    print()

    resolved_3 = resolve_audio(incomplete_structure())
    print_result("Case 3 incomplete", resolved_3)
    print()

    resolved_4 = resolve_audio(conflicting_structure())
    print_result("Case 4 conflicting", resolved_4)
    print()

    resolved_5, samples_5 = generate_audio(changed_structure(), OUTPUT_FILE_CHANGED)
    print_result("Case 5 changed", resolved_5)
    print()

    changed_structure_differs = resolved_1.get("structure_signature") != resolved_5.get("structure_signature")
    changed_audio_differs = resolved_1.get("audio_sha256") != resolved_5.get("audio_sha256")
    changed_certificate_differs = resolved_1.get("final_certificate") != resolved_5.get("final_certificate")
    incomplete_abstains = resolved_3.get("state") == "ABSTAIN"
    conflicting_blocks = resolved_4.get("state") == "BLOCKED"

    print("Structure change signature check:", "PASS" if changed_structure_differs else "FAIL")
    print("Structure change audio check:", "PASS" if changed_audio_differs else "FAIL")
    print("Structure change final certificate check:", "PASS" if changed_certificate_differs else "FAIL")
    print("Incomplete structure check:", "PASS" if incomplete_abstains else "FAIL")
    print("Conflicting structure check:", "PASS" if conflicting_blocks else "FAIL")
    print()

    waveform_file = create_waveform_image(samples_1, samples_2, samples_5, resolved_1, resolved_2, resolved_5)

    checks = [
        ("Structure determinism check", same_structure),
        ("Audio determinism check", same_audio),
        ("Final certificate check", same_certificate),
        ("Structure change signature check", changed_structure_differs),
        ("Structure change audio check", changed_audio_differs),
        ("Structure change final certificate check", changed_certificate_differs),
        ("Incomplete structure check", incomplete_abstains),
        ("Conflicting structure check", conflicting_blocks),
        ("Waveform image generated", waveform_file is not None)
    ]

    results = [
        ("Case 1", resolved_1),
        ("Case 2 repeat", resolved_2),
        ("Case 3 incomplete", resolved_3),
        ("Case 4 conflicting", resolved_4),
        ("Case 5 changed", resolved_5)
    ]

    write_verify_report(results, checks, waveform_file)

    print("Waveform image:", waveform_file if waveform_file else "not generated")
    print("Verify report:", VERIFY_FILE)
    print()
    print("Final law: audio_visible iff audio_structure_complete AND audio_structure_consistent")


if __name__ == "__main__":
    main()
