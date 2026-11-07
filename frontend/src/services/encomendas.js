import { api } from './api'

// Paradas que podem ser destino (todas, menos a origem): [{ id, nome, rota_nome }]
export function listarDestinos() {
  return api.get('/rotas/destinos')
}

// Destinatários do cliente logado. O CPF já chega mascarado (123.***.***-45).
export function listarDestinatarios() {
  return api.get('/destinatarios')
}

// O CPF vai só com dígitos.
export function cadastrarDestinatario({ nome, cpf, telefone, endereco, municipio }) {
  return api.post('/destinatarios', { nome, cpf, telefone, endereco, municipio })
}

// Devolve a encomenda criada, com `codigo_rastreio` e `destino_nome`.
export function criarEncomenda({ destinatarioId, paradaDestinoId, descricao }) {
  return api.post('/encomendas', {
    destinatario_id: destinatarioId,
    parada_destino_id: paradaDestinoId,
    descricao,
  })
}

// Encomendas do cliente logado, da mais recente para a mais antiga.
// Cada item tem: id, codigo_rastreio, destino_nome, destinatario_id, descricao, status, criado_em.
export function listarEncomendas() {
  return api.get('/encomendas')
}

// 404 quando o código não existe ou é de outro cliente.
export function buscarEncomenda(codigo) {
  return api.get(`/encomendas/${encodeURIComponent(codigo)}`)
}

// { codigo_rastreio, status_atual, historico: [{ id, status, parada_nome, criado_em }] }
// O histórico vem do mais antigo para o mais recente.
export function buscarRastreio(codigo) {
  return api.get(`/encomendas/${encodeURIComponent(codigo)}/rastreio`)
}

// { id, nome, cpf (mascarado), criado_em }, ou null quando ainda não foi cadastrada (404).
export async function buscarPessoaAutorizada(encomendaId) {
  try {
    return await api.get(`/encomendas/${encomendaId}/pessoa-autorizada`)
  } catch (erro) {
    if (erro.status === 404) return null
    throw erro
  }
}

// Cadastra ou troca a pessoa autorizada. Ou informa `nome` e `cpf` (só dígitos),
// ou `destinatarioEAPessoa: true`. A resposta traz o CPF mascarado.
export function definirPessoaAutorizada(encomendaId, { destinatarioEAPessoa, nome, cpf }) {
  const corpo = destinatarioEAPessoa ? { destinatario_e_a_pessoa: true } : { nome, cpf }

  return api.post(`/encomendas/${encomendaId}/pessoa-autorizada`, corpo)
}
