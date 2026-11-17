# Revisão · achados, rodadas e revisão final

Vale para orquestrações com `FLUXO="2"` no `orq.env`. Sem essa chave (pasta de estado montada antes de 16/11/2026), a
revisão segue só o [`PLAYBOOK.md`](PLAYBOOK.md): revisão completa a cada ciclo.

A primeira revisão de cada tarefa continua completa e adversarial. Nas orquestrações medidas ela pediu mudanças em
metade das tarefas M e em três quartos das G, quase sempre por defeito real ([`LICOES.md`](LICOES.md), "Medição de
novembro de 2026"). O que muda é o que vem depois dela.

## Régua de severidade

Uma régua só, para revisor, orquestrador e implementador:

| Severidade | O que é | O que acontece |
|---|---|---|
| **alta** | O caso que a tarefa pretende não funciona: critério de aceite falha, regressão, perda de dado, falha de segurança | Entra na devolutiva |
| **média** | Defeito real que quem usa a tarefa vai encontrar, dentro do objetivo dela | Entra na devolutiva |
| **baixa** | O resto: outro caminho, caso raro, custo pequeno, estilo | Não abre ciclo: segue o [`ESCOPO.md`](ESCOPO.md) |

Confira a severidade antes de repassar um achado: outro caminho, caso raro e custo pequeno são baixos, seja qual for o
rótulo com que vieram.

## Registro de achados

`tarefas/<ID>/achados.md` (modelo em `<estado>/modelos/achados.md`) é a lista única dos achados altos e médios da
tarefa. Você a mantém; implementador e revisores leem.

- **Quando nasce:** na primeira revisão com `MUDANÇAS`. Copie o modelo e lance cada achado alto ou médio com o ID que
  o revisor deu (`c1-1`, `c1-2`…). O ID não muda até o fim da tarefa.
- **Estados:** `aberto` → `corrigido` (o implementador diz que corrigiu, com o commit) → `resolvido` (um revisor
  conferiu). Ou `contestado` (o implementador discorda, com evidência) e `recusado` (você decidiu não corrigir, com o
  motivo).
- **Critério ligado:** anote em cada achado o critério de aceite que ele derruba. São esses critérios que pedem prova
  nova na rodada seguinte (`mkrev.py --reprovar`).

## Devolutiva e resposta

A devolutiva ([`PLAYBOOK.md`](PLAYBOOK.md), passo 4) leva um item por achado aberto, começando pelo ID. Peça a menor
correção que resolve: apagar ou estreitar código vem antes de acrescentar trava, cache, opção ou função auxiliar.
Quando o revisor gravou a reprodução como teste (`evidencias/revisao-c<N>/teste-<id>…`), a devolutiva manda
incorporá-lo: ele falha no head revisado, passa com a correção e fica no repositório como teste de regressão.

O implementador responde cada ID na seção **Ciclos** do relatório: `corrigido` com o commit, ou `contestado` com a
evidência (arquivo:linha, teste, saída). Atualize o registro com a resposta.

- **Contestação:** confira a evidência você mesmo. Procede → `recusado`, com o motivo. Não procede → o achado volta na
  mesma devolutiva, com a sua resposta à evidência. Achado contestado pela segunda vez vai para o usuário, com os dois
  lados em 2 ou 3 linhas cada: tarefa `em espera`, sem contar devolutiva.
- **A correção fez o diff crescer:** rode o `escopo.py` de novo. Acima do orçamento, peça o corte antes da rodada.

## Rodada seguinte: curta ou completa

Do ciclo 2 em diante, o `mkrev.py` escolhe ([`PLAYBOOK.md`](PLAYBOOK.md), passo 5.6):

```bash
$E/bin/mkrev.py <ID> <PR> <HEAD> <ciclo> <notas.md> --reprovar <critérios ligados aos achados abertos>
```

- **Rodada curta** (`REVISAO_RODADA="curta"`): o revisor novo confere cada achado do registro, lê a correção e o que
  ela alcança (quem chama o código alterado, os invariantes que ele sustenta), roda as checagens do projeto no head
  novo e refaz as provas dos critérios de `--reprovar` e dos que a correção tocar. As provas dos outros critérios são
  copiadas do ciclo anterior e marcadas como herdadas ([`PROVAS.md`](PROVAS.md), "Rodada curta"). Defeito alto ou
  médio que ele encontrar fora da correção vale como achado.
- **Revisão completa:** o `mkrev.py` volta para ela sozinho, e avisa no stderr, quando falta o `--reprovar` (com
  nenhum critério ligado a achado, passe `--reprovar nenhum`), quando falta o head revisado do ciclo anterior, quando
  o histórico foi reescrito (rebase) ou quando a correção passa de `RODADA_MAX_LINHAS`. Peça com
  `--completa` quando a correção mexe em contrato público, dados, autenticação ou concorrência, ou quando o revisor da
  rodada curta concluir com `BLOQUEADO` e o motivo `RODADA: …`.

Motivo da rodada curta: nas segundas revisões medidas, 20 de 25 achados estavam na própria correção. O que escapar
dela fica para quem topar com o defeito e para a revisão final.

O limite continua em 2 devolutivas por tarefa. Rodada que volta só com achados baixos é aprovação.

## Revisão final do épico

Com `REVISAO_FINAL` diferente de `nao`, antes do fechamento ([`PLAYBOOK.md`](PLAYBOOK.md), passo 6), com todas as
tarefas e gates concluídos e a sincronização feita. Pule com 3 tarefas ou menos.

1. **Quem revisa.** `conselho`: um revisor por alvo de `CONSELHO`, todos ao mesmo tempo
   (`$E/bin/alvo.py --lista CONSELHO` dá um `target` por linha). O que o conselho compra é cada modelo vir de um
   provedor diferente: se um alvo não estiver no `orchestrator_capabilities`, registre e siga com os outros, sem
   trocar por outro modelo do mesmo provedor. `unico`: só o `REVISOR_CRITICO`.
2. **Brief.** `$E/bin/mkfinal.py <n> <alvo>` gera `tarefas/FINAL/brief-final-<n>.md`, o mesmo texto para todos
   (`<alvo>` é o item de posição `<n>` em `CONSELHO`).
   `delegate_task` com `role: "review"`, `isolation: "worktree"`, `clientRequestId` `<ORQ_ID>-final-<n>`. Registre
   com `agentes.py set FINAL rev-<n> …` e respeite as vagas do `capacidade.sh`.
3. **Resultados.** Confira cada achado contra o código assim que a revisão dele chegar, sem esperar as outras. Achado
   alto ou médio que você confirmar vira tarefa de correção proposta no BACKLOG, com a origem `revisão final`, e
   entra em "Precisa de você" no PAINEL: criar tarefa é decisão do usuário ([`ESCOPO.md`](ESCOPO.md)). Os baixos vão
   para as Propostas.
4. **Registro.** Uma rodada só. O fechamento leva a tabela: revisor, nota de 0 a 10, achados altos, médios e baixos,
   e quantos você confirmou. Revisor que não deu nota fica com `sem nota`.
