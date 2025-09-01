import streamlit as st
import json
import os
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.title("Dream Printer Demo")

# ---- Dynamic Shape Form ----
shape = st.selectbox("Choose shape", ["Cup", "Box", "Ring"])
params = {}

if shape == "Cup":
    params["diameter"] = st.number_input("Diameter (mm)", value=40, min_value=1)
    params["height"] = st.number_input("Height (mm)", value=50, min_value=1)
    params["wall_thickness"] = st.number_input("Wall Thickness (mm)", value=3, min_value=1)
elif shape == "Box":
    params["length"] = st.number_input("Length (mm)", value=40, min_value=1)
    params["width"] = st.number_input("Width (mm)", value=30, min_value=1)
    params["height"] = st.number_input("Height (mm)", value=15, min_value=1)
elif shape == "Ring":
    params["inner_diameter"] = st.number_input("Inner Diameter (mm)", value=20, min_value=1)
    params["outer_diameter"] = st.number_input("Outer Diameter (mm)", value=25, min_value=1)
    params["height"] = st.number_input("Height (mm)", value=5, min_value=1)

# ---- STL Generation ----
if st.button("Generate STL"):
    spec = {
        "object_type": shape.lower(),
        "primary_dimensions_mm": params
    }
    from backend.pipeline import dream_printer_pipeline
    try:
        dream_printer_pipeline(spec)
        st.success("STL generated!")
        out_path = "backend/output.stl"
        if os.path.exists(out_path):
            with open(out_path, "rb") as f:
                st.download_button("Download STL", f, file_name="output.stl")
        else:
            st.error("STL not generated. Please try again.")
    except Exception as e:
        st.error(f"Error: {e}")
