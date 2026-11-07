import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  caminhoDetalheEmpresa,
  montarConsultaEncomendas,
  motivoNaoAssociar,
  podeAssociar,
  podeRealocar,
  resumoPagina,
  statusSeguintes,
  viagemAceitaEncomenda,
} from './gestaoEncomenda.js'

const encomenda = (extra = {}) => ({
  id: 1,
  status: 'recebida',
  parada_destino_id: 7,
  viagem_ativa: null,
  ...extra,
})

test('consulta vazia não gera query string', () => {
  assert.equal(montarConsultaEncomendas(), '')
  assert.equal(montarConsultaEncomendas({ busca: '   ', status: [], semViagemAtiva: false }), '')
})

test('consulta repete status e inclui só os filtros preenchidos', () => {
  assert.equal(
    montarConsultaEncomendas({
      status: ['recebida', 'aguardando_embarque'],
      paradaDestinoId: 7,
      rotaId: 2,
      semViagemAtiva: true,
      busca: ' flx-1 ',
      limite: 10,
      deslocamento: 20,
    }),
    '?status=recebida&status=aguardando_embarque&parada_destino_id=7&rota_id=2&sem_viagem_ativa=true&busca=flx-1&limite=10&deslocamento=20',
  )
})

test('consulta codifica a busca', () => {
  assert.equal(montarConsultaEncomendas({ busca: 'a b&c' }), '?busca=a+b%26c')
})

test('deslocamento zero não entra na consulta', () => {
  assert.equal(montarConsultaEncomendas({ limite: 10, deslocamento: 0 }), '?limite=10')
})

test('status seguintes seguem o fluxo e sempre oferecem imprevisto', () => {
  assert.deepEqual(statusSeguintes('pendente'), ['recebida', 'imprevisto'])
  assert.deepEqual(statusSeguintes('em_transito'), ['chegou_ao_destino', 'imprevisto'])
  assert.deepEqual(statusSeguintes('imprevisto'), ['recebida'])
})

test('entregue nunca é oferecido e não tem próximo status', () => {
  const origens = [
    'pendente',
    'recebida',
    'aguardando_embarque',
    'embarcada',
    'em_transito',
    'chegou_ao_destino',
    'a_retirar',
    'imprevisto',
  ]

  for (const origem of origens) {
    assert.ok(!statusSeguintes(origem).includes('entregue'), origem)
  }
  assert.deepEqual(statusSeguintes('entregue'), [])
  assert.deepEqual(statusSeguintes('desconhecido'), [])
})

test('só recebida e aguardando embarque, sem viagem ativa e com destino, podem ser associadas', () => {
  assert.equal(podeAssociar(encomenda()), true)
  assert.equal(podeAssociar(encomenda({ status: 'aguardando_embarque' })), true)
  assert.equal(podeAssociar(encomenda({ status: 'pendente' })), false)
  assert.equal(podeAssociar(encomenda({ status: 'imprevisto' })), false)
  assert.equal(podeAssociar(encomenda({ parada_destino_id: null })), false)
  assert.equal(podeAssociar(encomenda({ viagem_ativa: { id: 3, status: 'programada' } })), false)
})

test('motivo explica por que não pode associar', () => {
  assert.match(motivoNaoAssociar(encomenda({ viagem_ativa: { id: 3 } })), /viagem #3/)
  assert.match(motivoNaoAssociar(encomenda({ status: 'pendente' })), /Recebida ou Aguardando embarque/)
  assert.match(motivoNaoAssociar(encomenda({ parada_destino_id: null })), /não tem destino/)
  assert.equal(motivoNaoAssociar(encomenda()), '')
})

test('realocar vale só para imprevisto fora de viagem ativa', () => {
  assert.equal(podeRealocar(encomenda({ status: 'imprevisto' })), true)
  assert.equal(podeRealocar(encomenda({ status: 'imprevisto', viagem_ativa: { id: 1 } })), false)
  assert.equal(podeRealocar(encomenda({ status: 'recebida' })), false)
})

test('viagem aceita a encomenda se está ativa e a rota contém o destino', () => {
  const rota = { paradas: [{ id: 1 }, { id: 7 }] }

  assert.equal(viagemAceitaEncomenda({ status: 'programada' }, rota, encomenda()), true)
  assert.equal(viagemAceitaEncomenda({ status: 'em_andamento' }, rota, encomenda()), true)
  assert.equal(viagemAceitaEncomenda({ status: 'concluida' }, rota, encomenda()), false)
  assert.equal(viagemAceitaEncomenda({ status: 'cancelada' }, rota, encomenda()), false)
  assert.equal(viagemAceitaEncomenda({ status: 'programada' }, rota, encomenda({ parada_destino_id: 9 })), false)
  assert.equal(viagemAceitaEncomenda({ status: 'programada' }, rota, encomenda({ parada_destino_id: null })), false)
  assert.equal(viagemAceitaEncomenda({ status: 'programada' }, undefined, encomenda()), false)
})

test('resumo da página', () => {
  assert.equal(resumoPagina(0, 10, 10, 34), '1–10 de 34')
  assert.equal(resumoPagina(3, 10, 4, 34), '31–34 de 34')
  assert.equal(resumoPagina(0, 10, 0, 0), '')
})

test('caminho do detalhe codifica o código', () => {
  assert.equal(caminhoDetalheEmpresa('FLX 1/2'), '/empresa/encomendas/FLX%201%2F2')
})
