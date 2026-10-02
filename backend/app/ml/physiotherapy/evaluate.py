from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support

from app.ml.physiotherapy.feature_config import CLASSES


def evaluate_model(pipeline, features, targets) -> dict:
    predicted = pipeline.predict(features)
    precision, recall, f1, _ = precision_recall_fscore_support(targets, predicted, labels=CLASSES, average="macro", zero_division=0)
    report = classification_report(targets, predicted, labels=CLASSES, output_dict=True, zero_division=0)
    return {
        "accuracy": float(accuracy_score(targets, predicted)),
        "precision_macro": float(precision), "recall_macro": float(recall), "f1_macro": float(f1),
        "classes": CLASSES,
        "confusion_matrix": confusion_matrix(targets, predicted, labels=CLASSES).tolist(),
        "per_class": {label: {"precision": report[label]["precision"], "recall": report[label]["recall"], "f1": report[label]["f1-score"], "support": int(report[label]["support"])} for label in CLASSES},
        "classification_report": report,
    }
