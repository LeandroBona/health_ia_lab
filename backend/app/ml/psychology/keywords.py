import numpy as np


def extract_keywords(text: str, vectorizer, limit: int = 8) -> list[dict]:
    vector = vectorizer.transform([text]).toarray()[0]
    names = vectorizer.get_feature_names_out()
    ranked = np.argsort(vector)[::-1]
    return [{"term": str(names[index]), "score": round(float(vector[index]), 4)}
            for index in ranked if vector[index] > 0][:limit]
