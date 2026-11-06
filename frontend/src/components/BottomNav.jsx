import { NavLink } from 'react-router-dom'
import './BottomNav.css'

// Barra inferior do mobile (no web fica oculta; vale o menu lateral).
export default function BottomNav({ itens }) {
  return (
    <nav className="bottomnav" aria-label="Menu principal">
      {itens.map(({ para, rotulo, icone: Icone, exato }) => (
        <NavLink
          key={para}
          to={para}
          end={exato}
          className={({ isActive }) => `bottomnav__item${isActive ? ' bottomnav__item--ativo' : ''}`}
        >
          <Icone size={20} aria-hidden="true" />
          {rotulo}
        </NavLink>
      ))}
    </nav>
  )
}
