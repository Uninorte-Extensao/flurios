// Regras das telas de viagens (espelham o backend; as que só valem na tela estão marcadas).

export const FILTRO_TODOS = 'todas'

// Opções do filtro da lista: [valor, rótulo].
export const FILTROS_STATUS = [
  [FILTRO_TODOS, 'Todos os status'],
  ['programada', 'Programada'],
  ['em_andamento', 'Em andamento'],
  ['concluida', 'Concluída'],
  ['cancelada', 'Cancelada'],
]

// Mesmas transições do backend (TRANSICOES_VIAGEM): concluída e cancelada são finais.
const TRANSICOES = {
  programada: ['em_andamento', 'cancelada'],
  em_andamento: ['concluida', 'cancelada'],
  concluida: [],
  cancelada: [],
}

export function podeMudarPara(statusAtual, novoStatus) {
  return (TRANSICOES[statusAtual] ?? []).includes(novoStatus)
}

export function viagemFinalizada(status) {
  return (TRANSICOES[status] ?? []).length === 0
}

// Só uma viagem em andamento aceita registro de localização (backend: 409 nos outros casos).
export function podeRegistrarLocalizacao(status) {
  return status === 'em_andamento'
}

// Cancelar não mexe nas encomendas já entregues nem nas que já estão em imprevisto.
const STATUS_NAO_AFETADOS_PELO_CANCELAMENTO = ['entregue', 'imprevisto']

export function encomendasAfetadasPeloCancelamento(encomendas) {
  return encomendas.filter((e) => !STATUS_NAO_AFETADOS_PELO_CANCELAMENTO.includes(e.status))
}

// Encomendas "embarcada" passam a "em_transito" na primeira localização registrada.
export function encomendasEmbarcadas(encomendas) {
  return encomendas.filter((e) => e.status === 'embarcada')
}

export function ordenarParadas(paradas) {
  return [...paradas].sort((a, b) => a.ordem - b.ordem)
}

// O horário digitado é o de Manaus (UTC-4, sem horário de verão). A API guarda a data em UTC, sem
// fuso: "2026-11-10T08:00" (campo datetime-local) vira "2026-11-10T12:00:00". Inválido -> null.
const DESLOCAMENTO_MANAUS_HORAS = 4

export function dataManausParaApi(valor) {
  const partes = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::\d{2})?$/.exec(String(valor ?? '').trim())

  if (!partes) return null

  const [ano, mes, dia, hora, minuto] = partes.slice(1).map(Number)
  const utc = new Date(Date.UTC(ano, mes - 1, dia, hora + DESLOCAMENTO_MANAUS_HORAS, minuto))

  // Rejeita datas que o Date "corrige" sozinho (31/02, hora 25...).
  const mesmaData = new Date(Date.UTC(ano, mes - 1, dia, hora, minuto))
  if (mesmaData.getUTCMonth() !== mes - 1 || mesmaData.getUTCHours() !== hora) return null

  return utc.toISOString().slice(0, 19)
}

// Devolve { campo: 'mensagem' } (vazio = válido).
export function validarViagem({ embarcacaoId, rotaId, dataSaida }) {
  const erros = {}

  if (!embarcacaoId) erros.embarcacaoId = 'Escolha a embarcação.'
  if (!rotaId) erros.rotaId = 'Escolha a rota.'

  if (!String(dataSaida ?? '').trim()) erros.dataSaida = 'Informe a data e o horário de saída.'
  else if (dataManausParaApi(dataSaida) === null) erros.dataSaida = 'Data e horário de saída inválidos.'

  return erros
}
