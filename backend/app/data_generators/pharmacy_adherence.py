"""Deterministic, wholly fictional medication-adherence records."""

from pathlib import Path

import numpy as np
import pandas as pd

from app.schemas.pharmacy import ADHERENCE_COLUMNS


def generate_adherence(size: int = 1000, seed: int = 42) -> pd.DataFrame:
    if not 1 <= size <= 99999:
        raise ValueError("size deve estar entre 1 e 99999")
    rng = np.random.default_rng(seed)
    rows = []
    # As relações presentes neste dataset foram artificialmente definidas para fins educacionais e não representam evidência clínica ou farmacológica.
    for number in range(1, size + 1):
        age = int(rng.integers(18, 86))
        medicines = int(rng.integers(1, 9))
        doses = int(rng.integers(1, 6))
        complexity = int(np.clip(round((medicines + doses) / 3 + rng.normal(0, 1)), 1, 5))
        reminders = bool(rng.random() < 0.57)
        organizer = bool(rng.random() < 0.49)
        followups = int(rng.integers(0, 11))
        forgets = int(np.clip(rng.poisson(4 + complexity * 0.8 - 1.2 * reminders - 0.9 * organizer), 0, 30))
        delayed = int(np.clip(rng.poisson(1.1 + complexity * 0.25 - 0.25 * reminders), 0, 12))
        percentage = float(np.clip(93 - forgets * 2.8 - delayed * 5.5 - complexity * 2.3 + 6 * reminders + 5 * organizer + followups * 0.8 + rng.normal(0, 11), 0, 100))
        # Statistical noise is added before categorization; the percentage is never a model feature.
        category_score = percentage + rng.normal(0, 5)
        category = "alta" if category_score >= 80 else "moderada" if category_score >= 50 else "baixa"
        rows.append({
            "patient_id": f"FAR-{number:04d}", "idade": age,
            "quantidade_medicamentos": medicines, "doses_diarias": doses,
            "tempo_tratamento_dias": int(rng.integers(15, 1461)),
            "esquecimentos_30_dias": forgets, "retiradas_atrasadas": delayed,
            "consultas_acompanhamento": followups, "usa_organizador": organizer,
            "recebe_lembretes": reminders, "complexidade_rotina": complexity,
            "adesao_percentual": round(percentage, 2), "categoria_adesao": category,
        })
    return pd.DataFrame(rows, columns=ADHERENCE_COLUMNS)


def export_adherence(frame: pd.DataFrame, directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    csv_path = directory / "adesao_farmacia.csv"
    xlsx_path = directory / "adesao_farmacia.xlsx"
    frame.to_csv(csv_path, index=False)
    frame.to_excel(xlsx_path, index=False)
    return csv_path, xlsx_path
