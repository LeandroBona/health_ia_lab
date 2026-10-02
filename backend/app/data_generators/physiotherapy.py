"""Deterministic artificial relationships, without a trained model."""
import argparse
import random
from pathlib import Path

import pandas as pd

from app.schemas.physiotherapy import INJURIES, REQUIRED_COLUMNS, SEXES, PatientData

SEED = 42


def clamp(value: float, lower: int, upper: int) -> int:
    return max(lower, min(upper, round(value)))


def generate_patients(size: int = 1000, seed: int = SEED) -> pd.DataFrame:
    if not 1 <= size <= 10000:
        raise ValueError("O tamanho deve estar entre 1 e 10000 pacientes.")
    rng = random.Random(seed)
    rows = []
    # Os padrões utilizados neste dataset foram artificialmente construídos para fins educacionais e não representam conhecimento clínico validado.
    for number in range(1, size + 1):
        adherence = clamp(rng.betavariate(2.4, 1.3) * 100, 0, 100)
        planned = rng.randint(5, 30)
        absences = clamp(planned * (1 - adherence / 100) * rng.uniform(.2, .8), 0, planned)
        completed = clamp((planned - absences) * rng.uniform(.25, 1), 0, planned - absences)
        engagement = .55 * adherence / 100 + .45 * completed / planned - .3 * absences / planned
        progress = max(-.1, min(1, engagement + rng.gauss(0, .12)))
        pain = rng.randint(3, 10)
        mobility = rng.randint(15, 70)
        functional = clamp(mobility * .6 + (10 - pain) * 4 + rng.gauss(0, 8), 0, 100)
        current_pain = clamp(pain - progress * 7 + rng.gauss(0, .8), 0, 10)
        current_mobility = clamp(mobility + progress * (100 - mobility) + rng.gauss(0, 5), 0, 100)
        current_functional = clamp(functional + progress * (100 - functional) + rng.gauss(0, 5), 0, 100)
        improvement = ((pain - current_pain) / 10 + (current_mobility - mobility) / 100 + (current_functional - functional) / 100) / 3
        abandonment_weight = .02 + (1 - adherence / 100) ** 3 * (1 - completed / planned) * 5 + absences / planned * .3
        adequate_weight = .05 + max(0, engagement + improvement) ** 2 * 2
        slow_weight = .15 + (1 - max(0, progress)) ** 2
        result = rng.choices(["recuperacao_adequada", "recuperacao_lenta", "abandono"], weights=[adequate_weight, slow_weight, abandonment_weight])[0]
        row = PatientData(
            patient_id=f"PAC-{number:04d}", idade=rng.randint(18, 85), sexo=rng.choice(SEXES),
            tipo_lesao=rng.choice(INJURIES), tempo_lesao_dias=rng.randint(1, 730),
            dor_inicial=pain, dor_atual=current_pain, mobilidade_inicial=mobility,
            mobilidade_atual=current_mobility, forca_muscular=clamp(1 + current_mobility / 25 + rng.gauss(0, .5), 1, 5),
            sessoes_previstas=planned, sessoes_realizadas=completed, faltas=absences,
            adesao_exercicios=adherence, comorbidades=rng.randint(0, 5),
            indice_funcional_inicial=functional, indice_funcional_atual=current_functional, resultado=result,
        )
        rows.append(row.model_dump())
    return pd.DataFrame(rows, columns=REQUIRED_COLUMNS)


def export_dataset(frame: pd.DataFrame, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    frame.to_csv(directory / "pacientes_fisioterapia.csv", index=False, encoding="utf-8-sig")
    frame.to_excel(directory / "pacientes_fisioterapia.xlsx", index=False, engine="openpyxl")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerar o dataset padrão e sincronizar o SQLite.")
    parser.add_argument("--size", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--confirm", action="store_true", help="Confirmar substituição do dataset padrão existente.")
    args = parser.parse_args()
    from app.database.session import SessionLocal, engine
    from app.models.base import Base
    from app.services.physiotherapy_dataset import DEFAULT_ID, initialize_dataset, regenerate_dataset
    from app.models.physiotherapy import PhysiotherapyDataset
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        if session.get(PhysiotherapyDataset, DEFAULT_ID) is not None and not args.confirm:
            parser.error("Dataset existente. Use --confirm para substituí-lo; importações serão preservadas.")
        print(regenerate_dataset(session, args.size, args.seed))
