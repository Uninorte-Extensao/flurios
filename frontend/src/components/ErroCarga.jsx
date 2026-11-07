import Alerta from './Alerta'

// Falha ao carregar uma tela, com botão para tentar de novo.
export default function ErroCarga({ mensagem, aoTentarDeNovo }) {
  return (
    <Alerta tipo="erro">
      {mensagem}{' '}
      <button type="button" className="btn btn--contorno" onClick={aoTentarDeNovo}>
        Tentar novamente
      </button>
    </Alerta>
  )
}
