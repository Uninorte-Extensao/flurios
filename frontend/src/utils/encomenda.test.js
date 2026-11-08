import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  agruparDestinosPorRota,
  DESCRICAO_MAXIMA,
  normalizarCodigo,
  NOVO_DESTINATARIO,
  ordenarHistorico,
  podeDefinirPessoaAutorizada,
  proximaParadaDoCliente,
  validarEncomenda,
  validarPessoaAutorizada,
} from './encomenda.js'

const VALIDO = {
  destinoId: '2',
  destinatarioId: '7',
  descricao: 'Caixa de ferramentas',
  destNome: '',
  destCpf: '',
  destTelefone: '',
  destEndereco: '',
  destMunicipio: '',
}

const NOVO_VALIDO = {
  ...VALIDO,
  destinatarioId: NOVO_DESTINATARIO,
  destNome: 'João Pereira',
  destCpf: '111.222.333-96',
  destTelefone: '(92) 98888-7777',
  destEndereco: 'Rua das Flores, 123',
  destMunicipio: 'Tefé',
}

test('formulário completo com destinatário existente é válido', () => {
  assert.deepEqual(validarEncomenda(VALIDO), {})
})

test('formulário completo com destinatário novo é válido', () => {
  assert.deepEqual(validarEncomenda(NOVO_VALIDO), {})
})

test('exige destino, destinatário e descrição', () => {
  const erros = validarEncomenda({ ...VALIDO, destinoId: '', destinatarioId: '', descricao: '   ' })

  assert.equal(erros.destinoId, 'Escolha o destino.')
  assert.equal(erros.destinatarioId, 'Escolha um destinatário ou cadastre um novo.')
  assert.equal(erros.descricao, 'Descreva o que será enviado.')
})

test('descrição acima do limite é recusada', () => {
  const erros = validarEncomenda({ ...VALIDO, descricao: 'a'.repeat(DESCRICAO_MAXIMA + 1) })

  assert.match(erros.descricao, /no máximo 255/)
})

test('dados do destinatário só são exigidos quando é novo', () => {
  const erros = validarEncomenda({
    ...NOVO_VALIDO,
    destNome: '',
    destCpf: '',
    destTelefone: '',
    destEndereco: '',
    destMunicipio: '',
  })

  assert.deepEqual(Object.keys(erros).sort(), [
    'destCpf',
    'destEndereco',
    'destMunicipio',
    'destNome',
    'destTelefone',
  ])
})

test('CPF e telefone do destinatário novo são validados', () => {
  const erros = validarEncomenda({ ...NOVO_VALIDO, destCpf: '111.111.111-11', destTelefone: '123' })

  assert.equal(erros.destCpf, 'CPF inválido.')
  assert.equal(erros.destTelefone, 'Informe um telefone com DDD.')
})

test('agrupa destinos por rota mantendo a ordem', () => {
  const destinos = [
    { id: 2, nome: 'Tefé', rota_nome: 'Manaus - Coari' },
    { id: 3, nome: 'Coari', rota_nome: 'Manaus - Coari' },
    { id: 9, nome: 'Parintins', rota_nome: 'Manaus - Parintins' },
  ]

  assert.deepEqual(agruparDestinosPorRota(destinos), [
    { rota: 'Manaus - Coari', destinos: [destinos[0], destinos[1]] },
    { rota: 'Manaus - Parintins', destinos: [destinos[2]] },
  ])
})

test('histórico é exibido da movimentação mais recente para a mais antiga', () => {
  const historico = [{ id: 1 }, { id: 2 }, { id: 3 }]

  assert.deepEqual(ordenarHistorico(historico).map((m) => m.id), [3, 2, 1])
  assert.deepEqual(historico.map((m) => m.id), [1, 2, 3])
})

test('código da busca é aparado e posto em maiúsculas', () => {
  assert.equal(normalizarCodigo('  flx4k9ab3c1z '), 'FLX4K9AB3C1Z')
  assert.equal(normalizarCodigo('   '), '')
})

test('pessoa autorizada: cadastro e troca conforme o status', () => {
  assert.equal(podeDefinirPessoaAutorizada('pendente', true), true)
  assert.equal(podeDefinirPessoaAutorizada('em_transito', false), true)
  assert.equal(podeDefinirPessoaAutorizada('a_retirar', false), true)
  assert.equal(podeDefinirPessoaAutorizada('a_retirar', true), false)
  assert.equal(podeDefinirPessoaAutorizada('entregue', false), false)
})

test('pessoa autorizada: nome e CPF válidos são exigidos, exceto se for o destinatário', () => {
  assert.deepEqual(validarPessoaAutorizada({ usarDestinatario: true, nome: '', cpf: '' }), {})
  assert.deepEqual(
    validarPessoaAutorizada({ usarDestinatario: false, nome: 'Maria Silva', cpf: '111.222.333-96' }),
    {},
  )

  const erros = validarPessoaAutorizada({ usarDestinatario: false, nome: ' ', cpf: '111.111.111-11' })
  assert.equal(erros.nome, 'Informe o nome da pessoa autorizada.')
  assert.equal(erros.cpf, 'CPF inválido.')
})

// Rota Manaus (origem, fora da lista) -> Careiro -> Tefé -> Coari, e outra rota à parte.
const DESTINOS = [
  { id: 2, nome: 'Careiro', rota_nome: 'Manaus - Coari' },
  { id: 3, nome: 'Tefé', rota_nome: 'Manaus - Coari' },
  { id: 4, nome: 'Coari', rota_nome: 'Manaus - Coari' },
  { id: 9, nome: 'Parintins', rota_nome: 'Manaus - Parintins' },
]
const em = (parada_id) => ({ status: 'em_transito', parada_id })
const proxima = (status, destinoId, historico) =>
  proximaParadaDoCliente({ status, destinoId, destinos: DESTINOS, historico })

test('próxima parada: a seguinte à última localização, dentro do trecho até o destino', () => {
  assert.equal(proxima('embarcada', 3, []), 'Careiro')
  assert.equal(proxima('em_transito', 3, [em(null)]), 'Careiro')
  assert.equal(proxima('em_transito', 3, [em(null), em(1)]), 'Careiro') // 1 = origem, fora da lista
  assert.equal(proxima('em_transito', 3, [em(2)]), 'Tefé')
  assert.equal(proxima('em_transito', 4, [em(2), em(3)]), 'Coari')
})

test('próxima parada: nula ao chegar ao destino, depois dele ou fora da viagem a bordo', () => {
  assert.equal(proxima('em_transito', 3, [em(2), em(3)]), null)
  assert.equal(proxima('em_transito', 3, [em(2), em(3), em(4)]), null)
  assert.equal(proxima('pendente', 3, []), null)
  assert.equal(proxima('chegou_ao_destino', 3, [em(3)]), null)
  assert.equal(proxima('em_transito', null, []), null)
  assert.equal(proxima('em_transito', 99, []), null)
})

test('próxima parada: não mistura paradas de outra rota', () => {
  assert.equal(proxima('embarcada', 9, []), 'Parintins')
})
