# Dream-printer

> text to .stl basics

![License](https://img.shields.io/badge/license-MIT-green) ![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Language](https://img.shields.io/badge/language-Python-yellow) 

## 📋 Table of Contents

- [Features](#features)
- [Usage](#usage)
- [Requirements](#requirements)

## ℹ️ Project Information

- **👤 Author:** nik-r08
- **📦 Version:** 1.0.0
- **📄 License:** MIT
- **📂 Repository:** [https://github.com/nik-r08/Dream-printer](https://github.com/nik-r08/Dream-printer)

## Features

• Text-to-STL generation using natural language prompts
• Interactive web-based UI for 3D model creation
• Support for various 3D printing file formats
• Real-time preview of generated models
• Customizable model parameters and settings
• Local LLM integration for enhanced prompt processing
• Docker containerization for easy deployment
• Python-based backend with Streamlit frontend

## Usage

### Prerequisites
Ensure you have the following installed:
- Docker Desktop
- Python 3.8+
- Git

### Local Setup Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/dream-printer/dream-printer.git
   cd dream-printer
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your local LLM API configuration
   ```

3. Run with Docker:
   ```bash
   docker-compose up -d
   ```

4. Or run locally:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

### Basic Usage
1. Access the web interface at `http://localhost:8501`
2. Enter your text prompt in the input field
3. Adjust model parameters as needed
4. Click "Generate STL" to create your 3D model
5. Download the generated .stl file

### Extending and Customization
- Modify `models/` directory to add new 3D generation models
- Customize the UI by editing Streamlit components in `ui/`
- Add new prompt processing features in `processors/`

## Requirements

• Docker (for containerized deployment)
• Python 3.8 or higher
• Streamlit (for web interface)
• Local LLM API (for natural language processing)
• At least 4GB RAM recommended
• Compatible with Windows, macOS, and Linux

