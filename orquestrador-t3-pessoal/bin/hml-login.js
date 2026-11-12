#!/usr/bin/env node
// Login de verdade na homologação, chamado pelo `hml vivo`, que entrega HML_URL, HML_USUARIO, HML_SENHA, HML_PERFIL e
// HML_CHROME e mascara a saída. Com usuário e senha, abre um navegador limpo: sessão ou token vencido não engana a
// checagem. Seletores no orq.env: HML_LOGIN_USUARIO, HML_LOGIN_SENHA, HML_LOGIN_BOTAO; HML_LOGIN_OK é um trecho
// (regex) da URL depois do login. Login em duas etapas (e-mail, depois senha) usa HML_LOGIN_AVANCAR.
// Saída: 0 no ar · 10 credencial recusada · 11 fora do ar · 12 tela diferente da esperada · 14 sem login automático
const path = require('path');
const E = process.env;

function playwright() {
  const lugares = [E.HML_PASTA, process.cwd(), E.ORQ && path.join(E.ORQ, 'harness')].filter(Boolean);
  const tentativas = [() => require(E.HML_PLAYWRIGHT)];
  for (const nome of ['playwright-core', 'playwright'])
    for (const l of [E.HML_PLAYWRIGHT, ...lugares].filter(Boolean)) tentativas.push(() => require(require.resolve(nome, { paths: [l] })));
  for (const t of tentativas) { try { const m = t(); if (m && m.chromium) return m; } catch { /* próximo */ } }
  console.log('Playwright não encontrado: aponte HML_PLAYWRIGHT no orq.env para a pasta do playwright-core');
  process.exit(12);
}

const LOGIN = E.HML_LOGIN_URL || E.HML_URL;
const OK = E.HML_LOGIN_OK ? new RegExp(E.HML_LOGIN_OK) : null;
const SEL = {
  usuario: E.HML_LOGIN_USUARIO || 'input[type=email], input[name*=user i], input[name*=email i], input[type=text]',
  senha: E.HML_LOGIN_SENHA || 'input[type=password]',
  botao: E.HML_LOGIN_BOTAO,   // vazio: Enter no campo de senha (um submit qualquer pode ser o botão de SSO)
  avancar: E.HML_LOGIN_AVANCAR || 'button:has-text("Avançar"), button:has-text("Próximo"), button:has-text("Continuar"), button:has-text("Next")',
};
const RECUSA = /inv[aá]lid|incorret|n[aã]o confere|errad|bloquead|invalid|incorrect|wrong/i;

(async () => {
  const { chromium } = playwright();
  const opcoes = { headless: true, args: (E.HML_CHROME_ARGS || '').split(' ').filter(Boolean) };
  if (E.HML_CHROME) opcoes.executablePath = E.HML_CHROME; else opcoes.channel = 'chrome';
  const comSenha = Boolean(E.HML_USUARIO && E.HML_SENHA);
  if (!comSenha && !E.HML_PERFIL) { console.log('nada guardado: nem usuário e senha, nem sessão capturada'); process.exit(14); }
  const navegador = comSenha ? await chromium.launch(opcoes) : null;
  const ctx = comSenha ? await navegador.newContext() : await chromium.launchPersistentContext(E.HML_PERFIL, opcoes);
  const page = await ctx.newPage();
  const falhas = new Set(), negados = new Set();
  const conta = rq => ['document', 'xhr', 'fetch'].includes(rq.resourceType());
  const rotulo = (rq, s) => { const u = new URL(rq.url()); return `${s} ${rq.method()} ${u.host}${u.pathname}`; };
  page.on('response', r => {
    const rq = r.request(); if (!conta(rq)) return;
    if (r.status() >= 500) falhas.add(rotulo(rq, r.status()));
    else if (r.status() === 401 || r.status() === 403) negados.add(rotulo(rq, r.status()));
  });
  page.on('requestfailed', rq => {
    const erro = (rq.failure() || {}).errorText || 'sem resposta';
    if (conta(rq) && !/ERR_ABORTED/.test(erro)) falhas.add(rotulo(rq, erro));
  });
  const senhaVisivel = () => page.locator('input[type=password]').first().isVisible().catch(() => false);
  const sair = async (codigo, ...linhas) => {
    for (const l of linhas.filter(Boolean)) console.log(l);
    if (falhas.size) console.log('5xx ou sem resposta: ' + [...falhas].slice(0, 6).join(' | '));
    if (negados.size) console.log('401/403: ' + [...negados].slice(0, 6).join(' | '));
    await ctx.close().catch(() => {}); if (navegador) await navegador.close().catch(() => {});
    process.exit(codigo);
  };

  try { await page.goto(comSenha ? LOGIN : E.HML_URL, { waitUntil: 'domcontentloaded', timeout: 120000 }); }
  catch (e) { await sair(11, `não abriu ${comSenha ? LOGIN : E.HML_URL}: ${String(e.message).split('\n')[0]}`); }

  if (!comSenha) {  // só a sessão capturada (SSO ou MFA): ela vale se o app não pede senha
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    if (await senhaVisivel()) await sair(14, `a sessão capturada caiu na tela de login (${new URL(page.url()).pathname})`);
    await sair(falhas.size ? 11 : 0, `sessão capturada aceita em ${new URL(page.url()).pathname}`);
  }

  const aparece = (sel, ms) => page.locator(sel).first().waitFor({ state: 'visible', timeout: ms }).then(() => true, () => false);
  const onde = () => new URL(page.url()).pathname;
  if (!(await aparece(SEL.usuario, 60000))) await sair(falhas.size ? 11 : 12, `o campo de usuário (${SEL.usuario}) não apareceu em ${onde()}`);
  await page.locator(SEL.usuario).first().click(); await page.keyboard.type(E.HML_USUARIO); await page.keyboard.press('Tab');
  if (!(await aparece(SEL.senha, 5000))) {  // login em duas etapas
    if (await aparece(SEL.avancar, 2000)) await page.locator(SEL.avancar).first().click();
    if (!(await aparece(SEL.senha, 30000))) {
      const tela = (await page.locator('body').innerText().catch(() => '')).replace(/\s+/g, ' ').slice(0, 200);
      await sair(falhas.size ? 11 : RECUSA.test(tela) ? 10 : 12, `o campo de senha (${SEL.senha}) não apareceu depois do usuário`, `tela: ${tela}`);
    }
  }
  await page.locator(SEL.senha).first().click(); await page.keyboard.type(E.HML_SENHA);
  if (!SEL.botao) await page.keyboard.press('Enter');
  else if (await aparece(SEL.botao, 15000)) await page.locator(SEL.botao).first().click();
  else await sair(12, `o botão de entrar (${SEL.botao}) não apareceu`);

  const inicio = new URL(page.url()).pathname, limite = Date.now() + 45000;
  while (Date.now() < limite) {
    const u = new URL(page.url());
    const entrou = OK ? OK.test(u.pathname + u.search + u.hash) : (u.pathname !== inicio && !(await senhaVisivel()));
    if (entrou) await sair(0, `login ok: ${u.pathname}`);
    await page.waitForTimeout(500);
  }
  const tela = (await page.locator('body').innerText().catch(() => '')).replace(/\s+/g, ' ').slice(0, 200);
  const codigo = falhas.size ? 11 : (negados.size || RECUSA.test(tela)) ? 10 : 12;
  await sair(codigo, `o login não saiu de ${new URL(page.url()).pathname}`, `tela: ${tela}`);
})().catch(e => { console.log('erro no roteiro: ' + String(e.message).split('\n')[0]); process.exit(12); });
