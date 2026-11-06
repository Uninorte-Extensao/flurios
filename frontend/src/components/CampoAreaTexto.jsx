import { useId } from 'react'

// Campo de texto de várias linhas (mesmo visual do CampoTexto).
export default function CampoAreaTexto({ rotulo, erro, ajuda, ...props }) {
  const id = useId()
  const idMensagem = `${id}-msg`

  return (
    <div className={`campo${erro ? ' campo--erro' : ''}`}>
      <label className="campo__rotulo" htmlFor={id}>
        {rotulo}
      </label>
      <textarea
        id={id}
        className="campo__entrada campo__entrada--area"
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
