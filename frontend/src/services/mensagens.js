// Mensagens da API chegam sem acentuação; aqui ficam as versões para a interface.
const TRADUCOES = {
  'E-mail ou senha invalidos.': 'E-mail ou senha inválidos.',
  'E-mail já cadastrado.': 'Este e-mail já está cadastrado.',
  'CPF ja cadastrado.': 'Este CPF já está cadastrado.',
  'CPF invalido.': 'CPF inválido.',
  'Usuario ja possui cadastro de cliente.': 'Este usuário já possui cadastro de cliente.',
  'Usuario ja possui cadastro de empresa.': 'Este usuário já possui cadastro de empresa.',
  'Usuario nao possui cadastro de cliente.': 'Esta conta não é de cliente.',
  'Usuario nao possui cadastro de empresa.': 'Esta conta não é de empresa.',
  'Nao foi possivel validar as credenciais.': 'Sua sessão expirou. Entre novamente.',
  'Acao restrita a administradores.': 'Ação restrita a administradores.',
  'Embarcacao nao encontrada.': 'Embarcação não encontrada.',
  'Rota nao encontrada.': 'Rota não encontrada.',
  'Parada nao encontrada.': 'Parada não encontrada.',
  'Nao e possivel remover uma parada que e destino de encomendas.':
    'Não é possível remover uma parada que é destino de encomendas.',
  'Ja existe uma parada com essa ordem na rota.': 'Já existe uma parada com essa ordem nesta rota.',
  'Destinatario nao encontrado.': 'Destinatário não encontrado.',
  'Parada de destino nao encontrada.': 'O destino escolhido não existe mais. Atualize a página.',
  'A parada de origem nao pode ser o destino da encomenda.':
    'A origem (Manaus) não pode ser o destino da encomenda.',
  'Encomenda nao encontrada.': 'Encomenda não encontrada.',
  'Viagem nao encontrada.': 'Viagem não encontrada.',
  'So e possivel registrar localizacao em viagem em andamento.':
    'Só é possível registrar a localização de uma viagem em andamento.',
  'A parada nao pertence a rota da viagem.': 'Esta parada não pertence à rota da viagem.',
  'Informe nome e cpf da pessoa autorizada.': 'Informe o nome e o CPF da pessoa autorizada.',
  'Encomenda ja entregue: nao e possivel cadastrar pessoa autorizada.':
    'Esta encomenda já foi entregue: não é possível cadastrar pessoa autorizada.',
  'A encomenda ja esta a retirar: nao e possivel trocar a pessoa autorizada.':
    'Esta encomenda já está a retirar: não é possível trocar a pessoa autorizada.',
}

const STATUS_VIAGEM = {
  programada: 'programada',
  em_andamento: 'em andamento',
  concluida: 'concluída',
  cancelada: 'cancelada',
}

// "Transicao de status invalida: programada -> concluida." (a mensagem leva os dois status)
const TRANSICAO_VIAGEM = /^Transicao de status invalida: (\w+) -> (\w+)\.$/

export function traduzirMensagem(texto, padrao) {
  const limpo = String(texto).replace(/^Value error, /, '')

  const transicao = TRANSICAO_VIAGEM.exec(limpo)
  if (transicao && transicao[1] in STATUS_VIAGEM && transicao[2] in STATUS_VIAGEM) {
    return `Não é possível mudar a viagem de ${STATUS_VIAGEM[transicao[1]]} para ${STATUS_VIAGEM[transicao[2]]}.`
  }

  return TRADUCOES[limpo] ?? padrao ?? limpo
}
