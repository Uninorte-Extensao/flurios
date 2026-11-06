import { api } from './api'

export async function login(email, senha) {
  const { access_token: token } = await api.post(
    '/usuarios/login',
    { email, senha },
    { autenticado: false },
  )
  return token
}

// Devolve { id, nome, email, tipo: 'cliente' | 'empresa' | null, perfil }
export function obterUsuarioAtual() {
  return api.get('/usuarios/me')
}

export function cadastrarUsuario({ nome, email, senha }) {
  return api.post('/usuarios', { nome, email, senha }, { autenticado: false })
}

// Completa o cadastro do usuário logado como cliente. O CPF vai só com dígitos.
export function cadastrarCliente({ cpf, telefone }) {
  return api.post('/clientes', { cpf, telefone })
}
