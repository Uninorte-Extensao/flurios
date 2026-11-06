import { Navigate, Outlet } from 'react-router-dom'
import Carregando from '../components/Carregando'
import { useAuth } from '../hooks/useAuth'
import { caminhoInicial } from './caminhos'

// Telas de entrada (login/cadastro): quem já está logado vai direto para a própria área.
// `permitirIncompleto` deixa passar o usuário logado sem cadastro completo (tela de cadastro).
export default function RotaPublica({ permitirIncompleto = false }) {
  const { usuario, carregando } = useAuth()

  if (carregando) return <Carregando />
  if (usuario && !(permitirIncompleto && !usuario.tipo)) {
    return <Navigate to={caminhoInicial(usuario)} replace />
  }

  return <Outlet />
}
