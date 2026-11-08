import { useCarga } from '../hooks/useCarga'
import Card from './Card'
import Carregando from './Carregando'
import ErroCarga from './ErroCarga'
import './BlocoCarga.css'

// Bloco de tela com a própria carga: "Carregando...", erro com "Tentar novamente" e vazio ficam
// dentro do cartão, então a falha de um bloco não afeta os outros.
// - `carregar`: função estável (do módulo) que devolve a Promise da API.
// - `estaVazio(dados)`: true quando não há o que mostrar; aí aparece `iconeVazio` + `mensagemVazio`.
// - `semCartao`: no sucesso, desenha os filhos sem o cartão (o filho traz o próprio layout).
// - `children(dados)`: render do conteúdo.
export default function BlocoCarga({
  titulo,
  carregar,
  estaVazio,
  iconeVazio: IconeVazio,
  mensagemVazio,
  semCartao = false,
  className = '',
  children,
}) {
  const { carregando, erro, dados, recarregar } = useCarga(carregar)

  if (!carregando && !erro && semCartao && !estaVazio(dados)) return children(dados)

  return (
    <Card titulo={titulo} className={`bloco ${className}`.trim()}>
      {carregando && <Carregando />}
      {erro && <ErroCarga mensagem={erro.message} aoTentarDeNovo={recarregar} />}
      {!carregando && !erro && estaVazio(dados) && (
        <div className="bloco__vazio">
          {IconeVazio && <IconeVazio size={28} aria-hidden="true" />}
          <p className="texto-suave">{mensagemVazio}</p>
        </div>
      )}
      {!carregando && !erro && !estaVazio(dados) && children(dados)}
    </Card>
  )
}
