# Integração · portão de merge, fila, base e ponta do épico

Vale para orquestrações com `FLUXO="2"` no `orq.env`. Sem essa chave, a integração segue só o
[`PLAYBOOK.md`](PLAYBOOK.md) e o `PROJETO.md`.

## Portão de merge

O PR de uma tarefa entra no épico quando tudo isto é verdade no head atual dele:

- a revisão aprovou este conteúdo: o head revisado é o head atual, ou `base.py --equivale` deu `EQUIVALENTE`;
- `provas.py` deu `PROVADO` ([`PROVAS.md`](PROVAS.md)); o comentário de provas no PR não segura o merge;
- as checagens obrigatórias do `PROJETO.md` estão verdes neste head (o pipeline do PR, quando o projeto tem);
- a base: `base.py <head>` deu `EM DIA`. Com `MERGE_LIMPO="direto"`, `LIMPO` também fecha o portão, e o resultado
  combinado é conferido na ponta do épico (abaixo);
- com `FILA_INTEGRACAO="sim"`, o PR tem a vez na fila (abaixo);
- `guarda.py pr <n>` deu `OK`.

O merge vai pelo `gh pr merge`, com o head conferido (`--match-head-commit`). Proteção de branch,
checagem obrigatória e fila de merge ficam como estão: se o portão não fecha e você não tem como consertar, a tarefa
fica `aprovada — aguarda <o quê>` e o usuário é avisado.

## Fila de integração

Com `FILA_INTEGRACAO="sim"`, os PRs aprovados entram no épico um por vez. Quem tem a vez é o único que faz merge ou
traz a base. Enquanto ele não sai, a base fica parada, e por isso ninguém a traz duas vezes. Sem a fila, cada merge
desatualiza os outros PRs abertos, inclusive o que está no meio da atualização ([`LICOES.md`](LICOES.md), "Fluxo de
tarefas").

- **Antes da vez, ninguém traz a base.** A revisão roda no head que o implementador entregou, mesmo `COMUM` ou
  `CONFLITO`. A exceção é a tarefa que volta para correção: a devolutiva pede `git merge origin/$BASE` junto quando o
  `base.py` não deu `EM DIA`, porque o implementador já vai rodar as checagens.
- **Entrada:** revisão aprovada e provas conferidas ([`PLAYBOOK.md`](PLAYBOOK.md), passo 4):
  `$E/bin/fila.py entra <ID> <PR> <head>`. Status `aprovada — na fila`.
- **A cada iteração**, depois do `git fetch`: `$E/bin/fila.py vez` diz quem age e o que fazer (tabela abaixo). Depois
  de um merge, `fila.py sai <ID>` e `fila.py vez` de novo, até dar `esperar` ou `nada`: merge sem agente leva
  segundos, e a fila esvazia na mesma iteração.
- **Ordem:** primeiro quem entra sem agente; depois quem libera mais tarefas do BACKLOG (o caminho crítico); no
  empate, quem entrou antes. Quem já tem a vez termina: a ordem não tira a vez de ninguém.
- **Sem aviso no meio do caminho.** Com a base parada, não existe "a base andou de novo": não mande `steer` a quem
  está atualizando.
- **Prazo:** `ACAO=passar` quer dizer que o dono da vez esperou mais que `INTEGRACAO_PRAZO_MIN`. Rode
  `fila.py passa <ID>`: os outros andam, e ele volta a concorrer quando entrar com o head novo.
- **Saída:** `fila.py sai <ID>` depois do merge, e também quando a tarefa volta para correção ou para uma rodada de
  revisão. Aprovada de novo, ela entra de novo.
- **Pausa** não mexe na fila: na retomada, `fila.py vez` continua de onde parou.

| `ACAO` | Quando | O que fazer |
|---|---|---|
| `merge` | head `EM DIA` | feche o portão e faça o merge ([`PLAYBOOK.md`](PLAYBOOK.md), passo 4) |
| `direto` | `LIMPO`, com `MERGE_LIMPO="direto"` | o mesmo merge, sem trazer a base: o head revisado é o head atual |
| `servidor` | `COMUM`, com `MERGE_LIMPO="direto"` | `gh pr update-branch <n> -R "$REPO"`: o GitHub traz a base para a branch da tarefa, sem agente (abaixo) |
| `atualizar` | `LIMPO` ou `COMUM`, com `MERGE_LIMPO="atualizar"` | peça a base ao implementador, com as checagens obrigatórias inteiras |
| `resolver` | `CONFLITO` | peça a base ao implementador |
| `esperar` | o pedido já saiu neste head | nada: a conclusão do agente ou a vigília te acorda |
| `passar` | o prazo venceu | `fila.py passa <ID>` e `fila.py vez` de novo |
| `buscar` | o head não está no `CHECKOUT` | `git -C "$CHECKOUT" fetch origin` e `fila.py vez` de novo |
| `nada` | fila vazia ou parada | siga a iteração |

**`servidor`, passo a passo:** depois do `gh pr update-branch`, o head novo aparece em segundos
(`gh pr view <n> -R "$REPO" --json headRefOid --jq .headRefOid`). Rode o `git fetch`, o
`base.py --equivale <head revisado> <head novo>` (abaixo) e `fila.py entra <ID> <PR> <head novo>`: a ação passa a
`merge`. Projeto com pipeline no PR: `fila.py pediu <ID>` e espere o pipeline ficar verde no head novo. É a única
escrita sua numa branch de tarefa, e só vale para merge limpo de PR aprovado.

**Merge `direto` recusado** porque o repositório exige branch em dia: trate como `servidor`.

## Pedido de base ao implementador

Só quem tem a vez recebe o pedido, uma vez. `fila.py pediu <ID>` registra o evento `atualizar-base`; sem a fila,
`agentes.py evento <ID> atualizar-base head=<sha>`.

- **Modelo:** antes do pedido, `t3_thread_configure` no `childThreadId` para o alvo da classe
  (`alvo.py --tarefa <ID> --selecao`). Trazer a base não pede o degrau a que a tarefa subiu na escada. Se a tarefa
  voltar para correção, reconfigure para o alvo gravado em `agentes.py mostra <ID>`.
- **Como:**
  - padrão: `git merge origin/$BASE` na branch da tarefa e push normal. O PR entra por squash, então o commit de merge
    não chega ao épico;
  - com `REBASE_FORCADO="sim"` (autorização dada na montagem): `git rebase origin/$BASE` e
    `git push --force-with-lease=<branch>:<head que você viu no PR>`. Push recusado quer dizer que alguém mexeu na
    branch: `git fetch` e reavalie, sem forçar.
- **O que o pedido diz:** o commit em que o épico está, os arquivos em conflito, "resolva sem mudar o comportamento
  de nenhum dos lados e refaça os artefatos binários que conflitarem", as checagens a rodar e "o épico fica parado
  até você concluir: não confira se a base andou".
- **Checagens:** com `MERGE_LIMPO="direto"`, só as do `PROJETO.md` que valem para os arquivos em conflito. Conflito
  só em documentação não pede teste. A bateria inteira roda na ponta do épico. Com `MERGE_LIMPO="atualizar"`, as
  checagens obrigatórias inteiras, porque é este head que fecha o portão.

No `PRONTO` do implementador: `fila.py entra <ID> <PR> <head novo>` e o `base.py --equivale`.

## O head mudou depois da revisão

```bash
$E/bin/base.py --equivale <head revisado> <head novo>
```

- `EQUIVALENTE`: a mudança do PR em relação à base é a mesma. A revisão e as provas valem
  (`provas.py <ID> <N> --head <head revisado>`). Não é ciclo novo.
- `DIFERENTE`: os arquivos listados mudaram, por correção, por conflito resolvido ou porque a base mexeu ao lado das
  linhas do PR. `fila.py sai <ID>` e abra uma rodada de revisão ([`REVISAO.md`](REVISAO.md)) com as notas apontando
  esses arquivos. Não conta como devolutiva. Aprovada, a tarefa volta para a fila.
- `DIFERENTE` só em arquivo sem código (documentação, changelog): leia o diff você mesmo. Se as linhas da tarefa são
  as mesmas e só mudaram de posição, trate como `EQUIVALENTE` e registre `[decisão]`.

## Ponta do épico: checagem e suíte longa

Duas coisas rodam no resultado integrado, e não em cada head de PR:

- **Checagem de ponta** (`MERGE_LIMPO="direto"`): as checagens obrigatórias do projeto, depois de merge que entrou
  sem o implementador trazer a base (`direto` ou `servidor`). É ela que confere o resultado combinado que o portão
  deixou de conferir. O comando é `CHECAGEM_PONTA`. Com a chave vazia, valem as checagens do `PROJETO.md` para os
  arquivos que entraram desde a última ponta verde (`git diff --name-only <última ponta verde> origin/$BASE`).
- **Suíte longa** (`SUITE_LONGA`): suíte de dezenas de minutos (E2E inteira, bateria de desempenho). Rodando por head,
  cada devolutiva e cada atualização da base jogam fora uma rodada, e o merge de um PR já aprovado fica esperando:
  num épico medido, isso foi quase metade do tempo entre PRONTO e merge.

No PR, implementador e revisor rodam os testes da tarefa e das telas ou módulos que ela altera.

**Rodada na ponta:** depois de um merge, se há o que conferir e nenhuma rodada em andamento, despache um agente de
teste (`delegate_task`, `role: "test"`, alvo `P`, worktree a partir da ponta). O pedido leva os PRs que entraram desde
a última ponta verde e os comandos:

```bash
$E/bin/slot test -- $E/bin/prova $E/ponta/ponta-<sha>.log -- <checagem de ponta>
$E/bin/slot test -- $E/bin/prova $E/suite/suite-<sha>.log -- <SUITE_LONGA>
```

Ele conclui com o resultado e os testes que falharam. Merge que chegar durante a rodada entra na próxima: uma rodada
por vez. Registre o agente (`agentes.py set PONTA teste taskId=… threadId=… estado=rodando`: ele ocupa uma vaga) e os
eventos `agentes.py evento PONTA ponta-inicio head=<sha>` e `ponta-fim head=<sha> resultado=verde|vermelha`. A suíte
longa usa `SUITE`, `suite-inicio` e `suite-fim`.

**Ponta vermelha:**

1. pare a fila: `echo "<ID da tarefa que vai corrigir>" > $E/PONTA_VERMELHA`. Enquanto o arquivo existir, só essa
   tarefa recebe a vez. Sem saber ainda quem corrige, deixe o arquivo vazio;
2. segure o despacho das tarefas que dependem dos PRs que entraram desde a última ponta verde; as outras seguem;
3. ache o PR culpado: o agente de teste roda os testes que falharam em cada um desses merges, do mais novo ao mais
   antigo. Falha que já existia na última ponta verde, ou que passa quando repetida, é instabilidade: registre e
   leve para as Propostas;
4. mande a correção ao implementador daquele PR, pela thread dele (`t3_thread_send` ao `childThreadId`; thread
   assentada: `t3_thread_organize` `unsettle` antes), numa branch nova a partir da ponta e com PR próprio. A
   correção entra no registro de achados da tarefa, passa por uma rodada de revisão ([`REVISAO.md`](REVISAO.md)) e
   entra na fila;
5. rodada de novo depois do merge da correção. Verde: apague `$E/PONTA_VERMELHA`.

**Gate e fechamento** exigem a ponta verde: a checagem de ponta e, se houver, a suíte longa.

## Sem fila

Pasta de estado sem `FILA_INTEGRACAO`, ou com `nao`: vale a regra anterior. Depois de cada merge, e antes de despachar
o revisor de um PR, rode para cada PR aberto:

```bash
git -C "$CHECKOUT" fetch origin --quiet && $E/bin/base.py <head do PR>
```

| Resultado | Com `ATUALIZAR_BASE="limpo"` (padrão) | Com `ATUALIZAR_BASE="sempre"` |
|---|---|---|
| `EM DIA` | segue | segue |
| `LIMPO`: atrás, merge limpo, nenhum arquivo em comum | segue sem atualizar enquanto é revisado. Aprovado, peça a atualização uma vez só, antes do merge | peça a atualização |
| `COMUM`: merge limpo, mas a base mudou arquivos do PR | peça a atualização antes da revisão; com a revisão rodando, ao fim dela | peça a atualização |
| `CONFLITO` | peça a atualização já | peça a atualização já |

Dois PRs abertos com arquivos em comum: o que está mais perto do merge entra primeiro, e o outro se atualiza uma vez
só, depois dele. Avise o implementador do segundo para esperar. Este caminho refaz atualizações quando vários PRs
ficam aprovados ao mesmo tempo: para ligar a fila, acrescente as chaves de `modelos/orq.env` ao `orq.env`.

## Sincronização: a tarefa ainda faz sentido?

Depois do merge de cada `SYNC-…` ([`PLAYBOOK.md`](PLAYBOOK.md), passo 6), leia o que veio da `ORIGEM` contra as tarefas
ainda `pendente`: o mesmo problema já foi resolvido lá? A API, o tipo, o schema ou a dependência que a tarefa usa
mudou? O código que ela altera foi movido ou apagado? Se sim, a tarefa fica `em espera`, com a evidência no PAINEL, e o
usuário decide entre seguir, replanejar ou cancelar. Base sem conflito não prova que a tarefa continua valendo.

A `SYNC-…` passa pela fila como as outras, e o merge dela continua sendo merge commit.

## Vigília de PR e limite do GitHub

- **O despertar da vigília é notícia, não decisão de merge.** Confira o portão você mesmo, e trate só de checagem e
  comentário mais novos que o último push. Com a fila, aviso de conflito num PR que ainda não tem a vez não pede
  ação: a base entra na vez dele.
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
