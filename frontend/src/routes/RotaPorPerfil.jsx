import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { caminhoInicial } from './caminhos'

// Dentro de uma área já protegida: só deixa passar quem tem um dos `perfis` da empresa.
// Os demais voltam para o início da própria área. SÓ NA TELA: o backend não restringe por perfil.
export default function RotaPorPerfil({ perfis }) {
  const { usuario } = useAuth()

  if (!perfis.includes(usuario?.perfil)) return <Navigate to={caminhoInicial(usuario)} replace />

  return <Outlet />
}
