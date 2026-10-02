from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["temperatura", "frequencia_cardiaca", "atividade_percentual", "alimentacao_percentual", "hidratacao_percentual", "alteracoes_reportadas"]
assert not {"animal_id", "followup_id", "timestamp"}.intersection(FEATURES)


def preprocessor():
    return Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
