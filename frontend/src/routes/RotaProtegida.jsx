import { Navigate, Outlet } from 'react-router-dom'
import Carregando from '../components/Carregando'
import { useAuth } from '../hooks/useAuth'
import { caminhoInicial } from './caminhos'

// Só deixa passar quem está logado e é de um dos `tipos` (ex.: ['empresa']).
// Deslogado -> /login. Tipo errado -> área do próprio usuário.
export default function RotaProtegida({ tipos }) {
  const { usuario, carregando } = useAuth()

  if (carregando) return <Carregando />
  if (!usuario) return <Navigate to="/login" replace />
  if (!tipos.includes(usuario.tipo)) return <Navigate to={caminhoInicial(usuario)} replace />

  return <Outlet />
}
