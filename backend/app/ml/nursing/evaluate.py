from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score


def evaluate_labels(actual: list[str], detected: list[str]) -> dict:
    y_true = [value == "alterado" for value in actual]
    y_pred = [value == "anomalia" for value in detected]
    matrix = confusion_matrix(y_true, y_pred, labels=[False, True]).tolist()
    return {
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "confusion_matrix": matrix,
        "labels": ["padrao", "anomalia"],
        "artificial_anomalies": sum(y_true),
        "detected_anomalies": sum(y_pred),
    }
