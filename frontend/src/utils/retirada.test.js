import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  caminhoRetirada,
  interpretarErroRetirada,
  motivoRetiradaIndisponivel,
  PERFIS_RETIRADA,
  podeRetirar,
  TEXTO_TERMO,
  validarRetirada,
} from './retirada.js'

const CPF_VALIDO = '111.222.333-96'

test('só administrador e funcionário do ponto de retirada podem retirar', () => {
  assert.deepEqual(PERFIS_RETIRADA, ['administrador', 'funcionario_retirada'])
  assert.equal(podeRetirar({ tipo: 'empresa', perfil: 'administrador' }), true)
  assert.equal(podeRetirar({ tipo: 'empresa', perfil: 'funcionario_retirada' }), true)
  assert.equal(podeRetirar({ tipo: 'empresa', perfil: 'atendente' }), false)
  assert.equal(podeRetirar({ tipo: 'empresa', perfil: 'operador_embarcacao' }), false)
  assert.equal(podeRetirar({ tipo: 'cliente', perfil: 'administrador' }), false)
  assert.equal(podeRetirar(null), false)
})

test('validarRetirada barra CPF vazio, inválido e termo não aceito', () => {
  assert.deepEqual(validarRetirada({ cpf: CPF_VALIDO, termoAceito: true }), {})
  assert.equal(validarRetirada({ cpf: '', termoAceito: true }).cpf, 'Informe o CPF de quem está retirando.')
  assert.equal(validarRetirada({ cpf: '111.222.333-97', termoAceito: true }).cpf, 'CPF inválido.')
  assert.equal(validarRetirada({ cpf: '111.222', termoAceito: true }).cpf, 'CPF inválido.')

  const semTermo = validarRetirada({ cpf: CPF_VALIDO, termoAceito: false })
  assert.match(semTermo.termo, /obrigatório aceitar o termo/)
  assert.equal(semTermo.cpf, undefined)
})

test('validarRetirada acumula os dois erros', () => {
  assert.deepEqual(Object.keys(validarRetirada({ cpf: '', termoAceito: false })).sort(), ['cpf', 'termo'])
})

test('caminhoRetirada leva só o código na URL', () => {
  assert.equal(caminhoRetirada('FLX5MBAFUSZ3L'), '/empresa/retiradas/FLX5MBAFUSZ3L')
  assert.equal(caminhoRetirada('A B'), '/empresa/retiradas/A%20B')
})

test('o termo está em português e tem texto', () => {
  assert.ok(TEXTO_TERMO.length >= 3)
  assert.ok(TEXTO_TERMO.every((paragrafo) => paragrafo.endsWith('.')))
})

test('motivoRetiradaIndisponivel explica cada caso e libera só a retirar com pessoa autorizada', () => {
  const pessoa = { nome: 'Maria' }

  assert.equal(motivoRetiradaIndisponivel({ status: 'a_retirar' }, pessoa, 'A retirar'), '')
  assert.match(motivoRetiradaIndisponivel({ status: 'entregue' }, pessoa, 'Entregue'), /já foi entregue/)
  assert.match(motivoRetiradaIndisponivel({ status: 'em_transito' }, pessoa, 'Em trânsito'), /Em trânsito/)
  assert.match(motivoRetiradaIndisponivel({ status: 'a_retirar' }, null, 'A retirar'), /pessoa autorizada/)
})

test('interpretarErroRetirada usa a mensagem da API ou o erro do campo CPF', () => {
  assert.deepEqual(interpretarErroRetirada({ status: 403, message: 'CPF não confere.', erros: {} }), {
    cpf: '',
    geral: 'CPF não confere.',
  })
  assert.deepEqual(
    interpretarErroRetirada({ status: 422, message: 'Confira os dados informados.', erros: { cpf_retirante: 'CPF inválido.' } }),
    { cpf: 'CPF inválido.', geral: '' },
  )
  assert.match(interpretarErroRetirada(undefined).geral, /Não foi possível registrar a retirada/)
})
