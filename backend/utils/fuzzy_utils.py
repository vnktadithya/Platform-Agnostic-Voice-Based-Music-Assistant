from thefuzz import fuzz
from backend.utils.normalize_text import normalize_query

def fuzzy_db_match(query_name, objects, attr="name", threshold=80):
    """
    Finds the best fuzzy match in a list of SQLAlchemy objects.
    Returns (best_object, score) or (None, 0).
    """
    if not query_name:
        return None, 0

    norm_query = normalize_query(query_name)

    best, score = None, 0
    for obj in objects:
        raw_value = getattr(obj, attr, "")
        if not raw_value:
            continue

        norm_value = normalize_query(raw_value)
        match_score = fuzz.token_set_ratio(norm_query, norm_value)

        if match_score > score and match_score >= threshold:
            best = obj
            score = match_score

    return best, score


def fuzzy_search_cache(query, cache_objs, threshold=75):
    if not query:
        return None, 0

    norm_query = normalize_query(query)

    best, score = None, 0
    for obj in cache_objs:
        candidate = obj.normalized_query or ""
        norm_candidate = normalize_query(candidate)

        sc = fuzz.token_set_ratio(norm_query, norm_candidate)
        if sc > score and sc >= threshold:
            best, score = obj, sc

    return best, score
