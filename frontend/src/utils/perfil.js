// Só o administrador cria e edita embarcações e rotas; os demais perfis da empresa só consultam.
// `usuario` é a resposta de GET /usuarios/me.
export function ehAdministrador(usuario) {
  return usuario?.tipo === 'empresa' && usuario?.perfil === 'administrador'
}

// Itens de menu com `perfis` (lista de perfis da empresa) só aparecem para esses perfis;
// os sem `perfis` aparecem para todos. SÓ NA TELA: o backend não restringe por perfil.
export function itensDoMenuParaUsuario(itens, usuario) {
  return itens.filter((item) => !item.perfis || item.perfis.includes(usuario?.perfil))
}
