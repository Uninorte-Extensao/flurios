/* global process, console */
// Sobe backend e frontend em portas livres, com banco temporario, roda o Playwright e derruba tudo.
// Nao toca no flurios.db nem nas portas 8000/5173.
import { spawn, spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, mkdtempSync, rmSync, statSync } from 'node:fs'
import net from 'node:net'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const AQUI = path.dirname(fileURLToPath(import.meta.url))
const FRONTEND = path.resolve(AQUI, '..')
const BACKEND = path.resolve(FRONTEND, '..', 'backend')
const PYTHON = path.join(BACKEND, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
const BANCO_DO_USUARIO = path.join(BACKEND, 'flurios.db')

const ADMIN_EMAIL = 'admin@flurios.com'
const ADMIN_SENHA = 'senha123'
const SECRET_KEY = 'chave-e2e-nao-usar-em-producao'

function portaLivre() {
  return new Promise((resolver, rejeitar) => {
    const servidor = net.createServer()
    servidor.once('error', rejeitar)
    servidor.listen(0, '127.0.0.1', () => {
      const { port } = servidor.address()
      servidor.close(() => resolver(port))
    })
  })
}

async function esperar(url, rotulo, tentativas = 120) {
  for (let i = 0; i < tentativas; i++) {
    try {
      const resposta = await fetch(url)
      if (resposta.status < 500) return
    } catch {
      // ainda subindo
    }
    await new Promise((r) => setTimeout(r, 500))
  }
  throw new Error(`${rotulo} nao respondeu em ${url}`)
}

function encerrar(processo) {
  if (!processo || processo.exitCode !== null) return
  if (process.platform === 'win32') spawnSync('taskkill', ['/pid', String(processo.pid), '/T', '/F'])
  else processo.kill('SIGTERM')
}

if (!existsSync(PYTHON)) {
  console.error(`Python do backend nao encontrado em ${PYTHON}. Crie o .venv (ver README).`)
  process.exit(1)
}

const marcaBanco = existsSync(BANCO_DO_USUARIO) ? statSync(BANCO_DO_USUARIO).mtimeMs : null
const pasta = mkdtempSync(path.join(tmpdir(), 'flurios-e2e-'))
const banco = path.join(pasta, 'e2e.db')
const portaApi = await portaLivre()
const portaFront = await portaLivre()
const urlApi = `http://127.0.0.1:${portaApi}`
const urlFront = `http://127.0.0.1:${portaFront}`
const saida = process.env.E2E_SAIDA || path.resolve(FRONTEND, '..', 'docs', 'prints-teste', 'e2e')
mkdirSync(saida, { recursive: true })

const filhos = []
let codigo = 1

try {
  console.log(`[e2e] banco temporario: ${banco}`)
  console.log(`[e2e] API ${urlApi} | frontend ${urlFront}`)

  const preparo = spawnSync(PYTHON, [path.join(AQUI, 'preparar_banco.py'), banco, ADMIN_EMAIL, ADMIN_SENHA], {
    cwd: BACKEND,
    env: { ...process.env, PYTHONPATH: BACKEND, SECRET_KEY },
    encoding: 'utf-8',
  })
  if (preparo.status !== 0) throw new Error(`Falha ao preparar o banco:\n${preparo.stdout}\n${preparo.stderr}`)

  const api = spawn(PYTHON, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(portaApi)], {
    cwd: BACKEND,
    env: { ...process.env, DATABASE_URL: `sqlite:///${banco.replaceAll('\\', '/')}`, SECRET_KEY },
    stdio: 'ignore',
  })
  filhos.push(api)
  await esperar(`${urlApi}/health`, 'API')

  const vite = spawn(
    process.execPath,
    [path.join(FRONTEND, 'node_modules', 'vite', 'bin', 'vite.js'), '--config', path.join(AQUI, 'vite.e2e.config.js')],
    {
      cwd: FRONTEND,
      env: { ...process.env, VITE_API_URL: '/api', E2E_FRONT_PORT: String(portaFront), E2E_API_URL: urlApi },
      stdio: 'ignore',
    },
  )
  filhos.push(vite)
  await esperar(urlFront, 'Frontend')

  const playwright = spawnSync(
    process.execPath,
    [path.join(FRONTEND, 'node_modules', '@playwright', 'test', 'cli.js'), 'test', ...process.argv.slice(2)],
    {
      cwd: FRONTEND,
      stdio: 'inherit',
      env: {
        ...process.env,
        E2E_FRONT_URL: urlFront,
        E2E_API_DIRETA: urlApi,
        E2E_ADMIN_EMAIL: ADMIN_EMAIL,
        E2E_ADMIN_SENHA: ADMIN_SENHA,
        E2E_SAIDA: saida,
        E2E_TEMP: pasta,
      },
    },
  )
  codigo = playwright.status ?? 1
} catch (erro) {
  console.error(`[e2e] ${erro.message}`)
} finally {
  filhos.forEach(encerrar)
  rmSync(pasta, { recursive: true, force: true })
  const depois = existsSync(BANCO_DO_USUARIO) ? statSync(BANCO_DO_USUARIO).mtimeMs : null
  console.log(`[e2e] flurios.db ${marcaBanco === depois ? 'intacto' : 'ALTERADO (investigar!)'}`)
}

process.exit(codigo)
