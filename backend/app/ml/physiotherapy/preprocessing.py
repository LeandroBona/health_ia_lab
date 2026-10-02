from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.physiotherapy.feature_config import CATEGORICAL_FEATURES, NUMERIC_FEATURES


def build_preprocessor(scale_numeric: bool = False) -> ColumnTransformer:
    numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    categories = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("numeric", Pipeline(numeric_steps), NUMERIC_FEATURES),
        ("categorical", categories, CATEGORICAL_FEATURES),
    ], remainder="drop")
