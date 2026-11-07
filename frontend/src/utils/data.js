// A API devolve datas em UTC, mas sem o fuso ("2026-11-07T15:30:00"). Sem tratar isso, o
// navegador as lê como horário local e a hora exibida sai errada. Aqui elas são lidas como UTC
// e exibidas no horário de Manaus (UTC-4, sem horário de verão), em pt-BR.
const FUSO = 'America/Manaus'

const FORMATO_DATA = { timeZone: FUSO, day: '2-digit', month: '2-digit', year: 'numeric' }
const FORMATO_HORA = { timeZone: FUSO, hour: '2-digit', minute: '2-digit' }

export function lerDataApi(texto) {
  if (!texto) return null

  const temFuso = /(Z|[+-]\d{2}:?\d{2})$/.test(texto)
  const data = new Date(temFuso ? texto : `${texto}Z`)

  return Number.isNaN(data.getTime()) ? null : data
}

// 07/11/2026
export function formatarData(texto) {
  const data = lerDataApi(texto)
  return data ? data.toLocaleDateString('pt-BR', FORMATO_DATA) : '—'
}

// 07/11/2026 às 11:30
export function formatarDataHora(texto) {
  const data = lerDataApi(texto)
  if (!data) return '—'

  return `${data.toLocaleDateString('pt-BR', FORMATO_DATA)} às ${data.toLocaleTimeString('pt-BR', FORMATO_HORA)}`
}
