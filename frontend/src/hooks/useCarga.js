import { useCallback, useEffect, useState } from 'react'

// Carrega dados da API para uma tela. `carregar` precisa ter identidade estável
// (função do módulo ou useCallback), senão a carga se repete a cada render.
// Devolve { carregando, erro, dados, recarregar, definirDados }:
// `definirDados(fn)` atualiza a lista local depois de salvar, sem voltar ao "Carregando...".
export function useCarga(carregar) {
  const [estado, setEstado] = useState({ carregando: true, erro: '', dados: null })
  const [tentativa, setTentativa] = useState(0)

  useEffect(() => {
    let ativo = true

    carregar()
      .then((dados) => ativo && setEstado({ carregando: false, erro: '', dados }))
      .catch((erro) => ativo && setEstado({ carregando: false, erro, dados: null }))

    return () => {
      ativo = false
    }
  }, [carregar, tentativa])

  const recarregar = useCallback(() => {
    setEstado((atual) => ({ ...atual, carregando: true, erro: '' }))
    setTentativa((n) => n + 1)
  }, [])

  const definirDados = useCallback((atualizar) => {
    setEstado((atual) => ({ ...atual, dados: atualizar(atual.dados) }))
  }, [])

  // `erro` é o ApiError (tem `.message` em português e `.status`).
  return { ...estado, recarregar, definirDados }
}
