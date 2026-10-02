from sklearn.metrics.pairwise import cosine_similarity

from .preprocessing import normalize_text


def find_similar(text: str, bundle: dict, limit: int = 5) -> list[dict]:
    query = bundle["vectorizer"].transform([text])
    scores = cosine_similarity(query, bundle["matrix"])[0]
    normalized = normalize_text(text)
    rows = bundle["records"]
    indices = sorted(range(len(rows)), key=lambda index: float(scores[index]), reverse=True)
    return [{"record_id": rows[index]["record_id"], "similarity": round(float(scores[index]), 4),
             "theme": rows[index]["tema_principal"], "text": rows[index]["texto"]}
            for index in indices if scores[index] > 0 and normalize_text(rows[index]["texto"]) != normalized][:limit]
