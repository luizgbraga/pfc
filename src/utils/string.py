import json
import re


def clean_json(json_str: str) -> str:
    """
    Extracts JSON content from various formats in a string, including:
    - Markdown code blocks (```json ... ``` or ``` ... ```)
    - JSON embedded in text
    - Raw JSON

    Args:
        json_str (str): The string containing JSON in any format.

    Returns:
        dict: The parsed JSON as a dictionary.
    """
    pattern_json = r"```json\s*(.*?)\s*```"
    match = re.search(pattern_json, json_str, flags=re.DOTALL)
    if match:
        json_content = match.group(1).strip()
    else:
        pattern_code = r"```\s*(.*?)\s*```"
        match = re.search(pattern_code, json_str, flags=re.DOTALL)
        if match:
            json_content = match.group(1).strip()
        else:
            pattern_braces = r"({[\s\S]*?})"
            pattern_brackets = r"(\[[\s\S]*?\])"
            match_obj = re.search(pattern_braces, json_str)
            match_arr = re.search(pattern_brackets, json_str)
            if match_obj and (not match_arr or match_obj.start() < match_arr.start()):
                json_content = match_obj.group(1).strip()
            elif match_arr:
                json_content = match_arr.group(1).strip()
            else:
                json_content = json_str.strip()

    try:
        return json.loads(json_content)
    except json.JSONDecodeError:
        json_content_fixed = re.sub(r",\s*([}\]])", r"\1", json_content)
        try:
            return json.loads(json_content_fixed)
        except Exception as e:
            print(f"Invalid JSON content: {json_content}")
            raise e
