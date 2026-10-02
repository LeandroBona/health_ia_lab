"""Deterministic monthly inventory and consumption series for fictional products."""

from pathlib import Path

import numpy as np
import pandas as pd

from app.schemas.pharmacy import DEMAND_COLUMNS


def seasonality_for_month(month: int) -> float:
    return round(1 + 0.16 * float(np.sin(2 * np.pi * (month - 1) / 12)), 4)


def generate_demand(medications: int = 20, months: int = 36, seed: int = 42) -> pd.DataFrame:
    if not 1 <= medications <= 999 or not 12 <= months <= 120:
        raise ValueError("medications deve estar entre 1 e 999 e months entre 12 e 120")
    rng = np.random.default_rng(seed)
    periods = pd.period_range("2023-01", periods=months, freq="M")
    rows = []
    for number in range(1, medications + 1):
        baseline = float(rng.uniform(240, 850))
        slope = float(rng.uniform(-2, 5))
        stock = int(round(baseline * 1.2))
        for index, period in enumerate(periods):
            seasonality = seasonality_for_month(period.month)
            promotion = bool(rng.random() < 0.08)
            demand = max(1, int(round(baseline * seasonality + index * slope + (baseline * 0.23 if promotion else 0) + rng.normal(0, baseline * 0.055))))
            target_stock = int(round(baseline * 0.8))
            received = max(0, demand + target_stock - stock)
            used = demand
            final = stock + received - used
            rows.append({
                "medication_id": f"MED-{number:03d}", "month": period.month,
                "year": period.year, "period": str(period), "stock_initial": stock,
                "quantity_received": received, "quantity_used": used,
                "stock_final": final, "seasonality_index": seasonality,
                "trend_index": float(index), "promotion_event": promotion,
                "demand": demand,
            })
            stock = final
    return pd.DataFrame(rows, columns=DEMAND_COLUMNS)


def export_demand(frame: pd.DataFrame, directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    csv_path = directory / "demanda_farmacia.csv"
    xlsx_path = directory / "demanda_farmacia.xlsx"
    frame.to_csv(csv_path, index=False)
    frame.to_excel(xlsx_path, index=False)
    return csv_path, xlsx_path
