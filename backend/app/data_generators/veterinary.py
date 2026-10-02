"""Entirely fictional veterinary follow-up records."""
from pathlib import Path

import numpy as np
import pandas as pd

SPECIES = ["Cão", "Gato", "Equino", "Bovino", "Outros"]
PROCEDURES = ["Cirurgia ortopédica", "Procedimento abdominal", "Procedimento dermatológico", "Procedimento odontológico", "Tratamento de lesão", "Pós-operatório geral", "Outros"]
CLASSES = ["evolucao_esperada", "acompanhamento_adicional", "dados_insuficientes"]
ANIMAL_COLUMNS = ["animal_id", "especie", "idade_anos", "peso_kg", "sexo", "procedimento", "dias_pos_procedimento", "temperatura", "frequencia_cardiaca", "atividade_percentual", "alimentacao_percentual", "hidratacao_percentual", "medicacao_administrada_percentual", "retornos_realizados", "retornos_previstos", "alteracoes_reportadas", "indice_recuperacao", "evolucao"]


def generate_animals(size: int = 1000, seed: int = 42) -> pd.DataFrame:
    if size < 3:
        raise ValueError("O dataset precisa de ao menos três animais.")
    rng = np.random.default_rng(seed)
    rows = []
    weights = [0.49, 0.37, 0.06, 0.04, 0.04]
    for i in range(1, size + 1):
        species = str(rng.choice(SPECIES, p=weights))
        age = round(float(rng.uniform(.2, 20 if species in ("Cão", "Gato", "Outros") else 25)), 1)
        ranges = {"Cão": (2, 65), "Gato": (2, 10), "Equino": (180, 700), "Bovino": (80, 850), "Outros": (.5, 100)}
        weight = round(float(rng.uniform(*ranges[species])), 1)
        days = int(rng.integers(1, 61))
        quality = float(rng.beta(4, 2))
        sparse = bool(rng.random() < .15)
        if sparse:
            days = min(days, int(rng.integers(1, 5)))
        activity = float(np.clip(30 + 60 * quality + .3 * days + rng.normal(0, 15), 0, 100))
        food = float(np.clip(32 + 68 * quality + rng.normal(0, 16), 0, 100))
        water = float(np.clip(38 + 58 * quality + rng.normal(0, 14), 0, 100))
        medicine = float(np.clip(30 + 70 * quality + rng.normal(0, 20), 0, 100))
        planned = int(rng.integers(1, 5))
        completed = int(rng.binomial(planned, float(np.clip(.2 + .75 * quality, 0, 1))))
        changes = int(np.clip(rng.poisson(3.8 - 3 * quality), 0, 10))
        index = float(np.clip(20 + 75 * quality + rng.normal(0, 17), 0, 100))
        temperature = float(np.clip(38 + rng.normal(0, .7), 35, 41))
        heart = float(np.clip({"Cão": 95, "Gato": 145, "Equino": 45, "Bovino": 65, "Outros": 100}[species] + rng.normal(0, 18), 25, 230))
        # Essas relações foram artificialmente construídas para fins educacionais e não representam evidência veterinária validada.
        score = (.18 * activity + .19 * food + .12 * water + .12 * medicine + .21 * index
                 + 15 * completed / planned - 3.5 * changes + rng.normal(0, 12))
        insufficient = sparse and (rng.random() < .74) or (days < 3 and completed == 0 and rng.random() < .55)
        evolution = "dados_insuficientes" if insufficient else "evolucao_esperada" if score > 70 else "acompanhamento_adicional"
        rows.append([f"VET-{i:04d}", species, age, weight, str(rng.choice(["Fêmea", "Macho"])), str(rng.choice(PROCEDURES)), days,
                     round(temperature, 1), round(heart, 1), round(activity, 1), round(food, 1), round(water, 1), round(medicine, 1),
                     completed, planned, changes, round(index, 1), evolution])
    return pd.DataFrame(rows, columns=ANIMAL_COLUMNS)


def export_animals(frame: pd.DataFrame, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    frame.to_csv(directory / "animais_veterinaria.csv", index=False, encoding="utf-8-sig")
    frame.to_excel(directory / "animais_veterinaria.xlsx", index=False)
