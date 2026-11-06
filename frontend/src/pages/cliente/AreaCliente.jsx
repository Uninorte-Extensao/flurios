import { Link } from 'react-router-dom'
import Card from '../../components/Card'
import { useAuth } from '../../hooks/useAuth'

// Provisório: "meus códigos" e a linha do tempo de rastreio vêm na tarefa F.4.
export default function AreaCliente() {
  const { usuario } = useAuth()

  return (
    <>
      <h1 className="pagina__titulo">Visão do Cliente</h1>
      <p className="pagina__subtitulo">Acompanhe suas encomendas.</p>
      <Card titulo={`Olá, ${usuario.nome}`}>
        <p className="texto-suave">Você está na área do cliente. Suas encomendas aparecerão aqui.</p>
        <p style={{ marginTop: 'var(--espaco-4)' }}>
          <Link to="/cliente/nova-encomenda" className="btn btn--primario">
            Nova encomenda
          </Link>
        </p>
      </Card>
    </>
  )
}
