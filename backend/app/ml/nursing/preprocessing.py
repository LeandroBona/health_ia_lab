from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_pipeline(seed: int = 42, contamination: float = .07) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", IsolationForest(contamination=contamination, random_state=seed, n_estimators=150, n_jobs=-1)),
    ])
