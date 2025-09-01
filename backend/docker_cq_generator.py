import json
import cadquery as cq

with open("/scripts/spec_input.json", "r", encoding="utf-8") as f:
    spec = json.load(f)

object_type = spec.get("object_type", "").lower()
dims = spec.get("primary_dimensions_mm", {})

if object_type == "cup":
    diameter = dims.get("diameter", 40)
    height = dims.get("height", 50)
    wall = dims.get("wall_thickness", 3)
    result = (
        cq.Workplane("XY")
        .circle(diameter / 2)
        .extrude(height)
        .faces(">Z").workplane()
        .hole((diameter / 2) - wall)
    )

elif object_type == "box":
    length = dims.get("length", 40)
    width = dims.get("width", 30)
    height = dims.get("height", 15)
    result = cq.Workplane("XY").box(length, width, height)

elif object_type == "ring":
    idiam = dims.get("inner_diameter", 20) / 2
    odiam = dims.get("outer_diameter", 25) / 2
    height = dims.get("height", 5)
    result = (
        cq.Workplane("XY")
        .circle(odiam)
        .circle(idiam)
        .extrude(height)
    )

else:
    # Default fallback
    result = cq.Workplane("XY").box(20, 20, 20)

cq.exporters.export(result, "/scripts/output.stl")
