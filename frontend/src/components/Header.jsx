import { Bell, Search } from 'lucide-react'
import Logo from './Logo'
import './Header.css'

function iniciais(nome) {
  return (nome ?? '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((parte) => parte[0].toUpperCase())
    .join('')
}

// Header azul com logo, busca ao centro, sino e usuário logado à direita.
export default function Header({ nomeUsuario, rotuloUsuario, placeholderBusca = 'Buscar...' }) {
  return (
    <header className="header">
      <Logo />

      <form className="header__busca" role="search" onSubmit={(e) => e.preventDefault()}>
        <Search size={16} aria-hidden="true" />
        <input type="search" placeholder={placeholderBusca} aria-label={placeholderBusca} />
      </form>

      <div className="header__direita">
        <button type="button" className="header__sino" aria-label="Notificações">
          <Bell size={20} />
        </button>

        <div className="header__usuario">
          <span className="header__avatar" aria-hidden="true">
            {iniciais(nomeUsuario)}
          </span>
          <span className="header__usuario-texto">
            <small>{rotuloUsuario}:</small>
            <strong>{nomeUsuario}</strong>
          </span>
        </div>
      </div>
    </header>
  )
}
