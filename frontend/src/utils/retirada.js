// Regras da tela de retirada (as que só valem na tela estão marcadas).
// LGPD: nada aqui loga ou devolve o CPF digitado; ele só existe no estado do formulário.
import { cpfValido } from './cpf.js'

export const CAMINHO_FILA_RETIRADA = '/empresa/retiradas'

// Link para a tela de retirada de uma encomenda (só o código vai na URL, nunca CPF).
export const caminhoRetirada = (codigo) => `${CAMINHO_FILA_RETIRADA}/${encodeURIComponent(codigo)}`

export const TITULO_TERMO = 'Termo de compromisso de retirada'

export const TEXTO_TERMO = [
  'Declaro que sou a pessoa autorizada pelo cliente para retirar esta encomenda e que informei o meu próprio CPF.',
  'Conferi a encomenda e estou ciente de que, depois da confirmação, ela será registrada como entregue e a retirada não poderá ser desfeita.',
  'Assumo a responsabilidade pela guarda da encomenda a partir do momento da retirada.',
  'Estou ciente de que meu CPF será guardado para comprovar a retirada e que o sistema nunca o exibe por completo.',
]

export const TEXTO_ACEITE = 'A pessoa que está retirando leu e aceitou o termo de compromisso.'

// SÓ NA TELA: o backend aceita a retirada de qualquer perfil da empresa (só exige estar logado como
// empresa). A tela e o item de menu ficam restritos a estes dois perfis.
export const PERFIS_RETIRADA = ['administrador', 'funcionario_retirada']

export function podeRetirar(usuario) {
  return usuario?.tipo === 'empresa' && PERFIS_RETIRADA.includes(usuario?.perfil)
}

// Valida o formulário antes de enviar. Devolve { campo: 'mensagem' } (vazio = pode enviar).
// SÓ NA TELA: o CPF é conferido com os dígitos verificadores; o backend confere de novo e ainda
// compara com o CPF da pessoa autorizada (403 se for diferente).
export function validarRetirada({ cpf, termoAceito }) {
  const erros = {}

  if (!String(cpf ?? '').trim()) erros.cpf = 'Informe o CPF de quem está retirando.'
  else if (!cpfValido(cpf)) erros.cpf = 'CPF inválido.'

  if (!termoAceito) erros.termo = 'É obrigatório aceitar o termo de compromisso para retirar.'

  return erros
}

// Por que o formulário não está disponível ('' quando está). O backend confere tudo de novo (409).
export function motivoRetiradaIndisponivel(encomenda, pessoa, rotuloStatus) {
  if (encomenda.status === 'entregue') return 'Esta encomenda já foi entregue.'

  if (encomenda.status !== 'a_retirar') {
    return `Esta encomenda ainda não está a retirar (status atual: ${rotuloStatus}). A retirada só é liberada quando ela chega ao destino e fica “A retirar”.`
  }

  if (!pessoa) {
    return 'Esta encomenda não tem pessoa autorizada cadastrada. O cliente precisa cadastrá-la antes da retirada.'
  }

  return ''
}

// Traduz o erro da API (ApiError) para a tela. A mensagem do 403 não revela o CPF correto e a do
// 422 não repete o CPF digitado; mesmo assim, só `message` e `erros` são lidos, nunca o corpo.
export function interpretarErroRetirada(erro) {
  const cpf = erro?.erros?.cpf_retirante

  if (cpf) return { cpf, geral: '' }

  return { cpf: '', geral: erro?.message || 'Não foi possível registrar a retirada. Tente novamente.' }
}
