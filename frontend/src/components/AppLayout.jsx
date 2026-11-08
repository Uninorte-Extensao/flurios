import { Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { caminhoDaBusca } from '../utils/navegacao'
import { capitalizarNome } from '../utils/nome'
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

  // A busca do header serve para achar uma encomenda: o código digitado abre o detalhe dela na área.
  function aoBuscar(texto) {
    const caminho = caminhoDaBusca(area, texto)

    if (caminho) navegar(caminho)
  }

  return (
    <div className="app">
      <Header
        nomeUsuario={capitalizarNome(usuario?.nome)}
        rotuloUsuario={rotuloUsuario}
        placeholderBusca={menu.placeholderBusca}
        aoBuscar={aoBuscar}
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
