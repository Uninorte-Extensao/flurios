// Preposições que ficam em minúscula no meio do nome ("Maria da Silva").
const PREPOSICOES = new Set(['e', 'de', 'da', 'do', 'das', 'dos'])

// "kaue souza" / "KAUE SOUZA" -> "Kaue Souza". Só a apresentação: o cadastro guarda o nome como foi digitado.
export function capitalizarNome(nome) {
  const palavras = String(nome ?? '')
    .trim()
    .toLocaleLowerCase('pt-BR')
    .split(/\s+/)
    .filter(Boolean)

  return palavras
    .map((palavra, indice) => {
      if (indice > 0 && PREPOSICOES.has(palavra)) return palavra

      // Maiúscula no começo da palavra e depois de hífen ou apóstrofo ("ana-maria", "d'ávila").
      return palavra.replace(/(^|[-'’])(\p{L})/gu, (_, separador, letra) => separador + letra.toLocaleUpperCase('pt-BR'))
    })
    .join(' ')
}

// "Olá, Kaue". Sem nome, só "Olá".
export function saudacao(nome) {
  const limpo = capitalizarNome(nome)

  return limpo ? `Olá, ${limpo}` : 'Olá'
}
