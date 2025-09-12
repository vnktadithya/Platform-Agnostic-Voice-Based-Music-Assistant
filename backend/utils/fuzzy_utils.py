from thefuzz import fuzz

def fuzzy_db_match(query_name, objects, attr="name", threshold=80):
    """
    Finds the best fuzzy match in a list of SQLAlchemy objects.
    
    Returns (best_object, score) or (None, 0).
    """
    best, score = None, 0
    for obj in objects:
        value = getattr(obj, attr, "").lower()
        if not value:
            continue
        match_score = fuzz.token_set_ratio(query_name.lower(), value)
        if match_score > score and match_score >= threshold:
            best = obj
            score = match_score
    return best, score

def fuzzy_search_cache(query, cache_objs, threshold=75):
    best, score = None, 0
    for obj in cache_objs:
        candidate = (obj.normalized_query or "").lower()
        sc = fuzz.token_set_ratio(query.lower(), candidate)
        if sc > score and sc >= threshold:
            best, score = obj, sc
    return best, score
