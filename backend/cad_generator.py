import subprocess
import os
import json
import re

def extract_json(text):
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        return match.group(0)
    else:
        raise ValueError("No JSON found in LLM output!")

def json_spec_to_stl(json_spec, filename="backend/output.stl"):
    print("RAW LLM OUTPUT:", json_spec)
    
    # Step 1: Clean and save valid JSON only
    clean_json = extract_json(json_spec)
    with open("backend/spec_input.json", "w", encoding="utf-8") as f:
        # Dump as file for Docker script to read; ensures it's valid JSON
        json.dump(json.loads(clean_json), f, ensure_ascii=False)
    
    # Step 2: Call Docker to generate the STL
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{os.path.abspath('backend')}:/scripts",
        "cadquery/cadquery",
        "python", "/scripts/docker_cq_generator.py"
    ]
    subprocess.run(docker_cmd)
    # The STL will be created as 'backend/output.stl'
