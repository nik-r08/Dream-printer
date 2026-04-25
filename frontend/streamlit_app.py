from __future__ import annotations

import base64
import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.pipeline import ai_asset_pipeline, dream_printer_pipeline
from backend.trellis_client import DEFAULT_TRELLIS_SPACE, TrellisSettings

st.set_page_config(page_title="VoxelSmith Studio", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: #f4f1ea; color: #151515; }
    .block-container { padding-top: 1.5rem; max-width: 1220px; }
    section[data-testid="stSidebar"] { background: #202523; }
    h1 { font-size: 2.55rem !important; line-height: 1.02 !important; letter-spacing: 0 !important; }
    h2, h3 { letter-spacing: 0 !important; }
    .hero {
        min-height: 28vh;
        display: flex;
        align-items: end;
        border-bottom: 1px solid #d6cdbc;
        padding: 1.25rem 0 1.4rem 0;
        margin-bottom: 1rem;
    }
    .hero-copy { max-width: 820px; }
    .eyebrow { color: #6d4f2f; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
    .hint { color: #514b42; font-size: 1rem; line-height: 1.5; margin-top: 0.55rem; }
    .metric-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.75rem; margin: 1rem 0; }
    .metric-card { background: #fffaf0; border: 1px solid #ded5c4; border-radius: 8px; padding: 0.85rem 0.95rem; }
    .metric-card span { color: #666; font-size: 0.8rem; }
    .metric-card strong { display: block; color: #161616; font-size: 1.22rem; margin-top: 0.1rem; }
    .stButton button, .stDownloadButton button { border-radius: 8px; border: 1px solid #202523; background: #202523; color: white; min-height: 2.75rem; }
    .stButton button:hover, .stDownloadButton button:hover { border-color: #0f1110; background: #0f1110; color: white; }
    textarea { border-radius: 8px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-copy">
        <div class="eyebrow">Text to AI mesh to printable file</div>
        <h1>VoxelSmith Studio</h1>
        <div class="hint">Generate Meshy-style 3D assets with Hugging Face TRELLIS.2, then download GLB and STL files. Use Instant STL when you want fast local output with no cloud queue.</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

examples = {
    "Collectible dragon": "a highly detailed collectible dragon figurine, curled tail, layered wings, small horns, stylized resin toy, isolated object, clean white background",
    "Cyber sneaker": "a futuristic cyberpunk sneaker with translucent sole, hard surface panels, glowing accents, product render, isolated object",
    "Desk robot": "a cute desktop robot mascot with round eyes, chunky arms, small antenna, toy-like plastic material, isolated object",
    "Fantasy lamp": "an ornate fantasy lantern with carved metal frame, glass panels, small feet, premium game asset, isolated object",
    "Retro spaceship": "a retro sci-fi spaceship miniature with fins, circular windows, panel lines, tabletop model, isolated object",
}

with st.sidebar:
    st.subheader("Studio Presets")
    example_name = st.selectbox("Prompt starter", list(examples.keys()))
    engine = st.radio("Engine", ["TRELLIS.2 Cloud", "Instant STL"], horizontal=False)
    st.caption("TRELLIS.2 Cloud uses a Hugging Face Space. Set HF_TOKEN if the Space requires authentication or has queue limits.")

prompt = st.text_area("Prompt", value=examples[example_name], height=140)

ai_tab, local_tab = st.tabs(["AI Mesh", "Print Utility"])

with ai_tab:
    st.subheader("TRELLIS.2 Asset Generation")
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        resolution = st.selectbox("Resolution", ["512", "1024", "1536"], index=0)
    with col_b:
        target_faces = st.slider("Target faces", 50000, 500000, 150000, 10000)
    with col_c:
        texture_size = st.selectbox("Texture", [512, 1024, 2048, 4096], index=1)
    with col_d:
        seed = st.number_input("Seed", min_value=0, max_value=2147483647, value=0, step=1)

    with st.expander("Advanced sampler controls"):
        a1, a2, a3 = st.columns(3)
        with a1:
            ss_steps = st.slider("Structure steps", 1, 50, 12)
            ss_guidance = st.slider("Structure guidance", 1.0, 10.0, 7.5, 0.5)
        with a2:
            shape_steps = st.slider("Shape steps", 1, 50, 12)
            shape_guidance = st.slider("Shape guidance", 1.0, 10.0, 7.5, 0.5)
        with a3:
            tex_steps = st.slider("Texture steps", 1, 50, 12)
            tex_guidance = st.slider("Texture guidance", 1.0, 10.0, 1.0, 0.5)

    if st.button("Generate AI Asset", use_container_width=True, disabled=engine != "TRELLIS.2 Cloud"):
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("generated_models", f"voxelsmith_trellis_{run_id}")
        settings = TrellisSettings(
            space=os.getenv("VOXELSMITH_TRELLIS_SPACE", DEFAULT_TRELLIS_SPACE),
            resolution=resolution,
            target_faces=target_faces,
            texture_size=texture_size,
            seed=seed,
            randomize_seed=False,
            ss_sampling_steps=ss_steps,
            ss_guidance_strength=ss_guidance,
            shape_steps=shape_steps,
            shape_guidance=shape_guidance,
            tex_steps=tex_steps,
            tex_guidance=tex_guidance,
        )
        try:
            with st.status("Generating concept image and 3D asset through Hugging Face TRELLIS.2...", expanded=True):
                result = ai_asset_pipeline(prompt, output_dir=output_dir, settings=settings)
            st.success("AI asset generated.")
            _render_ai_result(result)
        except Exception as exc:
            st.error(f"TRELLIS generation failed: {exc}")
            st.info("Switch to Instant STL for local generation, or set HF_TOKEN and try again if the Hugging Face Space is busy.")

with local_tab:
    st.subheader("Instant Local STL")
    l1, l2 = st.columns(2)
    with l1:
        detail = st.radio("Mesh detail", ["fast", "balanced", "detailed"], index=1, horizontal=True)
    with l2:
        target_size = st.slider("Default size (mm)", min_value=30, max_value=180, value=90, step=5)
    if st.button("Generate Local STL", use_container_width=True, disabled=engine != "Instant STL"):
        safe_name = datetime.now().strftime("voxelsmith_local_%Y%m%d_%H%M%S.stl")
        output_path = os.path.join("generated_models", safe_name)
        try:
            result = dream_printer_pipeline(prompt, output_path=output_path, detail=detail, target_size_mm=target_size)
            spec = result["spec"]
            file_size_kb = result["size_bytes"] / 1024
            st.success("Local STL generated.")
            st.markdown(
                f"""
                <div class="metric-row">
                  <div class="metric-card"><span>Object</span><strong>{spec['object_type'].title()}</strong></div>
                  <div class="metric-card"><span>Triangles</span><strong>{result['triangle_count']:,}</strong></div>
                  <div class="metric-card"><span>File size</span><strong>{file_size_kb:.1f} KB</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            _download_file(output_path, "Download STL", "model/stl")
            st.subheader("Generated Spec")
            st.json(spec)
        except Exception as exc:
            st.error(f"Local generation failed: {exc}")


def _render_ai_result(result: dict) -> None:
    image_path = result.get("image_path")
    glb_path = result.get("glb_path")
    stl_path = result.get("stl_path")
    cols = st.columns([0.35, 0.65])
    with cols[0]:
        if image_path and os.path.exists(image_path):
            st.image(image_path, caption="Generated concept image", use_column_width=True)
        st.markdown(
            f"""
            <div class="metric-row" style="grid-template-columns: 1fr;">
              <div class="metric-card"><span>Engine</span><strong>TRELLIS.2</strong></div>
              <div class="metric-card"><span>Resolution</span><strong>{result.get('resolution')}</strong></div>
              <div class="metric-card"><span>Target faces</span><strong>{result.get('target_faces'):,}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[1]:
        if glb_path and os.path.exists(glb_path):
            st.components.v1.html(_model_viewer_html(glb_path), height=520)
            _download_file(glb_path, "Download GLB", "model/gltf-binary")
        if stl_path and os.path.exists(stl_path):
            _download_file(stl_path, "Download STL", "model/stl")
        elif result.get("stl_error"):
            st.warning(f"GLB was generated, but STL conversion failed: {result['stl_error']}")


def _download_file(path: str, label: str, mime: str) -> None:
    with open(path, "rb") as file:
        st.download_button(label, data=file, file_name=os.path.basename(path), mime=mime, use_container_width=True)


def _model_viewer_html(glb_path: str) -> str:
    data = base64.b64encode(Path(glb_path).read_bytes()).decode("ascii")
    return f"""
    <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
    <model-viewer
      src="data:model/gltf-binary;base64,{data}"
      camera-controls
      auto-rotate
      exposure="0.95"
      shadow-intensity="0.7"
      style="width:100%;height:500px;background:#efe8dc;border:1px solid #d6cdbc;border-radius:8px;">
    </model-viewer>
    """
