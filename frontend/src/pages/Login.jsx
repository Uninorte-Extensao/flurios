import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Alerta from '../components/Alerta'
import Card from '../components/Card'
import CampoTexto from '../components/CampoTexto'
import { useAuth } from '../hooks/useAuth'
import { caminhoInicial } from '../routes/caminhos'
import { emailValido } from '../utils/validacao'
import './Auth.css'

function validar({ email, senha }) {
  const erros = {}
  if (!email.trim()) erros.email = 'Informe o e-mail.'
  else if (!emailValido(email)) erros.email = 'Informe um e-mail válido.'
  if (!senha) erros.senha = 'Informe a senha.'
  return erros
}

export default function Login() {
  const { entrar } = useAuth()
  const navegar = useNavigate()
  const [campos, setCampos] = useState({ email: '', senha: '' })
  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState('')
  const [enviando, setEnviando] = useState(false)

  function alterar(evento) {
    const { name, value } = evento.target
    setCampos((atual) => ({ ...atual, [name]: value }))
    setErros((atual) => ({ ...atual, [name]: undefined }))
  }

  async function enviar(evento) {
    evento.preventDefault()
    setErroGeral('')

    const errosEncontrados = validar(campos)
    setErros(errosEncontrados)
    if (Object.keys(errosEncontrados).length > 0) return

    setEnviando(true)
    try {
      const usuario = await entrar(campos.email.trim(), campos.senha)
      // Cliente -> /cliente, empresa -> /empresa (conforme GET /usuarios/me).
      navegar(caminhoInicial(usuario), { replace: true })
    } catch (erro) {
      setErroGeral(erro.message)
      setEnviando(false)
    }
  }

  return (
    <Card className="auth-card">
      <h1 className="pagina__titulo">Entrar</h1>
      <p className="pagina__subtitulo">Acesse sua conta para acompanhar as entregas.</p>

      {erroGeral && <Alerta tipo="erro">{erroGeral}</Alerta>}

      <form onSubmit={enviar} noValidate>
        <CampoTexto
          rotulo="E-mail"
          name="email"
          type="email"
          autoComplete="email"
          placeholder="voce@exemplo.com"
          value={campos.email}
          onChange={alterar}
          erro={erros.email}
        />
        <CampoTexto
          rotulo="Senha"
          name="senha"
          type="password"
          autoComplete="current-password"
          value={campos.senha}
          onChange={alterar}
          erro={erros.senha}
        />

        <button type="submit" className="btn btn--primario btn--bloco" disabled={enviando}>
          {enviando ? 'Entrando...' : 'Entrar'}
        </button>
      </form>

      <p className="auth-card__rodape texto-suave">
        Ainda não tem conta? <Link to="/cadastro">Cadastre-se</Link>
      </p>
    </Card>
  )
}
