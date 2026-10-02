from pydantic import BaseModel, Field


class DashboardResponse(BaseModel):
    patients: int = Field(ge=0)
    datasets: int = Field(ge=0)
    analyses: int = Field(ge=0)
    models: int = Field(ge=0)
    anomalies: int = Field(ge=0)
