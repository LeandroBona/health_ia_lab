from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.pharmacy.adherence.feature_config import FEATURES


def build_preprocessor(scale: bool = False) -> ColumnTransformer:
    categorical = ["usa_organizador", "recebe_lembretes"]
    numeric = [feature for feature in FEATURES if feature not in categorical]
    numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        numeric_steps.append(("scaler", StandardScaler()))
    return ColumnTransformer([
        ("numeric", Pipeline(numeric_steps), numeric),
        ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical),
    ])
