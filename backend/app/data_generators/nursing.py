"""Reproducible, wholly synthetic monitoring measurements for teaching."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from app.schemas.nursing import REQUIRED_COLUMNS


def generate_measurements(size: int = 500, seed: int = 42) -> pd.DataFrame:
    if not 1 <= size <= 5000:
        raise ValueError("A quantidade de pacientes deve estar entre 1 e 5000.")
    rng = np.random.default_rng(seed)
    records: list[dict] = []
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    for patient_index in range(1, size + 1):
        patient_id = f"ENF-{patient_index:04d}"
        age = int(rng.integers(18, 91))
        baseline = np.array([
            rng.uniform(65, 90), rng.uniform(14, 21), rng.uniform(36.2, 37.0),
            rng.uniform(105, 135), rng.uniform(65, 90), rng.uniform(94, 99),
            rng.uniform(0, 5),
        ])
        count = int(rng.integers(10, 31))
        for measurement_index in range(count):
            # Os padrões utilizados neste dataset foram artificialmente construídos para fins educacionais e não representam conhecimento clínico validado.
            values = baseline + rng.normal(0, [4, 1.5, .17, 6, 4, 1, 1.2])
            altered = bool(rng.random() < .075)
            if altered:
                variant = int(rng.integers(0, 5))
                if variant == 0:
                    values[0] += rng.choice([-1, 1]) * rng.uniform(23, 43)
                elif variant == 1:
                    values[2] += rng.choice([-1, 1]) * rng.uniform(1.3, 2.3)
                elif variant == 2:
                    values[5] -= rng.uniform(8, 15)
                elif variant == 3:
                    values[3] += rng.choice([-1, 1]) * rng.uniform(27, 45)
                    values[4] += rng.choice([-1, 1]) * rng.uniform(14, 22)
                else:
                    values[[0, 1, 2, 5]] += np.array([17, 6, .8, -6])
            values = np.clip(values, [40, 8, 34.5, 75, 40, 75, 0], [150, 40, 41, 190, 125, 100, 10])
            values[3] = max(values[3], values[4] + 5)
            timestamp = start + timedelta(days=patient_index % 90, hours=measurement_index * 12)
            records.append({
                "measurement_id": f"MED-{len(records) + 1:06d}", "patient_id": patient_id,
                "timestamp": timestamp.isoformat(), "idade": age,
                "frequencia_cardiaca": round(float(values[0]), 1),
                "frequencia_respiratoria": round(float(values[1]), 1),
                "temperatura": round(float(values[2]), 1),
                "pressao_sistolica": round(float(values[3]), 1),
                "pressao_diastolica": round(float(values[4]), 1),
                "saturacao": round(float(values[5]), 1),
                "nivel_dor": round(float(values[6]), 1),
                "estado": "alterado" if altered else "padrao",
            })
    return pd.DataFrame(records, columns=REQUIRED_COLUMNS)


def export_dataset(frame: pd.DataFrame, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    frame.to_csv(directory / "monitoramento_enfermagem.csv", index=False, encoding="utf-8-sig")
    frame.to_excel(directory / "monitoramento_enfermagem.xlsx", index=False)
