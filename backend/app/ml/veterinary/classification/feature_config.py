from app.data_generators.veterinary import ANIMAL_COLUMNS, CLASSES

FEATURES = [column for column in ANIMAL_COLUMNS if column not in {"animal_id", "evolucao"}]
CATEGORICAL = ["especie", "sexo", "procedimento"]
NUMERIC = [column for column in FEATURES if column not in CATEGORICAL]
TARGET = "evolucao"
assert "animal_id" not in FEATURES and TARGET not in FEATURES
