#!/usr/bin/env python3
"""3D blocking / clay mannequin pass for The Cozy Spot (AI synthesis layout guide).

Run from anywhere:

    blender --background --python scripts/render_book_scenes.py

Optional page filter (Blender passes script args after ``--``):

    blender --background --python scripts/render_book_scenes.py -- --pages 1

Imports rigged munchie.fbx, lunie.fbx, and bast.fbx, poses armatures per manuscript
beat, and composites flat clay silhouettes plus key props over the clean living-room
plate. Render engine: Workbench flat shading when available, otherwise Eevee with
raytracing and fur disabled. Outputs land in assets/renders/blocking/page_XX.png
(multi-panel pages use page_XX_a.png, etc.) at 2560×1440.
"""

from __future__ import annotations

import math
import os
import re
import sys
from dataclasses import dataclass, field

CHARACTERS = ("munchie", "lunie", "bast")
RESOLUTION = (2560, 1440)
TARGET_HEIGHT = 0.50
MUNCHIE_HEIGHT = 0.50
LUNIE_HEIGHT = 0.55
BAST_HEIGHT = 0.425
CHARACTER_HEIGHTS = {
    "munchie": MUNCHIE_HEIGHT,
    "lunie": LUNIE_HEIGHT,
    "bast": BAST_HEIGHT,
}
FLOOR_Z = -0.65
Z_FLOOR = FLOOR_Z
Z_CUSHION_TOP = -0.35
Z_CUSHION = Z_CUSHION_TOP
Z_SILL = 0.10
BLOCKING_ENGINES = ("BLENDER_WORKBENCH", "BLENDER_EEVEE_NEXT", "BLENDER_EEVEE")
CHARACTER_CLAY = {
    "munchie": "F08060",
    "lunie": "5A9FE0",
    "bast": "70C090",
}
PROP_CLAY = "C4BCB4"
RENDER_BLOCKING_DIR = os.path.join("assets", "renders", "blocking")
CUSHION_MARKS = {"cushion", "scoot", "stretch", "curl", "cluster_m"}
SILL_MARKS = {"perch"}
OUTLINE_PX = 4.0
OUTLINE_COLOR = (0x3A / 255.0, 0x25 / 255.0, 0x18 / 255.0)  # #3A2518
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".tga", ".tif", ".tiff", ".bmp", ".webp")
SKIP_MAPS = ("normal", "nrm", "rough", "metal", "spec", "orm", "height", "emissive", "ao", "opacity", "mask")
STYLE_SUFFIX = (
    "2D vector style, flat illustration, soft outlines, Bluey aesthetic, "
    "clean pastel background, no 3D, no baked-in text."
)

# Optical 3D camera presets (focal length + transform). No 2D plate crop or lens-shift framing.
CAMERA_SENSOR = 36.0
ROOM_CENTER = (0.0, 1.05, -0.25)
CUSHION_TARGET = (-0.75, 1.1, Z_CUSHION_TOP)
SILL_TARGET = (-1.6, 1.8, 0.10)
SILL_FEET = (-1.55, 1.75, 0.10)
TEXT_MARGIN = 0.15
CAMERA_PRESETS = {
    "WIDE_SHOT": {"lens": 32.0, "location": (0.0, -3.6, 1.15), "target": ROOM_CENTER},
    "CUSHION_CLOSEUP": {"lens": 65.0, "location": (-0.5, -2.2, 0.45), "target": CUSHION_TARGET},
    "CUSHION_TIGHT": {"lens": 78.0, "location": (-0.55, -1.85, 0.38), "target": CUSHION_TARGET},
    "WINDOW_MEDIUM": {"lens": 55.0, "location": (-1.2, -2.4, 0.65), "target": SILL_TARGET},
    "LEAP_MEDIUM": {"lens": 50.0, "location": (-0.4, -2.6, 0.55), "target": CUSHION_TARGET},
}
PANEL_CAMERA_OVERRIDES = {
    3: ("WIDE_SHOT", "CUSHION_CLOSEUP", "CUSHION_TIGHT", "LEAP_MEDIUM"),
}
SCENE_FOLDER = os.path.join("assets", "backgrounds", "Background-master_living_room")
PLATE_CANDIDATES = (
    "master_living_room_clean.png.png",
    "master_living_room_clean.png",
)
TABLE_TOP_Z = -0.27
RUG_CENTER = (-0.75, 0.85, FLOOR_Z)
MUNCHIE_RUG_ROTATION = (0.0, 0.0, math.radians(-15.0))
SUN_SPOT = RUG_CENTER
CUSHION_LOCATION = (-0.95, 1.05, Z_CUSHION)
WINDOW_SILL = SILL_FEET
GAZE_RIGHT = (0.35, 1.85, FLOOR_Z + 0.15)
PROXY_FLOOR = (0.0, 1.0, -0.65)
PROXY_SILL = (-1.55, 1.55, -0.18)
PROXY_SILL_SIZE = (0.42, 1.15, 0.08)
CUSHION_SEATS = {
    "cushion": (0.00, 0.04),
    "scoot": (-0.14, 0.02),
    "stretch": (0.12, 0.06),
    "curl": (0.02, -0.10),
    "cluster_m": (-0.06, 0.00),
}
SUN_LOCATION = (-3.2, 0.3, 2.7)
SUN_TARGET = SUN_SPOT
SUN_COLOR = "FFCC4D"
LIMB_DROP_DEGREES = 68.0
WORLD_COLOR = "FFF6EA"

# Feet on the shadow catcher at the photographed floor, Z = -0.65.
MARKS = {
    "approach": (0.15, 1.35, FLOOR_Z),
    "crouch": (-0.2, 1.55, FLOOR_Z),
    "run": (-0.35, 1.65, FLOOR_Z),
    "leap": (-0.45, 1.75, FLOOR_Z + 0.2),
    "cushion": (-0.45, 1.8, Z_CUSHION),
    "scoot": (-0.65, 1.8, Z_CUSHION),
    "stretch": (-0.5, 1.9, Z_CUSHION),
    "curl": (-0.5, 1.75, Z_CUSHION),
    "perch": WINDOW_SILL,
    "drop": (-0.9, 1.6, FLOOR_Z + 0.26),
    "beside": (-0.1, 1.9, FLOOR_Z),
    "step_back": (0.15, 1.45, FLOOR_Z),
    "step_closer": (-0.25, 1.75, FLOOR_Z),
    "study": (0.05, 1.6, FLOOR_Z),
    "sit_close": (-0.15, 1.7, FLOOR_Z),
    "no_grab": (0.05, 1.55, FLOOR_Z),
    "lean": (-0.3, 1.75, FLOOR_Z),
    "between": (-0.2, 1.65, FLOOR_Z),
    "wait_beam": (-0.05, 1.45, FLOOR_Z),
    "look_second": (0.2, 1.7, FLOOR_Z),
    "watch": (0.25, 1.6, FLOOR_Z),
    "hold": (-0.7, 1.85, FLOOR_Z),
    "slide": (0.05, 1.85, FLOOR_Z),
    "push": (-0.35, 1.65, FLOOR_Z),
    "cluster_m": (-0.45, 1.8, Z_CUSHION),
    "cluster_l": (-0.1, 1.95, FLOOR_Z),
    "cluster_b": (-0.2, 1.55, FLOOR_Z),
    "rug_center": RUG_CENTER,
}

LOOK_TARGETS = {
    "approach": CUSHION_LOCATION,
    "crouch": CUSHION_LOCATION,
    "run": CUSHION_LOCATION,
    "leap": CUSHION_LOCATION,
    "cushion": CUSHION_TARGET,
    "scoot": CUSHION_TARGET,
    "stretch": CUSHION_TARGET,
    "curl": CUSHION_TARGET,
    "perch": CUSHION_TARGET,
    "drop": CUSHION_LOCATION,
    "beside": CUSHION_LOCATION,
    "step_back": CUSHION_LOCATION,
    "step_closer": CUSHION_LOCATION,
    "study": GAZE_RIGHT,
    "sit_close": CUSHION_LOCATION,
    "no_grab": CUSHION_LOCATION,
    "lean": CUSHION_LOCATION,
    "between": CUSHION_LOCATION,
    "wait_beam": CUSHION_LOCATION,
    "look_second": GAZE_RIGHT,
    "watch": CUSHION_LOCATION,
    "hold": CUSHION_LOCATION,
    "slide": GAZE_RIGHT,
    "push": CUSHION_LOCATION,
    "cluster_m": CUSHION_TARGET,
    "cluster_l": CUSHION_TARGET,
    "cluster_b": CUSHION_TARGET,
    "rug_center": ROOM_CENTER,
}

PITCHED_POSES = {"perch", "drop", "leap"}

POSE_RULES = {
    "munchie": [
        (("leaps", "bold bound", "lands squarely"), "leap"),
        (("charges", "mid-race"), "run"),
        (("crouches", "coiled"), "crouch"),
        (("freezes", "@munchie leans"), "approach"),
        (("scoot",), "scoot"),
        (("pushes",), "push"),
        (("curled",), "curl"),
        (("stretches", "spread across", "every inch"), "stretch"),
        (("hugs", "will not share", "holding on", "holds the spot", "planted", "grumpy", "peeks", "wrapped"), "cushion"),
        (("softens", "peaceful", "settle", "rest", "snug", "fitting"), "cluster_m"),
        (("turn to look",), "look_second"),
    ],
    "lunie": [
        (("slips down", "slips off"), "drop"),
        (("perch", "high on", "high above"), "perch"),
        (("slides a second", "slides"), "slide"),
        (("steps back", "one step back", "pauses one step"), "step_back"),
        (("steps closer",), "step_closer"),
        (("studies", "looks across", "better way", "goes still", "catching sight"), "study"),
        (("short distance", "little way"), "step_back"),
        (("wait there",), "wait_beam"),
        (("@lunie waits", "quiet patience", "hopeful"), "beside"),
        (("content", "settle", "rest", "snug"), "cluster_l"),
    ],
    "bast": [
        (("comes slowly", "sits close", "sitting close"), "sit_close"),
        (("does not reach", "not reaching", "keeps still"), "no_grab"),
        (("leans", "never pushing"), "lean"),
        (("holds the side", "holds one side"), "hold"),
        (("between",), "between"),
        (("watches",), "watch"),
        (("turn to look",), "look_second"),
        (("wait there",), "wait_beam"),
        (("settle", "rest", "calm center", "snug", "fitting"), "cluster_b"),
    ],
}

SHARED_MARKS = {"wait_beam", "look_second"}
SHARED_NUDGE = {
    "munchie": (-0.22, 0.0, 0.0),
    "lunie": (0.2, 0.14, 0.0),
    "bast": (0.02, -0.24, 0.0),
}

DEFAULT_POSE = {
    "munchie": "cushion",
    "lunie": "beside",
    "bast": "sit_close",
}


@dataclass
class Page:
    number: int
    layout: str
    narrative: str
    prompts: list[str] = field(default_factory=list)
    text_zone: str = ""

    @property
    def description(self) -> str:
        text = " ".join(self.prompts).replace(STYLE_SUFFIX, " ")
        return re.sub(r"\s+", " ", text).strip().lower()


def project_root() -> str:
    candidates = []
    script = globals().get("__file__")
    if script:
        script_dir = os.path.dirname(os.path.abspath(script))
        candidates.extend([script_dir, os.path.dirname(script_dir)])
    argv = sys.argv
    if "--python" in argv:
        script_path = os.path.abspath(argv[argv.index("--python") + 1])
        script_dir = os.path.dirname(script_path)
        candidates.extend([script_dir, os.path.dirname(script_dir)])
    candidates.append(os.getcwd())
    for candidate in candidates:
        manuscript = os.path.join(candidate, "books", "book_1_the_cozy_spot", "manuscript.md")
        if os.path.isfile(manuscript):
            return candidate
    raise FileNotFoundError(
        "Could not find books/book_1_the_cozy_spot/manuscript.md. "
        "Run Blender with the path to scripts/render_book_scenes.py."
    )


def parse_manuscript(path: str) -> list[Page]:
    text = open(path, encoding="utf-8").read()
    chunks = re.split(r"^## Page (\d+)\s*$", text, flags=re.M)
    pages = []
    for index in range(1, len(chunks), 2):
        number = int(chunks[index])
        body = chunks[index + 1]
        layout_match = re.search(r"\*\*Layout:\*\*\s*(.+)", body)
        layout = layout_match.group(1).strip() if layout_match else ""
        narrative = ""
        text_zone = ""
        text_match = re.search(r"\*\*Text(?: \(([^)]*)\))?:\*\*\s*(?:No Text|(.+))", body)
        if text_match:
            if text_match.group(1):
                text_zone = text_match.group(1).strip()
            if text_match.group(2):
                narrative = text_match.group(2).strip()
        prompts = [line.strip() for line in re.findall(r"\*\*Prompt:\*\*\s*\n(.+)", body)]
        pages.append(Page(number=number, layout=layout, narrative=narrative, prompts=prompts, text_zone=text_zone))
    pages.sort(key=lambda page: page.number)
    expected = list(range(1, 25))
    found = [page.number for page in pages]
    if found != expected:
        raise RuntimeError(f"Expected manuscript pages 1-24, found {found}")
    return pages


def filter_pages(pages: list[Page]) -> list[Page]:
    if "--" not in sys.argv:
        return pages
    extra = sys.argv[sys.argv.index("--") + 1 :]
    if "--pages" not in extra:
        return pages
    spec = extra[extra.index("--pages") + 1]
    wanted = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            wanted.update(range(int(start), int(end) + 1))
        else:
            wanted.add(int(part))
    return [page for page in pages if page.number in wanted]


def _sentences_with(description: str, handle: str) -> list[str]:
    token = f"@{handle}"
    sentences = re.split(r"(?<=[.])\s+", description)
    return [sentence for sentence in sentences if token in sentence]


def _has_phrase(sentence: str, phrase: str) -> bool:
    return re.search(rf"(?<![a-z@]){re.escape(phrase)}(?![a-z])", sentence) is not None


def feet_location(name: str, mark_name: str):
    base = MARKS[mark_name]
    if mark_name not in SHARED_MARKS:
        return (base[0], base[1], anchor_z(mark_name))
    nudge = SHARED_NUDGE[name]
    return (base[0] + nudge[0], base[1] + nudge[1], anchor_z(mark_name))


def anchor_z(mark_name: str) -> float:
    """Calibrated contact height for floor, cushion top, or window sill."""
    if mark_name in CUSHION_MARKS:
        return Z_CUSHION_TOP
    if mark_name in SILL_MARKS:
        return Z_SILL
    if mark_name == "leap":
        return Z_FLOOR + 0.20
    if mark_name == "drop":
        return Z_FLOOR + 0.26
    return Z_FLOOR


def blocking_for(page: Page) -> dict[str, str]:
    """Map each character named on the page to a fixed stage mark.

    Multi-panel pages collapse to one still: the last sentence that names a
    character wins, so a sequence lands on its final beat. Page 1 always
    places @munchie inside the golden sunbeam, facing the camera.
    """
    if page.number == 1:
        return {"munchie": "rug_center"}
    description = page.description
    blocking = {}
    for name in CHARACTERS:
        sentences = _sentences_with(description, name)
        if not sentences:
            continue
        pose = None
        for sentence in reversed(sentences):
            for phrases, mark in POSE_RULES[name]:
                if any(_has_phrase(sentence, phrase) for phrase in phrases):
                    pose = mark
                    break
            if pose:
                break
        blocking[name] = pose or DEFAULT_POSE[name]
    return blocking


def hex_rgba(value: str, alpha: float = 1.0):
    value = value.lstrip("#")
    return (
        int(value[0:2], 16) / 255.0,
        int(value[2:4], 16) / 255.0,
        int(value[4:6], 16) / 255.0,
        alpha,
    )


def _matte_principled(nodes, links, rgba):
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (40, 40)
    principled.inputs["Base Color"].default_value = rgba
    if "Roughness" in principled.inputs:
        principled.inputs["Roughness"].default_value = 0.92
    if "Metallic" in principled.inputs:
        principled.inputs["Metallic"].default_value = 0.0
    specular = "Specular IOR Level" if "Specular IOR Level" in principled.inputs else "Specular"
    if specular in principled.inputs:
        principled.inputs[specular].default_value = 0.12
    return principled


def strip_fur_and_particles(root):
    """Remove particle / fur systems so blocking stays clean mannequin meshes."""
    for obj in [root, *list(root.children_recursive)]:
        if obj.type != "MESH":
            continue
        for modifier in list(obj.modifiers):
            if modifier.type == "PARTICLE_SYSTEM":
                obj.modifiers.remove(modifier)


def apply_clay_material(bpy, obj, hex_color: str, prefix: str):
    """Single flat clay material for high-contrast blocking silhouettes."""
    mat_name = f"{prefix}_{obj.name}_Clay"
    material = bpy.data.materials.get(mat_name)
    if material is None:
        material = flat_toon_material(bpy, mat_name, hex_color)
        principled = material.node_tree.nodes.get("Principled BSDF")
        if principled is not None:
            if "Roughness" in principled.inputs:
                principled.inputs["Roughness"].default_value = 1.0
            specular = "Specular IOR Level" if "Specular IOR Level" in principled.inputs else "Specular"
            if specular in principled.inputs:
                principled.inputs[specular].default_value = 0.0
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj.color = (*hex_rgba(hex_color)[:3], 1.0)


def apply_clay_to_hierarchy(bpy, root, hex_color: str):
    strip_fur_and_particles(root)
    for obj in root.children_recursive:
        if obj.type == "MESH":
            apply_clay_material(bpy, obj, hex_color, root.name)


def flat_toon_material(bpy, name: str, hex_color: str, strength: float = 1.0, emit: bool = False):
    """Matte picture-book surface. Lights and ambient occlusion can shade it. Emission is only for the window and sunbeam."""
    rgba = hex_rgba(hex_color)
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = rgba
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (420, 0)
    if emit:
        emission = nodes.new("ShaderNodeEmission")
        emission.location = (40, 40)
        emission.inputs["Color"].default_value = rgba
        emission.inputs["Strength"].default_value = strength
        links.new(emission.outputs["Emission"], output.inputs["Surface"])
        material["flat_shader"] = "emission"
        return material
    principled = _matte_principled(nodes, links, rgba)
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    material["flat_shader"] = "matte"
    return material


def move_to_collection(bpy, obj, collection):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def soften_edges(bpy, obj, width: float):
    """Round CAD corners on solid props. Width stays under half the thinnest side."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    except RuntimeError:
        pass
    bevel = obj.modifiers.new("SoftBevel", "BEVEL")
    bevel.width = width
    bevel.segments = 3
    if hasattr(bevel, "affect"):
        bevel.affect = "EDGES"
    if hasattr(bevel, "limit_method"):
        bevel.limit_method = "ANGLE"
    if hasattr(bevel, "angle_limit"):
        bevel.angle_limit = math.radians(40.0)
    if hasattr(bevel, "profile"):
        bevel.profile = 0.5
    if hasattr(bevel, "miter_outer"):
        try:
            bevel.miter_outer = "ARC"
        except TypeError:
            pass
    if hasattr(bevel, "harden_normals"):
        bevel.harden_normals = True
    try:
        bpy.ops.object.shade_smooth()
    except RuntimeError:
        for poly in obj.data.polygons:
            poly.use_smooth = True


def add_plane(bpy, name, location, scale, rotation, material, collection):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    move_to_collection(bpy, obj, collection)
    return obj


def add_box(bpy, name, location, dimensions, material, collection):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = dimensions
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    move_to_collection(bpy, obj, collection)
    return obj


def add_cylinder(bpy, name, location, radius, depth, material, collection):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=radius, depth=depth, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    move_to_collection(bpy, obj, collection)
    return obj


def join_objects(bpy, objects, name):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    objects[0].name = name
    return objects[0]


def look_at(obj, target, track: str):
    from mathutils import Vector

    direction = Vector(target) - obj.location
    if direction.length < 1e-6:
        return
    obj.rotation_euler = direction.to_track_quat(track, "Z").to_euler()


def text_safe_shift(page: Page) -> tuple[float, float]:
    """Reserve a 15% band for typeset story text and speech bubbles."""
    zone = (page.text_zone or "").lower()
    layout = page.layout.lower()
    if not page.narrative and ("no text" in zone or "grid" in layout):
        return (0.0, 0.0)
    band = TEXT_MARGIN * 0.5
    if "top" in zone:
        return (0.0, -band)
    if "right" in zone or "whitespace, right" in zone:
        return (-band, band if page.narrative else 0.0)
    if page.narrative or "bottom" in zone:
        return (0.0, band)
    return (0.0, 0.0)


def apply_camera_preset(bpy, scene, preset_key: str, safe_shift: tuple[float, float] = (0.0, 0.0)):
    """Move the stage camera in 3D and zoom with focal length (no compositor crop)."""
    preset = CAMERA_PRESETS[preset_key]
    camera = scene.camera
    camera.data.lens = preset["lens"]
    camera.data.sensor_width = CAMERA_SENSOR
    camera.data.sensor_fit = "HORIZONTAL"
    camera.data.shift_x = safe_shift[0]
    camera.data.shift_y = safe_shift[1]
    camera.location = preset["location"]
    camera.rotation_mode = "XYZ"
    look_at(camera, preset["target"], "-Z")
    print(
        f"Camera {preset_key}: {preset['lens']:.0f}mm at {preset['location']} "
        f"→ target {preset['target']} safe_shift {safe_shift}"
    )


def camera_preset_for(page: Page, panel_index: int, prompt: str, blocking: dict[str, str]) -> str:
    """Pick a beat-appropriate 3D camera preset for this panel."""
    overrides = PANEL_CAMERA_OVERRIDES.get(page.number)
    if overrides and len(page.prompts or []) > 1 and panel_index < len(overrides):
        return overrides[panel_index]

    marks = set(blocking.values())
    text = prompt.lower()
    if marks & SILL_MARKS or any(phrase in text for phrase in ("window sill", "sill", "high perch", "high on", "high above")):
        return "WINDOW_MEDIUM"
    if "leap" in marks or any(phrase in text for phrase in ("leaps", "bold bound", "lands squarely")):
        return "LEAP_MEDIUM"

    focus = plate_focus(prompt, page.layout)
    if focus == "WINDOW_SILL":
        return "WINDOW_MEDIUM"
    if focus == "CLOSE_RUG":
        return "CUSHION_TIGHT"
    if focus == "rug" or marks & CUSHION_MARKS:
        if any(word in text for word in ("crouch", "coiled", "curl", "peeks", "low to the floor")):
            return "CUSHION_CLOSEUP"
        return "CUSHION_CLOSEUP"
    if "wide " in text or text.startswith("across a wide"):
        return "WIDE_SHOT"
    if "vignette" in page.layout.lower() and page.number == 1:
        return "CUSHION_CLOSEUP"
    if len(page.prompts or []) > 1:
        cycle = ("WIDE_SHOT", "CUSHION_CLOSEUP", "CUSHION_TIGHT", "WINDOW_MEDIUM", "LEAP_MEDIUM")
        return cycle[panel_index % len(cycle)]
    return "WIDE_SHOT"


def glow_material(bpy, name: str, hex_color: str, strength: float, alpha: float = 1.0):
    """Warm emission. Alpha below 1 keeps the slanted beam from reading as a solid sheet."""
    rgba = hex_rgba(hex_color, alpha)
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = rgba
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (420, 0)
    emission = nodes.new("ShaderNodeEmission")
    emission.location = (40, 40)
    emission.inputs["Color"].default_value = (*rgba[:3], 1.0)
    emission.inputs["Strength"].default_value = strength
    if alpha < 0.999 and hasattr(bpy.types, "ShaderNodeBsdfTransparent"):
        transparent = nodes.new("ShaderNodeBsdfTransparent")
        mix = nodes.new("ShaderNodeMixShader")
        mix.inputs["Fac"].default_value = alpha
        mix.location = (220, 20)
        links.new(transparent.outputs[0], mix.inputs[1])
        links.new(emission.outputs["Emission"], mix.inputs[2])
        links.new(mix.outputs[0], output.inputs["Surface"])
        for attr, value in (("blend_method", "BLEND"), ("surface_render_method", "BLENDED")):
            if hasattr(material, attr):
                try:
                    setattr(material, attr, value)
                except (TypeError, ValueError):
                    pass
    else:
        links.new(emission.outputs["Emission"], output.inputs["Surface"])
    material["flat_shader"] = "emission"
    return material


def inspect_armature_bones(armature) -> list[str]:
    """Print every bone on an imported armature."""
    names = [bone.name for bone in armature.data.bones]
    print(f"Armature '{armature.name}' — {len(names)} bones:")
    for name in names:
        print(f"  {name}")
    return names


def _fuzzy_limb(name: str) -> bool:
    """Bones whose names contain arm, shoulder, or leg, skipping fingers and forearm segments."""
    token = name.lower()
    if not any(hint in token for hint in ("arm", "shoulder", "leg")):
        return False
    if any(skip in token for skip in ("forearm", "finger", "thumb", "hand", "wrist", "twist", "toe", "ik")):
        return False
    return True


def _bone_axis(bone):
    direction = bone.tail_local - bone.head_local
    length = direction.length
    if length < 1e-8:
        return direction, 0.0
    return direction / length, length


def _generic_upper_limbs(armature) -> list[str]:
    """First bone of each sideways limb on an indexed SmartRig (Bone_007, Bone_020, and the rest)."""
    bones = list(armature.data.bones)
    if not bones:
        return []
    z_values = [bone.head_local.z for bone in bones] + [bone.tail_local.z for bone in bones]
    z_min = min(z_values)
    height = max(max(z_values) - z_min, 1e-4)
    min_length = max(height * 0.05, 0.04)
    center_x = height * 0.1
    floor_z = z_min + height * 0.22
    crown_z = z_min + height * 0.75

    def sideways(bone) -> bool:
        direction, length = _bone_axis(bone)
        if length <= 0.0:
            return False
        return abs(direction.z) < 0.82 and max(abs(direction.x), abs(direction.y)) > 0.45

    def continues_chain(parent, child) -> bool:
        if parent is None or not sideways(parent):
            return False
        gap = (child.head_local - parent.tail_local).length
        parent_length = _bone_axis(parent)[1]
        return gap < max(parent_length * 0.45, height * 0.04)

    def subtree_holds_spine(bone) -> bool:
        pending = list(bone.children)
        while pending:
            child = pending.pop()
            direction, length = _bone_axis(child)
            if length > height * 0.08 and abs(direction.z) > 0.75 and abs(child.head_local.x) < center_x:
                return True
            pending.extend(child.children)
        return False

    chosen = []
    for bone in bones:
        direction, length = _bone_axis(bone)
        if length < min_length or not sideways(bone) or direction.z > 0.35:
            continue
        if continues_chain(bone.parent, bone) or subtree_holds_spine(bone):
            continue
        on_center = abs(bone.head_local.x) < center_x
        along_depth = abs(direction.y) > abs(direction.x)
        near_floor = bone.head_local.z <= floor_z
        if on_center and along_depth and not near_floor:
            continue
        if bone.head_local.z >= crown_z:
            continue
        chosen.append(bone)
    paired = []
    mirror_z = height * 0.08
    for bone in chosen:
        for other in chosen:
            if other is bone:
                continue
            if abs(bone.head_local.z - other.head_local.z) > mirror_z:
                continue
            if bone.head_local.x * other.head_local.x < -1e-4:
                paired.append(bone.name)
                break
    return paired


def _drop_bone(armature, pose_bone, degrees: float) -> bool:
    """Swing one pose bone toward world down by ``degrees``."""
    from mathutils import Quaternion, Vector

    if degrees < 1.0:
        print(f"  {pose_bone.name} already hangs down")
        return False
    rest = pose_bone.bone.matrix_local.to_3x3()
    direction = (armature.matrix_world.to_3x3() @ rest @ Vector((0.0, 1.0, 0.0))).normalized()
    if direction.z < -0.9:
        print(f"  {pose_bone.name} already hangs down")
        return False
    axis = direction.cross(Vector((0.0, 0.0, -1.0)))
    if axis.length < 1e-5:
        return False
    axis.normalize()
    angle = math.radians(degrees)
    swing = Quaternion(axis, angle)
    if (swing @ direction).z > direction.z:
        swing = Quaternion(axis, -angle)
    parent = pose_bone.parent
    if parent is not None:
        parent_world = armature.matrix_world.to_3x3() @ parent.bone.matrix_local.to_3x3()
    else:
        parent_world = armature.matrix_world.to_3x3()
    local = (parent_world.inverted() @ swing.to_matrix() @ parent_world).to_quaternion()
    pose_bone.rotation_mode = "QUATERNION"
    pose_bone.rotation_quaternion = local @ pose_bone.rotation_quaternion
    print(f"  lowered {pose_bone.name} by {degrees:.0f}°")
    return True


def _hang_degrees(armature, pose_bone) -> float:
    """Degrees still needed to leave a limb about 20° off straight down."""
    from mathutils import Vector

    rest = pose_bone.bone.matrix_local.to_3x3()
    direction = (armature.matrix_world.to_3x3() @ rest @ Vector((0.0, 1.0, 0.0))).normalized()
    remaining = math.degrees(direction.angle(Vector((0.0, 0.0, -1.0)))) - 20.0
    return max(0.0, min(LIMB_DROP_DEGREES, remaining))


def relax_tpose(bpy, root) -> int:
    """Print every bone, then lower named limbs or SmartRig index chains out of T-pose."""
    moved = 0
    armatures = [obj for obj in [root, *list(root.children_recursive)] if obj.type == "ARMATURE"]
    if not armatures:
        print(f"@{root.name}: no armature bones found")
        return 0
    for armature in armatures:
        names = inspect_armature_bones(armature)
        matches = [name for name in names if _fuzzy_limb(name)]
        print(f"Fuzzy matches (arm/shoulder/leg): {', '.join(matches) if matches else 'none'}")
        if armature.animation_data:
            armature.animation_data_clear()
        if matches:
            targets = {name: LIMB_DROP_DEGREES for name in matches}
        else:
            generic = _generic_upper_limbs(armature)
            print(f"SmartRig upper limbs: {', '.join(generic) if generic else 'none'}")
            targets = {name: None for name in generic}
        for pose_bone in armature.pose.bones:
            if pose_bone.name not in targets:
                continue
            degrees = targets[pose_bone.name]
            if degrees is None:
                degrees = _hang_degrees(armature, pose_bone)
            if _drop_bone(armature, pose_bone, degrees):
                moved += 1
    bpy.context.view_layer.update()
    return moved


def resolve_plate_path(scene_dir: str) -> str:
    """Prefer the double-extension clean plate, then master_living_room_clean.png."""
    for name in PLATE_CANDIDATES:
        path = os.path.join(scene_dir, name)
        if os.path.isfile(path):
            return path
    tried = "\n".join(os.path.join(scene_dir, name) for name in PLATE_CANDIDATES)
    raise FileNotFoundError(f"Clean living-room plate is required. Tried:\n{tried}")


def bind_plate(bpy, scene, image_path: str):
    """Point the compositor plate at the clean living-room image for this panel."""
    tree = getattr(scene, "node_tree", None)
    if tree is None:
        tree = getattr(scene, "compositing_node_group", None)
    node = None if tree is None else tree.nodes.get("PlateImage")
    if node is None:
        return
    image = bpy.data.images.load(image_path, check_existing=True)
    try:
        image.colorspace_settings.name = "sRGB"
    except TypeError:
        pass
    node.image = image


def setup_compositor(bpy, scene, image_path: str):
    """Alpha-overlay the character render on the living-room plate."""
    if hasattr(scene, "use_nodes"):
        scene.use_nodes = True
    if hasattr(scene.render, "use_compositing"):
        scene.render.use_compositing = True
    tree = getattr(scene, "node_tree", None)
    if tree is None and hasattr(scene, "compositing_node_group"):
        if scene.compositing_node_group is None:
            scene.compositing_node_group = bpy.data.node_groups.new("BookComposite", "CompositorNodeTree")
        tree = scene.compositing_node_group
    if tree is None:
        raise RuntimeError("Could not enable the compositor. scene.use_nodes did not create a node tree.")
    nodes = tree.nodes
    links = tree.links
    for node in list(nodes):
        nodes.remove(node)

    render_layers = nodes.new("CompositorNodeRLayers")
    render_layers.location = (-640, 220)
    plate = nodes.new("CompositorNodeImage")
    plate.name = "PlateImage"
    plate.location = (-640, -80)
    image = bpy.data.images.load(image_path, check_existing=True)
    try:
        image.colorspace_settings.name = "sRGB"
    except TypeError:
        pass
    plate.image = image

    background_socket = plate.outputs["Image"]
    try:
        scale = nodes.new("CompositorNodeScale")
        scale.location = (-180, -80)
        scale.space = "RENDER_SIZE"
        if hasattr(scale, "frame_method"):
            scale.frame_method = "STRETCH"
        links.new(background_socket, scale.inputs["Image"])
        background_socket = scale.outputs["Image"]
    except (TypeError, KeyError, RuntimeError) as exc:
        print(f"Background scale node skipped: {exc}")

    overlay = nodes.new("CompositorNodeAlphaOver")
    overlay.location = (0, 80)
    if hasattr(overlay, "use_premultiply"):
        overlay.use_premultiply = True
    links.new(background_socket, overlay.inputs[1])
    links.new(render_layers.outputs["Image"], overlay.inputs[2])

    try:
        composite = nodes.new("CompositorNodeComposite")
        image_input = composite.inputs["Image"]
    except (RuntimeError, KeyError):
        composite = nodes.new("NodeGroupOutput")
        if hasattr(tree, "interface"):
            tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        image_input = composite.inputs[0]
    composite.location = (280, 80)
    links.new(overlay.outputs["Image"], image_input)
    print(f"Compositor: character alpha over {image_path}")


def _mark_proxy(obj):
    """Invisible collision surface. The shadow catcher keeps the mesh out of the beauty pass."""
    obj.is_shadow_catcher = True
    obj.hide_render = True


def build_stage(bpy, background_path: str):
    """Lights, camera, and invisible placement proxies. The room is the background plate."""
    scene = bpy.context.scene
    root = bpy.data.collections.new("Set")
    scene.collection.children.link(root)

    world = bpy.data.worlds.new("PlateWorld")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is None:
        background = world.node_tree.nodes.new("ShaderNodeBackground")
        output = world.node_tree.nodes.new("ShaderNodeOutputWorld")
        world.node_tree.links.new(background.outputs["Background"], output.inputs["Surface"])
    background.inputs["Color"].default_value = hex_rgba(WORLD_COLOR)
    background.inputs["Strength"].default_value = 0.35

    bpy.ops.mesh.primitive_plane_add(size=10.0, location=PROXY_FLOOR)
    floor = bpy.context.active_object
    floor.name = "Proxy_Floor"
    floor.is_shadow_catcher = False
    floor.hide_render = True
    move_to_collection(bpy, floor, root)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=PROXY_SILL)
    sill = bpy.context.active_object
    sill.name = "Proxy_Sill"
    sill.scale = PROXY_SILL_SIZE
    _mark_proxy(sill)
    move_to_collection(bpy, sill, root)
    bpy.context.view_layer.update()

    light_data = bpy.data.lights.new("WindowSun", type="SUN")
    light_data.energy = 4.5
    light_data.angle = math.radians(12.0)
    light_data.color = hex_rgba(SUN_COLOR)[:3]
    if hasattr(light_data, "use_shadow"):
        light_data.use_shadow = False
    sun = bpy.data.objects.new("WindowSun", light_data)
    root.objects.link(sun)
    sun.location = SUN_LOCATION
    look_at(sun, SUN_TARGET, "-Z")

    camera_data = bpy.data.cameras.new("PageCamera")
    camera_data.clip_start = 0.05
    camera_data.clip_end = 40.0
    camera = bpy.data.objects.new("PageCamera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    apply_camera_preset(bpy, scene, "WIDE_SHOT")

    setup_compositor(bpy, scene, background_path)
    return scene


def world_bbox(objects):
    from mathutils import Vector

    points = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            points.append(obj.matrix_world @ Vector(corner))
    if not points:
        raise RuntimeError("Imported character has no mesh bounds.")
    xs = [point.x for point in points]
    ys = [point.y for point in points]
    zs = [point.z for point in points]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def find_diffuse_textures(folder: str, character_name: str) -> list[str]:
    """Image files next to the FBX whose names belong to this character and are not utility maps."""
    if not os.path.isdir(folder):
        return []
    found = []
    needle = character_name.lower()
    for dirpath, _, files in os.walk(folder):
        for filename in files:
            stem, ext = os.path.splitext(filename)
            if ext.lower() not in IMAGE_EXTS:
                continue
            haystack = f"{dirpath} {stem}".lower()
            if needle not in haystack:
                continue
            if any(skip in stem.lower() for skip in SKIP_MAPS):
                continue
            score = 0
            lowered = stem.lower()
            if any(hint in lowered for hint in ("diffuse", "albedo", "basecolor", "base_color", "color")):
                score += 5
            if lowered.startswith(needle):
                score += 2
            found.append((score, os.path.join(dirpath, filename)))
    found.sort(key=lambda item: (-item[0], item[1]))
    return [path for _, path in found]


def _image_is_readable(bpy, image) -> bool:
    if image is None:
        return False
    if getattr(image, "packed_file", None) is not None:
        return True
    filepath = bpy.path.abspath(image.filepath) if image.filepath else ""
    return bool(filepath) and os.path.isfile(filepath)


def _load_image(bpy, path: str):
    image = bpy.data.images.load(path, check_existing=True)
    try:
        image.colorspace_settings.name = "sRGB"
    except TypeError:
        pass
    return image


def _set_matte_values(principled):
    if "Roughness" in principled.inputs:
        principled.inputs["Roughness"].default_value = 0.92
    if "Metallic" in principled.inputs:
        principled.inputs["Metallic"].default_value = 0.0
    specular = "Specular IOR Level" if "Specular IOR Level" in principled.inputs else "Specular"
    if specular in principled.inputs:
        principled.inputs[specular].default_value = 0.12


def _principled_node(material):
    nodes = material.node_tree.nodes
    principled = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    if principled is not None:
        return principled
    output = next((node for node in nodes if node.type == "OUTPUT_MATERIAL"), None)
    if output is None:
        output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    material.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return principled


def relink_material_images(bpy, material, search_dirs: list[str]) -> bool:
    """Point existing image nodes at files in the FBX folder when their paths are broken."""
    if material is None or not material.use_nodes or material.node_tree is None:
        return False
    linked = False
    for node in material.node_tree.nodes:
        if node.type != "TEX_IMAGE":
            continue
        if _image_is_readable(bpy, node.image):
            linked = True
            continue
        filename = ""
        if node.image is not None:
            filename = os.path.basename(node.image.filepath or node.image.name)
        if not filename:
            continue
        for directory in search_dirs:
            candidate = os.path.join(directory, filename)
            if os.path.isfile(candidate):
                node.image = _load_image(bpy, candidate)
                linked = True
                break
    return linked


def bind_diffuse_to_material(bpy, material, image_path: str):
    """Connect a diffuse texture to the matte shader so the character renders in full color."""
    material.use_nodes = True
    if material.node_tree is None:
        return
    principled = _principled_node(material)
    _set_matte_values(principled)
    already = False
    for link in material.node_tree.links:
        if link.to_node == principled and link.to_socket.name == "Base Color" and link.from_node.type == "TEX_IMAGE":
            if _image_is_readable(bpy, link.from_node.image):
                already = True
            else:
                link.from_node.image = _load_image(bpy, image_path)
                already = True
            break
    if not already:
        tex = material.node_tree.nodes.new("ShaderNodeTexImage")
        tex.label = "Diffuse"
        tex.location = (-360, 80)
        tex.image = _load_image(bpy, image_path)
        material.node_tree.links.new(tex.outputs["Color"], principled.inputs["Base Color"])
    material["flat_shader"] = "textured"


def material_has_diffuse(bpy, material) -> bool:
    if material is None or not material.use_nodes or material.node_tree is None:
        return False
    return any(node.type == "TEX_IMAGE" and _image_is_readable(bpy, node.image) for node in material.node_tree.nodes)


def bind_character_textures(bpy, meshes, models_dir: str, character_name: str):
    search_dirs = [
        models_dir,
        os.path.join(models_dir, character_name),
        os.path.join(models_dir, "textures"),
        os.path.join(models_dir, f"{character_name}.fbm"),
    ]
    diffuse_paths = find_diffuse_textures(models_dir, character_name)
    primary = diffuse_paths[0] if diffuse_paths else None
    try:
        bpy.ops.file.find_missing_files(directory=models_dir + os.sep)
    except Exception as exc:
        print(f"Missing-file search skipped for @{character_name}: {exc}")
    used_folder_texture = False
    kept_fbx_texture = False
    for obj in meshes:
        if not obj.data.materials:
            material = bpy.data.materials.new(f"{character_name}_diffuse")
            obj.data.materials.append(material)
        for material in obj.data.materials:
            if material is None:
                continue
            relink_material_images(bpy, material, search_dirs)
            if material_has_diffuse(bpy, material):
                material.use_nodes = True
                principled = _principled_node(material)
                _set_matte_values(principled)
                for node in material.node_tree.nodes:
                    if node.type == "TEX_IMAGE" and _image_is_readable(bpy, node.image):
                        material.node_tree.links.new(node.outputs["Color"], principled.inputs["Base Color"])
                        break
                kept_fbx_texture = True
                continue
            if primary:
                bind_diffuse_to_material(bpy, material, primary)
                used_folder_texture = True
                continue
            material.use_nodes = True
            principled = _principled_node(material)
            _set_matte_values(principled)
    if used_folder_texture:
        print(f"Bound diffuse for @{character_name}: {primary}")
    elif kept_fbx_texture:
        print(f"Using diffuse already packed in @{character_name}.fbx")
    else:
        print(f"No diffuse image found beside @{character_name}.fbx; using the FBX material color.")


def import_character_fbx(bpy, path: str):
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.fbx(filepath=path, use_image_search=True)
    except TypeError:
        bpy.ops.import_scene.fbx(filepath=path)
    return [obj for obj in bpy.data.objects if obj not in before and obj.type in {"MESH", "ARMATURE", "EMPTY", "CURVE"}]


def find_prop_fbx(folder: str) -> str:
    """First .fbx under a prop folder. The Meshy filename is ignored; the folder is the identity."""
    found = []
    for dirpath, _, files in os.walk(folder):
        for name in files:
            if name.lower().endswith(".fbx"):
                found.append(os.path.join(dirpath, name))
    if not found:
        raise FileNotFoundError(f"No .fbx model inside {folder}")
    found.sort(key=lambda path: (path.count(os.sep), len(os.path.basename(path))))
    return found[0]


PROP_LAYOUT = (
    {"key": "Cushion", "folder": "Mustard-Yellow Floor Cushion", "fit": "width", "size": 0.90, "xy": (-0.45, 0.95), "z": "floor"},
    {"key": "Box", "folder": "Cardboard Box", "fit": "width", "size": 0.50, "xy": (0.85, 2.2), "z": -0.45},
    {"key": "Bowl", "folder": "Pet Water Bowl", "fit": "width", "size": 0.25, "xy": (-1.40, 1.45), "z": "floor"},
    {"key": "Books", "folder": "Books and Mug", "fit": "width", "size": 0.48, "xy": (0.62, 1.22), "z": "table"},
    {"key": "Mouse", "folder": "Plush Cat Toy Mouse", "fit": "length", "size": 0.22, "xy": (-0.95, 0.22), "z": "floor"},
    {"key": "Balls", "folder": "Cat_Toys_Balls", "fit": "diameter", "size": 0.08, "xy": (0.58, 0.42), "z": "floor"},
)
PROP_ROOTS = {}


def _extent(minimum, maximum, fit: str) -> float:
    size = [maximum[i] - minimum[i] for i in range(3)]
    if fit == "height":
        return size[2]
    if fit == "length":
        return max(size)
    if fit == "diameter":
        usable = [value for value in size if value > 1e-4]
        return min(usable) if usable else 1e-4
    return max(size[0], size[1])


def load_props(bpy, scene_dir: str):
    """Import the Meshy props that are not already painted into the clean plate."""
    collection = bpy.data.collections.new("Props")
    bpy.context.scene.collection.children.link(collection)
    for spec in PROP_LAYOUT:
        folder = os.path.join(scene_dir, spec["folder"])
        path = find_prop_fbx(folder)
        imported = import_character_fbx(bpy, path)
        if not imported:
            raise RuntimeError(f"FBX import produced no objects: {path}")
        root = bpy.data.objects.new(spec["key"], None)
        collection.objects.link(root)
        bpy.context.view_layer.update()
        imported_ids = {obj.as_pointer() for obj in imported}
        top_level = [obj for obj in imported if obj.parent is None or obj.parent.as_pointer() not in imported_ids]
        for obj in top_level:
            world = obj.matrix_world.copy()
            for current in list(obj.users_collection):
                current.objects.unlink(obj)
            collection.objects.link(obj)
            obj.parent = root
            obj.matrix_world = world
        bpy.context.view_layer.update()
        meshes = [obj for obj in root.children_recursive if obj.type == "MESH"]
        if not meshes:
            raise RuntimeError(f"No meshes found in {path}")
        minimum, maximum = world_bbox(meshes)
        current = max(_extent(minimum, maximum, spec["fit"]), 1e-6)
        factor = spec["size"] / current
        root.scale = (factor, factor, factor)
        root.location.x = spec["xy"][0]
        root.location.y = spec["xy"][1]
        bpy.context.view_layer.update()
        minimum, maximum = world_bbox(meshes)
        if isinstance(spec["z"], (int, float)):
            seat = spec["z"]
        elif spec["z"] == "table":
            seat = TABLE_TOP_Z
        else:
            seat = FLOOR_Z
        root.location.z += seat - minimum[2]
        bpy.context.view_layer.update()
        PROP_ROOTS[spec["key"]] = root
        apply_clay_to_hierarchy(bpy, root, PROP_CLAY)
        print(f"Prop {spec['key']} from {os.path.basename(path)} at {spec['size']:.2f}m {spec['fit']} (clay)")
    return PROP_ROOTS


def load_characters(bpy, models_dir: str):
    missing = [
        os.path.join(models_dir, f"{name}.fbx")
        for name in CHARACTERS
        if not os.path.isfile(os.path.join(models_dir, f"{name}.fbx"))
    ]
    if missing:
        joined = "\n".join(missing)
        raise FileNotFoundError(f"Character models are required:\n{joined}")

    collection = bpy.data.collections.new("Characters")
    bpy.context.scene.collection.children.link(collection)
    loaded = {}
    for name in CHARACTERS:
        path = os.path.join(models_dir, f"{name}.fbx")
        imported = import_character_fbx(bpy, path)
        if not imported:
            raise RuntimeError(f"FBX import produced no objects: {path}")

        root = bpy.data.objects.new(name, None)
        collection.objects.link(root)
        bpy.context.view_layer.update()
        imported_ids = {obj.as_pointer() for obj in imported}
        top_level = [obj for obj in imported if obj.parent is None or obj.parent.as_pointer() not in imported_ids]
        for obj in top_level:
            world = obj.matrix_world.copy()
            for current in list(obj.users_collection):
                current.objects.unlink(obj)
            collection.objects.link(obj)
            obj.parent = root
            obj.matrix_world = world

        bpy.context.view_layer.update()
        meshes = [obj for obj in root.children_recursive if obj.type == "MESH"]
        if not meshes:
            raise RuntimeError(f"No meshes found in {path}")
        minimum, maximum = world_bbox(meshes)
        height = max(maximum[2] - minimum[2], 1e-6)
        target_height = CHARACTER_HEIGHTS.get(name, MUNCHIE_HEIGHT)
        root.scale = (target_height / height,) * 3
        bpy.context.view_layer.update()
        lowered = relax_tpose(bpy, root)
        apply_clay_to_hierarchy(bpy, root, CHARACTER_CLAY[name])
        height = anchor_feet_to_origin(bpy, root)
        set_character_hidden(root, True)
        loaded[name] = root
        print(f"Loaded @{name} from {path} at height {height:.2f}; lowered {lowered} limb bones")
    return loaded


def set_character_hidden(root, hidden: bool):
    objects = [root, *list(root.children_recursive)]
    for obj in objects:
        obj.hide_render = hidden
        try:
            obj.hide_set(hidden)
        except RuntimeError:
            obj.hide_viewport = hidden


def anchor_feet_to_origin(bpy, root) -> float:
    """Put the root origin at the feet so a placement Z is the floor contact."""
    bpy.context.view_layer.update()
    meshes = [obj for obj in root.children_recursive if obj.type == "MESH"]
    minimum, maximum = world_bbox(meshes)
    root.location.x -= (minimum[0] + maximum[0]) * 0.5
    root.location.y -= (minimum[1] + maximum[1]) * 0.5
    root.location.z -= minimum[2]
    bpy.context.view_layer.update()
    worlds = {obj: obj.matrix_world.copy() for obj in list(root.children)}
    root.location = (0.0, 0.0, 0.0)
    root.rotation_mode = "XYZ"
    root.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    for obj, world in worlds.items():
        obj.matrix_world = world
    bpy.context.view_layer.update()
    minimum, maximum = world_bbox(meshes)
    return maximum[2] - minimum[2]


def _prop_meshes(root):
    if root.type == "MESH":
        return [root]
    return [obj for obj in root.children_recursive if obj.type == "MESH"]


def _member_names(root) -> set[str]:
    return {root.name, *(obj.name for obj in root.children_recursive)}


def top_polygon_point(root, xy=None):
    """Highest upward-facing polygon on a prop, or the one nearest ``xy``."""
    from mathutils import Vector

    meshes = _prop_meshes(root)
    ranked = []
    for mesh_obj in meshes:
        matrix = mesh_obj.matrix_world
        rotation = matrix.to_3x3()
        for poly in mesh_obj.data.polygons:
            normal = (rotation @ poly.normal).normalized()
            if normal.z < 0.55:
                continue
            center = matrix @ poly.center
            distance = 0.0 if xy is None else (center.x - xy[0]) ** 2 + (center.y - xy[1]) ** 2
            ranked.append((center.z, -distance, center, normal))
    if not ranked:
        minimum, maximum = world_bbox(meshes)
        point = Vector(((minimum[0] + maximum[0]) * 0.5, (minimum[1] + maximum[1]) * 0.5, maximum[2]))
        return point, Vector((0.0, 0.0, 1.0))
    if xy is None:
        ranked.sort(key=lambda item: item[0], reverse=True)
    else:
        ranked.sort(key=lambda item: (item[1], item[0]), reverse=True)
    _height, _near, center, normal = ranked[0]
    if normal.z < 0.0:
        normal = -normal
    return center, normal.normalized()


def ray_onto_prop(bpy, root, xy):
    """Drop a ray onto this prop and keep the hit when it lands on an upward face."""
    from mathutils import Vector

    meshes = _prop_meshes(root)
    _minimum, maximum = world_bbox(meshes)
    origin = Vector((xy[0], xy[1], maximum[2] + 1.5))
    direction = Vector((0.0, 0.0, -1.0))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    hit, location, normal, _index, obj, _matrix = bpy.context.scene.ray_cast(depsgraph, origin, direction, distance=8.0)
    if hit and obj is not None and obj.name in _member_names(root):
        normal = Vector(normal)
        if normal.length < 1e-6:
            normal = Vector((0.0, 0.0, 1.0))
        normal.normalize()
        if normal.z < 0.0:
            normal.negate()
        if normal.z > 0.35:
            return Vector(location), normal
    if root.name in {"Proxy_Floor", "Proxy_Sill"}:
        _minimum, maximum = world_bbox(meshes)
        return Vector((xy[0], xy[1], maximum[2])), Vector((0.0, 0.0, 1.0))
    return top_polygon_point(root, xy)


def cushion_contact(cushion, xy):
    """Feet on the calibrated cushion top (Z = -0.35 m), XY clamped to the mesh footprint."""
    from mathutils import Vector

    meshes = _prop_meshes(cushion)
    minimum, maximum = world_bbox(meshes)
    x = min(max(xy[0], minimum[0] + 0.04), maximum[0] - 0.04)
    y = min(max(xy[1], minimum[1] + 0.04), maximum[1] - 0.04)
    return Vector((x, y, Z_CUSHION_TOP)), Vector((0.0, 0.0, 1.0))


def snap_feet(bpy, mark_name: str, xy):
    """Snap feet onto the cushion top, the window sill, or the floor."""
    lift = 0.0
    if mark_name in CUSHION_MARKS and "Cushion" in PROP_ROOTS:
        cushion = PROP_ROOTS["Cushion"]
        seat = CUSHION_SEATS.get(mark_name, (0.0, 0.0))
        return cushion_contact(cushion, (cushion.location.x + seat[0], cushion.location.y + seat[1]))
    if mark_name in SILL_MARKS:
        from mathutils import Vector

        return Vector(SILL_FEET), Vector((0.0, 0.0, 1.0))
    if mark_name == "leap":
        lift = 0.20
    elif mark_name == "drop":
        lift = 0.26
    from mathutils import Vector

    return Vector((xy[0], xy[1], FLOOR_Z + lift)), Vector((0.0, 0.0, 1.0))


def place_characters(bpy, characters, blocking: dict[str, str]):
    bpy.context.view_layer.update()
    for name, root in characters.items():
        mark_name = blocking.get(name)
        if not mark_name:
            set_character_hidden(root, True)
            continue
        mark = feet_location(name, mark_name)
        location, normal = snap_feet(bpy, mark_name, (mark[0], mark[1]))
        root.location = location
        root.rotation_mode = "XYZ"
        if name == "munchie" and mark_name == "rug_center":
            root.rotation_euler = MUNCHIE_RUG_ROTATION
        else:
            target = LOOK_TARGETS[mark_name]
            if mark_name in PITCHED_POSES:
                look_at(root, target, "-Y")
            else:
                look_at(root, (target[0], target[1], location.z), "-Y")
        _align_up_to_normal(root, normal)
        set_character_hidden(root, False)
        print(f"Snapped @{name} {mark_name} to { _proxy_name(mark_name) } at ({location.x:.2f}, {location.y:.2f}, {location.z:.2f})")
    bpy.context.view_layer.update()


def _proxy_name(mark_name: str) -> str:
    if mark_name in CUSHION_MARKS:
        return "Cushion"
    if mark_name in SILL_MARKS:
        return "Proxy_Sill"
    return "Proxy_Floor"


def _align_up_to_normal(root, normal):
    """Tilt the placed root so its up axis follows the proxy surface normal."""
    from mathutils import Vector

    up = Vector((0.0, 0.0, 1.0))
    if normal.dot(up) > 0.999:
        return
    tilt = up.rotation_difference(normal)
    root.rotation_mode = "QUATERNION"
    root.rotation_quaternion = tilt @ root.rotation_euler.to_quaternion()


def setup_freestyle(bpy, scene):
    scene.render.use_freestyle = True
    if hasattr(scene.render, "line_thickness_mode"):
        scene.render.line_thickness_mode = "ABSOLUTE"
    scene.render.line_thickness = 1.0
    view_layer = scene.view_layers[0]
    view_layer.use_freestyle = True
    settings = view_layer.freestyle_settings
    while settings.linesets:
        settings.linesets.remove(settings.linesets[0])
    lineset = settings.linesets.new("PictureBookOutline")
    for attr, value in {
        "select_silhouette": True,
        "select_border": True,
        "select_crease": False,
        "select_edge_mark": False,
        "select_external_contour": True,
        "select_contour": True,
        "select_suggestive_contour": False,
        "select_material_boundary": False,
    }.items():
        if hasattr(lineset, attr):
            setattr(lineset, attr, value)
    style = lineset.linestyle
    style.color = OUTLINE_COLOR
    style.alpha = 0.92
    style.thickness = OUTLINE_PX
    if hasattr(style, "caps"):
        style.caps = "ROUND"
    style.name = "SoftDarkOutline"


def setup_gpencil_line_art(bpy):
    """Try a Grease Pencil Line Art modifier. Return False when this Blender build cannot add one."""
    try:
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.object.gpencil_add(type="LRT_SCENE", location=(0.0, 0.0, 0.0))
    except Exception:
        return False
    gp = bpy.context.view_layer.objects.active
    if gp is None:
        return False
    modifiers = getattr(gp, "grease_pencil_modifiers", None)
    if modifiers is None:
        modifiers = getattr(gp, "modifiers", None)
    if modifiers is None:
        return False
    modifier = next((item for item in modifiers if getattr(item, "type", "") in {"GP_LINEART", "LINEART"}), None)
    if modifier is None:
        try:
            modifier = modifiers.new("LineArt", "LINEART")
        except Exception:
            return False
    if hasattr(modifier, "thickness"):
        modifier.thickness = int(OUTLINE_PX) if isinstance(modifier.thickness, int) else OUTLINE_PX
    if hasattr(modifier, "opacity"):
        modifier.opacity = 0.92
    gp.name = "LineArtOutline"
    return True


def enable_ambient_occlusion(scene):
    """Soft contact darkening under props and characters."""
    world = scene.world
    if world is not None and hasattr(world, "light_settings"):
        settings = world.light_settings
        if hasattr(settings, "use_ambient_occlusion"):
            settings.use_ambient_occlusion = True
        if hasattr(settings, "ao_factor"):
            settings.ao_factor = 0.7
        if hasattr(settings, "distance"):
            settings.distance = 0.5
    eevee = getattr(scene, "eevee", None)
    if eevee is None:
        return
    for name, value in (
        ("use_gtao", True),
        ("gtao_distance", 0.45),
        ("gtao_factor", 0.8),
        ("gtao_quality", 0.4),
        ("use_soft_shadows", True),
        ("use_shadows", True),
        ("use_raytracing", True),
        ("fast_gi_distance", 0.45),
        ("fast_gi_thickness_near", 0.15),
    ):
        if hasattr(eevee, name):
            try:
                setattr(eevee, name, value)
            except (TypeError, ValueError):
                pass
    if hasattr(eevee, "use_fast_gi"):
        try:
            eevee.use_fast_gi = True
        except TypeError:
            pass
    if hasattr(eevee, "fast_gi_method"):
        for choice in ("AMBIENT_OCCLUSION", "AMBIENT_OCCLUSION_ONLY"):
            try:
                eevee.fast_gi_method = choice
                break
            except TypeError:
                continue


def enable_flat_outlines(bpy, scene):
    """4px dark-brown picture-book outline. Freestyle is the background-render path; Line Art is the fallback."""
    if hasattr(scene.render, "use_freestyle"):
        setup_freestyle(bpy, scene)
        print(f"Outlines: Freestyle line art, {OUTLINE_PX:.0f}px #3A2518")
        return
    if setup_gpencil_line_art(bpy):
        print(f"Outlines: Line Art modifier, {OUTLINE_PX:.0f}px #3A2518")
        return
    print("Warning: this Blender build has no Freestyle or Line Art outline.")


def _prefer_cycles_device(bpy) -> str:
    """GPU when Cycles can see a compute device, otherwise CPU."""
    try:
        import addon_utils

        addon_utils.enable("cycles")
    except Exception as exc:
        print(f"Cycles addon: {exc}")
    try:
        preferences = bpy.context.preferences.addons["cycles"].preferences
        preferences.get_devices()
    except Exception as exc:
        print(f"Cycles devices unavailable, using CPU: {exc}")
        return "CPU"
    for choice in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        if not any(getattr(device, "type", "") == choice for device in preferences.devices):
            continue
        try:
            preferences.compute_device_type = choice
        except (TypeError, ValueError):
            continue
        for device in preferences.devices:
            device.use = getattr(device, "type", "") == choice
        print(f"Cycles compute device: {choice}")
        return "GPU"
    return "CPU"


def configure_render(bpy, scene):
    """Workbench or Eevee flat blocking pass — no Cycles, fur, or photoreal texture work."""
    engine = None
    for choice in BLOCKING_ENGINES:
        try:
            scene.render.engine = choice
            engine = choice
            break
        except TypeError:
            continue
    if engine is None:
        scene.render.engine = "BLENDER_EEVEE"
        engine = scene.render.engine

    scene.render.use_freestyle = False
    scene.render.film_transparent = True
    scene.render.resolution_x = RESOLUTION[0]
    scene.render.resolution_y = RESOLUTION[1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    if hasattr(scene.render, "use_compositing"):
        scene.render.use_compositing = True

    if engine == "BLENDER_WORKBENCH":
        shading = scene.display.shading
        if hasattr(shading, "light"):
            shading.light = "FLAT"
        if hasattr(shading, "color_type"):
            shading.color_type = "MATERIAL"
        for flag, value in (
            ("show_shadows", False),
            ("show_cavity", False),
            ("show_object_outline", True),
            ("show_specular_highlight", False),
        ):
            if hasattr(shading, flag):
                setattr(shading, flag, value)
    else:
        eevee = getattr(scene, "eevee", None)
        if eevee is not None:
            for name, value in (
                ("use_raytracing", False),
                ("use_gtao", False),
                ("use_ssr", False),
                ("use_soft_shadows", False),
                ("use_shadows", False),
                ("use_bloom", False),
            ):
                if hasattr(eevee, name):
                    try:
                        setattr(eevee, name, value)
                    except (TypeError, ValueError):
                        pass
            if hasattr(eevee, "taa_render_samples"):
                eevee.taa_render_samples = 1

    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    print(
        f"Blocking render: {engine}, clay mannequins, transparent film, "
        f"{RESOLUTION[0]}x{RESOLUTION[1]}"
    )


def plate_focus(prompt: str, layout: str) -> str:
    """Pick a wide, rug, window-sill, or close-rug lens for this panel's beat."""
    text = prompt.lower()
    layout_name = layout.lower()
    on_sill = any(phrase in text for phrase in ("window sill", "sill", "high perch", "silent perch", "high on", "high above"))
    on_rug = any(phrase in text for phrase in ("rug", "cushion", "sunbeam", "cozy", "morning light"))
    wide_room = "wide " in text or text.startswith("across a wide")
    looking_down = "seen from" in text or "stretch" in text
    if on_sill and not on_rug:
        return "WINDOW_SILL"
    if on_sill and on_rug and not wide_room and not looking_down:
        return "WINDOW_SILL"
    if wide_room and "full-bleed" in layout_name:
        return "wide"
    close = "vignette" in layout_name or any(word in text for word in ("curl", "peeks", "close"))
    if on_rug and close:
        return "CLOSE_RUG"
    if on_rug:
        return "rug"
    if "vignette" in layout_name or "grid" in layout_name:
        return "CLOSE_RUG"
    if "panel" in layout_name:
        return "rug"
    return "wide"


def render_pages(bpy, scene, characters, pages, render_dir: str, plate_path: str):
    """Every page and panel uses the clean plate, props, per-beat 3D camera, and surface snaps."""
    for page in pages:
        prompts = page.prompts or [""]
        safe_shift = text_safe_shift(page)
        for index, prompt in enumerate(prompts):
            shot = Page(
                number=page.number,
                layout=page.layout,
                narrative=page.narrative,
                prompts=[prompt],
                text_zone=page.text_zone,
            )
            blocking = blocking_for(shot)
            preset = camera_preset_for(page, index, prompt, blocking)
            apply_camera_preset(bpy, scene, preset, safe_shift)
            place_characters(bpy, characters, blocking)
            bind_plate(bpy, scene, plate_path)
            if len(prompts) == 1:
                filename = f"page_{page.number:02d}.png"
            else:
                filename = f"page_{page.number:02d}_{chr(ord('a') + index)}.png"
            filepath = os.path.join(render_dir, filename)
            scene.render.filepath = filepath
            placed = ", ".join(f"@{name}->{mark}" for name, mark in blocking.items()) or "empty set"
            label = f"{page.number:02d}" if len(prompts) == 1 else f"{page.number:02d}{chr(ord('a') + index)}"
            print(
                f"Page {label} [{page.layout}] {preset} plate {os.path.basename(plate_path)} "
                f"text_band {TEXT_MARGIN:.0%} {placed}"
            )
            bpy.ops.render.render(write_still=True)
            print(f"Wrote {filepath}")


def main():
    import bpy

    root = project_root()
    manuscript = os.path.join(root, "books", "book_1_the_cozy_spot", "manuscript.md")
    pages = filter_pages(parse_manuscript(manuscript))
    render_dir = os.path.join(root, RENDER_BLOCKING_DIR)
    os.makedirs(render_dir, exist_ok=True)

    scene_dir = os.path.join(root, SCENE_FOLDER)
    background = resolve_plate_path(scene_dir)
    print(f"Clean plate for every page: {background}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = build_stage(bpy, background)
    load_props(bpy, scene_dir)
    characters = load_characters(bpy, os.path.join(root, "assets", "models"))
    configure_render(bpy, scene)
    render_pages(bpy, scene, characters, pages, render_dir, background)


if __name__ == "__main__":
    main()
