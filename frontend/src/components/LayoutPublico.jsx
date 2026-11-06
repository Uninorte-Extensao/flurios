import Logo from './Logo'
import './LayoutPublico.css'

// Telas sem login (entrar, cadastro): mesmo header azul, conteúdo centralizado.
export default function LayoutPublico({ children }) {
  return (
    <div className="publico">
      <header className="publico__header">
        <Logo />
      </header>
      <main className="publico__conteudo">{children}</main>
    </div>
  )
}
