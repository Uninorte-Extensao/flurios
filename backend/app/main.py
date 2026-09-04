from fastapi import FastAPI

from app.db.session import engine

app = FastAPI(
  title="Flurios API",
  description= "APi para genciamento e rastreamento de entregas fluviais",
  version="0.1.0",

)

@app.get("/health")
def verificar_saude():
  return{
    "status": "ok",
    "sistema": "flurios",
  }