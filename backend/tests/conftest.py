import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main
from app.database.session import get_db
from app.services import physiotherapy_dataset as datasets
from app.ml.physiotherapy import model_manager
from app.services import nursing_dataset
from app.ml.nursing import anomaly_service
from app.services import pharmacy_dataset
from app.ml.pharmacy.adherence import model_manager as adherence_model
from app.ml.pharmacy.demand import model_manager as demand_model
from app.services import veterinary_dataset
from app.ml.veterinary.classification import model_manager as veterinary_model
from app.ml.veterinary.anomaly import model_manager as veterinary_anomaly_model
from app.services import psychology_dataset
from app.ml.psychology import model_manager as psychology_model


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main, "SessionLocal", sessions)
    monkeypatch.setattr(datasets, "DATASET_DIR", tmp_path / "datasets" / "fisioterapia")
    monkeypatch.setattr(model_manager, "MODEL_DIR", tmp_path / "models" / "physiotherapy")
    monkeypatch.setattr(model_manager, "_bundle", None)
    monkeypatch.setattr(model_manager, "_load_error", None)
    monkeypatch.setattr(main, "initialize_model", lambda db: None)
    monkeypatch.setattr(nursing_dataset, "DATASET_DIR", tmp_path / "datasets" / "enfermagem")
    monkeypatch.setattr(anomaly_service, "MODEL_DIR", tmp_path / "models" / "nursing")
    monkeypatch.setattr(anomaly_service, "_bundle", None)
    monkeypatch.setattr(main, "initialize_nursing_dataset", lambda db: None)
    monkeypatch.setattr(main, "initialize_nursing_model", lambda db: None)
    monkeypatch.setattr(pharmacy_dataset, "DATASET_DIR", tmp_path / "datasets" / "farmacia")
    monkeypatch.setattr(adherence_model, "MODEL_DIR", tmp_path / "models" / "pharmacy" / "adherence")
    monkeypatch.setattr(demand_model, "MODEL_DIR", tmp_path / "models" / "pharmacy" / "demand")
    monkeypatch.setattr(adherence_model, "_bundle", None)
    monkeypatch.setattr(demand_model, "_bundle", None)
    monkeypatch.setattr(main, "initialize_pharmacy_datasets", lambda db: None)
    monkeypatch.setattr(main, "initialize_adherence_model", lambda db: None)
    monkeypatch.setattr(main, "initialize_demand_model", lambda db: None)
    monkeypatch.setattr(veterinary_dataset, "DATASET_DIR", tmp_path / "datasets" / "veterinaria")
    monkeypatch.setattr(veterinary_model, "MODEL_DIR", tmp_path / "models" / "veterinary")
    monkeypatch.setattr(veterinary_anomaly_model, "MODEL_DIR", tmp_path / "models" / "veterinary")
    monkeypatch.setattr(veterinary_model, "_bundle", None)
    monkeypatch.setattr(veterinary_anomaly_model, "_bundle", None)
    monkeypatch.setattr(main, "initialize_veterinary_datasets", lambda db: None)
    monkeypatch.setattr(main, "initialize_veterinary_model", lambda db: None)
    monkeypatch.setattr(main, "initialize_veterinary_anomaly_model", lambda db: None)
    monkeypatch.setattr(psychology_dataset, "DATASET_DIR", tmp_path / "datasets" / "psicologia")
    monkeypatch.setattr(psychology_model, "MODEL_DIR", tmp_path / "models" / "psychology")
    monkeypatch.setattr(psychology_model, "_bundle", None)
    monkeypatch.setattr(main, "initialize_psychology_dataset", lambda db: None)
    monkeypatch.setattr(main, "initialize_psychology_model", lambda db: None)

    def override():
        with sessions() as db:
            yield db

    main.app.dependency_overrides[get_db] = override
    with TestClient(main.app) as client:
        client.test_sessions = sessions
        yield client
    main.app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def ml_client(client):
    with client.test_sessions() as db:
        model_manager.initialize_model(db)
    return client


@pytest.fixture
def nursing_client(client):
    with client.test_sessions() as db:
        nursing_dataset.initialize_dataset(db)
        anomaly_service.initialize_model(db)
    return client


@pytest.fixture
def pharmacy_client(client):
    with client.test_sessions() as db:
        pharmacy_dataset.initialize_datasets(db)
        adherence_model.initialize_model(db)
        demand_model.initialize_model(db)
    return client


@pytest.fixture
def veterinary_client(client):
    with client.test_sessions() as db:
        veterinary_dataset.initialize_datasets(db, size=200)
        veterinary_model.initialize_model(db)
        veterinary_anomaly_model.initialize_model(db)
    return client


@pytest.fixture
def psychology_client(client):
    with client.test_sessions() as db:
        psychology_dataset.initialize_dataset(db, size=240)
        psychology_model.initialize_model(db)
    return client
