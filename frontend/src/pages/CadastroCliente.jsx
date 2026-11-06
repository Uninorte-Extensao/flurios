import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Alerta from '../components/Alerta'
import Card from '../components/Card'
import CampoTexto from '../components/CampoTexto'
import { useAuth } from '../hooks/useAuth'
import { caminhoInicial } from '../routes/caminhos'
import { cadastrarCliente, cadastrarUsuario } from '../services/auth'
import { cpfValido, formatarCpfDigitado, somenteDigitos } from '../utils/cpf'
import { formatarTelefoneDigitado, telefoneValido } from '../utils/telefone'
import { emailValido } from '../utils/validacao'
import './Auth.css'

const SENHA_MINIMA = 6

const CAMPOS_VAZIOS = {
  nome: '',
  email: '',
  senha: '',
  confirmarSenha: '',
  cpf: '',
  telefone: '',
}

function validar(campos, apenasCompletar) {
  const erros = {}

  if (!apenasCompletar) {
    if (!campos.nome.trim()) erros.nome = 'Informe o nome.'
    if (!campos.email.trim()) erros.email = 'Informe o e-mail.'
    else if (!emailValido(campos.email)) erros.email = 'Informe um e-mail válido.'
    if (!campos.senha) erros.senha = 'Informe a senha.'
    else if (campos.senha.length < SENHA_MINIMA) {
      erros.senha = `A senha deve ter pelo menos ${SENHA_MINIMA} caracteres.`
    }
    if (campos.confirmarSenha !== campos.senha) erros.confirmarSenha = 'As senhas não conferem.'
  }

  if (!campos.cpf.trim()) erros.cpf = 'Informe o CPF.'
  else if (!cpfValido(campos.cpf)) erros.cpf = 'CPF inválido.'

  if (!campos.telefone.trim()) erros.telefone = 'Informe o telefone.'
  else if (!telefoneValido(campos.telefone)) erros.telefone = 'Informe um telefone com DDD.'

  return erros
}

export default function CadastroCliente() {
  const { usuario, entrar, sair, recarregarUsuario } = useAuth()
  const navegar = useNavigate()
  const [campos, setCampos] = useState(CAMPOS_VAZIOS)
  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState('')
  const [enviando, setEnviando] = useState(false)

  // Conta criada, mas sem CPF/telefone (ex.: CPF já usado): só falta completar.
  const apenasCompletar = Boolean(usuario) && !usuario.tipo

  function alterar(evento) {
    const { name, value } = evento.target
    const formatadores = { cpf: formatarCpfDigitado, telefone: formatarTelefoneDigitado }
    const novoValor = formatadores[name] ? formatadores[name](value) : value

    setCampos((atual) => ({ ...atual, [name]: novoValor }))
    setErros((atual) => ({ ...atual, [name]: undefined }))
  }

  async function enviar(evento) {
    evento.preventDefault()
    setErroGeral('')

    const errosEncontrados = validar(campos, apenasCompletar)
    setErros(errosEncontrados)
    if (Object.keys(errosEncontrados).length > 0) return

    setEnviando(true)
    try {
      if (!apenasCompletar) {
        try {
          await cadastrarUsuario({
            nome: campos.nome.trim(),
            email: campos.email.trim(),
            senha: campos.senha,
          })
        } catch (erro) {
          // A única regra de negócio desta etapa é e-mail já cadastrado.
          setErros(erro.status === 400 ? { email: erro.message } : erro.erros)
          if (erro.status !== 400 && Object.keys(erro.erros).length === 0) setErroGeral(erro.message)
          setEnviando(false)
          return
        }
        await entrar(campos.email.trim(), campos.senha)
      }

      try {
        await cadastrarCliente({
          cpf: somenteDigitos(campos.cpf),
          telefone: somenteDigitos(campos.telefone),
        })
      } catch (erro) {
        const porCampo = { ...erro.erros }
        if (erro.status === 400) {
          porCampo[/cpf/i.test(erro.message) ? 'cpf' : 'telefone'] = erro.message
        }
        setErros(porCampo)
        if (Object.keys(porCampo).length === 0) setErroGeral(erro.message)
        setEnviando(false)
        return
      }

      const atual = await recarregarUsuario()
      navegar(caminhoInicial(atual), { replace: true })
    } catch (erro) {
      setErroGeral(erro.message)
      setEnviando(false)
    }
  }

  return (
    <Card className="auth-card">
      <h1 className="pagina__titulo">{apenasCompletar ? 'Complete seu cadastro' : 'Criar conta de cliente'}</h1>
      <p className="pagina__subtitulo">
        {apenasCompletar
          ? 'Sua conta já foi criada. Falta informar CPF e telefone.'
          : 'Cadastre-se para enviar e acompanhar suas encomendas.'}
      </p>

      {erroGeral && <Alerta tipo="erro">{erroGeral}</Alerta>}

      <form onSubmit={enviar} noValidate>
        {!apenasCompletar && (
          <>
            <CampoTexto
              rotulo="Nome completo"
              name="nome"
              autoComplete="name"
              value={campos.nome}
              onChange={alterar}
              erro={erros.nome}
            />
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
            <div className="auth-card__linha">
              <CampoTexto
                rotulo="Senha"
                name="senha"
                type="password"
                autoComplete="new-password"
                value={campos.senha}
                onChange={alterar}
                erro={erros.senha}
              />
              <CampoTexto
                rotulo="Confirmar senha"
                name="confirmarSenha"
                type="password"
                autoComplete="new-password"
                value={campos.confirmarSenha}
                onChange={alterar}
                erro={erros.confirmarSenha}
              />
            </div>
          </>
        )}

        <div className="auth-card__linha">
          <CampoTexto
            rotulo="CPF"
            name="cpf"
            inputMode="numeric"
            autoComplete="off"
            placeholder="000.000.000-00"
            value={campos.cpf}
            onChange={alterar}
            erro={erros.cpf}
          />
          <CampoTexto
            rotulo="Telefone"
            name="telefone"
            type="tel"
            autoComplete="tel"
            placeholder="(92) 99999-0000"
            value={campos.telefone}
            onChange={alterar}
            erro={erros.telefone}
          />
        </div>

        <button type="submit" className="btn btn--primario btn--bloco" disabled={enviando}>
          {enviando ? 'Cadastrando...' : apenasCompletar ? 'Concluir cadastro' : 'Cadastrar'}
        </button>
      </form>

      <p className="auth-card__rodape texto-suave">
        {apenasCompletar ? (
          <button type="button" className="btn btn--contorno" onClick={sair}>
            Sair
          </button>
        ) : (
          <>
            Já tem conta? <Link to="/login">Entrar</Link>
          </>
        )}
      </p>
    </Card>
  )
}
