# Escrita para o operador ler

Adaptação para o português do `unslop` (contrato de reescrita e catálogo de vícios). Os scanners do `unslop`
recusam texto que não seja em inglês; aqui o verificador é `bin/texto.py`.

O operador lê entre uma reunião e outra, muitas vezes no celular. Texto longo ou difícil ele pula, e a orquestração
perde o humano que decide. **Cada texto precisa ser lido em 30 segundos.**

## Regras

1. **Comece pelo que importa.** A primeira linha diz o que mudou ou o que você precisa dele, em até 25 palavras.
2. **Fatos, não adjetivos.** ID da tarefa, número do PR, minutos, arquivos, contagens. "Robusto" e "significativo"
   não informam; "3 testes novos, 0 falhas" informa.
3. **Uma ideia por frase.** Até ~25 palavras por frase e 3 linhas por parágrafo. Sem telegrafar: frase completa.
4. **Português do Brasil simples.** Os termos do dia a dia do time ficam como estão (PR, merge, branch, commit,
   rebase, worktree, CI, deploy, build, lint). Termo menos comum ganha uma explicação curta na primeira vez.
5. **Corte a enrolação** do catálogo em [`VICIOS.md`](VICIOS.md): abertura que atrasa, ênfase fabricada, resto de
   chatbot, meta-comentário, conclusão genérica.
6. **Problema com o mesmo destaque do sucesso.** Falha, risco, "não testado" e incerteza aparecem, sem suavizar.
7. **Não repita o painel.** Diga o que mudou e aponte o `PAINEL.md` para o resto.
8. **Pergunta é fechada.** Alternativas, a sua recomendação e o que acontece se ele não responder. Com o usuário
   presente (montagem, sabatina, ensaio), a pergunta vai pelo painel do `AskUserQuestion`, uma por vez e com
   alternativas clicáveis ([`../sabatina/SABATINA.md`](../sabatina/SABATINA.md)). No loop, vai em texto: o painel
   segura o turno e o orquestrador deixaria de processar os despertares.
9. **Preserve** números, ressalvas, nomes, citações e todo "nunca", "sempre" e "obrigatório" de regras.
10. **Forma:** negrito só em rótulos; sem exclamação; travessão no máximo um por parágrafo; ícones só os de status
    (✅ entregue, ⚠️ atenção, ⛔ precisa de você, ⏸️ pausa, 🔨 implementação, 🔍 revisão).
11. **Use a interface do T3** ([`../T3-V2.md`](../T3-V2.md), "Interface do T3"):
    - thread de agente é link clicável: `[🔨 T2.2](t3-thread://v1/<childThreadId>)`, nunca o id solto;
    - prova visual aparece na mensagem: `![T1.2 · tela depois](/caminho/absoluto/login-depois.png)` (vídeo também),
      no máximo 2 por mensagem;
    - tabela grande ou dependências entre tarefas viram página (`html_preview` e depois `html_render`) nos marcos:
      backlog, gate, relatório final e `status`. O texto depois da página só diz o que ela não diz;
    - o título da thread mostra o estado, e um pedido de decisão deixa a thread como não lida.

## Formatos

| Texto | Limite | Verificação |
|---|---|---|
| Notificação (`PushNotification`) | 120 caracteres | `--tipo push` |
| Resumo da iteração na thread | 6 linhas, 90 palavras | `--tipo thread` |
| Pedido de decisão | 10 linhas, 140 palavras | `--tipo decisao` |
| Entrada do DIARIO | 4 linhas, 60 palavras | `--tipo diario` |
| Relatório de pausa | 15 linhas e 200 palavras fora da tabela | `--tipo pausa` |
| Relatório final | 20 linhas e 250 palavras fora das tabelas | `--tipo final` |
| Devolutiva ao implementador | 12 itens, 40 palavras por item | `--tipo devolutiva` |
| Relatório do implementador | 450 palavras fora das tabelas | `--tipo relatorio` |
| Revisão | 550 palavras fora das tabelas | `--tipo revisao` |
| Página no T3 (`html_render`): backlog, gate, final, `status` | o que couber na tela sem rolar; texto depois em até 4 linhas | `html_preview` antes |
| Pergunta no painel (`AskUserQuestion`, JSON) | 4 perguntas por chamada, 70 palavras por pergunta, 2 a 4 alternativas | `--tipo pergunta` |
| Rodada de sabatina em texto (sem o painel) | 7 perguntas, 70 palavras por pergunta | `--tipo sabatina` |

### Resumo da iteração

```text
✅ T1.2 entrou no épico (#14), com 3 provas. Nada precisa de você agora.
- Em andamento: [🔍 T2.1](t3-thread://v1/<id>) em revisão (ciclo 1); [🔨 T2.2](t3-thread://v1/<id>) há 40 min.
- Fila: T2.3 e T2.4 esperam vaga (6/6 agentes).
- Próximo: merge da T2.1 se a revisão aprovar.
![T1.2 · tela depois](/caminho/absoluto/evidencias/revisao-c1/login-depois.png)
```

Iteração sem mudança termina numa linha só (`· sem mudança · 4 agentes rodando`) e na linha do DIARIO.

### Pedido de decisão

```text
⛔ Preciso de uma decisão sobre a T2.1 (login OAuth).
O teste de login também falha na main, antes da mudança. A tarefa não fecha sem resolver isso.
1. Corrigir o teste dentro da T2.1 (aumenta o escopo em ~40 linhas).
2. Abrir uma tarefa nova só para o teste e seguir a T2.1 sem ele.
Recomendo a 2: mantém o escopo da T2.1 e o teste ganha revisão própria.
Sem resposta, a T2.1 fica em espera e as outras seguem.
```

Junto com o pedido, o título da thread ganha `⛔` e a thread fica marcada como não lida. Ela está fixada no topo da
barra lateral, então é isso que ele vê primeiro.

### Entrada do DIARIO

```text
- `14:32` T1.2 mergeada (#14) depois de 1 ciclo. [decisão] Segui sem o lint de CSS, que falha na main.
```

### Relatório de pausa

```text
⏸️ Pausado às 18:30: 3 agentes em ponto seguro, 1 cortado no prazo.
| Tarefa | Estado | HEAD | Worktree | Falta |
|---|---|---|---|---|
Para retomar, diga "continue" aqui.
```

### Relatório final

```text
✅ <Nome da orquestração> terminou: 9 tarefas entregues em 2 dias, 0 bloqueadas.
| Tarefa | PR | Ciclos | Resultado |
|---|---|---|---|
- Decisões sem você: 3 (marcadas [decisão] no DIARIO).
- Ficou de fora: 4 propostas no BACKLOG, esperando o seu "pode".
- Riscos: <até 3 linhas>.
- Não testado: <o que ficou sem validação, ou "nada">.
```

### Devolutiva

Lista numerada. Cada item: o que corrigir, onde (`arquivo:linha`) e como conferir. Primeiro os obrigatórios, depois
os recomendados.

## Antes de enviar

O mesmo fluxo do `unslop`, em duas passadas:

1. **Diagnóstico:** releia o texto e rode `<estado>/bin/texto.py --tipo <tipo> <arquivo>` (ou pelo stdin).
2. **Conserto mínimo:** corrija só o que for vício de verdade. Achado do script é candidato: termo de domínio,
   citação, nome de tarefa e mensagem de erro ficam. Não troque uma enrolação por outra nem corte um fato para caber
   no limite; se não couber, mova o detalhe para um arquivo e aponte o caminho.
3. Rode de novo. `Resultado: LIMPO` (nenhum achado grave) libera o envio.

É obrigatório no relatório de pausa, no relatório final, no pedido de decisão, na devolutiva e na conclusão dos
agentes (relatório e revisão). No resumo da iteração e no DIARIO, siga os modelos; rode o script quando o texto sair
do modelo.
