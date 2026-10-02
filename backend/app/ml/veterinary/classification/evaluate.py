from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def evaluate(y_true, y_pred) -> dict:
    return {"accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "precision_macro": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
            "recall_macro": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
            "f1_macro": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4)}
