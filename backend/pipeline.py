from __future__ import annotations

import os
from typing import Any

from backend.stl_builder import build_mesh_from_spec, compile_prompt_to_spec, generate_stl_from_prompt, write_ascii_stl
from backend.trellis_client import TrellisSettings, generate_trellis_asset


def dream_printer_pipeline(input_value: str | dict[str, Any], output_path: str = "generated_models/output.stl", detail: str = "balanced", target_size_mm: int = 80) -> dict[str, Any]:
    """Generate a local procedural STL from a natural-language prompt or spec dict."""
    if isinstance(input_value, str):
        return generate_stl_from_prompt(input_value, output_path, detail=detail, target_size_mm=target_size_mm)

    spec = dict(input_value)
    spec.setdefault("detail", detail)
    spec.setdefault("target_size_mm", target_size_mm)
    spec.setdefault("prompt", spec.get("object_type", "custom object"))
    if "seed" not in spec:
        compiled = compile_prompt_to_spec(str(spec["prompt"]), detail=spec["detail"], target_size_mm=spec["target_size_mm"])
        compiled.update(spec)
        spec = compiled

    mesh = build_mesh_from_spec(spec)
    write_ascii_stl(mesh, output_path)
    return {
        "engine": "local-stl",
        "spec": spec,
        "triangle_count": len(mesh.triangles),
        "output_path": output_path,
        "size_bytes": os.path.getsize(output_path),
    }


def ai_asset_pipeline(prompt: str, output_dir: str = "generated_models/trellis", settings: TrellisSettings | None = None) -> dict[str, Any]:
    """Generate a Meshy-style AI asset through Hugging Face TRELLIS.2."""
    return generate_trellis_asset(prompt, output_dir=output_dir, settings=settings)
