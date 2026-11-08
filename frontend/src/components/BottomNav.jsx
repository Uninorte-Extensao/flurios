import { Ellipsis, LogOut } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { matchPath, NavLink, useLocation } from 'react-router-dom'
import { dividirItensDaBarra } from '../utils/navegacao'
import './BottomNav.css'

function classeDoItem({ isActive }) {
  return `bottomnav__item${isActive ? ' bottomnav__item--ativo' : ''}`
}

function classeDaOpcao({ isActive }) {
  return `bottomnav__opcao${isActive ? ' bottomnav__opcao--ativa' : ''}`
}

// Barra inferior do mobile (no web fica oculta; vale o menu lateral).
// Até 4 itens fixos; o que passar disso, mais Suporte e Sair (que no mobile não têm outro lugar,
// pois o menu lateral some), abre no botão "Mais".
export default function BottomNav({ itens, suporte, aoSair }) {
  const { fixos, extras } = dividirItensDaBarra(itens)
  const { pathname } = useLocation()
  // Guarda a rota em que o "Mais" foi aberto: ao navegar (inclusive voltar do navegador) ele fecha sozinho.
  const [abertoEm, setAbertoEm] = useState(null)
  const botaoRef = useRef(null)
  const folhaRef = useRef(null)

  const temMais = extras.length > 0
  const aberto = temMais && abertoEm === pathname
  const destinosDoMais = suporte ? [...extras, suporte] : extras
  const ativoNoMais = destinosDoMais.some((item) => matchPath({ path: item.para, end: Boolean(item.exato) }, pathname))

  useEffect(() => {
    if (!aberto) return undefined

    folhaRef.current?.querySelector('a, button')?.focus()

    function aoTeclar(evento) {
      if (evento.key !== 'Escape') return

      setAbertoEm(null)
      botaoRef.current?.focus()
    }

    document.addEventListener('keydown', aoTeclar)
    return () => document.removeEventListener('keydown', aoTeclar)
  }, [aberto])

  function sair() {
    setAbertoEm(null)
    aoSair?.()
  }

  return (
    <nav className="bottomnav" aria-label="Menu principal">
      {fixos.map(({ para, rotulo, icone: Icone, exato }) => (
        <NavLink key={para} to={para} end={exato} className={classeDoItem}>
          <Icone size={20} aria-hidden="true" />
          {rotulo}
        </NavLink>
      ))}

      {temMais && (
        <button
          ref={botaoRef}
          type="button"
          className={`bottomnav__item${aberto || ativoNoMais ? ' bottomnav__item--ativo' : ''}`}
          aria-expanded={aberto}
          aria-controls="bottomnav-mais"
          onClick={() => setAbertoEm(aberto ? null : pathname)}
        >
          <Ellipsis size={20} aria-hidden="true" />
          Mais
        </button>
      )}

      {aberto && (
        <>
          <div className="bottomnav__fundo" onClick={() => setAbertoEm(null)} aria-hidden="true" />
          <div id="bottomnav-mais" ref={folhaRef} className="bottomnav__folha" role="group" aria-label="Mais opções">
            {extras.map(({ para, rotulo, icone: Icone, exato }) => (
              <NavLink key={para} to={para} end={exato} className={classeDaOpcao}>
                <Icone size={18} aria-hidden="true" />
                {rotulo}
              </NavLink>
            ))}

            {(suporte || aoSair) && <hr className="bottomnav__divisor" />}

            {suporte && (
              <NavLink to={suporte.para} className={classeDaOpcao}>
                <suporte.icone size={18} aria-hidden="true" />
                {suporte.rotulo}
              </NavLink>
            )}
            {aoSair && (
              <button type="button" className="bottomnav__opcao" onClick={sair}>
                <LogOut size={18} aria-hidden="true" />
                Sair
              </button>
            )}
          </div>
        </>
      )}
    </nav>
  )
}
