import hashlib
import json

import pandas as pd


def record_fingerprint(record: dict) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def dataset_fingerprint(frame: pd.DataFrame) -> str:
    records = frame.sort_values("patient_id").to_dict(orient="records")
    return record_fingerprint({"records": records})
