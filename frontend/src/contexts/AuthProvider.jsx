import { useCallback, useEffect, useMemo, useState } from 'react'
import { definirAoNaoAutorizado, tokenStorage } from '../services/api'
import { login, obterUsuarioAtual } from '../services/auth'
import { AuthContext } from './auth-context'

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  // Só há o que carregar se existir token guardado.
  const [carregando, setCarregando] = useState(() => Boolean(tokenStorage.obter()))

  const sair = useCallback(() => {
    tokenStorage.remover()
    setUsuario(null)
  }, [])

  const recarregarUsuario = useCallback(async () => {
    const atual = await obterUsuarioAtual()
    setUsuario(atual)
    return atual
  }, [])

  const iniciarSessao = useCallback(
    async (token) => {
      tokenStorage.salvar(token)
      try {
        return await recarregarUsuario()
      } catch (erro) {
        tokenStorage.remover()
        throw erro
      }
    },
    [recarregarUsuario],
  )

  const entrar = useCallback(
    async (email, senha) => iniciarSessao(await login(email, senha)),
    [iniciarSessao],
  )

  // Qualquer 401 da API encerra a sessão local.
  useEffect(() => {
    definirAoNaoAutorizado(sair)
    return () => definirAoNaoAutorizado(null)
  }, [sair])

  // Restaura a sessão a partir do token guardado.
  useEffect(() => {
    if (!tokenStorage.obter()) return

    let ativo = true
    obterUsuarioAtual()
      .then((atual) => ativo && setUsuario(atual))
      .catch(() => ativo && sair())
      .finally(() => ativo && setCarregando(false))

    return () => {
      ativo = false
    }
  }, [sair])

  const valor = useMemo(
    () => ({ usuario, carregando, entrar, sair, iniciarSessao, recarregarUsuario }),
    [usuario, carregando, entrar, sair, iniciarSessao, recarregarUsuario],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}
