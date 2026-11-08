import { Bell, Search } from 'lucide-react'
import { useState } from 'react'
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
// `aoBuscar(texto)` é chamado ao enviar a busca (Enter) com texto preenchido; sem ele, a busca não faz nada.
export default function Header({ nomeUsuario, rotuloUsuario, placeholderBusca = 'Buscar...', aoBuscar }) {
  const [busca, setBusca] = useState('')

  function enviarBusca(evento) {
    evento.preventDefault()

    const texto = busca.trim()
    if (!aoBuscar || !texto) return

    aoBuscar(texto)
    setBusca('')
  }

  return (
    <header className="header">
      <Logo />

      <form className="header__busca" role="search" onSubmit={enviarBusca}>
        <Search size={16} aria-hidden="true" />
        <input
          type="search"
          placeholder={placeholderBusca}
          aria-label={placeholderBusca}
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
        />
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
            <strong title={nomeUsuario}>{nomeUsuario}</strong>
          </span>
        </div>
      </div>
    </header>
  )
}
