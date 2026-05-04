#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import hashlib
import math
import os

WIDTH = 1280
HEIGHT = 720

BG = (5, 8, 16)
PANEL = (10, 16, 29)
PANEL_DARK = (8, 12, 22)
CARD = (11, 16, 28)
WHITE = (245, 248, 252)
MUTED = (205, 216, 235)
GOLD = (255, 202, 92)
ACCENT = (120, 230, 190)
BLUE = (110, 165, 255)
PURPLE = (175, 130, 255)
TEAL = (80, 210, 190)
LINE = (48, 62, 94)
GREEN = (90, 235, 160)
ORANGE = (255, 165, 60)
RED = (255, 95, 115)

VERSION = "2.0"


def font(size, bold=False):
    try:
        if os.name == "nt":
            path = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
        else:
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


FONT_TITLE = font(34, True)
FONT_SUBTITLE = font(18, True)
FONT_PANEL = font(20, True)
FONT_LABEL = font(16, True)
FONT_TEXT = font(15)
FONT_SMALL = font(13)
FONT_TINY = font(10)
FONT_NODE = font(17, True)
FONT_STATE = font(23, True)
FONT_BAR = font(13, True)


def structural_signature(payload):
    normalized = "|".join(f"{k}={payload[k]}" for k in sorted(payload))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def result(state, reason, kind, payload=None):
    data = {"state": state, "reason": reason, "kind": kind}
    if payload:
        data.update(payload)
    data["signature"] = structural_signature(data)
    return data


def resolve(structure):
    if "type" not in structure:
        return result("ABSTAIN", "missing diagram type", "none")

    kind = structure["type"]

    if kind == "flowchart":
        return resolve_flowchart(structure)

    if kind == "mindmap":
        return resolve_mindmap(structure)

    if kind == "sequence":
        return resolve_sequence(structure)

    if kind == "shape":
        return resolve_shape(structure)

    return result("BLOCKED", "unsupported diagram type", "none", {"type": kind})


def resolve_flowchart(structure):
    required = ["nodes", "edges", "layout"]
    missing = [key for key in required if key not in structure]

    if missing:
        return result("ABSTAIN", "missing flowchart structure", "flowchart", {"missing": ",".join(missing)})

    nodes = structure["nodes"]
    edges = structure["edges"]
    layout = structure["layout"]

    if not nodes:
        return result("ABSTAIN", "no nodes supplied", "flowchart")

    node_ids = [node["id"] for node in nodes if "id" in node]

    if len(node_ids) != len(nodes):
        return result("BLOCKED", "node missing id", "flowchart")

    if len(set(node_ids)) != len(node_ids):
        return result("BLOCKED", "duplicate node id", "flowchart")

    valid_ids = set(node_ids)

    for edge in edges:
        if edge[0] not in valid_ids or edge[1] not in valid_ids:
            return result("BLOCKED", "edge references missing node", "flowchart")

    if layout != "horizontal":
        return result("BLOCKED", "unsupported layout: horizontal only", "flowchart", {"layout": layout})

    return result(
        "RESOLVED",
        "complete flowchart",
        "flowchart",
        {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "layout": layout,
            "source_nodes": nodes,
            "source_edges": edges
        }
    )


def resolve_mindmap(structure):
    required = ["center", "central_label", "branches"]
    missing = [key for key in required if key not in structure]

    if missing:
        return result("ABSTAIN", "missing mindmap structure", "mindmap", {"missing": ",".join(missing)})

    branches = structure["branches"]

    if len(branches) < 2:
        return result("BLOCKED", "mindmap needs at least 2 branches", "mindmap")

    return result(
        "RESOLVED",
        "complete mindmap",
        "mindmap",
        {
            "branch_count": len(branches),
            "central_label": structure["central_label"],
            "source_center": structure["center"],
            "source_branches": branches
        }
    )


def resolve_sequence(structure):
    required = ["participants", "messages"]
    missing = [key for key in required if key not in structure]

    if missing:
        return result("ABSTAIN", "missing sequence structure", "sequence", {"missing": ",".join(missing)})

    participants = structure["participants"]
    messages = structure["messages"]

    if len(participants) < 2:
        return result("BLOCKED", "sequence needs at least 2 participants", "sequence")

    participant_ids = [participant["id"] for participant in participants]

    if len(set(participant_ids)) != len(participant_ids):
        return result("BLOCKED", "duplicate participant id", "sequence")

    valid_ids = set(participant_ids)

    for message in messages:
        if message[0] not in valid_ids or message[1] not in valid_ids:
            return result("BLOCKED", "message references unknown participant", "sequence")

    return result(
        "RESOLVED",
        "complete sequence",
        "sequence",
        {
            "participant_count": len(participants),
            "message_count": len(messages),
            "source_participants": participants,
            "source_messages": messages
        }
    )


def resolve_shape(structure):
    required = ["points", "radius", "center", "rotation_deg"]
    missing = [key for key in required if key not in structure]

    if missing:
        return result("ABSTAIN", "missing shape structure", "shape", {"missing": ",".join(missing)})

    if structure["points"] < 3:
        return result("BLOCKED", "shape needs at least 3 points", "shape")

    if structure["radius"] <= 0:
        return result("BLOCKED", "radius must be positive", "shape")

    return result(
        "RESOLVED",
        "complete polygon",
        "shape",
        {
            "points": structure["points"],
            "radius": structure["radius"],
            "center_point": structure["center"],
            "rotation_deg": structure["rotation_deg"]
        }
    )


def text_size(draw, text, active_font):
    bbox = draw.textbbox((0, 0), text, font=active_font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def centered(draw, text, y, active_font, color, width=WIDTH):
    text_width, _ = text_size(draw, text, active_font)
    draw.text(((width - text_width) // 2, y), text, font=active_font, fill=color)


def rounded(draw, box, radius=18, fill=CARD, outline=LINE, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_arrow(draw, start, end, color=ACCENT, width=4):
    x1, y1 = start
    x2, y2 = end

    draw.line((x1, y1, x2, y2), fill=color, width=width)

    if abs(x2 - x1) >= abs(y2 - y1):
        if x2 >= x1:
            arrow = [(x2, y2), (x2 - 15, y2 - 9), (x2 - 15, y2 + 9)]
        else:
            arrow = [(x2, y2), (x2 + 15, y2 - 9), (x2 + 15, y2 + 9)]
    else:
        if y2 >= y1:
            arrow = [(x2, y2), (x2 - 9, y2 - 15), (x2 + 9, y2 - 15)]
        else:
            arrow = [(x2, y2), (x2 - 9, y2 + 15), (x2 + 9, y2 + 15)]

    draw.polygon(arrow, fill=color)


def draw_node(draw, x, y, width, height, label, color=BLUE, center=False):
    box = (x - width // 2, y - height // 2, x + width // 2, y + height // 2)
    fill = (18, 28, 49) if not center else (30, 24, 58)
    draw.rounded_rectangle(box, radius=16, fill=fill, outline=color, width=2)

    text_width, text_height = text_size(draw, label, FONT_NODE)
    draw.text((x - text_width // 2, y - text_height // 2 - 1), label, font=FONT_NODE, fill=WHITE)


def base_canvas(diagram_title, subtitle, color):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    rounded(draw, (42, 34, 1238, 492), radius=26, fill=PANEL, outline=color, width=3)
    centered(draw, diagram_title, 38, FONT_PANEL, GOLD)
    centered(draw, subtitle, 68, FONT_SMALL, MUTED)

    return img, draw


def draw_bottom_panel(draw, title, structure_lines, resolved, color):
    rounded(draw, (42, 520, 1238, 692), radius=22, fill=PANEL_DARK, outline=LINE, width=2)

    draw.text((66, 542), "STRUMER-D v" + VERSION, font=FONT_TITLE, fill=GOLD)
    draw.text((66, 586), title, font=FONT_SUBTITLE, fill=WHITE)

    draw.text((430, 542), "Structure", font=FONT_LABEL, fill=color)
    y = 570

    for line in structure_lines:
        draw.text((430, y), line, font=FONT_SMALL, fill=WHITE if line else MUTED)
        y += 20

    state_color = GREEN if resolved["state"] == "RESOLVED" else ORANGE if resolved["state"] == "ABSTAIN" else RED

    draw.text((760, 542), "Resolution", font=FONT_LABEL, fill=GOLD)
    draw.text((760, 574), resolved["state"], font=FONT_STATE, fill=state_color)
    draw.text((760, 614), resolved["reason"], font=FONT_SMALL, fill=WHITE)
    draw.text((760, 642), "sig = " + resolved["signature"], font=FONT_SMALL, fill=color)

    draw.text((1010, 546), "Core Law", font=FONT_LABEL, fill=GOLD)
    draw.text((1010, 582), "diagram != drawing", font=FONT_SMALL, fill=WHITE)
    draw.text((1010, 606), "diagram = resolve(structure)", font=FONT_SMALL, fill=color)
    draw.text((1010, 642), "same structure -> same diagram", font=FONT_SMALL, fill=ACCENT)


def draw_flowchart_top(draw, resolved):
    box = (150, 172, 1130, 380)
    nodes = resolved["source_nodes"]
    edges = resolved["source_edges"]
    positions = {}
    start_x = box[0] + 125
    gap = 245
    y = (box[1] + box[3]) // 2

    for index, node in enumerate(nodes):
        positions[node["id"]] = {
            "x": start_x + index * gap,
            "y": y,
            "label": node["label"],
            "w": 170,
            "h": 68
        }

    for edge in edges:
        a = positions[edge[0]]
        b = positions[edge[1]]
        draw_arrow(draw, (a["x"] + a["w"] // 2, a["y"]), (b["x"] - b["w"] // 2, b["y"]), ACCENT, 5)

    for node in positions.values():
        draw_node(draw, node["x"], node["y"], node["w"], node["h"], node["label"], BLUE)


def draw_mindmap_top(draw, resolved):
    center_x = 640
    center_y = 286
    branches = resolved["source_branches"]
    radius = 164
    positions = []

    for index, branch in enumerate(branches):
        angle = math.radians(index * (360 / len(branches)) - 90)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        positions.append((int(round(x)), int(round(y)), branch["label"]))

    for x, y, label in positions:
        draw.line((center_x, center_y, x, y), fill=PURPLE, width=5)

    draw_node(draw, center_x, center_y, 178, 64, resolved["central_label"], GOLD, True)

    for x, y, label in positions:
        draw_node(draw, x, y, 148, 50, label, PURPLE)


def draw_sequence_top(draw, resolved):
    participants = resolved["source_participants"]
    messages = resolved["source_messages"]
    positions = {}
    start_x = 230
    gap = 275
    y_top = 158
    y_bottom = 430

    for index, participant in enumerate(participants):
        x = start_x + index * gap
        positions[participant["id"]] = {"x": x, "label": participant["label"]}
        draw_node(draw, x, y_top, 150, 52, participant["label"], TEAL)
        draw.line((x, y_top + 34, x, y_bottom), fill=(70, 90, 110), width=2)

    y = y_top + 92

    for index, message in enumerate(messages):
        src, dst, label = message
        start = positions[src]
        end = positions[dst]
        color = TEAL if index % 2 == 0 else BLUE

        draw.line((start["x"], y, end["x"], y), fill=color, width=4)

        if end["x"] > start["x"]:
            arrow = [(end["x"] - 11, y - 7), (end["x"], y), (end["x"] - 11, y + 7)]
        else:
            arrow = [(end["x"] + 11, y - 7), (end["x"], y), (end["x"] + 11, y + 7)]

        draw.polygon(arrow, fill=color)

        label_width, _ = text_size(draw, label, FONT_SMALL)
        draw.text(((start["x"] + end["x"]) // 2 - label_width // 2, y - 22), label, font=FONT_SMALL, fill=WHITE)

        y += 48


def draw_polygon_top(draw, resolved):
    points = resolved["points"]
    radius = 155
    center_x = 640
    center_y = 270
    rotation = resolved["rotation_deg"]
    vertices = []

    for index in range(points):
        angle = math.radians(rotation + index * (360 / points))
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        vertices.append((int(round(x)), int(round(y))))

    draw.polygon(vertices, fill=(34, 30, 48), outline=GOLD)
    draw.line(vertices + [vertices[0]], fill=WHITE, width=3)

    for x, y in vertices:
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=ACCENT)

    draw.ellipse((center_x - 8, center_y - 8, center_x + 8, center_y + 8), fill=GOLD)


def overview_card(draw, box, title, resolved, color):
    rounded(draw, box, radius=18, fill=PANEL, outline=color, width=2)

    draw.text((box[0] + 18, box[1] + 16), title, font=FONT_LABEL, fill=color)

    state_color = GREEN if resolved["state"] == "RESOLVED" else ORANGE if resolved["state"] == "ABSTAIN" else RED

    draw.text((box[0] + 18, box[1] + 52), resolved["state"], font=FONT_STATE, fill=state_color)
    draw.text((box[0] + 18, box[1] + 90), "sig = " + resolved["signature"], font=FONT_SMALL, fill=color)


def create_overview(results):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    centered(draw, "STRUMER-D v" + VERSION, 32, FONT_TITLE, GOLD)
    centered(draw, "STRUMER for Diagrams - Diagrams Without Drawing", 78, FONT_SUBTITLE, WHITE)
    centered(draw, "4 diagram domains | 1 resolver | zero manual drawing | same structure -> same output", 110, FONT_BAR, MUTED)

    overview_card(draw, (72, 178, 352, 318), "Flowchart", results["flowchart"], ACCENT)
    overview_card(draw, (384, 178, 664, 318), "Mind Map", results["mindmap"], PURPLE)
    overview_card(draw, (696, 178, 976, 318), "Sequence", results["sequence"], TEAL)
    overview_card(draw, (72, 354, 352, 494), "Polygon", results["shape"], GOLD)
    overview_card(draw, (384, 354, 664, 494), "Incomplete", results["abstain"], ORANGE)
    overview_card(draw, (696, 354, 976, 494), "Conflicting", results["blocked"], RED)
    overview_card(draw, (1010, 354, 1210, 494), "Unsupported", results["unsupported"], RED)

    rounded(draw, (1010, 178, 1210, 318), radius=20, fill=PANEL_DARK, outline=LINE, width=2)

    draw.text((1032, 204), "Core Law", font=FONT_PANEL, fill=GOLD)
    draw.text((1032, 250), "diagram != drawing", font=FONT_SMALL, fill=WHITE)
    draw.text((1032, 278), "diagram = resolve", font=FONT_SMALL, fill=ACCENT)

    rounded(draw, (92, 602, 1188, 656), radius=18, fill=PANEL_DARK, outline=LINE, width=2)
    centered(draw, "diagram_output = resolve(structure) | diagram_visible iff structure_complete AND structure_consistent", 621, FONT_BAR, ACCENT)

    img.save("STRUMER_D_v2_0_overview.png")


def create_flowchart(resolved):
    img, draw = base_canvas("Flowchart Resolution", "nodes + edges + horizontal layout -> visible diagram", ACCENT)
    draw_flowchart_top(draw, resolved)
    draw_bottom_panel(draw, "Flowchart Resolution", ["type = flowchart", "nodes = Request, Gateway, Logic, Store", "edges = request->gateway->logic->store", "layout = horizontal"], resolved, ACCENT)
    img.save("STRUMER_D_v2_0_flowchart.png")


def create_mindmap(resolved):
    img, draw = base_canvas("Mind Map Resolution", "central concept + branches -> visible diagram", PURPLE)
    draw_mindmap_top(draw, resolved)
    draw_bottom_panel(draw, "Mind Map Resolution", ["type = mindmap", "center = STRUMER-D", "branches = Structure, Diagram, Resolve", "branches += Signature, Safety"], resolved, PURPLE)
    img.save("STRUMER_D_v2_0_mindmap.png")


def create_sequence(resolved):
    img, draw = base_canvas("Sequence Diagram Resolution", "participants + messages -> visible interaction structure", TEAL)
    draw_sequence_top(draw, resolved)
    draw_bottom_panel(draw, "Sequence Diagram Resolution", ["type = sequence", "participants = User, Auth, Cache, Store", "messages = request, check, verify", "messages += record, session"], resolved, TEAL)
    img.save("STRUMER_D_v2_0_sequence.png")


def create_polygon(resolved):
    img, draw = base_canvas("Polygon Resolution", "points + radius + center + rotation -> visible shape", GOLD)
    draw_polygon_top(draw, resolved)
    draw_bottom_panel(draw, "Polygon Resolution", ["type = shape", "points = 6", "radius = 76", "rotation = -30"], resolved, GOLD)
    img.save("STRUMER_D_v2_0_polygon.png")


def build_structures():
    flowchart = {
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
    }

    mindmap = {
        "type": "mindmap",
        "center": (0, 0),
        "central_label": "STRUMER-D",
        "branches": [
            {"id": "b1", "label": "Structure"},
            {"id": "b2", "label": "Diagram"},
            {"id": "b3", "label": "Resolve"},
            {"id": "b4", "label": "Signature"},
            {"id": "b5", "label": "Safety"}
        ]
    }

    sequence = {
        "type": "sequence",
        "participants": [
            {"id": "u", "label": "User"},
            {"id": "a", "label": "Auth"},
            {"id": "c", "label": "Cache"},
            {"id": "d", "label": "Store"}
        ],
        "messages": [
            ("u", "a", "request"),
            ("a", "c", "check"),
            ("a", "d", "verify"),
            ("d", "a", "record"),
            ("a", "u", "session")
        ]
    }

    shape = {
        "type": "shape",
        "points": 6,
        "radius": 76,
        "center": (0, 0),
        "rotation_deg": -30
    }

    incomplete = {
        "type": "flowchart",
        "nodes": [
            {"id": "input", "label": "Input"},
            {"id": "output", "label": "Output"}
        ],
        "layout": "horizontal"
    }

    conflicting = {
        "type": "sequence",
        "participants": [
            {"id": "u", "label": "User"},
            {"id": "a", "label": "Auth"}
        ],
        "messages": [
            ("u", "missing", "request")
        ]
    }

    unsupported = {
        "type": "flowchart",
        "nodes": [
            {"id": "top", "label": "Top"},
            {"id": "bottom", "label": "Bottom"}
        ],
        "edges": [
            ("top", "bottom")
        ],
        "layout": "vertical"
    }

    return {
        "flowchart": resolve(flowchart),
        "mindmap": resolve(mindmap),
        "sequence": resolve(sequence),
        "shape": resolve(shape),
        "abstain": resolve(incomplete),
        "blocked": resolve(conflicting),
        "unsupported": resolve(unsupported)
    }


def main():
    results = build_structures()

    create_overview(results)
    create_flowchart(results["flowchart"])
    create_mindmap(results["mindmap"])
    create_sequence(results["sequence"])
    create_polygon(results["shape"])

    print("STRUMER-D v" + VERSION)
    print("Structural Diagram Resolution")
    print("Created: STRUMER_D_v2_0_overview.png")
    print("Created: STRUMER_D_v2_0_flowchart.png")
    print("Created: STRUMER_D_v2_0_mindmap.png")
    print("Created: STRUMER_D_v2_0_sequence.png")
    print("Created: STRUMER_D_v2_0_polygon.png")
    print("Flowchart state:", results["flowchart"]["state"])
    print("Flowchart signature:", results["flowchart"]["signature"])
    print("Mindmap state:", results["mindmap"]["state"])
    print("Mindmap signature:", results["mindmap"]["signature"])
    print("Sequence state:", results["sequence"]["state"])
    print("Sequence signature:", results["sequence"]["signature"])
    print("Shape state:", results["shape"]["state"])
    print("Shape signature:", results["shape"]["signature"])
    print("Incomplete state:", results["abstain"]["state"])
    print("Incomplete signature:", results["abstain"]["signature"])
    print("Conflicting state:", results["blocked"]["state"])
    print("Conflicting signature:", results["blocked"]["signature"])
    print("Unsupported state:", results["unsupported"]["state"])
    print("Unsupported signature:", results["unsupported"]["signature"])
    print("Unsupported reason:", results["unsupported"]["reason"])
    print("Principle: diagram_visible iff diagram_structure_complete AND diagram_structure_consistent")


if __name__ == "__main__":
    main()
