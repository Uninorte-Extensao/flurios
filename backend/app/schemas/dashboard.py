from pydantic import BaseModel


class ResumoEncomendasOut(BaseModel):
    total: int
    por_status: dict[str, int]
