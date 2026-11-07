// Regras de validação das telas de embarcações, rotas e paradas (mesmos limites do backend).
export const NOME_MAXIMO = 100
export const ORIGEM_NOME = 'Manaus'
export const ORDEM_ORIGEM = 1

function normalizar(texto) {
  return String(texto ?? '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .trim()
    .toLowerCase()
}

// "manaus", " MANAUS " e "Mánaus" contam como Manaus.
export function ehManaus(nome) {
  return normalizar(nome) === normalizar(ORIGEM_NOME)
}

function validarNome(nome, rotulo) {
  const texto = String(nome ?? '').trim()

  if (!texto) return `Informe o nome ${rotulo}.`
  if (texto.length > NOME_MAXIMO) return `O nome deve ter no máximo ${NOME_MAXIMO} caracteres.`

  return ''
}

// Inteiro positivo digitado em um campo de texto ("12" -> 12). Qualquer outra coisa -> null.
export function lerInteiroPositivo(valor) {
  const texto = String(valor ?? '').trim()

  if (!/^\d+$/.test(texto)) return null

  const numero = Number(texto)

  return Number.isSafeInteger(numero) && numero > 0 ? numero : null
}

// Devolve { campo: 'mensagem' } (vazio = válido).
export function validarEmbarcacao({ nome, capacidade }) {
  const erros = {}

  const erroNome = validarNome(nome, 'da embarcação')
  if (erroNome) erros.nome = erroNome

  if (!String(capacidade ?? '').trim()) erros.capacidade = 'Informe a capacidade.'
  else if (lerInteiroPositivo(capacidade) === null) {
    erros.capacidade = 'A capacidade deve ser um número inteiro maior que zero.'
  }

  return erros
}

export function validarRota({ nome }) {
  const erroNome = validarNome(nome, 'da rota')

  return erroNome ? { nome: erroNome } : {}
}

export function ordenarParadas(paradas) {
  return [...paradas].sort((a, b) => a.ordem - b.ordem)
}

// Sugestão para a próxima parada: uma depois da última (ou 1, se a rota ainda não tem paradas).
export function proximaOrdem(paradas) {
  return paradas.reduce((maior, parada) => Math.max(maior, parada.ordem), 0) + 1
}

// A rota só é válida se a parada de ordem 1 for Manaus.
export function origemEhManaus(paradas) {
  return paradas.some((parada) => parada.ordem === ORDEM_ORIGEM && ehManaus(parada.nome))
}

// A origem (Manaus, ordem 1) só sai da rota se for a última parada: senão a rota ficaria sem
// origem. Uma ordem 1 que não é Manaus (dado fora da regra) pode sair, para a rota ser corrigida.
export function podeRemoverParada(parada, paradas) {
  return parada.ordem !== ORDEM_ORIGEM || paradas.length === 1 || !ehManaus(parada.nome)
}

// Valores iniciais do formulário "Adicionar parada": sem origem, começa por Manaus na ordem 1;
// depois sugere a ordem seguinte à última.
export function sugestaoParada(paradas) {
  if (!paradas.some((parada) => parada.ordem === ORDEM_ORIGEM)) {
    return { nome: ORIGEM_NOME, ordem: ORDEM_ORIGEM }
  }

  return { nome: '', ordem: proximaOrdem(paradas) }
}

// Valida o formulário "Adicionar parada" contra as paradas que a rota já tem.
export function validarParada({ nome, ordem }, paradas) {
  const erros = {}

  const erroNome = validarNome(nome, 'da parada')
  if (erroNome) erros.nome = erroNome

  const numero = lerInteiroPositivo(ordem)

  if (!String(ordem ?? '').trim()) erros.ordem = 'Informe a ordem da parada.'
  else if (numero === null) erros.ordem = 'A ordem deve ser um número inteiro maior que zero.'
  else if (paradas.some((parada) => parada.ordem === numero)) {
    erros.ordem = 'Já existe uma parada com essa ordem nesta rota.'
  } else if (numero === ORDEM_ORIGEM) {
    if (!erros.nome && !ehManaus(nome)) erros.nome = `A parada de ordem 1 deve ser ${ORIGEM_NOME}.`
  } else if (!paradas.some((parada) => parada.ordem === ORDEM_ORIGEM)) {
    erros.ordem = `Cadastre primeiro a parada de ordem 1 (${ORIGEM_NOME}).`
  }

  return erros
}
