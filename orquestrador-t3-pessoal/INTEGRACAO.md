# Integração · portão de merge, base e suíte longa

Vale para orquestrações com `FLUXO="2"` no `orq.env`. Sem essa chave, a integração segue só o
[`PLAYBOOK.md`](PLAYBOOK.md) e o `PROJETO.md`.

## Portão de merge

O PR de uma tarefa entra no épico quando tudo isto é verdade no head atual dele:

- a revisão aprovou este conteúdo: o head revisado é o head atual, ou `base.py --equivale` deu `EQUIVALENTE`;
- `provas.py` deu `PROVADO` ([`PROVAS.md`](PROVAS.md)); o comentário de provas no PR não segura o merge;
- as checagens obrigatórias do `PROJETO.md` estão verdes neste head (o pipeline do PR, quando o projeto tem);
- `base.py <head>` deu `EM DIA`: as checagens rodaram no head que já contém a base, ou seja, no resultado combinado;
- `guarda.py pr <n>` deu `OK`.

O merge vai pelo `gh pr merge`, com o head conferido (`--match-head-commit`). Proteção de branch,
checagem obrigatória e fila de merge ficam como estão: se o portão não fecha e você não tem como consertar, a tarefa
fica `aprovada — aguarda <o quê>` e o usuário é avisado.

## PR atrás da base

Depois de cada merge, e antes de despachar o revisor de um PR, rode para cada PR aberto:

```bash
git -C "$CHECKOUT" fetch origin --quiet && $E/bin/base.py <head do PR>
```

| Resultado | Com `ATUALIZAR_BASE="limpo"` | Com `ATUALIZAR_BASE="sempre"` |
|---|---|---|
| `EM DIA` | segue | segue |
| `LIMPO`: atrás, merge limpo, nenhum arquivo em comum | segue sem atualizar enquanto é revisado. Aprovado, peça a atualização uma vez só, antes do merge | peça a atualização |
| `COMUM`: merge limpo, mas a base mudou arquivos do PR | peça a atualização antes da revisão; com a revisão rodando, ao fim dela | peça a atualização |
| `CONFLITO` | peça a atualização já | peça a atualização já |

Com `limpo`, a base andar não interrompe a revisão de quem não divide arquivo com o que entrou. A atualização final
traz a base, o implementador roda as checagens obrigatórias no resultado e o `base.py --equivale` confirma que a
revisão vale (abaixo): o PR entra sempre `EM DIA`, sem revisão nova.

Dois PRs abertos com arquivos em comum: o que está mais perto do merge entra primeiro, e o outro se atualiza uma vez
só, depois dele. Avise o implementador do segundo para esperar.

**Como o implementador atualiza** (registre o pedido: `agentes.py evento <ID> atualizar-base head=<sha>`):

- padrão: `git merge origin/$BASE` na branch da tarefa e push normal. O PR entra por squash, então o commit de merge
  não chega ao épico;
- com `REBASE_FORCADO="sim"` (autorização dada na montagem): `git rebase origin/$BASE` e
  `git push --force-with-lease=<branch>:<head que você viu no PR>`. Push recusado quer dizer que alguém mexeu na
  branch: `git fetch` e reavalie, sem forçar.

O pedido diz só isso: trazer a base, resolver conflitos sem mudar o comportamento de nenhum dos lados e refazer os
artefatos binários que conflitarem.

## O head mudou depois da revisão

```bash
$E/bin/base.py --equivale <head revisado> <head novo>
```

- `EQUIVALENTE`: a mudança do PR em relação à base é a mesma. A revisão e as provas valem
  (`provas.py <ID> <N> --head <head revisado>`); rode de novo só as checagens obrigatórias no head novo. Não é ciclo
  novo.
- `DIFERENTE`: os arquivos listados mudaram, por correção ou por conflito resolvido. Abra uma rodada de revisão
  ([`REVISAO.md`](REVISAO.md)) com as notas apontando esses arquivos. Não conta como devolutiva.

## Suíte longa

Suíte de dezenas de minutos (E2E inteira, bateria de desempenho) fica em `SUITE_LONGA` no `orq.env` e roda no
resultado integrado, não em cada head de PR. Rodando por head, cada devolutiva e cada atualização da base jogam fora
uma rodada, e o merge de um PR já aprovado fica esperando a fila: num épico medido, isso foi quase metade do tempo
entre PRONTO e merge.

- **No PR:** implementador e revisor rodam os testes da tarefa e das telas ou módulos que ela altera.
- **Na ponta do épico:** depois de um merge, se não há suíte rodando, despache um agente de teste (`delegate_task`,
  `role: "test"`, alvo `P`, worktree a partir da ponta) que roda
  `$E/bin/slot test -- $E/bin/prova $E/suite/suite-<sha>.log -- <SUITE_LONGA>` e conclui com o resultado. Merge que
  chegar durante a rodada entra na próxima: uma suíte por vez. Registre
  `agentes.py evento SUITE suite-inicio head=<sha>` e `suite-fim head=<sha> resultado=verde|vermelha`.
- **Ponta vermelha:**
  1. segure o despacho das tarefas que dependem dos PRs que entraram desde a última ponta verde; as outras seguem;
  2. ache o PR culpado: o agente de teste roda os testes que falharam em cada um desses merges, do mais novo ao mais
     antigo. Falha que já existia na última ponta verde, ou que passa quando repetida, é instabilidade: registre e
     leve para as Propostas;
  3. mande a correção ao implementador daquele PR, pela thread dele (`t3_thread_send` ao `childThreadId`; thread
     assentada: `t3_thread_organize` `unsettle` antes), numa branch nova a partir da ponta e com PR próprio. A
     correção entra no registro de achados da tarefa e passa por uma rodada de revisão ([`REVISAO.md`](REVISAO.md));
  4. suíte de novo depois do merge da correção.
- **Gate e fechamento** exigem a suíte verde na ponta do épico.

## Sincronização: a tarefa ainda faz sentido?

Depois do merge de cada `SYNC-…` ([`PLAYBOOK.md`](PLAYBOOK.md), passo 6), leia o que veio da `ORIGEM` contra as tarefas
ainda `pendente`: o mesmo problema já foi resolvido lá? A API, o tipo, o schema ou a dependência que a tarefa usa
mudou? O código que ela altera foi movido ou apagado? Se sim, a tarefa fica `em espera`, com a evidência no PAINEL, e o
usuário decide entre seguir, replanejar ou cancelar. Base sem conflito não prova que a tarefa continua valendo.

## Vigília de PR e limite do GitHub

- **O despertar da vigília é notícia, não decisão de merge.** Confira o portão você mesmo, e trate só de checagem e
  comentário mais novos que o último push.
- **Robô de revisão no repositório** (Greptile, Macroscope, CodeRabbit…): confira cada achado dele contra o código
  antes de repassar. Achado real entra no registro de achados da tarefa e segue a devolutiva. Falso positivo: responda
  no PR com o motivo escrito e resolva a conversa. O CodeRabbit é consultivo: o merge não espera por ele.
- **"Parou de vigiar, não consegui ler"** costuma ser o limite do GraphQL do GitHub:
  `gh api rate_limit --jq .resources.graphql`. Com `remaining` perto de 0, espere o `reset` antes de vigiar de novo.
  A API REST tem limite próprio e segue respondendo: `gh api repos/<dono>/<repo>/pulls/<n>` lê o PR, e
  `gh api repos/<dono>/<repo>/commits/<sha>/check-runs` lê as checagens.
- **Comentário em PR em nome do usuário** começa pela nota abaixo, com o modelo que escreveu e o login dele. A
  resposta vem fora da nota: a conclusão primeiro, depois o código ou a checagem que a sustenta, sem agradecimento
  nem narração. O `pr-provas.py` já põe a nota.

  ```md
  > [!NOTE]
  > 🤖 **<modelo> respondendo por <usuário>**
  ```

## PR final do épico

Com `PR_FINAL="abrir"` (autorização dada na montagem, e a única exceção à regra de nenhum PR para branch protegida),
depois da revisão final e do fechamento:

1. confira a ponta: `git fetch origin`, checagens obrigatórias e suíte longa verdes em `origin/$BASE`, e o épico em dia
   com a `$ORIGEM` (senão, mais uma `SYNC-…` antes);
2. abra o PR de verdade, não rascunho:
   `gh pr create --repo "$REPO" --base "$ORIGEM" --head "$BASE" --title "<título>" --body-file $E/fechamento.md`.
   O título diz o que o épico muda para quem usa. O corpo abre pelo problema e traz as tarefas com seus PRs, a tabela
   da revisão final, os riscos e o que não foi testado. Confira que o texto não leva segredo nem dado pessoal;
3. deixe o PR aberto. O fluxo não faz o merge, não liga auto-merge e não entra em fila de merge: promover o épico é
   do usuário. Se o repositório mescla sozinho PR aprovado e você não tem como impedir, avise o usuário em vez de
   abrir;
4. relate o estado: `pronto para merge` (checagens verdes, sem conflito), `aguarda aprovação` ou `bloqueado`, com o
   link, o head e os riscos. Antes de devolver a thread, `unwatch_pull_request`.
