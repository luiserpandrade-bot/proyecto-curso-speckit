from pydantic import BaseModel, ConfigDict


class GastoCreate(BaseModel):
    descripcion: str
    monto: float
    categoria: str


class GastoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    descripcion: str
    monto: float
    categoria: str
