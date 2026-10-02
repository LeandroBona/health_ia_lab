import numpy as np


def cluster_summary(bundle: dict) -> list[dict]:
    labels = bundle["clusters"]
    names = bundle["vectorizer"].get_feature_names_out()
    matrix = bundle["matrix"]
    results = []
    for group in range(bundle["kmeans"].n_clusters):
        indices = np.flatnonzero(labels == group)
        center = bundle["kmeans"].cluster_centers_[group]
        top = [str(names[index]) for index in np.argsort(center)[::-1][:8]]
        distances = np.linalg.norm(matrix[indices].toarray() - center, axis=1)
        examples = [bundle["records"][int(indices[pos])]["record_id"] for pos in np.argsort(distances)[:3]]
        results.append({"cluster_id": group + 1, "label": f"Grupo {group + 1}", "quantidade": int(len(indices)),
                        "top_terms": top, "sample_records": examples})
    return results


def approximate_group(text: str, bundle: dict) -> dict:
    vector = bundle["vectorizer"].transform([text])
    group = int(bundle["kmeans"].predict(vector)[0]) + 1
    return {"cluster_id": group, "label": f"Grupo {group}"}
