// Área inicial de cada tipo de usuário (resposta de GET /usuarios/me).
export function caminhoInicial(usuario) {
  if (usuario?.tipo === 'empresa') return '/empresa'
  if (usuario?.tipo === 'cliente') return '/cliente'
  // Logado, mas sem cadastro de cliente/empresa: precisa completar o cadastro.
  if (usuario) return '/cadastro'
  return '/login'
}
