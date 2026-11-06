from pydantic import BaseModel


class ResumoEncomendasOut(BaseModel):
    total: int
    por_status: dict[str, int]


class ResumoViagensOut(BaseModel):
    em_andamento: int
    total: int
    por_status: dict[str, int]


class MunicipioContagemOut(BaseModel):
    municipio: str
    total: int


class EncomendasPorMunicipioOut(BaseModel):
    total: int
    municipios: list[MunicipioContagemOut]
