from __future__ import annotations

import os
import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


DEFAULT_TRELLIS_SPACE = "prithivMLmods/TRELLIS.2-Text-to-3D"
MAX_SEED = 2_147_483_647
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")


@dataclass(frozen=True)
class TrellisSettings:
    space: str = DEFAULT_TRELLIS_SPACE
    resolution: str = "512"
    target_faces: int = 150000
    texture_size: int = 1024
    seed: int = 0
    randomize_seed: bool = True
    ss_guidance_strength: float = 7.5
    ss_guidance_rescale: float = 0.7
    ss_sampling_steps: int = 12
    ss_rescale_t: float = 5.0
    shape_guidance: float = 7.5
    shape_rescale: float = 0.5
    shape_steps: int = 12
    shape_rescale_t: float = 3.0
    tex_guidance: float = 1.0
    tex_rescale: float = 0.0
    tex_steps: int = 12
    tex_rescale_t: float = 3.0


def generate_trellis_asset(prompt: str, output_dir: str, settings: TrellisSettings | None = None) -> dict[str, Any]:
    """Generate a high-fidelity 3D asset through a Hugging Face TRELLIS Space.

    The default Space currently uses a three-step Gradio flow: text-to-image,
    image-to-3D latent generation, then GLB extraction. Older forks exposed a
    direct ``/generate_3d`` endpoint, so we keep that path as a fallback.
    """
    if not prompt.strip():
        raise ValueError("Prompt is required for TRELLIS generation")

    try:
        from gradio_client import Client, handle_file
    except ImportError as exc:
        raise RuntimeError("Install gradio_client to use TRELLIS Cloud mode") from exc

    settings = settings or TrellisSettings()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    client = Client(settings.space, hf_token=token) if token else Client(settings.space)
    return _generate_trellis_asset_with_client(client, handle_file, prompt, output, settings)


def _generate_trellis_asset_with_client(
    client: Any,
    handle_file_func: Callable[[str], Any],
    prompt: str,
    output: Path,
    settings: TrellisSettings,
) -> dict[str, Any]:
    seed = _resolve_seed(settings)
    errors: list[str] = []

    try:
        image_result, generation_result = _generate_current_space_asset(client, handle_file_func, prompt, output, settings, seed)
    except Exception as exc:
        errors.append(f"current TRELLIS.2 Space flow failed: {exc}")
        try:
            image_result, generation_result = _generate_legacy_space_asset(client, handle_file_func, prompt, output, settings, seed)
        except Exception as legacy_exc:
            errors.append(f"legacy TRELLIS.2 flow failed: {legacy_exc}")
            raise RuntimeError("; ".join(errors)) from legacy_exc

    image_path = _copy_first_file(image_result, output / "concept", suffixes=IMAGE_SUFFIXES)
    processed_image_path = _copy_optional_file(generation_result, output / "concept_processed", suffixes=IMAGE_SUFFIXES)
    if processed_image_path:
        image_path = processed_image_path

    glb_path = _copy_first_file(generation_result, output / "asset.glb", suffixes=(".glb",))
    rrd_path = _copy_optional_file(generation_result, output / "preview.rrd", suffixes=(".rrd",))
    stl_path = output / "asset.stl"
    stl_error = None
    try:
        _convert_glb_to_stl(glb_path, str(stl_path))
    except Exception as exc:
        stl_path = None
        stl_error = str(exc)

    return {
        "engine": "trellis-cloud",
        "prompt": prompt,
        "space": settings.space,
        "resolution": settings.resolution,
        "target_faces": settings.target_faces,
        "texture_size": settings.texture_size,
        "seed": seed,
        "image_path": image_path,
        "glb_path": glb_path,
        "stl_path": str(stl_path) if stl_path else None,
        "rrd_path": rrd_path,
        "stl_error": stl_error,
        "raw_result": str(generation_result),
    }


def _generate_current_space_asset(
    client: Any,
    handle_file_func: Callable[[str], Any],
    prompt: str,
    output: Path,
    settings: TrellisSettings,
    seed: int,
) -> tuple[Any, Any]:
    image_result = client.predict(prompt, api_name="/generate_text_to_image")
    image_path = _copy_first_file(image_result, output / "concept", suffixes=IMAGE_SUFFIXES)

    generation_result = client.predict(
        handle_file_func(image_path),
        seed,
        str(settings.resolution),
        [
            int(settings.ss_sampling_steps),
            float(settings.ss_guidance_strength),
            float(settings.ss_guidance_rescale),
            float(settings.ss_rescale_t),
        ],
        [
            int(settings.shape_steps),
            float(settings.shape_guidance),
            float(settings.shape_rescale),
            float(settings.shape_rescale_t),
        ],
        [
            int(settings.tex_steps),
            float(settings.tex_guidance),
            float(settings.tex_rescale),
            float(settings.tex_rescale_t),
        ],
        api_name="/generate_3d_from_image",
    )
    state = _first_non_file_value(generation_result)
    if state is None:
        raise ValueError(f"TRELLIS.2 generation did not return latent state: {generation_result}")

    glb_result = client.predict(
        state,
        int(settings.target_faces),
        int(settings.texture_size),
        api_name="/extract_glb",
    )
    return image_result, [generation_result, glb_result]


def _generate_legacy_space_asset(
    client: Any,
    handle_file_func: Callable[[str], Any],
    prompt: str,
    output: Path,
    settings: TrellisSettings,
    seed: int,
) -> tuple[Any, Any]:
    image_result = client.predict(prompt, api_name="/generate_txt2img")
    image_path = _copy_first_file(image_result, output / "concept", suffixes=IMAGE_SUFFIXES)

    try:
        processed_image = client.predict(handle_file_func(image_path), api_name="/preprocess_image")
        processed_path = _copy_first_file(processed_image, output / "concept_processed", suffixes=IMAGE_SUFFIXES)
        image_path = processed_path
    except Exception:
        # Some Spaces preprocess uploaded images automatically. Keep the raw concept image.
        pass

    generation_result = client.predict(
        handle_file_func(image_path),
        seed,
        str(settings.resolution),
        int(settings.target_faces),
        int(settings.texture_size),
        float(settings.ss_guidance_strength),
        float(settings.ss_guidance_rescale),
        int(settings.ss_sampling_steps),
        float(settings.ss_rescale_t),
        float(settings.shape_guidance),
        float(settings.shape_rescale),
        int(settings.shape_steps),
        float(settings.shape_rescale_t),
        float(settings.tex_guidance),
        float(settings.tex_rescale),
        int(settings.tex_steps),
        float(settings.tex_rescale_t),
        api_name="/generate_3d",
    )
    return image_result, generation_result


def _resolve_seed(settings: TrellisSettings) -> int:
    if settings.randomize_seed:
        return random.randint(0, MAX_SEED)
    return max(0, min(MAX_SEED, int(settings.seed)))


def _convert_glb_to_stl(glb_path: str, stl_path: str) -> None:
    try:
        import trimesh
    except ImportError as exc:
        raise RuntimeError("Install trimesh to convert GLB assets to STL") from exc

    loaded = trimesh.load(glb_path, force="scene")
    if hasattr(loaded, "dump"):
        meshes = [mesh for mesh in loaded.dump() if getattr(mesh, "faces", None) is not None and len(mesh.faces) > 0]
        if not meshes:
            raise ValueError("GLB did not contain exportable mesh geometry")
        mesh = trimesh.util.concatenate(meshes)
    else:
        mesh = loaded
    mesh.export(stl_path)


def _copy_optional_file(value: Any, destination: Path, suffixes: tuple[str, ...]) -> str | None:
    try:
        return _copy_first_file(value, destination, suffixes=suffixes)
    except ValueError:
        return None


def _copy_first_file(value: Any, destination: Path, suffixes: tuple[str, ...] | None = None) -> str:
    source = _first_file_path(value, suffixes=suffixes)
    if source is None:
        raise ValueError(f"No generated file found in Hugging Face response: {value}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.suffix == "" and source.suffix:
        destination = destination.with_suffix(source.suffix)
    shutil.copyfile(source, destination)
    return str(destination)


def _first_file_path(value: Any, suffixes: tuple[str, ...] | None = None) -> Path | None:
    if isinstance(value, (str, os.PathLike)):
        candidate = Path(value)
        if candidate.exists() and _suffix_ok(candidate, suffixes):
            return candidate
        return None

    if isinstance(value, dict):
        for key in ("path", "name", "orig_name", "url"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                path = Path(candidate)
                if path.exists() and _suffix_ok(path, suffixes):
                    return path
        for item in value.values():
            found = _first_file_path(item, suffixes=suffixes)
            if found is not None:
                return found
        return None

    if isinstance(value, (list, tuple)):
        for item in value:
            found = _first_file_path(item, suffixes=suffixes)
            if found is not None:
                return found
    return None


def _first_non_file_value(value: Any) -> Any | None:
    if isinstance(value, dict):
        if _first_file_path(value) is None:
            return value
        for item in value.values():
            found = _first_non_file_value(item)
            if found is not None:
                return found
        return None
    if isinstance(value, (list, tuple)):
        for item in value:
            found = _first_non_file_value(item)
            if found is not None:
                return found
    return None


def _suffix_ok(path: Path, suffixes: tuple[str, ...] | None) -> bool:
    if suffixes is None:
        return True
    return path.suffix.lower() in suffixes
