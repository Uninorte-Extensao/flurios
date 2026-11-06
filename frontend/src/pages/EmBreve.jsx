import Card from '../components/Card'

// Página provisória das telas ainda não implementadas.
export default function EmBreve({ titulo }) {
  return (
    <>
      <h1 className="pagina__titulo">{titulo}</h1>
      <p className="pagina__subtitulo">Esta tela ainda está em construção.</p>
      <Card>
        <p className="texto-suave">Em breve você poderá usar esta área.</p>
      </Card>
    </>
  )
}
