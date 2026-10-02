from app.ml.nursing.preprocessing import build_pipeline
from app.schemas.nursing import FEATURES


def fit_model(frame, seed: int = 42, contamination: float = .07):
    """The synthetic `estado` label is intentionally excluded from fit()."""
    pipeline = build_pipeline(seed, contamination)
    pipeline.fit(frame[FEATURES])
    return pipeline
