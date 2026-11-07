// Só o administrador cria e edita embarcações e rotas; os demais perfis da empresa só consultam.
// `usuario` é a resposta de GET /usuarios/me.
export function ehAdministrador(usuario) {
  return usuario?.tipo === 'empresa' && usuario?.perfil === 'administrador'
}
