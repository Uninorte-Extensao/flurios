import { useEffect, useState } from "react";

function App() {
  const [status, setStatus] = useState("Verificando API...");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/health")
      .then((resposta) => resposta.json())
      .then((dados) => {
        setStatus(`${dados.status} - ${dados.sistema}`);
      })
      .catch(() => {
        setStatus("API offline");
      });
  }, []);

  return (
    <div>
      <h1>Flurios</h1>
      <p>Sistema de gerenciamento e rastreamento de entregas fluviais.</p>

      <h2>Status da API</h2>
      <p>{status}</p>
    </div>
  );
}

export default App;