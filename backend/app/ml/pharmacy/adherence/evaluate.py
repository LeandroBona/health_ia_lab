from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score

from app.ml.pharmacy.adherence.feature_config import CLASSES


def evaluate_model(pipeline, x_test, y_test) -> dict:
    predictions = pipeline.predict(x_test)
    report = classification_report(y_test, predictions, labels=CLASSES, output_dict=True, zero_division=0)
    return {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision_macro": round(float(precision_score(y_test, predictions, labels=CLASSES, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_test, predictions, labels=CLASSES, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_test, predictions, labels=CLASSES, average="macro", zero_division=0)), 4),
        "classes": CLASSES, "confusion_matrix": confusion_matrix(y_test, predictions, labels=CLASSES).tolist(),
        "per_class": {label: {metric: round(float(report[label][metric]), 4) for metric in ("precision", "recall", "f1-score", "support")} for label in CLASSES},
    }
