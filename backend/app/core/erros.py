from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def tratar_erro_de_validacao(request: Request, exc: RequestValidationError):
    """Igual ao 422 padrao do FastAPI, mas sem o campo "input".

    O "input" repete o valor enviado pelo chamador, e isso inclui CPF digitado
    errado (dado pessoal). Os demais campos (loc, msg, type) continuam.
    """
    erros = [
        {chave: valor for chave, valor in erro.items() if chave != "input"}
        for erro in exc.errors()
    ]

    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(erros)})
