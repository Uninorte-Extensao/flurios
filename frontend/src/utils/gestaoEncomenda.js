// Regras da gestão de encomendas pela empresa (as que só valem na tela estão marcadas).

export const FILTRO_TODOS = 'todos'
export const ITENS_POR_PAGINA = 10

export const ROTULOS_STATUS = {
  pendente: 'Pendente',
  recebida: 'Recebida',
  aguardando_embarque: 'Aguardando embarque',
  embarcada: 'Embarcada',
  em_transito: 'Em trânsito',
  chegou_ao_destino: 'Chegou ao destino',
  a_retirar: 'A retirar',
  entregue: 'Entregue',
  imprevisto: 'Imprevisto',
}

// Opções do filtro de status da lista: [valor, rótulo].
export const FILTROS_STATUS = [[FILTRO_TODOS, 'Todos os status'], ...Object.entries(ROTULOS_STATUS)]

// SÓ NA TELA: o backend aceita qualquer status em PATCH /encomendas/{id}/status. Aqui só se oferece o
// próximo passo do fluxo ou "imprevisto". "Entregue" não aparece: só nasce da retirada (termo de
// compromisso + pessoa autorizada). De "imprevisto" só se volta para "recebida" (realocar).
const TRANSICOES_MANUAIS = {
  pendente: ['recebida', 'imprevisto'],
  recebida: ['aguardando_embarque', 'imprevisto'],
  aguardando_embarque: ['embarcada', 'imprevisto'],
  embarcada: ['em_transito', 'imprevisto'],
  em_transito: ['chegou_ao_destino', 'imprevisto'],
  chegou_ao_destino: ['a_retirar', 'imprevisto'],
  a_retirar: ['imprevisto'],
  entregue: [],
  imprevisto: ['recebida'],
}

export function statusSeguintes(status) {
  return TRANSICOES_MANUAIS[status] ?? []
}

// Mesma regra do backend: só estas duas fases aceitam ser colocadas em uma viagem.
const STATUS_ASSOCIAVEIS = ['recebida', 'aguardando_embarque']
const STATUS_VIAGEM_ATIVA = ['programada', 'em_andamento']

export function statusAssociavel(status) {
  return STATUS_ASSOCIAVEIS.includes(status)
}

// Por que a encomenda não pode ser associada agora ('' quando pode). O backend confere tudo de novo (409).
export function motivoNaoAssociar(encomenda) {
  if (encomenda.viagem_ativa) {
    return `Esta encomenda já está na viagem #${encomenda.viagem_ativa.id}.`
  }

  if (!statusAssociavel(encomenda.status)) {
    return 'Só encomendas Recebida ou Aguardando embarque podem ser associadas a uma viagem.'
  }

  if (encomenda.parada_destino_id == null) return 'A encomenda não tem destino definido.'

  return ''
}

export function podeAssociar(encomenda) {
  return motivoNaoAssociar(encomenda) === ''
}

// Realocar = devolver à fase "recebida" uma encomenda em imprevisto (e depois associar a outra viagem).
// Se ainda estiver presa a uma viagem ativa, ela precisa sair dela antes (só viagem programada permite).
export function podeRealocar(encomenda) {
  return encomenda.status === 'imprevisto' && !encomenda.viagem_ativa
}

// A viagem entra na lista de associação se está ativa e a rota (com `paradas`) contém o destino da encomenda.
export function viagemAceitaEncomenda(viagem, rota, encomenda) {
  if (!STATUS_VIAGEM_ATIVA.includes(viagem.status)) return false
  if (encomenda.parada_destino_id == null) return false

  return (rota?.paradas ?? []).some((parada) => parada.id === encomenda.parada_destino_id)
}

// Filtros da lista -> query string de GET /empresa/encomendas ('' quando não há filtro).
// status é repetido (status=a&status=b); busca vazia e filtros neutros são omitidos.
export function montarConsultaEncomendas({
  status = [],
  paradaDestinoId,
  rotaId,
  semViagemAtiva = false,
  busca = '',
  limite,
  deslocamento,
} = {}) {
  const params = new URLSearchParams()

  for (const item of status) params.append('status', item)
  if (paradaDestinoId) params.set('parada_destino_id', String(paradaDestinoId))
  if (rotaId) params.set('rota_id', String(rotaId))
  if (semViagemAtiva) params.set('sem_viagem_ativa', 'true')
  if (busca.trim()) params.set('busca', busca.trim())
  if (limite) params.set('limite', String(limite))
  if (deslocamento) params.set('deslocamento', String(deslocamento))

  const texto = params.toString()
  return texto ? `?${texto}` : ''
}

// "11–20 de 34" (a página começa em 0). Sem resultados: ''.
export function resumoPagina(pagina, itensPorPagina, quantidadeNaPagina, total) {
  if (total === 0 || quantidadeNaPagina === 0) return ''

  const inicio = pagina * itensPorPagina + 1
  return `${inicio}–${inicio + quantidadeNaPagina - 1} de ${total}`
}

// Link para o detalhe da encomenda na área da empresa.
export const caminhoDetalheEmpresa = (codigo) => `/empresa/encomendas/${encodeURIComponent(codigo)}`
