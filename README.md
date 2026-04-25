# Dream Printer

Dream Printer turns a text prompt into a downloadable STL file from a Streamlit UI.

The current generator is local-first: it does not require Docker, CadQuery, OpenSCAD, an API key, or a running LLM service. It parses the prompt into a printable object spec, composes mesh primitives in Python, and writes an ASCII STL.

## Features

- Prompt-first STL generation
- Streamlit UI with examples, mesh detail, size controls, generated spec preview, and STL download
- Pure-Python STL writer with no CAD runtime dependency
- Built-in templates for mugs, rings, boxes, vases, castles, robots, dragons, rockets, chairs, gears, lamps, and abstract sculptures
- Deterministic output: the same prompt produces the same generated spec and mesh style

## Setup

Prerequisites:

- Python 3.10+

Install and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run frontend\streamlit_app.py
```

Open the local Streamlit URL shown in the terminal, usually `http://localhost:8501`.

## Usage

1. Choose an example or type your own prompt.
2. Pick mesh detail and default size.
3. Click **Generate STL**.
4. Download the generated `.stl` file.

Example prompts:

- `a detailed dragon lamp with wings, horns, a long tail, and a round base, about 120 mm tall`
- `an ornate castle tower planter with battlements and a wide base, 100 mm`
- `a cute mechanical robot toy with arms, legs, square head, and big eyes, 85 mm`
- `a small sci-fi rocket ship with fins, circular windows, and a sturdy base, 60 mm`

## How It Works

1. `backend.stl_builder.compile_prompt_to_spec` extracts object type, style tags, features, size, and a deterministic seed from the prompt.
2. `backend.stl_builder.build_mesh_from_spec` turns the spec into triangles using built-in primitive builders.
3. `backend.stl_builder.write_ascii_stl` writes a standard ASCII STL file.
4. `frontend/streamlit_app.py` displays the UI and serves the generated STL as a download.

## Tests

```powershell
python -m unittest discover -s tests
```

## Limits

This is a deterministic procedural generator, not a full text-to-CAD AI model. It will create printable STL geometry for broad object prompts, but it does not understand arbitrary engineering constraints or produce production-ready mechanical parts. Inspect every STL before printing.

## License

MIT
