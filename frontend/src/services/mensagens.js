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
  'Informe nome e cpf da pessoa autorizada.': 'Informe o nome e o CPF da pessoa autorizada.',
  'Encomenda ja entregue: nao e possivel cadastrar pessoa autorizada.':
    'Esta encomenda já foi entregue: não é possível cadastrar pessoa autorizada.',
  'A encomenda ja esta a retirar: nao e possivel trocar a pessoa autorizada.':
    'Esta encomenda já está a retirar: não é possível trocar a pessoa autorizada.',
}

export function traduzirMensagem(texto, padrao) {
  const limpo = String(texto).replace(/^Value error, /, '')
  return TRADUCOES[limpo] ?? padrao ?? limpo
}
