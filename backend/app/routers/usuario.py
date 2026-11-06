from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import usuario_logado
from app.core.security import criar_token_acesso
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import (
    LoginRequest,
    Token,
    UsuarioCreate,
    UsuarioMeOut,
    UsuarioOut,
)
from app.services.usuario import autenticar, criar_usuario, montar_usuario_me

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(dados: UsuarioCreate, db: Session = Depends(get_db)):
    try:
        return criar_usuario(db, dados)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro))


@router.post("/login", response_model=Token)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    usuario = autenticar(db, dados.email, dados.senha)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha invalidos.",
        )

    access_token = criar_token_acesso({"sub": str(usuario.id)})

    return Token(access_token=access_token)


@router.post("/token", response_model=Token, include_in_schema=False)
def login_formulario(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    usuario = autenticar(db, form_data.username, form_data.password)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha invalidos.",
        )

    access_token = criar_token_acesso({"sub": str(usuario.id)})

    return Token(access_token=access_token)


@router.get("/me", response_model=UsuarioMeOut)
def usuario_atual(
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db),
):
    return montar_usuario_me(db, usuario)
