import { api } from './api'

// Cada embarcação: { id, nome, capacidade (nº de encomendas), ativa, criado_em }. Ordenadas por nome.
export function listarEmbarcacoes() {
  return api.get('/embarcacoes')
}

export function cadastrarEmbarcacao({ nome, capacidade }) {
  return api.post('/embarcacoes', { nome, capacidade })
}

// Manda só o que mudou: { nome?, capacidade?, ativa? }.
export function editarEmbarcacao(id, alteracoes) {
  return api.patch(`/embarcacoes/${id}`, alteracoes)
}
