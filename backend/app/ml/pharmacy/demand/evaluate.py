import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def evaluate_model(pipeline, x_test, y_test) -> tuple[dict, np.ndarray]:
    predictions = np.maximum(0, pipeline.predict(x_test))
    return {
        "mae": round(float(mean_absolute_error(y_test, predictions)), 3),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, predictions))), 3),
        "r2": round(float(r2_score(y_test, predictions)), 4),
    }, predictions
