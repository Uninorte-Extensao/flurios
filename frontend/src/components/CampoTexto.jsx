import { useId } from 'react'

// Campo de formulário com rótulo, ajuda e mensagem de erro.
export default function CampoTexto({ rotulo, erro, ajuda, ...props }) {
  const id = useId()
  const idMensagem = `${id}-msg`

  return (
    <div className={`campo${erro ? ' campo--erro' : ''}`}>
      <label className="campo__rotulo" htmlFor={id}>
        {rotulo}
      </label>
      <input
        id={id}
        className="campo__entrada"
        aria-invalid={erro ? 'true' : undefined}
        aria-describedby={erro || ajuda ? idMensagem : undefined}
        {...props}
      />
      {erro ? (
        <span id={idMensagem} className="campo__erro" role="alert">
          {erro}
        </span>
      ) : (
        ajuda && (
          <span id={idMensagem} className="campo__ajuda">
            {ajuda}
          </span>
        )
      )}
    </div>
  )
}
