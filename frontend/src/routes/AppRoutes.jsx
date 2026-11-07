import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from '../components/AppLayout'
import Carregando from '../components/Carregando'
import LayoutPublico from '../components/LayoutPublico'
import { useAuth } from '../hooks/useAuth'
import CadastroCliente from '../pages/CadastroCliente'
import AreaCliente from '../pages/cliente/AreaCliente'
import DetalheEncomenda from '../pages/cliente/DetalheEncomenda'
import MinhasEncomendas from '../pages/cliente/MinhasEncomendas'
import NovaEncomenda from '../pages/cliente/NovaEncomenda'
import EmBreve from '../pages/EmBreve'
import DetalheRota from '../pages/empresa/DetalheRota'
import Embarcacoes from '../pages/empresa/Embarcacoes'
import PainelOperacional from '../pages/empresa/PainelOperacional'
import Rotas from '../pages/empresa/Rotas'
import Login from '../pages/Login'
import { caminhoInicial } from './caminhos'
import RotaProtegida from './RotaProtegida'
import RotaPublica from './RotaPublica'

// Vitrine do design system: só existe no ambiente de desenvolvimento.
const DesignSystem = import.meta.env.DEV ? lazy(() => import('../pages/DesignSystem')) : null

function Inicio() {
  const { usuario, carregando } = useAuth()

  if (carregando) return <Carregando />

  return <Navigate to={caminhoInicial(usuario)} replace />
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Inicio />} />

      <Route element={<RotaPublica />}>
        <Route
          path="/login"
          element={
            <LayoutPublico>
              <Login />
            </LayoutPublico>
          }
        />
      </Route>

      <Route element={<RotaPublica permitirIncompleto />}>
        <Route
          path="/cadastro"
          element={
            <LayoutPublico>
              <CadastroCliente />
            </LayoutPublico>
          }
        />
      </Route>

      <Route element={<RotaProtegida tipos={['empresa']} />}>
        <Route path="/empresa" element={<AppLayout area="empresa" />}>
          <Route index element={<PainelOperacional />} />
          <Route path="embarcacoes" element={<Embarcacoes />} />
          <Route path="rotas" element={<Rotas />} />
          <Route path="rotas/:rotaId" element={<DetalheRota />} />
          <Route path="viagens" element={<EmBreve titulo="Viagens" />} />
          <Route path="encomendas" element={<EmBreve titulo="Encomendas" />} />
          <Route path="dashboard" element={<EmBreve titulo="Dashboard" />} />
          <Route path="suporte" element={<EmBreve titulo="Suporte" />} />
        </Route>
      </Route>

      <Route element={<RotaProtegida tipos={['cliente']} />}>
        <Route path="/cliente" element={<AppLayout area="cliente" />}>
          <Route index element={<AreaCliente />} />
          <Route path="nova-encomenda" element={<NovaEncomenda />} />
          <Route path="encomendas" element={<MinhasEncomendas />} />
          <Route path="encomendas/:codigo" element={<DetalheEncomenda />} />
          <Route path="suporte" element={<EmBreve titulo="Suporte" />} />
        </Route>
      </Route>

      {DesignSystem && (
        <Route
          path="/design-system"
          element={
            <Suspense fallback={<Carregando />}>
              <DesignSystem />
            </Suspense>
          }
        />
      )}

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
