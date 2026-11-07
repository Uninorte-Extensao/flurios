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

test('traduz todas as mensagens de associação de encomendas à viagem', () => {
  const esperado = {
    'So e possivel associar encomendas a viagens programadas ou em andamento.':
      'Só é possível associar encomendas a viagens programadas ou em andamento.',
    'Encomenda ja esta associada a uma viagem ativa.': 'Esta encomenda já está associada a uma viagem ativa.',
    'So e possivel associar encomendas com status recebida ou aguardando_embarque.':
      'Só é possível associar encomendas com status Recebida ou Aguardando embarque.',
    'A encomenda nao tem destino definido.': 'A encomenda não tem destino definido.',
    'O destino da encomenda nao pertence a rota da viagem.':
      'O destino da encomenda não faz parte da rota desta viagem.',
    'A embarcacao da viagem nao tem capacidade para mais encomendas.':
      'A embarcação desta viagem não tem capacidade para mais encomendas.',
    'So e possivel remover encomendas de viagens programadas.':
      'Só é possível remover encomendas de viagens programadas.',
    'A encomenda nao esta associada a esta viagem.': 'Esta encomenda não está associada a esta viagem.',
  }

  for (const [original, traduzida] of Object.entries(esperado)) {
    assert.equal(traduzirMensagem(original), traduzida)
  }
})

test('traduz as mensagens de programação de viagem', () => {
  assert.equal(
    traduzirMensagem('Nao e possivel programar viagem com embarcacao inativa.'),
    'Não é possível programar viagem com embarcação inativa.',
  )
  assert.equal(
    traduzirMensagem('Nao e possivel programar viagem com rota sem paradas.'),
    'Não é possível programar viagem com uma rota sem paradas.',
  )
})
