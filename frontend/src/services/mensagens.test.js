import assert from 'node:assert/strict'
import { test } from 'node:test'
import { traduzirMensagem } from './mensagens.js'

test('traduz as mensagens de parada e de viagem da API', () => {
  assert.equal(
    traduzirMensagem('Nao e possivel remover uma parada que e destino de encomendas.'),
    'Não é possível remover uma parada que é destino de encomendas.',
  )
  assert.equal(traduzirMensagem('Viagem nao encontrada.'), 'Viagem não encontrada.')
  assert.equal(
    traduzirMensagem('So e possivel registrar localizacao em viagem em andamento.'),
    'Só é possível registrar a localização de uma viagem em andamento.',
  )
  assert.equal(
    traduzirMensagem('A parada nao pertence a rota da viagem.'),
    'Esta parada não pertence à rota da viagem.',
  )
})

test('transição inválida de viagem cita os dois status em português', () => {
  assert.equal(
    traduzirMensagem('Transicao de status invalida: programada -> concluida.'),
    'Não é possível mudar a viagem de programada para concluída.',
  )
  assert.equal(
    traduzirMensagem('Transicao de status invalida: em_andamento -> programada.'),
    'Não é possível mudar a viagem de em andamento para programada.',
  )
})

test('mensagem desconhecida volta como veio, ou usa o padrão', () => {
  assert.equal(traduzirMensagem('Algo inesperado.'), 'Algo inesperado.')
  assert.equal(traduzirMensagem('Algo inesperado.', 'Erro padrão.'), 'Erro padrão.')
})
