# Dream-printer

> text to .stl basics

![License](https://img.shields.io/badge/license-MIT-green) ![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Language](https://img.shields.io/badge/language-Python-yellow) 
## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Requirements](#requirements)
- [Safety & Disclaimers](#custom-1756759270578)

## ℹ️ Project Information

- **👤 Author:** nik-r08
- **📦 Version:** 1.0.0
- **📄 License:** MIT
- **📂 Repository:** [https://github.com/nik-r08/Dream-printer](https://github.com/nik-r08/Dream-printer)

## Features

• Text-to-3D conversion using natural language prompts
• End-to-end pipeline: LLM prompt → specification → CAD → STL file
• Fast Streamlit frontend for user interaction
• Local-first approach - no subscriptions required
• Built-in examples and templates included
• Support for parametric CAD generation
• Compatible with CadQuery and OpenSCAD
• Optional Docker containerization for easy deployment

## Installation

## Setup Instructions

### Prerequisites
- Python 3.8+
- CadQuery or OpenSCAD
- Streamlit
- Requests library
- Docker (optional)
- Local LLM API (optional)

### Installation Steps

1. **Create virtual environment:**
```bash
python -m venv dream-printer-env
source dream-printer-env/bin/activate  # On Windows: dream-printer-env\Scripts\activate
```

2. **Clone the repository:**
```bash
git clone https://github.com/dream-printer/dream-printer.git
cd dream-printer
```

3. **Install requirements:**
```bash
pip install -r requirements.txt
```

4. **Run the application:**
```bash
streamlit run app.py
```

5. **Access the app:**
Open your browser to `http://localhost:8501`

## Usage

## How It Works

Dream Printer follows a simple 3-step process:

### 1. Prompt Parsing
- Input your natural language description (e.g., "a coffee mug shaped like an octopus")
- The system analyzes and interprets your request
- Extracts key dimensional and geometric parameters

### 2. Parametric CAD Generation
- Converts parsed specifications into parametric CAD code
- Uses CadQuery or OpenSCAD for 3D modeling
- Applies design constraints and optimizations

### 3. Frontend Preview
- Displays real-time 3D preview in Streamlit interface
- Allows parameter adjustments before final generation
- Exports finished model as STL file for 3D printing

## Example Usage

### Basic Workflow
1. Launch the application: `streamlit run app.py`
2. Enter prompt: "a coffee mug shaped like an octopus"
3. Review generated specifications
4. Adjust parameters if needed
5. Download your STL file

### Sample Spec JSON
```json
{
  "object_type": "mug",
  "shape_modifier": "octopus",
  "dimensions": {
    "height": 10,
    "diameter": 8,
    "wall_thickness": 2
  },
  "features": [
    "handle",
    "tentacle_details",
    "curved_body"
  ]
}
```

### CAD Generator Example
```python
import cadquery as cq

def generate_octopus_mug(spec):
    # Create basic mug shape
    mug = cq.Workplane("XY").cylinder(
        height=spec["dimensions"]["height"],
        radius=spec["dimensions"]["diameter"] / 2
    )
    
    # Add octopus tentacles
    for i in range(8):
        angle = i * 45
        tentacle = create_tentacle(angle)
        mug = mug.union(tentacle)
    
    return mug
```

## Requirements

• Docker (for containerized deployment)
• Python 3.8 or higher
• Streamlit (for web interface)
• Local LLM API (for natural language processing)
• At least 4GB RAM recommended
• Compatible with Windows, macOS, and Linux

## Safety & Disclaimers

⚠️ **Important Safety Information:**
- This system is experimental and in active development
- Always inspect generated STL files before printing
- Test with small, non-critical objects first
- Verify dimensions and structural integrity
- Check for printability (overhangs, supports needed)
- Follow your 3D printer's safety guidelines

## Credits & Acknowledgments

- Built with [CadQuery](https://cadquery.readthedocs.io/) for parametric CAD
- Powered by [Streamlit](https://streamlit.io/) for the web interface
- Utilizes open-source AI models for natural language processing
- Inspired by innovations from OpenAI Hackathons
- Special thanks to the 3D printing and maker communities

## License

This project is dual-licensed under MIT and Apache-2.0. Choose the license that best fits your use case.

