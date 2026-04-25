from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass, field
from typing import Iterable

Vec3 = tuple[float, float, float]
Triangle = tuple[Vec3, Vec3, Vec3]


@dataclass
class Mesh:
    triangles: list[Triangle] = field(default_factory=list)

    def add(self, a: Vec3, b: Vec3, c: Vec3) -> None:
        self.triangles.append((a, b, c))

    def extend(self, other: "Mesh") -> None:
        self.triangles.extend(other.triangles)


DETAIL_SEGMENTS = {
    "fast": 18,
    "balanced": 32,
    "detailed": 56,
}

OBJECT_KEYWORDS = {
    "cup": ("cup", "mug", "goblet", "bowl"),
    "ring": ("ring", "donut", "torus", "bracelet"),
    "box": ("box", "crate", "case", "container"),
    "vase": ("vase", "bottle", "jar", "urn"),
    "castle": ("castle", "tower", "fort", "fortress"),
    "robot": ("robot", "android", "mech", "droid"),
    "dragon": ("dragon", "wyvern", "serpent"),
    "rocket": ("rocket", "spaceship", "ship", "shuttle"),
    "chair": ("chair", "stool", "seat", "bench"),
    "gear": ("gear", "cog", "sprocket"),
    "lamp": ("lamp", "lantern", "light"),
}

STYLE_KEYWORDS = {
    "organic": ("organic", "smooth", "curvy", "flower", "leaf", "tree", "coral", "tentacle"),
    "mechanical": ("mechanical", "industrial", "engine", "cyber", "sci-fi", "robotic"),
    "spiky": ("spiky", "spikes", "horn", "horns", "teeth", "dragon"),
    "cute": ("cute", "tiny", "toy", "cartoon"),
    "decorative": ("ornate", "pattern", "decorated", "carved", "fancy"),
}


def compile_prompt_to_spec(prompt: str, detail: str = "balanced", target_size_mm: int = 80) -> dict:
    text = prompt.lower().strip()
    if not text:
        text = "abstract printable sculpture"

    object_type = "sculpture"
    for candidate, words in OBJECT_KEYWORDS.items():
        if any(word in text for word in words):
            object_type = candidate
            break

    styles = [name for name, words in STYLE_KEYWORDS.items() if any(word in text for word in words)]
    if not styles:
        styles = ["decorative"] if len(text) > 35 else ["clean"]

    features = _features_from_prompt(text, object_type)
    size = _size_from_prompt(text, target_size_mm)
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)

    return {
        "prompt": prompt,
        "object_type": object_type,
        "detail": detail if detail in DETAIL_SEGMENTS else "balanced",
        "target_size_mm": size,
        "style_tags": styles,
        "features": features,
        "seed": seed,
    }


def _features_from_prompt(text: str, object_type: str) -> list[str]:
    features: set[str] = set()
    keyword_features = {
        "handle": ("handle", "mug", "cup"),
        "lid": ("lid", "cap", "covered"),
        "base": ("base", "stand", "pedestal"),
        "wings": ("wing", "wings", "dragon", "spaceship"),
        "tail": ("tail", "dragon", "serpent"),
        "legs": ("leg", "legs", "chair", "robot"),
        "arms": ("arm", "arms", "robot"),
        "windows": ("window", "windows", "spaceship", "rocket"),
        "spikes": ("spike", "spikes", "horn", "horns", "dragon"),
        "battlements": ("castle", "fortress", "tower"),
        "teeth": ("gear", "cog", "sprocket", "teeth"),
    }
    for feature, words in keyword_features.items():
        if any(word in text for word in words):
            features.add(feature)

    defaults = {
        "cup": ["handle", "base"],
        "box": ["lid", "base"],
        "castle": ["battlements", "base"],
        "robot": ["arms", "legs", "base"],
        "dragon": ["wings", "tail", "spikes", "legs", "base"],
        "rocket": ["wings", "windows", "base"],
        "chair": ["legs", "base"],
        "gear": ["teeth"],
        "lamp": ["base"],
    }
    features.update(defaults.get(object_type, []))
    return sorted(features)


def _size_from_prompt(text: str, fallback: int) -> int:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(mm|millimeter|millimeters|cm|centimeter|centimeters|in|inch|inches)", text)
    if not match:
        return max(25, min(180, int(fallback)))
    value = float(match.group(1))
    unit = match.group(2)
    if unit.startswith("cm") or unit.startswith("centimeter"):
        value *= 10
    elif unit in {"in", "inch", "inches"}:
        value *= 25.4
    return max(15, min(220, int(value)))


def build_mesh_from_spec(spec: dict) -> Mesh:
    segments = DETAIL_SEGMENTS.get(spec.get("detail", "balanced"), 32)
    size = float(spec.get("target_size_mm", 80))
    object_type = spec.get("object_type", "sculpture")
    features = set(spec.get("features", []))
    seed = int(spec.get("seed", 0))

    builders = {
        "cup": _build_cup,
        "ring": _build_ring,
        "box": _build_box,
        "vase": _build_vase,
        "castle": _build_castle,
        "robot": _build_robot,
        "dragon": _build_dragon,
        "rocket": _build_rocket,
        "chair": _build_chair,
        "gear": _build_gear,
        "lamp": _build_lamp,
    }
    mesh = builders.get(object_type, _build_sculpture)(size, segments, features, seed)
    _add_prompt_texture(mesh, size, segments, seed, features)
    return mesh


def generate_stl_from_prompt(prompt: str, output_path: str, detail: str = "balanced", target_size_mm: int = 80) -> dict:
    spec = compile_prompt_to_spec(prompt, detail=detail, target_size_mm=target_size_mm)
    mesh = build_mesh_from_spec(spec)
    write_ascii_stl(mesh, output_path, name="dream_printer_model")
    return {
        "spec": spec,
        "triangle_count": len(mesh.triangles),
        "output_path": output_path,
        "size_bytes": os.path.getsize(output_path),
    }


def write_ascii_stl(mesh: Mesh, filename: str, name: str = "model") -> None:
    folder = os.path.dirname(filename)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as file:
        file.write(f"solid {name}\n")
        for a, b, c in mesh.triangles:
            normal = _normal(a, b, c)
            file.write(f"  facet normal {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")
            file.write("    outer loop\n")
            for vertex in (a, b, c):
                file.write(f"      vertex {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")
            file.write("    endloop\n")
            file.write("  endfacet\n")
        file.write(f"endsolid {name}\n")


def _build_cup(size: float, segments: int, features: set[str], seed: int) -> Mesh:
    mesh = _open_cylinder_shell((0, 0, size * 0.35), size * 0.28, size * 0.65, size * 0.045, segments)
    if "handle" in features:
        mesh.extend(_arc_tube((size * 0.28, 0, size * 0.38), size * 0.22, size * 0.035, -70, 70, segments, 10))
    if "base" in features:
        mesh.extend(_cylinder((0, 0, size * 0.035), size * 0.34, size * 0.07, segments))
    return mesh


def _build_ring(size: float, segments: int, features: set[str], seed: int) -> Mesh:
    return _torus((0, 0, size * 0.18), size * 0.31, size * 0.075, segments, 12)


def _build_box(size: float, segments: int, features: set[str], seed: int) -> Mesh:
    mesh = _box((0, 0, size * 0.23), (size * 0.75, size * 0.52, size * 0.38))
    if "lid" in features:
        mesh.extend(_box((0, 0, size * 0.45), (size * 0.82, size * 0.58, size * 0.06)))
        mesh.extend(_cylinder((0, 0, size * 0.51), size * 0.11, size * 0.045, segments))
    return mesh


def _build_vase(size: float, segments: int, features: set[str], seed: int) -> Mesh:
    profile = [
        (size * 0.18, 0),
        (size * 0.28, size * 0.10),
        (size * 0.20, size * 0.36),
        (size * 0.30, size * 0.58),
        (size * 0.17, size * 0.82),
    ]
    mesh = _lathe(profile, segments)
    if "base" in features:
        mesh.extend(_cylinder((0, 0, size * 0.025), size * 0.32, size * 0.05, segments))
    return mesh


def _build_castle(size: float, segments: int, features: set[str], seed: int) -> Mesh:
    mesh = _box((0, 0, size * 0.22), (size * 0.75, size * 0.48, size * 0.36))
    for x in (-0.34, 0.34):
        for y in (-0.22, 0.22):
            mesh.extend(_cylinder((x * size, y * size, size * 0.36), size * 0.12, size * 0.72, segments))
            mesh.extend(_cone((x * size, y * size, size * 0.78), size * 0.14, size * 0.24, segments))
    if "battlements" in features:
        for x in [i * size * 0.12 for i in range(-3, 4)]:
            mesh.extend(_box((x, -size * 0.27, size * 0.44), (size * 0.055, size * 0.08, size * 0.10)))
            mesh.extend(_box((x, size * 0.27, size * 0.44), (size * 0.055, size * 0.08, size * 0.10)))
    return mesh


def _build_robot(size: float, segments: int, features: set[str], seed: int) -> Mesh:
    mesh = _box((0, 0, size * 0.38), (size * 0.38, size * 0.24, size * 0.48))
    mesh.extend(_box((0, 0, size * 0.74), (size * 0.30, size * 0.22, size * 0.24)))
    for x in (-0.08, 0.08):
        mesh.extend(_sphere((x * size, -size * 0.115, size * 0.77), size * 0.025, segments // 2, 8))
    if "arms" in features:
        mesh.extend(_cylinder_between((-size * 0.23, 0, size * 0.52), (-size * 0.45, 0, size * 0.36), size * 0.035, segments // 2))
        mesh.extend(_cylinder_between((size * 0.23, 0, size * 0.52), (size * 0.45, 0, size * 0.36), size * 0.035, segments // 2))
    if "legs" in features:
        for x in (-0.12, 0.12):
            mesh.extend(_cylinder_between((x * size, 0, size * 0.16), (x * size, 0, 0), size * 0.045, segments // 2))
    return mesh


def _build_dragon(size: float, segments: int, features: set[str], seed: int) -> Mesh:
    mesh = _sphere((0, 0, size * 0.32), size * 0.22, segments, 12)
    mesh.extend(_sphere((size * 0.27, 0, size * 0.40), size * 0.12, segments, 10))
    if "tail" in features:
        mesh.extend(_arc_tube((-size * 0.18, 0, size * 0.28), size * 0.34, size * 0.035, 130, 245, segments, 8))
    if "wings" in features:
        mesh.extend(_wing((-size * 0.05, size * 0.12, size * 0.46), size, side=1))
        mesh.extend(_wing((-size * 0.05, -size * 0.12, size * 0.46), size, side=-1))
    if "spikes" in features:
        for i in range(6):
            x = (-0.18 + i * 0.075) * size
            mesh.extend(_cone((x, 0, size * 0.55), size * 0.035, size * 0.10, 10))
    if "legs" in features:
        for x in (-0.12, 0.12):
            for y in (-0.11, 0.11):
                mesh.extend(_cylinder_between((x * size, y * size, size * 0.18), (x * size, y * size, 0), size * 0.035, 12))
    return mesh


def _build_rocket(size: float, segments: int, features: set[str], seed: int) -> Mesh:
    mesh = _cylinder((0, 0, size * 0.38), size * 0.16, size * 0.68, segments)
    mesh.extend(_cone((0, 0, size * 0.79), size * 0.16, size * 0.22, segments))
    for angle in (0, 120, 240):
        mesh.extend(_fin(angle, size))
    if "windows" in features:
        mesh.extend(_sphere((0, -size * 0.155, size * 0.55), size * 0.045, segments // 2, 8))
    return mesh


def _build_chair(size: float, segments: int, features: set[str], seed: int) -> Mesh:
    mesh = _box((0, 0, size * 0.34), (size * 0.55, size * 0.48, size * 0.08))
    mesh.extend(_box((0, size * 0.22, size * 0.58), (size * 0.55, size * 0.08, size * 0.48)))
    if "legs" in features:
        for x in (-0.22, 0.22):
            for y in (-0.18, 0.18):
                mesh.extend(_cylinder_between((x * size, y * size, size * 0.30), (x * size, y * size, 0), size * 0.025, 10))
    return mesh


def _build_gear(size: float, segments: int, features: set[str], seed: int) -> Mesh:
    mesh = _cylinder((0, 0, size * 0.10), size * 0.26, size * 0.20, segments)
    teeth = 14
    for i in range(teeth):
        angle = 2 * math.pi * i / teeth
        x = math.cos(angle) * size * 0.31
        y = math.sin(angle) * size * 0.31
        mesh.extend(_rotated_box((x, y, size * 0.10), (size * 0.11, size * 0.055, size * 0.20), angle))
    mesh.extend(_torus((0, 0, size * 0.105), size * 0.11, size * 0.025, segments, 8))
    return mesh


def _build_lamp(size: float, segments: int, features: set[str], seed: int) -> Mesh:
    mesh = _cylinder((0, 0, size * 0.04), size * 0.26, size * 0.08, segments)
    mesh.extend(_cylinder_between((0, 0, size * 0.08), (0, 0, size * 0.52), size * 0.035, segments // 2))
    mesh.extend(_cone((0, 0, size * 0.54), size * 0.28, size * 0.24, segments))
    mesh.extend(_cylinder((0, 0, size * 0.80), size * 0.12, size * 0.06, segments))
    return mesh


def _build_sculpture(size: float, segments: int, features: set[str], seed: int) -> Mesh:
    mesh = _cylinder((0, 0, size * 0.035), size * 0.34, size * 0.07, segments)
    count = 4 + seed % 5
    for i in range(count):
        angle = 2 * math.pi * i / count
        radius = size * (0.11 + ((seed >> i) & 3) * 0.025)
        height = size * (0.20 + i * 0.055)
        x = math.cos(angle) * size * 0.16
        y = math.sin(angle) * size * 0.16
        mesh.extend(_sphere((x, y, height), radius, max(12, segments // 2), 8))
        mesh.extend(_cylinder_between((0, 0, size * 0.07), (x, y, height), size * 0.025, 10))
    return mesh


def _add_prompt_texture(mesh: Mesh, size: float, segments: int, seed: int, features: set[str]) -> None:
    if "spikes" in features:
        for i in range(8):
            angle = 2 * math.pi * i / 8
            x = math.cos(angle) * size * 0.28
            y = math.sin(angle) * size * 0.28
            mesh.extend(_cone((x, y, size * 0.48), size * 0.025, size * 0.08, 8))
    elif seed % 3 == 0:
        for i in range(6):
            angle = 2 * math.pi * i / 6
            x = math.cos(angle) * size * 0.31
            y = math.sin(angle) * size * 0.31
            mesh.extend(_sphere((x, y, size * 0.08), size * 0.025, 10, 6))


def _box(center: Vec3, size: Vec3) -> Mesh:
    cx, cy, cz = center
    sx, sy, sz = (size[0] / 2, size[1] / 2, size[2] / 2)
    v = [
        (cx - sx, cy - sy, cz - sz), (cx + sx, cy - sy, cz - sz),
        (cx + sx, cy + sy, cz - sz), (cx - sx, cy + sy, cz - sz),
        (cx - sx, cy - sy, cz + sz), (cx + sx, cy - sy, cz + sz),
        (cx + sx, cy + sy, cz + sz), (cx - sx, cy + sy, cz + sz),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh = Mesh()
    for a, b, c, d in faces:
        mesh.add(v[a], v[b], v[c])
        mesh.add(v[a], v[c], v[d])
    return mesh


def _rotated_box(center: Vec3, size: Vec3, angle: float) -> Mesh:
    base = _box((0, 0, 0), size)
    ca, sa = math.cos(angle), math.sin(angle)
    out = Mesh()
    for tri in base.triangles:
        out.add(*tuple((center[0] + p[0] * ca - p[1] * sa, center[1] + p[0] * sa + p[1] * ca, center[2] + p[2]) for p in tri))
    return out


def _cylinder(center: Vec3, radius: float, height: float, segments: int) -> Mesh:
    cx, cy, cz = center
    z0, z1 = cz - height / 2, cz + height / 2
    mesh = Mesh()
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        p0 = (cx + radius * math.cos(a0), cy + radius * math.sin(a0), z0)
        p1 = (cx + radius * math.cos(a1), cy + radius * math.sin(a1), z0)
        p2 = (cx + radius * math.cos(a1), cy + radius * math.sin(a1), z1)
        p3 = (cx + radius * math.cos(a0), cy + radius * math.sin(a0), z1)
        mesh.add(p0, p1, p2)
        mesh.add(p0, p2, p3)
        mesh.add((cx, cy, z0), p1, p0)
        mesh.add((cx, cy, z1), p3, p2)
    return mesh


def _open_cylinder_shell(center: Vec3, radius: float, height: float, wall: float, segments: int) -> Mesh:
    cx, cy, cz = center
    inner = max(radius - wall, radius * 0.55)
    z0, z1 = cz - height / 2, cz + height / 2
    mesh = Mesh()
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        outer0 = (cx + radius * math.cos(a0), cy + radius * math.sin(a0), z0)
        outer1 = (cx + radius * math.cos(a1), cy + radius * math.sin(a1), z0)
        outer2 = (cx + radius * math.cos(a1), cy + radius * math.sin(a1), z1)
        outer3 = (cx + radius * math.cos(a0), cy + radius * math.sin(a0), z1)
        inner0 = (cx + inner * math.cos(a0), cy + inner * math.sin(a0), z0 + wall)
        inner1 = (cx + inner * math.cos(a1), cy + inner * math.sin(a1), z0 + wall)
        inner2 = (cx + inner * math.cos(a1), cy + inner * math.sin(a1), z1)
        inner3 = (cx + inner * math.cos(a0), cy + inner * math.sin(a0), z1)
        mesh.add(outer0, outer1, outer2)
        mesh.add(outer0, outer2, outer3)
        mesh.add(inner1, inner0, inner3)
        mesh.add(inner1, inner3, inner2)
        mesh.add(outer3, outer2, inner2)
        mesh.add(outer3, inner2, inner3)
        mesh.add(outer0, inner0, inner1)
        mesh.add(outer0, inner1, outer1)
    return mesh


def _cone(center: Vec3, radius: float, height: float, segments: int) -> Mesh:
    cx, cy, cz = center
    z0 = cz - height / 2
    apex = (cx, cy, cz + height / 2)
    mesh = Mesh()
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        p0 = (cx + radius * math.cos(a0), cy + radius * math.sin(a0), z0)
        p1 = (cx + radius * math.cos(a1), cy + radius * math.sin(a1), z0)
        mesh.add(p0, p1, apex)
        mesh.add((cx, cy, z0), p1, p0)
    return mesh


def _sphere(center: Vec3, radius: float, segments: int, rings: int) -> Mesh:
    mesh = Mesh()
    for r in range(rings):
        phi0 = math.pi * r / rings
        phi1 = math.pi * (r + 1) / rings
        for s in range(segments):
            theta0 = 2 * math.pi * s / segments
            theta1 = 2 * math.pi * (s + 1) / segments
            p00 = _sphere_point(center, radius, phi0, theta0)
            p01 = _sphere_point(center, radius, phi0, theta1)
            p10 = _sphere_point(center, radius, phi1, theta0)
            p11 = _sphere_point(center, radius, phi1, theta1)
            mesh.add(p00, p10, p11)
            mesh.add(p00, p11, p01)
    return mesh


def _sphere_point(center: Vec3, radius: float, phi: float, theta: float) -> Vec3:
    return (
        center[0] + radius * math.sin(phi) * math.cos(theta),
        center[1] + radius * math.sin(phi) * math.sin(theta),
        center[2] + radius * math.cos(phi),
    )


def _torus(center: Vec3, major_radius: float, tube_radius: float, segments: int, tube_segments: int) -> Mesh:
    mesh = Mesh()
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        for j in range(tube_segments):
            b0 = 2 * math.pi * j / tube_segments
            b1 = 2 * math.pi * (j + 1) / tube_segments
            p00 = _torus_point(center, major_radius, tube_radius, a0, b0)
            p01 = _torus_point(center, major_radius, tube_radius, a0, b1)
            p10 = _torus_point(center, major_radius, tube_radius, a1, b0)
            p11 = _torus_point(center, major_radius, tube_radius, a1, b1)
            mesh.add(p00, p10, p11)
            mesh.add(p00, p11, p01)
    return mesh


def _torus_point(center: Vec3, major: float, tube: float, a: float, b: float) -> Vec3:
    return (
        center[0] + (major + tube * math.cos(b)) * math.cos(a),
        center[1] + (major + tube * math.cos(b)) * math.sin(a),
        center[2] + tube * math.sin(b),
    )


def _lathe(profile: list[tuple[float, float]], segments: int) -> Mesh:
    mesh = Mesh()
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        for j in range(len(profile) - 1):
            r0, z0 = profile[j]
            r1, z1 = profile[j + 1]
            p00 = (r0 * math.cos(a0), r0 * math.sin(a0), z0)
            p01 = (r0 * math.cos(a1), r0 * math.sin(a1), z0)
            p10 = (r1 * math.cos(a0), r1 * math.sin(a0), z1)
            p11 = (r1 * math.cos(a1), r1 * math.sin(a1), z1)
            mesh.add(p00, p01, p11)
            mesh.add(p00, p11, p10)
    return mesh


def _cylinder_between(start: Vec3, end: Vec3, radius: float, segments: int) -> Mesh:
    axis = _sub(end, start)
    length = _length(axis)
    if length == 0:
        return Mesh()
    w = _scale(axis, 1 / length)
    helper = (0, 0, 1) if abs(w[2]) < 0.9 else (0, 1, 0)
    u = _normalize(_cross(w, helper))
    v = _cross(w, u)
    mesh = Mesh()
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        r0 = _add(_scale(u, math.cos(a0) * radius), _scale(v, math.sin(a0) * radius))
        r1 = _add(_scale(u, math.cos(a1) * radius), _scale(v, math.sin(a1) * radius))
        p0 = _add(start, r0)
        p1 = _add(start, r1)
        p2 = _add(end, r1)
        p3 = _add(end, r0)
        mesh.add(p0, p1, p2)
        mesh.add(p0, p2, p3)
    return mesh


def _arc_tube(center: Vec3, radius: float, tube_radius: float, start_deg: float, end_deg: float, segments: int, tube_segments: int) -> Mesh:
    arc_steps = max(8, segments // 2)
    mesh = Mesh()
    rings: list[list[Vec3]] = []
    for i in range(arc_steps + 1):
        angle = math.radians(start_deg + (end_deg - start_deg) * i / arc_steps)
        radial = (math.cos(angle), 0, math.sin(angle))
        c = (center[0] + radius * radial[0], center[1], center[2] + radius * radial[2])
        ring = []
        for j in range(tube_segments):
            b = 2 * math.pi * j / tube_segments
            ring.append((c[0] + tube_radius * math.cos(b) * radial[0], c[1] + tube_radius * math.sin(b), c[2] + tube_radius * math.cos(b) * radial[2]))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for j in range(tube_segments):
            p00 = rings[i][j]
            p01 = rings[i][(j + 1) % tube_segments]
            p10 = rings[i + 1][j]
            p11 = rings[i + 1][(j + 1) % tube_segments]
            mesh.add(p00, p10, p11)
            mesh.add(p00, p11, p01)
    return mesh


def _wing(origin: Vec3, size: float, side: int) -> Mesh:
    ox, oy, oz = origin
    p0 = (ox, oy, oz)
    p1 = (ox - size * 0.28, oy + side * size * 0.40, oz + size * 0.08)
    p2 = (ox + size * 0.04, oy + side * size * 0.22, oz - size * 0.18)
    p3 = (ox - size * 0.13, oy + side * size * 0.27, oz - size * 0.05)
    mesh = Mesh()
    mesh.add(p0, p1, p3)
    mesh.add(p0, p3, p2)
    mesh.add(p0, p3, p1)
    mesh.add(p0, p2, p3)
    return mesh


def _fin(angle_deg: float, size: float) -> Mesh:
    angle = math.radians(angle_deg)
    radial = (math.cos(angle), math.sin(angle), 0)
    tangent = (-math.sin(angle), math.cos(angle), 0)
    base = _scale(radial, size * 0.15)
    p0 = (base[0], base[1], size * 0.10)
    p1 = _add(p0, _scale(tangent, size * 0.07))
    p2 = _add(p0, _scale(radial, size * 0.18))
    p2 = (p2[0], p2[1], size * 0.32)
    p3 = _add(p0, _scale(tangent, -size * 0.07))
    mesh = Mesh()
    mesh.add(p0, p1, p2)
    mesh.add(p0, p2, p3)
    return mesh


def _normal(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    return _normalize(_cross(_sub(b, a), _sub(c, a)))


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _scale(a: Vec3, value: float) -> Vec3:
    return (a[0] * value, a[1] * value, a[2] * value)


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _length(a: Vec3) -> float:
    return math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)


def _normalize(a: Vec3) -> Vec3:
    length = _length(a)
    if length == 0:
        return (0.0, 0.0, 0.0)
    return (a[0] / length, a[1] / length, a[2] / length)
