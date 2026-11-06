import './Tabela.css'

// colunas: [{ chave, titulo, render?: (linha) => node }]
export default function Tabela({ colunas, linhas, chaveLinha = 'id', vazio = 'Nenhum registro encontrado.' }) {
  return (
    <div className="tabela__rolagem">
      <table className="tabela">
        <thead>
          <tr>
            {colunas.map((coluna) => (
              <th key={coluna.chave} scope="col">
                {coluna.titulo}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {linhas.length === 0 ? (
            <tr>
              <td className="tabela__vazio" colSpan={colunas.length}>
                {vazio}
              </td>
            </tr>
          ) : (
            linhas.map((linha) => (
              <tr key={linha[chaveLinha]}>
                {colunas.map((coluna) => (
                  <td key={coluna.chave}>{coluna.render ? coluna.render(linha) : linha[coluna.chave]}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
