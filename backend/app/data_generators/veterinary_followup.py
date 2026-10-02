from pathlib import Path

import numpy as np
import pandas as pd

FOLLOWUP_COLUMNS = ["followup_id", "animal_id", "timestamp", "temperatura", "frequencia_cardiaca", "atividade_percentual", "alimentacao_percentual", "hidratacao_percentual", "alteracoes_reportadas"]


def generate_followups(animals: pd.DataFrame, seed: int = 42, fraction: float = .3) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 1)
    # Daily observations fit within the recorded number of follow-up days.
    eligible = animals[animals["dias_pos_procedimento"] >= 10]
    selected = eligible.sample(n=min(len(eligible), round(len(animals) * fraction)), random_state=seed)
    rows = []
    for animal in selected.to_dict("records"):
        count = int(rng.integers(10, min(20, int(animal["dias_pos_procedimento"])) + 1))
        shift = rng.normal(0, 5)
        for i in range(count):
            unusual = rng.random() < .07
            offset = -float(rng.uniform(23, 48)) if unusual else 0
            progress = (i / max(count - 1, 1) - .5) * 16
            rows.append([f"FUP-{len(rows)+1:06d}", animal["animal_id"],
                         (pd.Timestamp("2025-01-01") + pd.Timedelta(days=i)).isoformat(),
                         round(float(np.clip(animal["temperatura"] + rng.normal(0, .3) + (1.5 if unusual else 0), 35, 41)), 1),
                         round(float(np.clip(animal["frequencia_cardiaca"] + rng.normal(0, 7) + (24 if unusual else 0), 25, 230)), 1),
                         round(float(np.clip(animal["atividade_percentual"] + shift + progress + rng.normal(0, 8) + offset, 0, 100)), 1),
                         round(float(np.clip(animal["alimentacao_percentual"] + progress + rng.normal(0, 8) + offset, 0, 100)), 1),
                         round(float(np.clip(animal["hidratacao_percentual"] + rng.normal(0, 8) + offset, 0, 100)), 1),
                         int(np.clip(animal["alteracoes_reportadas"] + rng.integers(-1, 2) + (3 if unusual else 0), 0, 10))])
    return pd.DataFrame(rows, columns=FOLLOWUP_COLUMNS)


def export_followups(frame: pd.DataFrame, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    frame.to_csv(directory / "acompanhamento_veterinario.csv", index=False, encoding="utf-8-sig")
    frame.to_excel(directory / "acompanhamento_veterinario.xlsx", index=False)
