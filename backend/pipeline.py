import json
from backend.cad_generator import json_spec_to_stl

def dream_printer_pipeline(spec_dict):
    # Ensure robust encoding to JSON
    json_spec = json.dumps(spec_dict, ensure_ascii=False)
    json_spec_to_stl(json_spec)
