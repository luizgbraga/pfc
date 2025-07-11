import json
import re


def clean_json(json_str: str) -> str:
    """
    Extracts JSON content from markdown code blocks (```json ... ```).

    Args:
        json_str (str): The string containing JSON markdown.

    Returns:
        str: The parsed JSON as a dictionary.
    """
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, json_str, flags=re.DOTALL)

    if match:
        json_content = match.group(1).strip()
    else:
        json_content = json_str.strip()

    try:
        cleaned_dict = json.loads(json_content)
        return cleaned_dict
    except json.JSONDecodeError as e:
        print(f"Invalid JSON content: {json_content}")
        raise e
