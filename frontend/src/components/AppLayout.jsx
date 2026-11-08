import { Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { normalizarCodigo } from '../utils/encomenda'
import { itensDoMenuParaUsuario } from '../utils/perfil'
import { MENUS, ROTULOS_PERFIL_EMPRESA } from '../routes/menus'
import BottomNav from './BottomNav'
import Header from './Header'
import Sidebar from './Sidebar'
import './AppLayout.css'

// Estrutura das áreas logadas: header + menu lateral (web) / barra inferior (mobile) + conteúdo.
export default function AppLayout({ area }) {
  const menu = MENUS[area]
  const { usuario, sair } = useAuth()
  const navegar = useNavigate()

  const rotuloUsuario =
    area === 'empresa'
      ? (ROTULOS_PERFIL_EMPRESA[usuario?.perfil] ?? menu.rotuloUsuario)
      : menu.rotuloUsuario

  function aoSair() {
    sair()
    navegar('/login', { replace: true })
  }

  // Só o cliente tem busca funcional por enquanto: o código digitado abre o detalhe da encomenda.
  function aoBuscar(texto) {
    navegar(`/cliente/encomendas/${encodeURIComponent(normalizarCodigo(texto))}`)
  }

  return (
    <div className="app">
      <Header
        nomeUsuario={usuario?.nome}
        rotuloUsuario={rotuloUsuario}
        placeholderBusca={menu.placeholderBusca}
        aoBuscar={area === 'cliente' ? aoBuscar : undefined}
      />
      <div className="app__corpo">
        <Sidebar itens={itensDoMenuParaUsuario(menu.itens, usuario)} suporte={menu.suporte} aoSair={aoSair} />
        <main className="app__conteudo">
          <Outlet />
        </main>
      </div>
      <BottomNav
        itens={itensDoMenuParaUsuario(menu.barraInferior, usuario)}
        suporte={menu.suporte}
        aoSair={aoSair}
      />
    </div>
  )
}
