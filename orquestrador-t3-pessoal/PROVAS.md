# Provas · nada é aprovado sem prova

O revisor só aprova com uma prova concreta para cada critério de aceite, produzida por ele no head revisado. O
relatório do implementador não é prova. As provas ficam na pasta de estado, e o resumo delas vai como comentário no PR
antes do merge.

## Tipos

| Tipo | O que é | Como gerar |
|---|---|---|
| `log` | Saída de um comando (testes, lint, build), com cabeçalho e código de saída | `<estado>/bin/prova <arquivo>.log -- <comando>` |
| `mutacao` | A linha central do comportamento removida ou trocada, e o teste caindo | `bin/prova mutacao-<nome>.log --tipo mutacao -- <teste>` com a mutação aplicada; depois desfaça |
| `print` | Captura da tela (PNG) do estado que o critério pede | Playwright `page.screenshot`, ou `google-chrome-stable --headless --screenshot=<arquivo>.png <url>` |
| `video` | Gravação curta (até 90 s) do fluxo que o critério descreve | Playwright com `recordVideo` (abaixo) |
| `medicao` | Números com o método (tempo, contagem de chamadas, tamanho) | `bin/prova medicao-<nome>.log --tipo medicao -- <comando que mede>` |
| `requisicao` | Pedido e resposta de API local ou de homologação (outro host é recusado) | `bin/prova req-<nome>.log --tipo requisicao -- curl -sS -i <url>` |

O `bin/prova` grava a data, o head, a pasta e o comando, mascara segredos e anota `# exit=<código>` no fim. Prova de
`log` e `medicao` com saída diferente de zero não serve para aprovar; prova de `mutacao` precisa de saída diferente
de zero (o teste caiu).

### Print e vídeo com Playwright

Use o Playwright do projeto ou a skill `playwright-skill`, pelo `slot browser` e pelo `hml exec`, que entrega a
sessão de teste já logada ([`AMBIENTE.md`](AMBIENTE.md)). Com o Chrome do sistema não é preciso baixar navegador:

```js
// <estado>/bin/slot browser -- <estado>/bin/hml exec -- node gravar.js
const { chromium } = require('playwright');
const context = await chromium.launchPersistentContext(process.env.HML_PERFIL, {
  channel: 'chrome', args: process.env.HML_CHROME_ARGS.split(' '),
  recordVideo: { dir: PASTA_DE_PROVAS, size: { width: 1280, height: 720 } },
});
const page = await context.newPage();
await page.goto(process.env.HML_URL);
// … passos do critério …
await page.screenshot({ path: `${PASTA_DE_PROVAS}/login-depois.png`, fullPage: true });
await context.close();   // o vídeo só é gravado no close
```

Renomeie o vídeo gerado para algo legível (`fluxo-login.webm`). Use contas e dados de teste: print e vídeo aparecem
na thread do orquestrador, e o script não consegue mascarar imagem.

## Manifesto

O revisor grava `tarefas/<ID>/evidencias/revisao-c<N>/provas.json`, com os arquivos na mesma pasta. A lista de
critérios esperada sai de `<estado>/bin/provas.py <ID> --criterios`.

```json
{
  "tarefa": "T1.1", "ciclo": 1, "head": "<sha completo revisado>", "pr": "<url do PR>",
  "criterios": [
    {"id": "1.1", "descricao": "login com OAuth funciona", "resultado": "ok",
     "provas": [
       {"tipo": "log", "arquivo": "testes-login.log", "resumo": "12 passed, exit 0"},
       {"tipo": "video", "arquivo": "fluxo-login.webm", "resumo": "login, redirecionamento e sessão ativa"}
     ]}
  ],
  "mutacao": [{"tipo": "mutacao", "arquivo": "mutacao-auth.log", "resumo": "sem a troca do code, 3 testes caem"}]
}
```

## Validação

`<estado>/bin/provas.py <ID> <ciclo> [--head <sha>]` confere:

- todo critério do aceite está no manifesto, com `resultado: "ok"` e pelo menos uma prova;
- os arquivos existem, não estão vazios, têm até `PROVA_MAX_MB` e são do formato do tipo (PNG/JPEG, vídeo válido
  com até `PROVA_VIDEO_MAX_S`);
- os tipos que o campo `**Provas:**` da tarefa exige estão presentes (ex.: `print, vídeo` em tarefa de tela);
- existe prova de mutação nas classes M, G e GG (salvo `**Provas:** sem mutação`);
- o head do manifesto é o head revisado;
- nenhum arquivo de texto tem segredo (tokens, chaves, senhas, CPF).

`Resultado: PROVADO` libera a aprovação. `INCOMPLETO` não é aprovação: o orquestrador devolve ao mesmo revisor
(`t3_thread_send`) a lista do que falta, e isso não conta como ciclo.

## Rodada curta

Vale só quando o brief da revisão diz "rodada curta" (ciclo 2 em diante, em orquestração com `FLUXO="2"`). Na revisão
completa, toda prova é nova e esta seção não se aplica. Na rodada curta, o revisor prova de novo só o que a correção
pode ter mudado:

- **prova nova, no head da rodada:** os critérios ligados aos achados (`mkrev.py --reprovar`) e os que a correção
  tocou;
- **prova herdada:** nos outros critérios, ele copia os arquivos de `evidencias/revisao-c<N-1>/` para a pasta da
  rodada e marca o critério com `"herdada_de": "<N-1>"`. Os arquivos ficam na pasta nova, e o envio segue igual;
- **checagens no head novo:** os logs das checagens do projeto, gravados com `bin/prova`, entram em `"checagens"`;
- **mutação:** onde a tarefa exige, a mutação é feita na linha central da correção e entra em `"mutacao"`.

```json
{
  "tarefa": "T1.1", "ciclo": 2, "head": "<sha completo desta rodada>", "pr": "<url do PR>",
  "checagens": [{"tipo": "log", "arquivo": "testes-c2.log", "resumo": "214 passed, exit 0"}],
  "criterios": [
    {"id": "1.1", "descricao": "login com OAuth funciona", "resultado": "ok",
     "provas": [{"tipo": "log", "arquivo": "testes-login-c2.log", "resumo": "o caso do achado c1-1 passa"}]},
    {"id": "1.2", "descricao": "logout encerra a sessão", "resultado": "ok", "herdada_de": "1",
     "provas": [{"tipo": "video", "arquivo": "fluxo-logout.webm", "resumo": "copiado do ciclo 1"}]}
  ],
  "mutacao": [{"tipo": "mutacao", "arquivo": "mutacao-correcao.log", "resumo": "sem a linha da correção, o teste do c1-1 cai"}]
}
```

O `provas.py` recusa a prova herdada fora de rodada curta, em critério de `--reprovar`, vinda de um ciclo em que o
critério não estava `ok`, ou sem um log de checagem gravado no head da rodada.

## No PR

Com a revisão aprovada e `PROVADO`, antes do merge:

```bash
<estado>/bin/pr-provas.py <ID> <ciclo> [--pr <url ou número>]
```

Ele comenta no PR a lista de provas por critério (nome do arquivo e resumo) e a `revisao-c<N>.md` dobrada, com os
segredos em texto mascarados. Os arquivos de prova não sobem: ficam em `tarefas/<ID>/evidencias/`, na pasta de estado.
O que já foi comentado fica em `tarefas/<ID>/pr-comentarios.json` (repetir não duplica). `--simular` mostra o
comentário sem enviar. Confira o acesso com `pr-provas.py --checar` (usa o `gh` autenticado).

O comentário não segura o merge: se o envio falhar, o orquestrador registra no DIARIO e segue. Em repositório
público o comentário é público. Para não comentar, `PROVAS_PR="desligado"` no `orq.env`.
