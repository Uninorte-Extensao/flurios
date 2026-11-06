import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  agruparDestinosPorRota,
  DESCRICAO_MAXIMA,
  NOVO_DESTINATARIO,
  validarEncomenda,
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
