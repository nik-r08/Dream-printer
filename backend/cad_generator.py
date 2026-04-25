from __future__ import annotations

import json
from typing import Any

from backend.stl_builder import build_mesh_from_spec, compile_prompt_to_spec, write_ascii_stl


def json_spec_to_stl(json_spec: str | dict[str, Any], filename: str = "generated_models/output.stl") -> dict[str, Any]:
    """Generate an STL from JSON text or a spec dict.

    This keeps the original public function name, but it now writes STL files
    directly with the pure-Python mesh builder instead of shelling out to Docker.
    """
    if isinstance(json_spec, str):
        spec = json.loads(_extract_json(json_spec))
    else:
        spec = dict(json_spec)

    if "seed" not in spec:
        prompt = spec.get("prompt") or spec.get("object_type") or "custom printable object"
        compiled = compile_prompt_to_spec(str(prompt), detail=spec.get("detail", "balanced"), target_size_mm=int(spec.get("target_size_mm", 80)))
        compiled.update(spec)
        spec = compiled

    mesh = build_mesh_from_spec(spec)
    write_ascii_stl(mesh, filename)
    return {
        "spec": spec,
        "triangle_count": len(mesh.triangles),
        "output_path": filename,
    }


def _extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in input")
    return text[start : end + 1]
