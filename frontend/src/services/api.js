import { traduzirMensagem } from './mensagens'

// URL da API vem de VITE_API_URL (ver .env.example).
const URL_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '')

const CHAVE_TOKEN = 'flurios.token'

export const tokenStorage = {
  obter: () => localStorage.getItem(CHAVE_TOKEN),
  salvar: (token) => localStorage.setItem(CHAVE_TOKEN, token),
  remover: () => localStorage.removeItem(CHAVE_TOKEN),
}

let aoNaoAutorizado = null

// O contexto de autenticação registra aqui o que fazer quando a API devolve 401.
export function definirAoNaoAutorizado(funcao) {
  aoNaoAutorizado = funcao
}

export class ApiError extends Error {
  constructor(status, mensagem, erros = {}) {
    super(mensagem)
    this.name = 'ApiError'
    this.status = status
    // Erros por campo (422): { cpf: 'CPF inválido.' }
    this.erros = erros
  }
}

function criarErro(status, dados) {
  const detalhe = dados?.detail

  if (Array.isArray(detalhe)) {
    const erros = {}
    for (const item of detalhe) {
      const campo = item.loc?.[item.loc.length - 1]
      if (campo !== undefined && !(campo in erros)) {
        erros[campo] = traduzirMensagem(item.msg, 'Valor inválido.')
      }
    }
    return new ApiError(status, 'Confira os dados informados.', erros)
  }

  if (typeof detalhe === 'string') {
    return new ApiError(status, traduzirMensagem(detalhe))
  }

  return new ApiError(status, 'Não foi possível concluir a operação. Tente novamente.')
}

async function lerCorpo(resposta) {
  if (resposta.status === 204) return null
  try {
    return await resposta.json()
  } catch {
    return null
  }
}

export async function requisitar(caminho, { metodo = 'GET', corpo, autenticado = true } = {}) {
  const cabecalhos = { Accept: 'application/json' }
  const token = tokenStorage.obter()

  if (corpo !== undefined) cabecalhos['Content-Type'] = 'application/json'
  if (autenticado && token) cabecalhos.Authorization = `Bearer ${token}`

  let resposta
  try {
    resposta = await fetch(`${URL_BASE}${caminho}`, {
      method: metodo,
      headers: cabecalhos,
      body: corpo !== undefined ? JSON.stringify(corpo) : undefined,
    })
  } catch {
    throw new ApiError(0, 'Não foi possível conectar ao servidor. Tente novamente.')
  }

  const dados = await lerCorpo(resposta)

  if (!resposta.ok) {
    if (resposta.status === 401 && autenticado && token && aoNaoAutorizado) {
      aoNaoAutorizado()
    }
    throw criarErro(resposta.status, dados)
  }

  return dados
}

export const api = {
  get: (caminho, opcoes) => requisitar(caminho, { ...opcoes, metodo: 'GET' }),
  post: (caminho, corpo, opcoes) => requisitar(caminho, { ...opcoes, metodo: 'POST', corpo }),
  patch: (caminho, corpo, opcoes) => requisitar(caminho, { ...opcoes, metodo: 'PATCH', corpo }),
  delete: (caminho, opcoes) => requisitar(caminho, { ...opcoes, metodo: 'DELETE' }),
}
