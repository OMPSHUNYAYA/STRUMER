from PIL import Image, ImageDraw, ImageFont
import hashlib
import json
from copy import deepcopy

VERSION = "1.1"

image_structure = {
    "system": "STRUMER-I",
    "version": VERSION,
    "title": "Structural Object-Field Image Resolution",
    "canvas": {"width": 1280, "height": 720},
    "output": {
        "image": "STRUMER_I_v1_1.png",
        "image_repeat": "STRUMER_I_v1_1_repeat.png",
        "image_changed": "STRUMER_I_v1_1_changed.png",
        "image_incomplete": "STRUMER_I_v1_1_incomplete.png",
        "image_conflict": "STRUMER_I_v1_1_conflict.png",
        "verify": "STRUMER_I_v1_1_VERIFY.txt",
        "manifest": "STRUMER_I_v1_1_MANIFEST.json"
    },
    "state": {
        "structure_complete": True,
        "structure_consistent": True,
        "field_resolved": True,
        "visibility_admissible": True
    },
    "field": {
        "name": "canonical_object_field",
        "objects": [
            {
                "id": "origin_core",
                "kind": "core",
                "complete": True,
                "consistent": True,
                "position": [640, 358],
                "radius": 27,
                "links": ["north_arc", "east_node", "south_arc", "west_node"]
            },
            {
                "id": "north_arc",
                "kind": "arc",
                "complete": True,
                "consistent": True,
                "position": [640, 248],
                "radius": 33,
                "links": ["origin_core", "east_node", "west_node"]
            },
            {
                "id": "east_node",
                "kind": "node",
                "complete": True,
                "consistent": True,
                "position": [810, 358],
                "radius": 31,
                "links": ["origin_core", "north_arc", "south_arc"]
            },
            {
                "id": "south_arc",
                "kind": "arc",
                "complete": True,
                "consistent": True,
                "position": [640, 457],
                "radius": 33,
                "links": ["origin_core", "east_node", "west_node"]
            },
            {
                "id": "west_node",
                "kind": "node",
                "complete": True,
                "consistent": True,
                "position": [470, 358],
                "radius": 31,
                "links": ["origin_core", "north_arc", "south_arc"]
            }
        ]
    },
    "colors": {
        "background_top": [4, 9, 20],
        "background_bottom": [12, 27, 52],
        "gold": [255, 205, 70],
        "cyan": [70, 255, 220],
        "white": [245, 248, 252],
        "muted": [180, 200, 220],
        "blue": [70, 145, 255],
        "green": [92, 230, 160],
        "red": [255, 95, 95],
        "violet": [190, 120, 255],
        "panel": [8, 16, 30]
    },
    "text": {
        "title": "STRUCTURE -> IMAGE",
        "subtitle": "Structural Object-Field Resolution",
        "law_line_1": "object_visible iff object_structure_complete",
        "law_line_2": "AND object_structure_consistent",
        "identity": "same object field -> same image -> same certificate"
    },
    "layout": {
        "title_y": 24,
        "subtitle_y": 82,
        "state_y": 122,
        "diagram": [110, 190, 1170, 552],
        "law_line_1_y": 580,
        "law_line_2_y": 610,
        "identity_y": 646,
        "certificate_y": 678
    },
    "principle": "image_output = resolve(structure)",
    "law": "image_visible iff structure_complete AND structure_consistent",
    "object_law": "object_visible iff object_structure_complete AND object_structure_consistent",
    "guarantees": [
        "same object field -> same image",
        "same object field -> same certificate",
        "changed object field -> visibly changed image",
        "changed object field -> changed certificate",
        "incomplete object field -> no forced image",
        "conflicting object field -> no arbitrary image"
    ]
}


def canonical_text(value):
    if isinstance(value, dict):
        return "{" + "|".join(str(k) + "=" + canonical_text(value[k]) for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + "|".join(canonical_text(v) for v in value) + "]"
    if isinstance(value, tuple):
        return "(" + "|".join(canonical_text(v) for v in value) + ")"
    return str(value)


def render_structure(structure):
    clean = deepcopy(structure)
    clean.pop("output", None)
    return clean


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def rgb(structure, key):
    return tuple(structure["colors"][key])


def load_font(size, bold=False):
    candidates = []
    if bold:
        candidates.extend(["arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"])
    else:
        candidates.extend(["arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except:
            pass
    return ImageFont.load_default()


def text_width(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def draw_centered_text(draw, width, text, y, font, fill):
    w = text_width(draw, text, font)
    draw.text(((width - w) // 2, y), text, fill=fill, font=font)


def object_signature(obj):
    return sha256_text(canonical_text(obj))


def object_certificate(obj):
    return object_signature(obj)[:16]


def object_certificates(structure):
    return {obj["id"]: object_certificate(obj) for obj in structure["field"]["objects"]}


def object_map(structure):
    return {obj["id"]: obj for obj in structure["field"]["objects"]}


def field_state(structure):
    state = structure["state"]
    if not state.get("structure_complete", False):
        return "INCOMPLETE", "global structure incomplete"
    if not state.get("structure_consistent", False):
        return "CONFLICT", "global structure inconsistent"
    if not state.get("field_resolved", False):
        return "ABSTAIN", "object field unresolved"
    if not state.get("visibility_admissible", False):
        return "BLOCKED", "visibility not admissible"

    ids = set()
    for obj in structure["field"]["objects"]:
        if obj["id"] in ids:
            return "CONFLICT", "duplicate object identity: " + obj["id"]
        ids.add(obj["id"])
        if not obj.get("complete", False):
            return "INCOMPLETE", "object incomplete: " + obj["id"]
        if not obj.get("consistent", False):
            return "CONFLICT", "object inconsistent: " + obj["id"]

    for obj in structure["field"]["objects"]:
        for link in obj.get("links", []):
            if link not in ids:
                return "INCOMPLETE", "missing linked object: " + link

    return "RESOLVED", "object field resolved"


def structural_diff(a, b):
    diffs = []
    a_objects = {obj["id"]: obj for obj in a["field"]["objects"]}
    b_objects = {obj["id"]: obj for obj in b["field"]["objects"]}

    if a["field"]["name"] != b["field"]["name"]:
        diffs.append("field.name: " + a["field"]["name"] + " -> " + b["field"]["name"])

    for obj_id in sorted(set(a_objects) | set(b_objects)):
        if obj_id not in a_objects:
            diffs.append(obj_id + ": added")
            continue
        if obj_id not in b_objects:
            diffs.append(obj_id + ": removed")
            continue
        left = a_objects[obj_id]
        right = b_objects[obj_id]
        for key in sorted(set(left) | set(right)):
            if left.get(key) != right.get(key):
                diffs.append(obj_id + "." + key + ": " + str(left.get(key)) + " -> " + str(right.get(key)))
    return diffs


def draw_gradient_background(draw, structure):
    width = structure["canvas"]["width"]
    height = structure["canvas"]["height"]
    top = rgb(structure, "background_top")
    bottom = rgb(structure, "background_bottom")
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def draw_field_grid(draw, structure):
    x1, y1, x2, y2 = structure["layout"]["diagram"]
    draw.rounded_rectangle([x1, y1, x2, y2], radius=28, outline=rgb(structure, "blue"), width=2)
    grid = (10, 40, 82)
    for x in range(x1 + 90, x2 - 30, 80):
        draw.line([(x, y1 + 18), (x, y2 - 18)], fill=grid, width=1)
    for y in range(y1 + 52, y2 - 18, 70):
        draw.line([(x1 + 10, y), (x2 - 10, y)], fill=grid, width=1)


def draw_links(draw, structure):
    objs = object_map(structure)
    for obj in structure["field"]["objects"]:
        x1, y1 = obj["position"]
        for link in obj.get("links", []):
            target = objs.get(link)
            if target:
                x2, y2 = target["position"]
                draw.line([(x1, y1), (x2, y2)], fill=rgb(structure, "blue"), width=2)
                mx = (x1 + x2) // 2
                my = (y1 + y2) // 2
                draw.ellipse([mx - 3, my - 3, mx + 3, my + 3], fill=rgb(structure, "cyan"))


def draw_core(draw, x, y, r, structure):
    for rr in range(r + 22, r, -7):
        draw.ellipse([x - rr, y - rr, x + rr, y + rr], outline=rgb(structure, "cyan"), width=1)
    draw.ellipse([x - r, y - r, x + r, y + r], fill=rgb(structure, "white"), outline=rgb(structure, "gold"), width=4)
    draw.ellipse([x - 9, y - 9, x + 9, y + 9], fill=rgb(structure, "gold"))


def draw_node(draw, x, y, r, structure, changed=False):
    edge = rgb(structure, "violet") if changed else rgb(structure, "cyan")
    draw.ellipse([x - r, y - r, x + r, y + r], outline=edge, width=4)
    draw.ellipse([x - r + 10, y - r + 10, x + r - 10, y + r - 10], outline=rgb(structure, "gold"), width=2)
    draw.ellipse([x - 6, y - 6, x + 6, y + 6], fill=edge)


def draw_arc_object(draw, x, y, r, structure, changed=False):
    edge = rgb(structure, "violet") if changed else rgb(structure, "gold")
    for offset in range(0, 22, 7):
        draw.arc([x - r - offset, y - r - offset, x + r + offset, y + r + offset], 25, 335, fill=edge, width=2)
    draw.line([(x - r, y), (x + r, y)], fill=rgb(structure, "cyan"), width=2)
    draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill=rgb(structure, "cyan"))


def draw_object_label(draw, structure, obj):
    label_font = load_font(15, True)
    small_font = load_font(12)
    x, y = obj["position"]
    r = obj["radius"]
    cert = object_certificate(obj)[:10]

    if obj["id"] == "north_arc":
        lx, ly = x - 49, y + r + 5
    elif obj["id"] == "south_arc":
        lx, ly = x - 49, y + r + 1
    elif obj["id"] == "east_node":
        lx, ly = x - 18, y + r + 7
    elif obj["id"] == "west_node":
        lx, ly = x - 54, y + r + 7
    else:
        lx, ly = x - 49, y + r + 7

    draw.text((lx, ly), obj["id"], fill=rgb(structure, "white"), font=label_font)
    draw.text((lx, ly + 16), "id: " + cert, fill=rgb(structure, "muted"), font=small_font)


def draw_objects(draw, structure):
    changed = structure["field"]["name"] == "changed_object_field"
    for obj in structure["field"]["objects"]:
        x, y = obj["position"]
        r = obj["radius"]
        if obj["kind"] == "core":
            draw_core(draw, x, y, r, structure)
        elif obj["kind"] == "node":
            draw_node(draw, x, y, r, structure, changed)
        elif obj["kind"] == "arc":
            draw_arc_object(draw, x, y, r, structure, changed)
    for obj in structure["field"]["objects"]:
        draw_object_label(draw, structure, obj)


def draw_resolved(draw, structure, certificate, state_name, state_reason):
    width = structure["canvas"]["width"]
    text = structure["text"]
    layout = structure["layout"]

    draw_centered_text(draw, width, text["title"], layout["title_y"], load_font(46), rgb(structure, "gold"))
    draw_centered_text(draw, width, text["subtitle"], layout["subtitle_y"], load_font(26, True), rgb(structure, "white"))

    state_color = rgb(structure, "green")
    visible_state = state_name
    if structure["field"]["name"] == "changed_object_field":
        state_color = rgb(structure, "violet")
        visible_state = "RESOLVED - CHANGED OBJECT FIELD"

    draw_centered_text(draw, width, "Resolution state: " + visible_state, layout["state_y"], load_font(20, True), state_color)
    draw_centered_text(draw, width, "Resolution note: " + state_reason, layout["state_y"] + 24, load_font(18), rgb(structure, "muted"))

    draw_field_grid(draw, structure)
    draw_links(draw, structure)
    draw_objects(draw, structure)

    draw_centered_text(draw, width, text["law_line_1"], layout["law_line_1_y"], load_font(25), rgb(structure, "cyan"))
    draw_centered_text(draw, width, text["law_line_2"], layout["law_line_2_y"], load_font(25), rgb(structure, "cyan"))
    draw_centered_text(draw, width, text["identity"], layout["identity_y"], load_font(21), rgb(structure, "white"))
    draw_centered_text(draw, width, "certificate: " + certificate, layout["certificate_y"], load_font(21), rgb(structure, "muted"))


def draw_non_resolved(draw, structure, certificate, state_name, state_reason):
    width = structure["canvas"]["width"]
    draw_centered_text(draw, width, "NO FORCED IMAGE", 270, load_font(56, True), rgb(structure, "red"))
    draw_centered_text(draw, width, state_name + ": " + state_reason, 350, load_font(30), rgb(structure, "white"))
    draw_centered_text(draw, width, "Object visibility is not admitted until the object field is complete and consistent.", 420, load_font(24), rgb(structure, "cyan"))
    draw_centered_text(draw, width, "certificate: " + certificate, 660, load_font(23), rgb(structure, "muted"))


def resolve_image(structure):
    identity = render_structure(structure)
    state_name, state_reason = field_state(identity)
    signature = sha256_text(canonical_text(identity))
    certificate = signature[:16]

    width = identity["canvas"]["width"]
    height = identity["canvas"]["height"]
    img = Image.new("RGB", (width, height), rgb(identity, "background_top"))
    draw = ImageDraw.Draw(img)
    draw_gradient_background(draw, identity)

    if state_name == "RESOLVED":
        draw_resolved(draw, identity, certificate, state_name, state_reason)
    else:
        draw_non_resolved(draw, identity, certificate, state_name, state_reason)

    return img, signature, certificate, state_name, state_reason


def make_changed_structure(structure):
    changed = deepcopy(structure)
    changed["field"]["name"] = "changed_object_field"
    changed["field"]["objects"][0]["radius"] = 35
    changed["field"]["objects"][1]["position"] = [595, 248]
    changed["field"]["objects"][2]["position"] = [850, 371]
    changed["field"]["objects"][2]["radius"] = 39
    changed["field"]["objects"][3]["position"] = [690, 457]
    changed["field"]["objects"][4]["position"] = [430, 343]
    changed["field"]["objects"][4]["radius"] = 27
    return changed


def make_incomplete_structure(structure):
    incomplete = deepcopy(structure)
    incomplete["field"]["name"] = "incomplete_object_field"
    incomplete["field"]["objects"][3]["complete"] = False
    incomplete["field"]["objects"][3]["links"] = ["origin_core", "missing_object"]
    return incomplete


def make_conflict_structure(structure):
    conflict = deepcopy(structure)
    conflict["field"]["name"] = "conflict_object_field"
    conflict["field"]["objects"][2]["consistent"] = False
    conflict["field"]["objects"][2]["position"] = [470, 358]
    conflict["field"]["objects"][4]["position"] = [470, 358]
    return conflict


def save_case(label, structure, path):
    img, signature, certificate, state_name, state_reason = resolve_image(structure)
    img.save(path)
    return {
        "label": label,
        "image_path": path,
        "resolution_state": state_name,
        "resolution_note": state_reason,
        "structure_signature": signature,
        "certificate": certificate,
        "image_sha256": sha256_file(path),
        "object_certificates": object_certificates(render_structure(structure))
    }


def write_manifest(structure, results, diffs):
    manifest = {
        "system": structure["system"],
        "version": structure["version"],
        "principle": structure["principle"],
        "law": structure["law"],
        "object_law": structure["object_law"],
        "canonical": results["canonical"],
        "repeat": results["repeat"],
        "changed": results["changed"],
        "incomplete": results["incomplete"],
        "conflict": results["conflict"],
        "changed_structural_diff": diffs["changed"],
        "incomplete_structural_diff": diffs["incomplete"],
        "conflict_structural_diff": diffs["conflict"],
        "repeat_matches_original": results["canonical"]["image_sha256"] == results["repeat"]["image_sha256"],
        "repeat_certificate_matches_original": results["canonical"]["certificate"] == results["repeat"]["certificate"],
        "changed_differs_from_original": results["canonical"]["image_sha256"] != results["changed"]["image_sha256"],
        "changed_certificate_differs_from_original": results["canonical"]["certificate"] != results["changed"]["certificate"],
        "incomplete_blocks_forced_image": results["incomplete"]["resolution_state"] == "INCOMPLETE",
        "conflict_blocks_arbitrary_image": results["conflict"]["resolution_state"] == "CONFLICT",
        "guarantees": structure["guarantees"]
    }
    with open(structure["output"]["manifest"], "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def write_verify(structure, results, diffs):
    with open(structure["output"]["verify"], "w", encoding="utf-8") as f:
        f.write("STRUMER-I v1.1 VERIFY\n")
        f.write("Structural Object-Field Image Resolution\n\n")
        f.write("Principle: " + structure["principle"] + "\n")
        f.write("Law: " + structure["law"] + "\n")
        f.write("Object law: " + structure["object_law"] + "\n\n")

        for key in ["canonical", "repeat", "changed", "incomplete", "conflict"]:
            item = results[key]
            f.write(key.upper() + "\n")
            f.write("created_image: " + item["image_path"] + "\n")
            f.write("resolution_state: " + item["resolution_state"] + "\n")
            f.write("resolution_note: " + item["resolution_note"] + "\n")
            f.write("structure_signature: " + item["structure_signature"] + "\n")
            f.write("certificate: " + item["certificate"] + "\n")
            f.write("image_sha256: " + item["image_sha256"] + "\n")
            f.write("object_certificates:\n")
            for obj_id in sorted(item["object_certificates"]):
                f.write("  " + obj_id + ": " + item["object_certificates"][obj_id] + "\n")
            f.write("\n")

        for label in ["changed", "incomplete", "conflict"]:
            f.write("Structural diff: " + label.upper() + "\n")
            for line in diffs[label]:
                f.write("  " + line + "\n")
            f.write("\n")

        f.write("Determinism checks:\n")
        f.write("same object field -> same image: " + str(results["canonical"]["image_sha256"] == results["repeat"]["image_sha256"]) + "\n")
        f.write("same object field -> same certificate: " + str(results["canonical"]["certificate"] == results["repeat"]["certificate"]) + "\n")
        f.write("changed object field -> visibly changed image: " + str(results["canonical"]["image_sha256"] != results["changed"]["image_sha256"]) + "\n")
        f.write("changed object field -> changed certificate: " + str(results["canonical"]["certificate"] != results["changed"]["certificate"]) + "\n")
        f.write("incomplete object field -> no forced image: " + str(results["incomplete"]["resolution_state"] == "INCOMPLETE") + "\n")
        f.write("conflicting object field -> no arbitrary image: " + str(results["conflict"]["resolution_state"] == "CONFLICT") + "\n\n")

        f.write("FINAL VISIBLE IMAGE: " + results["canonical"]["resolution_state"] + "\n")
        f.write("FINAL REPEAT IMAGE: " + results["repeat"]["resolution_state"] + "\n")
        f.write("FINAL CHANGED IMAGE: " + results["changed"]["resolution_state"] + "\n")
        f.write("FINAL INCOMPLETE IMAGE: BLOCKED\n")
        f.write("FINAL CONFLICT IMAGE: BLOCKED\n\n")

        f.write("Guarantees:\n")
        for item in structure["guarantees"]:
            f.write(item + "\n")


def main():
    changed_structure = make_changed_structure(image_structure)
    incomplete_structure = make_incomplete_structure(image_structure)
    conflict_structure = make_conflict_structure(image_structure)

    canonical = save_case("canonical", image_structure, image_structure["output"]["image"])
    repeat = save_case("repeat", image_structure, image_structure["output"]["image_repeat"])
    changed = save_case("changed", changed_structure, image_structure["output"]["image_changed"])
    incomplete = save_case("incomplete", incomplete_structure, image_structure["output"]["image_incomplete"])
    conflict = save_case("conflict", conflict_structure, image_structure["output"]["image_conflict"])

    results = {
        "canonical": canonical,
        "repeat": repeat,
        "changed": changed,
        "incomplete": incomplete,
        "conflict": conflict
    }

    diffs = {
        "changed": structural_diff(render_structure(image_structure), render_structure(changed_structure)),
        "incomplete": structural_diff(render_structure(image_structure), render_structure(incomplete_structure)),
        "conflict": structural_diff(render_structure(image_structure), render_structure(conflict_structure))
    }

    write_manifest(image_structure, results, diffs)
    write_verify(image_structure, results, diffs)

    print("STRUMER-I v1.1")
    print("Structural Object-Field Image Resolution")
    print("Created: " + canonical["image_path"])
    print("Created: " + repeat["image_path"])
    print("Created: " + changed["image_path"])
    print("Created: " + incomplete["image_path"])
    print("Created: " + conflict["image_path"])
    print("Created: " + image_structure["output"]["verify"])
    print("Created: " + image_structure["output"]["manifest"])
    print("certificate: " + canonical["certificate"])
    print("repeat_certificate: " + repeat["certificate"])
    print("changed_certificate: " + changed["certificate"])
    print("incomplete_certificate: " + incomplete["certificate"])
    print("conflict_certificate: " + conflict["certificate"])
    print("image_sha256: " + canonical["image_sha256"])
    print("repeat_image_sha256: " + repeat["image_sha256"])
    print("changed_image_sha256: " + changed["image_sha256"])
    print("incomplete_image_sha256: " + incomplete["image_sha256"])
    print("conflict_image_sha256: " + conflict["image_sha256"])
    print("same object field -> same image: " + str(canonical["image_sha256"] == repeat["image_sha256"]))
    print("same object field -> same certificate: " + str(canonical["certificate"] == repeat["certificate"]))
    print("changed object field -> visibly changed image: " + str(canonical["image_sha256"] != changed["image_sha256"]))
    print("incomplete object field -> no forced image: " + str(incomplete["resolution_state"] == "INCOMPLETE"))
    print("conflicting object field -> no arbitrary image: " + str(conflict["resolution_state"] == "CONFLICT"))
    print("FINAL VISIBLE IMAGE: " + canonical["resolution_state"])
    print("FINAL INCOMPLETE IMAGE: BLOCKED")
    print("FINAL CONFLICT IMAGE: BLOCKED")
    print("Principle: " + image_structure["principle"])
    print("Law: " + image_structure["law"])
    print("Object law: " + image_structure["object_law"])


if __name__ == "__main__":
    main()
