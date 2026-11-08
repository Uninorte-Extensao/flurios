/* global process */
import { mkdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'

export const SAIDA = process.env.E2E_SAIDA
export const API_DIRETA = process.env.E2E_API_DIRETA

export const DESKTOP = { width: 1440, height: 900 }
export const MOBILE = { width: 360, height: 740 }

// Achados automáticos (texto, visual e dados) para o relatório. Gravados no fim da bateria.
export const achados = []
export const respostasComErro = []
export const errosDeConsole = []

let contador = 0

export function proximoNumero() {
  contador += 1
  return String(contador).padStart(2, '0')
}

// ------------------------------------------------------------------ API direta (só para montar a massa)
export async function chamarApi(metodo, caminho, corpo, token) {
  const resposta = await fetch(`${API_DIRETA}${caminho}`, {
    method: metodo,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: corpo ? JSON.stringify(corpo) : undefined,
  })
  const texto = await resposta.text()
  try {
    return { status: resposta.status, dados: texto ? JSON.parse(texto) : null }
  } catch {
    return { status: resposta.status, dados: texto }
  }
}

export async function loginApi(email, senha) {
  const { status, dados } = await chamarApi('POST', '/usuarios/login', { email, senha })
  if (status !== 200) throw new Error(`login via API falhou para ${email}: ${status}`)
  return dados.access_token
}

// ------------------------------------------------------------------ observação da página
export function observar(page, papel) {
  page.on('console', (mensagem) => {
    if (mensagem.type() === 'error') {
      errosDeConsole.push({ papel, url: page.url(), texto: mensagem.text().slice(0, 300) })
    }
  })
  page.on('pageerror', (erro) => {
    errosDeConsole.push({ papel, url: page.url(), texto: `pageerror: ${String(erro.message).slice(0, 300)}` })
  })
  page.on('response', (resposta) => {
    if (resposta.status() >= 400) {
      respostasComErro.push({
        papel,
        pagina: page.url(),
        metodo: resposta.request().method(),
        url: resposta.url().replace(/^https?:\/\/[^/]+/, ''),
        status: resposta.status(),
      })
    }
  })
}

// ------------------------------------------------------------------ inspeção automática de cada tela
const PALAVRAS_SEM_ACENTO = [
  'nao', 'voce', 'informacao', 'informacoes', 'descricao', 'embarcacao', 'embarcacoes', 'localizacao',
  'concluida', 'municipio', 'municipios', 'destinatario', 'codigo', 'endereco', 'previsao', 'ocupacao',
  'movimentacao', 'movimentacoes', 'transito', 'invalido', 'invalida', 'obrigatorio', 'proxima', 'ultima',
  'ja', 'tambem', 'numero', 'saida', 'operacao', 'situacao', 'atencao', 'ate', 'sao', 'sera',
]

function inspecionarNoNavegador(palavras) {
  const resultado = []
  const visivel = (el) => {
    const r = el.getBoundingClientRect()
    const estilo = getComputedStyle(el)
    return r.width > 0 && r.height > 0 && estilo.visibility !== 'hidden' && estilo.display !== 'none'
  }
  const descrever = (el) => {
    const texto = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 60)
    const classe = typeof el.className === 'string' ? el.className.split(' ')[0] : ''
    return `<${el.tagName.toLowerCase()}${classe ? '.' + classe : ''}> "${texto}"`
  }

  // 1. rolagem horizontal da página
  const raiz = document.documentElement
  if (raiz.scrollWidth > raiz.clientWidth + 1) {
    resultado.push({
      tipo: 'visual',
      detalhe: `A página rola na horizontal (largura do conteúdo ${raiz.scrollWidth}px > janela ${raiz.clientWidth}px).`,
    })
  }

  // 2. elementos que estouram a janela ou têm texto cortado
  const limite = window.innerWidth
  const estourando = []
  const cortados = []
  for (const el of document.body.querySelectorAll('*')) {
    if (!visivel(el)) continue
    const r = el.getBoundingClientRect()
    const estilo = getComputedStyle(el)

    let dentroDeRolagem = false
    for (let pai = el.parentElement; pai && pai !== document.body; pai = pai.parentElement) {
      const ox = getComputedStyle(pai).overflowX
      if ((ox === 'auto' || ox === 'scroll') && pai.scrollWidth > pai.clientWidth) {
        dentroDeRolagem = true
        break
      }
    }

    if (!dentroDeRolagem && r.right > limite + 1 && el.children.length === 0 && (el.innerText || '').trim()) {
      estourando.push(descrever(el))
    }

    const corta = ['hidden', 'clip'].includes(estilo.overflowX) || estilo.textOverflow === 'ellipsis'
    if (corta && el.scrollWidth > el.clientWidth + 1 && (el.innerText || '').trim() && el.tagName !== 'SELECT') {
      cortados.push(`${descrever(el)} (${el.scrollWidth}px de texto em ${el.clientWidth}px)`)
    }
  }
  if (estourando.length) {
    resultado.push({ tipo: 'visual', detalhe: `Texto fora da janela (${estourando.length}): ${estourando.slice(0, 4).join(' | ')}` })
  }
  if (cortados.length) {
    resultado.push({ tipo: 'visual', detalhe: `Texto cortado (${cortados.length}): ${cortados.slice(0, 4).join(' | ')}` })
  }

  // 3. selects com a opção escolhida cortada
  const tela = document.createElement('canvas').getContext('2d')
  for (const select of document.querySelectorAll('select')) {
    if (!visivel(select) || select.selectedIndex < 0) continue
    const estilo = getComputedStyle(select)
    tela.font = `${estilo.fontWeight} ${estilo.fontSize} ${estilo.fontFamily}`
    const largura = tela.measureText(select.options[select.selectedIndex].text).width
    const util = select.clientWidth - parseFloat(estilo.paddingLeft) - parseFloat(estilo.paddingRight)
    if (largura > util + 1) {
      resultado.push({
        tipo: 'visual',
        detalhe: `Select com texto cortado: "${select.options[select.selectedIndex].text}" (${Math.round(largura)}px em ${Math.round(util)}px)`,
      })
    }
  }

  // 4. imagens quebradas
  for (const img of document.querySelectorAll('img')) {
    if (visivel(img) && img.complete && img.naturalWidth === 0) {
      resultado.push({ tipo: 'visual', detalhe: `Imagem quebrada: ${img.getAttribute('src')}` })
    }
  }

  // 5. texto visível: valores técnicos, traduções e acentos
  const textos = (document.body.innerText || '').split('\n').map((l) => l.trim()).filter(Boolean)
  const atributos = []
  for (const el of document.querySelectorAll('[placeholder],[title],[aria-label],[alt]')) {
    if (!visivel(el)) continue
    for (const nome of ['placeholder', 'title', 'aria-label', 'alt']) {
      const valor = el.getAttribute(nome)
      if (valor) atributos.push(valor)
    }
  }
  const todos = [...textos, ...atributos]

  const tecnicos = /\b(undefined|null|NaN|Invalid Date|\[object Object\]|Infinity)\b/
  const ingles = /\b(Loading|Error|Submit|Cancel|Delete|Save|Search|Unauthorized|Forbidden|Not Found|Failed|Please|Required|Invalid|Success|Welcome|Dashboard Overview)\b/
  const semAcento = new RegExp(`\\b(${palavras.join('|')})\\b`, 'i')

  for (const linha of todos) {
    if (tecnicos.test(linha)) resultado.push({ tipo: 'dados', detalhe: `Valor técnico exposto na tela: "${linha.slice(0, 100)}"` })
    if (ingles.test(linha)) resultado.push({ tipo: 'texto', detalhe: `Texto em inglês: "${linha.slice(0, 100)}"` })
    if (!linha.includes('@') && semAcento.test(linha)) resultado.push({ tipo: 'texto', detalhe: `Possível palavra sem acento: "${linha.slice(0, 100)}"` })
  }

  // 6. dados ausentes: "—" e células vazias
  const traços = todos.filter((l) => /(^|\s)—(\s|$)/.test(l))
  if (traços.length) {
    resultado.push({ tipo: 'dados', detalhe: `Valor "—" exibido (${traços.length}x): ${traços.slice(0, 5).map((t) => `"${t.slice(0, 70)}"`).join(' | ')}` })
  }
  const vazias = [...document.querySelectorAll('td, dd')].filter((el) => visivel(el) && !el.innerText.trim() && !el.querySelector('button,a,svg,input,img'))
  if (vazias.length) {
    resultado.push({ tipo: 'dados', detalhe: `Células/campos de dados vazios (${vazias.length}): ${vazias.slice(0, 3).map((e) => e.tagName.toLowerCase() + (e.previousElementSibling ? ` após "${e.previousElementSibling.innerText.slice(0, 30)}"` : '')).join(' | ')}` })
  }

  // 7. percentuais e barras de progresso
  const percentuais = todos.filter((l) => /(^|[^\d])(\d{1,4}(?:[.,]\d+)?)\s?%/.test(l))
  if (percentuais.length) {
    resultado.push({ tipo: 'info', detalhe: `Percentuais na tela: ${percentuais.slice(0, 6).map((t) => `"${t.slice(0, 50)}"`).join(' | ')}` })
  }

  return resultado
}

export async function inspecionar(page, tela, viewport) {
  const encontrados = await page.evaluate(inspecionarNoNavegador, PALAVRAS_SEM_ACENTO)
  for (const achado of encontrados) {
    achados.push({ tela, viewport, ...achado })
  }
  return encontrados
}

// Tira o print da tela atual em desktop e em celular (360px) e inspeciona os dois.
export async function capturar(page, nome, { aguardar = 400 } = {}) {
  mkdirSync(SAIDA, { recursive: true })
  const numero = proximoNumero()
  await page.waitForLoadState('networkidle').catch(() => {})

  for (const [rotulo, tamanho] of [
    ['desktop', DESKTOP],
    ['mobile', MOBILE],
  ]) {
    await page.setViewportSize(tamanho)
    await page.waitForTimeout(aguardar)
    await inspecionar(page, `${numero}-${nome}`, rotulo)
    await page.screenshot({ path: path.join(SAIDA, `${numero}-${nome}-${rotulo}.png`), fullPage: true })
  }

  await page.setViewportSize(DESKTOP)
  await page.waitForTimeout(150)
}

export function gravarAchados(extra = {}) {
  mkdirSync(SAIDA, { recursive: true })
  writeFileSync(
    path.join(SAIDA, 'achados-automaticos.json'),
    JSON.stringify({ ...extra, achados, respostasComErro, errosDeConsole }, null, 2),
    'utf-8',
  )
}
