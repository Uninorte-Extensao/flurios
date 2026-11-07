import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  dataManausParaApi,
  encomendasAfetadasPeloCancelamento,
  encomendasEmbarcadas,
  ordenarParadas,
  podeMudarPara,
  podeRegistrarLocalizacao,
  validarViagem,
  viagemFinalizada,
} from './viagem.js'

test('transições de viagem iguais às do backend', () => {
  assert.equal(podeMudarPara('programada', 'em_andamento'), true)
  assert.equal(podeMudarPara('programada', 'cancelada'), true)
  assert.equal(podeMudarPara('programada', 'concluida'), false)
  assert.equal(podeMudarPara('em_andamento', 'concluida'), true)
  assert.equal(podeMudarPara('em_andamento', 'cancelada'), true)
  assert.equal(podeMudarPara('em_andamento', 'programada'), false)
  assert.equal(podeMudarPara('concluida', 'cancelada'), false)
  assert.equal(podeMudarPara('cancelada', 'em_andamento'), false)
})

test('concluída e cancelada são finais', () => {
  assert.equal(viagemFinalizada('concluida'), true)
  assert.equal(viagemFinalizada('cancelada'), true)
  assert.equal(viagemFinalizada('programada'), false)
  assert.equal(viagemFinalizada('em_andamento'), false)
})

test('localização só com a viagem em andamento', () => {
  assert.equal(podeRegistrarLocalizacao('em_andamento'), true)
  assert.equal(podeRegistrarLocalizacao('programada'), false)
  assert.equal(podeRegistrarLocalizacao('concluida'), false)
})

test('cancelamento não afeta encomendas entregues nem em imprevisto', () => {
  const encomendas = [
    { id: 1, status: 'embarcada' },
    { id: 2, status: 'entregue' },
    { id: 3, status: 'imprevisto' },
    { id: 4, status: 'em_transito' },
  ]

  assert.deepEqual(
    encomendasAfetadasPeloCancelamento(encomendas).map((e) => e.id),
    [1, 4],
  )
  assert.deepEqual(
    encomendasEmbarcadas(encomendas).map((e) => e.id),
    [1],
  )
})

test('paradas são ordenadas pela ordem, sem alterar a lista original', () => {
  const paradas = [
    { id: 1, ordem: 3 },
    { id: 2, ordem: 1 },
    { id: 3, ordem: 2 },
  ]

  assert.deepEqual(
    ordenarParadas(paradas).map((p) => p.id),
    [2, 3, 1],
  )
  assert.equal(paradas[0].id, 1)
})

test('horário de Manaus vira UTC sem fuso (soma 4 horas)', () => {
  assert.equal(dataManausParaApi('2026-11-10T08:00'), '2026-11-10T12:00:00')
  assert.equal(dataManausParaApi('2026-11-10T08:30:15'), '2026-11-10T12:30:00')
})

test('horário de Manaus perto da meia-noite muda o dia em UTC', () => {
  assert.equal(dataManausParaApi('2026-12-31T21:00'), '2027-01-01T01:00:00')
})

test('data inválida ou vazia vira null', () => {
  assert.equal(dataManausParaApi(''), null)
  assert.equal(dataManausParaApi(undefined), null)
  assert.equal(dataManausParaApi('10/11/2026 08:00'), null)
  assert.equal(dataManausParaApi('2026-02-31T08:00'), null)
  assert.equal(dataManausParaApi('2026-11-10T25:00'), null)
})

test('validarViagem exige embarcação, rota e data de saída', () => {
  assert.deepEqual(Object.keys(validarViagem({ embarcacaoId: '', rotaId: '', dataSaida: '' })).sort(), [
    'dataSaida',
    'embarcacaoId',
    'rotaId',
  ])
  assert.deepEqual(validarViagem({ embarcacaoId: '1', rotaId: '2', dataSaida: '2026-11-10T08:00' }), {})
  assert.equal(
    validarViagem({ embarcacaoId: '1', rotaId: '2', dataSaida: 'lixo' }).dataSaida,
    'Data e horário de saída inválidos.',
  )
})
