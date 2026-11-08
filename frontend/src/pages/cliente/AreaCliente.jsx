import { Link } from 'react-router-dom'
import Card from '../../components/Card'
import { useAuth } from '../../hooks/useAuth'
import { saudacao } from '../../utils/nome'

export default function AreaCliente() {
  const { usuario } = useAuth()

  return (
    <>
      <h1 className="pagina__titulo">Visão do Cliente</h1>
      <p className="pagina__subtitulo">Acompanhe suas encomendas.</p>
      <Card titulo={saudacao(usuario.nome)}>
        <p className="texto-suave">
          Cadastre uma encomenda ou acompanhe as que você já enviou. Também dá para digitar um código
          na busca do topo.
        </p>
        <p style={{ marginTop: 'var(--espaco-4)', display: 'flex', flexWrap: 'wrap', gap: 'var(--espaco-3)' }}>
          <Link to="/cliente/nova-encomenda" className="btn btn--primario">
            Nova encomenda
          </Link>
          <Link to="/cliente/encomendas" className="btn btn--contorno">
            Minhas encomendas
          </Link>
        </p>
      </Card>
    </>
  )
}
