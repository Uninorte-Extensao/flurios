import './Card.css'

// Cartão branco com cantos arredondados e sombra leve. `acoes` aparece à direita do título.
export default function Card({ titulo, acoes, className = '', children }) {
  return (
    <section className={`card ${className}`.trim()}>
      {(titulo || acoes) && (
        <header className="card__cabecalho">
          {titulo && <h2 className="card__titulo">{titulo}</h2>}
          {acoes && <div className="card__acoes">{acoes}</div>}
        </header>
      )}
      {children}
    </section>
  )
}
