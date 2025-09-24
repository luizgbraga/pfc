import json
import re


def clean_json(json_str: str) -> dict:
    """
    Extracts and parses the first valid JSON object from a messy string.
    Handles random prefixes, markdown blocks, and embedded JSON structures.

    Args:
        json_str (str): The raw input string potentially containing JSON.

    Returns:
        dict: The parsed JSON object.
    """
    # Normalize newlines and whitespace
    json_str = json_str.replace("\r\n", "\n").replace("\r", "\n")

    # Remove markdown fences like json or
    json_str = re.sub(r"(?:json)?", "", json_str, flags=re.IGNORECASE)
    json_str = json_str.replace("", "")

    # Match all possible brace-based JSON candidates
    brace_stack = []
    json_candidates = []
    start = None

    for i, char in enumerate(json_str):
        if char == "{":
            if not brace_stack:
                start = i
            brace_stack.append(char)
        elif char == "}":
            if brace_stack:
                brace_stack.pop()
                if not brace_stack and start is not None:
                    candidate = json_str[start : i + 1]
                    json_candidates.append(candidate)

    # Try parsing candidates until one works
    for candidate in json_candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    print("The JSON string was: ", json_str)
    raise ValueError("No valid JSON found. Even in the darkest corners.")
