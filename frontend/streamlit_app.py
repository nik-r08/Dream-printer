from __future__ import annotations

import os
import sys
from datetime import datetime

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.pipeline import dream_printer_pipeline

st.set_page_config(page_title="Dream Printer", page_icon="DP", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: #f7f5ef; color: #171717; }
    .block-container { padding-top: 2rem; max-width: 1180px; }
    section[data-testid="stSidebar"] { background: #202523; }
    h1 { font-size: 2.35rem !important; line-height: 1.05 !important; letter-spacing: 0 !important; }
    h2, h3 { letter-spacing: 0 !important; }
    .hero {
        border-bottom: 1px solid #d9d2c4;
        padding: 0.25rem 0 1.25rem 0;
        margin-bottom: 1rem;
    }
    .metric-row {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: #fffaf0;
        border: 1px solid #ded5c4;
        border-radius: 8px;
        padding: 0.8rem 0.9rem;
    }
    .metric-card span { color: #666; font-size: 0.8rem; }
    .metric-card strong { display: block; color: #161616; font-size: 1.25rem; margin-top: 0.1rem; }
    .hint {
        color: #4f4a42;
        font-size: 0.92rem;
        line-height: 1.45;
        margin-top: 0.5rem;
    }
    .stButton button, .stDownloadButton button {
        border-radius: 8px;
        border: 1px solid #262b28;
        background: #262b28;
        color: white;
        min-height: 2.7rem;
    }
    .stButton button:hover, .stDownloadButton button:hover {
        border-color: #0f1110;
        background: #0f1110;
        color: white;
    }
    textarea { border-radius: 8px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>Dream Printer</h1>
      <div class="hint">Type an object idea, generate a deterministic printable STL, then download it. No Docker, no API key, no CadQuery setup.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

examples = {
    "Dragon lamp": "a detailed dragon lamp with wings, horns, a long tail, and a round base, about 120 mm tall",
    "Castle planter": "an ornate castle tower planter with battlements and a wide base, 100 mm",
    "Robot toy": "a cute mechanical robot toy with arms, legs, square head, and big eyes, 85 mm",
    "Rocket keychain": "a small sci-fi rocket ship with fins, circular windows, and a sturdy base, 60 mm",
    "Abstract desk sculpture": "an abstract coral-like desk sculpture with smooth organic branches, 90 mm",
}

with st.sidebar:
    st.subheader("Build Settings")
    example_name = st.selectbox("Example", list(examples.keys()))
    detail = st.segmented_control("Mesh detail", ["fast", "balanced", "detailed"], default="balanced")
    target_size = st.slider("Default size (mm)", min_value=30, max_value=180, value=90, step=5)
    st.caption("Prompts can override size with values like 75 mm, 8 cm, or 3 inches.")

left, right = st.columns([1.25, 0.75], gap="large")

with left:
    prompt = st.text_area(
        "Prompt",
        value=examples[example_name],
        height=155,
        placeholder="Example: a complex dragon-shaped pencil holder with wings and spikes, 120 mm tall",
    )
    generate = st.button("Generate STL", use_container_width=True)

with right:
    st.subheader("What it can build")
    st.markdown(
        """
        - Cups and mugs with handles
        - Rings, gears, boxes, vases, lamps
        - Castles, rockets, robots, chairs
        - Dragon and abstract sculptures
        """
    )
    st.caption("The generator composes printable primitives from the prompt. It is deterministic, so the same prompt creates the same model.")

if generate:
    safe_name = datetime.now().strftime("dream_printer_%Y%m%d_%H%M%S.stl")
    output_path = os.path.join("generated_models", safe_name)
    try:
        result = dream_printer_pipeline(prompt, output_path=output_path, detail=detail or "balanced", target_size_mm=target_size)
        spec = result["spec"]
        file_size_kb = result["size_bytes"] / 1024

        st.success("STL generated.")
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

        with open(output_path, "rb") as file:
            st.download_button(
                "Download STL",
                data=file,
                file_name=safe_name,
                mime="model/stl",
                use_container_width=True,
            )

        st.subheader("Generated Spec")
        st.json(spec)
    except Exception as exc:
        st.error(f"Generation failed: {exc}")
else:
    st.info("Enter a prompt and generate an STL.")
