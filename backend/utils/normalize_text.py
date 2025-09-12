import re
import unicodedata

def normalize_query(text: str) -> str:
    """
    Normalizes input text for search/fuzzy matching by:
    - Unicode normalization (NFKD)
    - Removing non-word characters (punctuation)
    - Lowercasing
    - Collapsing multiple spaces
    - Stripping leading/trailing whitespace
    """
    if not isinstance(text, str):
        return ""

    # Normalize unicode characters (e.g., é -> e + ')
    text = unicodedata.normalize("NFKD", text)

    # Replace non-word characters (anything except letters, digits) with space
    text = re.sub(r"\W+", " ", text)

    # Lowercase the text
    text = text.lower()

    # Collapse multiple spaces to single space
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing spaces
    return text.strip()