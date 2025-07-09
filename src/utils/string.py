import json


def clean_json(json_str: str) -> str:
    """
    Cleans a JSON string by removing code block markers and leading/trailing whitespace.

    Args:
        json_str (str): The JSON string to clean.

    Returns:
        str: The cleaned JSON string.
    """
    cleaned = json_str.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    cleaned_dict = json.loads(cleaned)

    return cleaned_dict
