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
  'Destinatario nao encontrado.': 'Destinatário não encontrado.',
  'Parada de destino nao encontrada.': 'O destino escolhido não existe mais. Atualize a página.',
  'A parada de origem nao pode ser o destino da encomenda.':
    'A origem (Manaus) não pode ser o destino da encomenda.',
}

export function traduzirMensagem(texto, padrao) {
  const limpo = String(texto).replace(/^Value error, /, '')
  return TRADUCOES[limpo] ?? padrao ?? limpo
}
