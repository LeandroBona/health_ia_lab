import io
import math
import zipfile
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from app.schemas.physiotherapy import CATEGORICAL_COLUMNS, REQUIRED_COLUMNS, PatientData

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10000


class DatasetError(Exception):
    def __init__(self, message: str, status: int = 422, **details: object):
        self.status = status
        self.body = {"success": False, "message": message, **details}


def read_file(content: bytes, filename: str, max_rows: int = MAX_ROWS) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise DatasetError("Formato não suportado. Envie CSV ou XLSX.", 415)
    if not content:
        raise DatasetError("O arquivo está vazio.")
    if len(content) > MAX_BYTES:
        raise DatasetError("O arquivo excede o limite de 5 MB.", 413)
    try:
        if suffix == ".csv":
            frame = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig", sep=None, engine="python", dtype=object, nrows=max_rows + 1)
        else:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if sum(item.file_size for item in archive.infolist()) > 50 * 1024 * 1024:
                    raise DatasetError("A planilha descompactada excede o limite permitido.", 413)
            frame = pd.read_excel(io.BytesIO(content), engine="openpyxl", dtype=object, nrows=max_rows + 1)
    except DatasetError:
        raise
    except Exception:
        raise DatasetError("Não foi possível ler o arquivo. Confira o formato, a codificação UTF-8 e o cabeçalho.") from None
    if frame.empty:
        raise DatasetError("A planilha deve conter ao menos um paciente.")
    if len(frame) > max_rows:
        raise DatasetError(f"O limite é de {max_rows} registros por importação.", 413)
    return frame


def validate_frame(frame: pd.DataFrame, filename: str) -> tuple[dict, list[dict]]:
    columns = [str(column) for column in frame.columns]
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    extra = [column for column in columns if column not in REQUIRED_COLUMNS]
    if missing or extra:
        raise DatasetError("Confira as colunas do modelo. Colunas adicionais não são aceitas para evitar dados pessoais.", missing_columns=missing, extra_columns=extra)
    frame = frame[REQUIRED_COLUMNS].replace(r"^\s*$", None, regex=True)
    absent = {column: int(frame[column].isna().sum()) for column in REQUIRED_COLUMNS}
    rows, errors = [], []
    error_count = 0
    for index, raw in enumerate(frame.to_dict(orient="records"), start=2):
        data = {key: None if pd.isna(value) else value for key, value in raw.items()}
        try:
            # Reject bools and non-finite values instead of silently coercing them.
            if any(isinstance(value, bool) or isinstance(value, float) and not math.isfinite(value) for value in data.values()):
                raise ValueError("Valores booleanos ou não finitos não são permitidos.")
            rows.append(PatientData.model_validate(data).model_dump())
        except (ValidationError, ValueError) as exc:
            error_count += 1
            if len(errors) < 100:
                if isinstance(exc, ValidationError):
                    fields = [str(error["loc"][0]) if error["loc"] else "sessoes_realizadas/faltas" for error in exc.errors()]
                    message = "Verifique tipo, faixa ou valor obrigatório: " + ", ".join(fields)
                else:
                    message = str(exc)
                errors.append({"row": index, "message": message})
    if errors:
        raise DatasetError("Foram encontrados registros inválidos. Corrija o arquivo e valide novamente.", errors=errors, invalid_rows=error_count, missing_values=absent, missing_total=sum(absent.values()))
    numeric_frame = pd.DataFrame(rows)
    metadata = {
        "success": True, "filename": filename, "record_count": len(rows), "column_count": len(columns),
        "columns": REQUIRED_COLUMNS,
        "detected_types": {column: "categórica" if column in CATEGORICAL_COLUMNS else str(numeric_frame[column].dtype) for column in REQUIRED_COLUMNS},
        "missing_values": absent, "missing_total": sum(absent.values()), "preview": rows[:20],
    }
    return metadata, rows
