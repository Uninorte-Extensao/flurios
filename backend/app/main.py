from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine




app = FastAPI(
  title="Flurios API",
  description= "APi para genciamento e rastreamento de entregas fluviais",
  version="0.1.0",

)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.get("/health")
def verificar_saude():
  return{
    "status": "ok",
    "sistema": "flurios",
  }