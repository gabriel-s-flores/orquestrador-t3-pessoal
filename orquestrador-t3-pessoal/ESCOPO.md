# Escopo fechado · as três barreiras contra scope creep

Scope creep entra por quatro portas: o implementador "aproveita para melhorar", o revisor pede extras na devolutiva,
o orquestrador cria tarefas que ninguém pediu e o plano nasce sem limites. Cada porta tem uma barreira.

## O contrato de cada tarefa

Toda entrada do BACKLOG tem, além de escopo e aceite:

- **Fora do escopo:** o que parece próximo e não entra (vem dos não-objetivos da sabatina, no `PLANO.md`).
- **Arquivos:** globs das áreas que a tarefa pode tocar (`src/auth/**, test/auth/**`). Arquivo fora delas precisa
  de justificativa.
- **Orçamento:** tamanho esperado do diff em linhas (`~300`). É um sinal, não um teto rígido.

O brief do implementador e o do revisor trazem esse contrato inteiro.

## Barreira 1 · plano (montagem)

- A sabatina só termina com os **não-objetivos** escritos e aceitos pelo usuário.
- Cada tarefa do BACKLOG cita o requisito do `PLANO.md` (`R<n>`) ou o critério que atende. Tarefa sem origem não entra.
- O revisor do plano (`PLANO_REVISOR`) procura tarefas que extrapolam o plano e requisitos sem tarefa.

## Barreira 2 · implementação e conferência objetiva

- O implementador entrega o aceite e nada além. Bug, refatoração ou melhoria fora do escopo vai para a seção
  **Propostas** do relatório, nunca para o código.
- O relatório tem o **Mapa de escopo**: cada arquivo alterado → o critério de aceite ou item X.Y que o justifica.
- Antes de gastar um ciclo de revisão, o orquestrador roda
  `<estado>/bin/escopo.py <ID> --head <sha do PR> > tarefas/<ID>/escopo-c<N>.md` (no `CHECKOUT`, depois do fetch).
  - Arquivo fora dos globs sem linha no Mapa de escopo, dependência nova não prevista, CI ou configuração tocada sem
    pedido, ou diff acima de 2× o orçamento → devolva ao implementador com `t3_thread_send` ("corte ou justifique").
    Isso não conta como ciclo.

## Barreira 3 · revisão

O revisor faz uma **auditoria de escopo** obrigatória e escreve `Escopo: DENTRO | EXTRAPOLA` na revisão.

| O que achou | Severidade |
|---|---|
| Mudança necessária para o aceite, explicada no Mapa de escopo | ok |
| Refatoração, renomeação ou "melhoria" não pedida; feature extra; mudança de comportamento não pedida; dependência nova não prevista | **média** (bloqueia) |
| Mudança em contrato público, dados, segurança ou CI fora do escopo | **alta** |
| Critério de aceite não atendido (escopo a menos) | alta ou média, conforme o critério |

O revisor também não amplia o escopo: **sugestão de melhoria não é achado**. Vai na seção "Fora do escopo /
propostas" da revisão.

## O que o orquestrador faz com os extras

- **Devolutiva obrigatória** = achados altos e médios ligados a aceite, correção, regressão, segurança ou escopo.
  Sugestões não entram.
- **Propostas** (do implementador, do revisor ou suas) vão para `## Propostas` no BACKLOG, com origem e motivo, no
  status `proposta`. Nunca são despachadas sem o "pode" do usuário.
- **Achados baixos dentro do escopo** de tarefas concluídas se juntam numa única tarefa de limpeza, que também
  precisa do "pode".
- Você não cria tarefa nova, não muda aceite e não amplia globs sem o usuário. Uma tarefa que só fecha com escopo
  maior vira `em espera`, com a pergunta no PAINEL.
