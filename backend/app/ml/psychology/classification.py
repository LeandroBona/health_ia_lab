from datetime import datetime, timezone

import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.data_generators.psychology import THEMES
from .preprocessing import make_vectorizer


def train_classifier(frame: pd.DataFrame, version: str = "1.0", seed: int = 42) -> dict:
    if len(frame) < 60 or set(frame.tema_principal) != set(THEMES) or frame.tema_principal.value_counts().min() < 2:
        raise ValueError("São necessários ao menos 60 relatos e duas amostras de cada tema.")
    x_train, x_test, y_train, y_test = train_test_split(frame.texto, frame.tema_principal,
                                                         test_size=.2, stratify=frame.tema_principal, random_state=42)
    pipeline = Pipeline([("tfidf", make_vectorizer()), ("classifier", LogisticRegression(max_iter=1500, random_state=seed))])
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    metrics = {"accuracy": round(float(accuracy_score(y_test, predictions)), 4),
               "precision_macro": round(float(precision_score(y_test, predictions, average="macro", zero_division=0)), 4),
               "recall_macro": round(float(recall_score(y_test, predictions, average="macro", zero_division=0)), 4),
               "f1_macro": round(float(f1_score(y_test, predictions, average="macro", zero_division=0)), 4)}
    metadata = {"version": version, "algorithm": "TF-IDF + LogisticRegression", "date": datetime.now(timezone.utc).isoformat(),
                "dataset": "relatos_psicologia", "records": len(frame), "seed": seed, "train_records": len(x_train), "test_records": len(x_test),
                "input": ["texto"], "target": "tema_principal", "metrics": metrics, "labels": THEMES,
                "confusion_matrix": confusion_matrix(y_test, predictions, labels=THEMES).tolist(), "sklearn_version": sklearn.__version__,
                "evaluation_note": "Divisão estratificada 80/20 em relatos sintéticos. Temas linguísticos, sem interpretação clínica."}
    return {"pipeline": pipeline, "metadata": metadata}


def classify_text(text: str, bundle: dict) -> dict:
    pipeline = bundle["pipeline"]
    probabilities = {str(label): round(float(score), 6) for label, score in zip(pipeline.classes_, pipeline.predict_proba([text])[0])}
    ordered = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
    return {"prediction": str(pipeline.predict([text])[0]), "probabilities": probabilities,
            "top_themes": [{"theme": label, "probability": score} for label, score in ordered[:3]]}
