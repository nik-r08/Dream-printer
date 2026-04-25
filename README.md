# VoxelSmith Studio

VoxelSmith Studio is a prompt-to-3D workbench for generating AI 3D assets and printer-friendly files from one interface.

It has two engines:

- **TRELLIS.2 Cloud**: calls a Hugging Face Space that chains text-to-image with Microsoft TRELLIS.2 image-to-3D generation, then returns GLB and attempts STL conversion.
- **Instant STL**: a local procedural generator that creates a deterministic STL with no account, no GPU, and no cloud queue.

## Why It Stands Out

- **Meshy-style workflow, open model stack**: prompt in, AI mesh out, using TRELLIS.2 instead of a closed-only workflow.
- **GLB and STL outputs**: GLB for textured asset workflows, STL for 3D printing.
- **Built-in fallback**: if the Hugging Face Space is busy, the local STL engine still works.
- **Prompt craft presets**: example prompts are written for isolated product/object generation, which is what image-to-3D models need.
- **Inspectable generation**: local mode exposes the generated object spec; AI mode shows the generated concept image and 3D preview.

## Setup

Prerequisites:

- Python 3.10+
- Internet access for TRELLIS.2 Cloud mode
- Optional: a Hugging Face token if the Space is rate-limited or requires auth

Install and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run frontend\streamlit_app.py
```

Optional environment variables:

```powershell
$env:HF_TOKEN="your_hugging_face_token"
$env:VOXELSMITH_TRELLIS_SPACE="prithivMLmods/TRELLIS.2-Text-to-3D"
```

Open the Streamlit URL shown in the terminal, usually `http://localhost:8501`.

## Usage

1. Pick a prompt starter or write your own prompt.
2. Choose **TRELLIS.2 Cloud** for high-fidelity AI assets, or **Instant STL** for local generation.
3. In AI Mesh mode, choose resolution, face target, texture size, and sampler settings.
4. Generate and download GLB and/or STL.

Example prompts:

- `a highly detailed collectible dragon figurine, curled tail, layered wings, small horns, stylized resin toy, isolated object, clean white background`
- `a futuristic cyberpunk sneaker with translucent sole, hard surface panels, glowing accents, product render, isolated object`
- `a cute desktop robot mascot with round eyes, chunky arms, small antenna, toy-like plastic material, isolated object`
- `an ornate fantasy lantern with carved metal frame, glass panels, small feet, premium game asset, isolated object`

## How It Works

### TRELLIS.2 Cloud

1. `backend.trellis_client.generate_trellis_asset` calls the configured Hugging Face Space.
2. The Space generates a concept image from the prompt.
3. TRELLIS.2 converts that image into a textured GLB asset.
4. VoxelSmith copies the GLB locally and attempts STL conversion with `trimesh`.

### Instant STL

1. `backend.stl_builder.compile_prompt_to_spec` extracts object type, style tags, features, size, and seed.
2. `backend.stl_builder.build_mesh_from_spec` turns the spec into triangle geometry.
3. `backend.stl_builder.write_ascii_stl` writes a standard ASCII STL file.

## Tests

```powershell
python -m unittest discover -s tests
```

The tests cover local generation and file-response parsing. TRELLIS.2 Cloud mode requires network access and is best verified manually from the Streamlit app.

## Limits

TRELLIS.2 Cloud depends on Hugging Face Space availability, queue time, and upstream API compatibility. Generated meshes can still need inspection, repair, scaling, or support planning before printing.

Instant STL is procedural and fast, but it is not a replacement for high-fidelity AI mesh generation or engineering CAD.

## License

MIT
