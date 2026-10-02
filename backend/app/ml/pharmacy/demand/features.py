"""Lag features use past demand only; never same-period or future target values."""

import pandas as pd

from app.data_generators.pharmacy_demand import seasonality_for_month

FEATURES = ["medication_id", "month", "year", "lag_1", "lag_2", "lag_3", "rolling_mean_3", "rolling_mean_6", "seasonality_index", "trend_index"]


def add_temporal_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.sort_values(["medication_id", "period"]).copy()
    grouped = result.groupby("medication_id", sort=False)["demand"]
    for lag in (1, 2, 3):
        result[f"lag_{lag}"] = grouped.shift(lag)
    result["rolling_mean_3"] = grouped.transform(lambda values: values.shift(1).rolling(3).mean())
    result["rolling_mean_6"] = grouped.transform(lambda values: values.shift(1).rolling(6).mean())
    return result.dropna(subset=FEATURES[1:]).reset_index(drop=True)


def next_period_features(history: pd.DataFrame) -> tuple[dict, str]:
    ordered = history.sort_values("period")
    if len(ordered) < 6:
        raise ValueError("São necessários pelo menos seis períodos anteriores.")
    recent = ordered.tail(6)
    periods = pd.PeriodIndex(recent["period"], freq="M")
    if any(periods[index] + 1 != periods[index + 1] for index in range(5)):
        raise ValueError("Os seis períodos mais recentes precisam ser consecutivos.")
    next_period = periods[-1] + 1
    values = recent["demand"].astype(float).tolist()
    return {
        "medication_id": str(recent.iloc[-1]["medication_id"]), "month": next_period.month, "year": next_period.year,
        "lag_1": values[-1], "lag_2": values[-2], "lag_3": values[-3],
        "rolling_mean_3": sum(values[-3:]) / 3, "rolling_mean_6": sum(values) / 6,
        "seasonality_index": seasonality_for_month(next_period.month),
        "trend_index": float(recent.iloc[-1]["trend_index"]) + 1,
    }, str(next_period)
