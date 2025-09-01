import requests

def prompt_to_json_spec(user_prompt):
    system_prompt = (
        "You are a 3D print designer. Given a creative request for an object, output a JSON spec with "
        "object_type, primary_dimensions_mm, style_tags, required_features, constraints."
    )
    payload = {
        "model": "gpt-oss:20b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    print("Sending request to:", "http://localhost:11434/v1/chat/completions")
    print("Payload:", payload)
    response = requests.post(
        "http://localhost:11434/v1/chat/completions",
        json=payload
    )
    print("LLM RAW RESPONSE:", response.text)  
    data = response.json()
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    else:
        raise ValueError(f"LLM API error: {data}")
