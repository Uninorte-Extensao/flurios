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


class OcupacaoViagemOut(BaseModel):
    viagem_id: int
    embarcacao_id: int
    embarcacao_nome: str
    rota_nome: str
    capacidade: int
    encomendas_ativas: int
    # encomendas_ativas / capacidade (0.5 = 50%). Pode passar de 1.0 se a
    # embarcacao estiver com mais encomendas que a capacidade.
    ocupacao: float


class OcupacaoOut(BaseModel):
    total: int
    viagens: list[OcupacaoViagemOut]
