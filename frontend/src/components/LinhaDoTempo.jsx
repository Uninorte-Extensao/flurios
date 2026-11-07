import { MapPin } from 'lucide-react'
import { formatarDataHora } from '../utils/data'
import { ordenarHistorico } from '../utils/encomenda'
import StatusBadge from './StatusBadge'
import './LinhaDoTempo.css'

// Histórico de movimentações de uma encomenda (a API manda do mais antigo; aqui o mais recente fica no topo).
export default function LinhaDoTempo({ historico }) {
  const movimentacoes = ordenarHistorico(historico)

  if (movimentacoes.length === 0) {
    return <p className="texto-suave">Ainda não há movimentações registradas.</p>
  }

  return (
    <ol className="linha-do-tempo">
      {movimentacoes.map((m, indice) => (
        <li
          key={m.id}
          className={`linha-do-tempo__item${indice === 0 ? ' linha-do-tempo__item--atual' : ''}`}
        >
          <span className="linha-do-tempo__ponto" aria-hidden="true" />
          <div className="linha-do-tempo__conteudo">
            <StatusBadge status={m.status} />
            {m.parada_nome && (
              <span className="linha-do-tempo__local">
                <MapPin size={14} aria-hidden="true" />
                {m.parada_nome}
              </span>
            )}
            <time className="texto-suave" dateTime={m.criado_em}>
              {formatarDataHora(m.criado_em)}
            </time>
          </div>
        </li>
      ))}
    </ol>
  )
}
