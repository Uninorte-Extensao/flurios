import { LogOut } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import './Sidebar.css'

function ItemMenu({ para, rotulo, icone: Icone, exato }) {
  return (
    <NavLink
      to={para}
      end={exato}
      className={({ isActive }) => `sidebar__item${isActive ? ' sidebar__item--ativo' : ''}`}
    >
      <Icone size={18} aria-hidden="true" />
      {rotulo}
    </NavLink>
  )
}

// Menu lateral (web). Item ativo em verde; rodapé com Suporte e Sair.
export default function Sidebar({ itens, suporte, aoSair }) {
  return (
    <aside className="sidebar">
      <nav className="sidebar__nav" aria-label="Menu principal">
        {itens.map((item) => (
          <ItemMenu key={item.para} {...item} />
        ))}
      </nav>

      <div className="sidebar__rodape">
        <ItemMenu {...suporte} />
        <button type="button" className="sidebar__item" onClick={aoSair}>
          <LogOut size={18} aria-hidden="true" />
          Sair
        </button>
      </div>
    </aside>
  )
}
