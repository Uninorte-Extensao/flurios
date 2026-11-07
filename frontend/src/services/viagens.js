import { api } from './api'

// Cada viagem: { id, embarcacao_id, rota_id, data_saida, status, criado_em }.
// Status: programada | em_andamento | concluida | cancelada. Da data de saída mais recente para a mais antiga.
// A lista não traz os nomes: cruze `embarcacao_id` e `rota_id` com GET /embarcacoes e GET /rotas.
export function listarViagens() {
  return api.get('/viagens')
}

// Viagem + `embarcacao` ({ id, nome, capacidade, ativa }) + `rota` ({ id, nome, paradas: [{ id, nome, ordem }] }).
export function obterViagem(id) {
  return api.get(`/viagens/${id}`)
}

// `dataSaida` é a data em UTC sem fuso (ver `dataManausParaApi`). A viagem nasce `programada`.
export function programarViagem({ embarcacaoId, rotaId, dataSaida }) {
  return api.post('/viagens', {
    embarcacao_id: embarcacaoId,
    rota_id: rotaId,
    data_saida: dataSaida,
  })
}

// Transições aceitas: programada -> em_andamento | cancelada; em_andamento -> concluida | cancelada.
// Qualquer outra devolve 409. Cancelar passa as encomendas da viagem para `imprevisto`.
export function atualizarStatusViagem(id, status) {
  return api.patch(`/viagens/${id}/status`, { status })
}

// Encomendas associadas: [{ id, codigo_rastreio, destino_nome, descricao, status, criado_em, ... }]
export function listarEncomendasDaViagem(id) {
  return api.get(`/viagens/${id}/encomendas`)
}

// Só com a viagem em andamento e com uma parada da rota (409 nos outros casos).
// Devolve { viagem_id, parada_id, encomendas_registradas }.
export function registrarLocalizacao(id, paradaId) {
  return api.post(`/viagens/${id}/localizacao`, { parada_id: paradaId })
}

// Só viagem programada ou em andamento; encomenda recebida ou aguardando embarque, com destino na rota
// da viagem, ainda sem viagem ativa e com capacidade livre (409 com a mensagem do motivo nos outros casos).
export function associarEncomenda(viagemId, encomendaId) {
  return api.post(`/viagens/${viagemId}/encomendas`, { encomenda_id: encomendaId })
}

// Só com a viagem programada (409 nos outros casos). A encomenda volta ao status `recebida`.
export function desassociarEncomenda(viagemId, encomendaId) {
  return api.delete(`/viagens/${viagemId}/encomendas/${encomendaId}`)
}
