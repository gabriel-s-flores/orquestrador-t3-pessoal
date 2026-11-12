# Sabatina · entrevista implacável até o entendimento comum

Adaptação em português de `grilling` / `grill-me` (Matt Pocock). Use para dar forma a uma ideia, plano ou decisão
antes de qualquer artefato: nas etapas 1 e 2 da [`MONTAGEM.md`](../MONTAGEM.md). Com vocabulário de domínio em jogo, use junto com [`MODELAGEM.md`](MODELAGEM.md):
essa combinação é o `grill-with-docs`.

Entreviste o usuário sem trégua até chegarem a um entendimento comum. Organize tudo como uma **árvore de decisões**:
cada decisão abre as decisões que dependem dela.

## Rodadas e fronteira

Trabalhe a árvore em **rodadas**. A **fronteira** é o conjunto das decisões cujos pré-requisitos já estão
resolvidos: as perguntas que dá para fazer *agora* sem chutar respostas que você ainda não ouviu. Pergunte a
fronteira inteira numa rodada, sempre com a sua recomendação. Depois espere as respostas antes da próxima rodada.

## Como perguntar: o painel do `AskUserQuestion`

Com o usuário presente, a rodada vai pela ferramenta `AskUserQuestion`, nunca como lista em texto. No T3, uma
chamada abre um painel no lugar do compositor, com **uma pergunta por vez**: ele clica numa alternativa e avança em
**Next question**, volta em **Previous** e termina em **Submit answers**. Se ele escrever no compositor, o texto
vale como resposta livre e substitui a alternativa marcada. Detalhes do T3 em [`../T3-V2.md`](../T3-V2.md).

1. **Antes do painel**, numa mensagem curta: os fatos que você conferiu e que mudam as perguntas (até 6 linhas,
   tabela se forem muitos). O painel não mostra tabela bem; a mensagem sim.
2. **Uma chamada leva até 4 perguntas.** Com mais de 4 na fronteira, faça primeiro as 4 que destravam mais ramos e
   chame de novo logo depois de receber as respostas, no mesmo turno. Uma pergunta que depende de outra ainda sem
   resposta vai para uma chamada seguinte.
3. **Cada pergunta** segue este molde:

   | Campo | Regra |
   |---|---|
   | `header` | Rótulo da pergunta, até 12 caracteres (ex.: `Spinner`, `Ease`, `Deploy`). Aparece como etiqueta |
   | `question` | O contexto e a pergunta, até 70 palavras, terminando em `?`. Aceita Markdown curto (código entre crases). O texto precisa ser único: o T3 usa a pergunta como chave da resposta |
   | `options` | De 2 a 4 alternativas que se excluem. A recomendada vem primeiro, com ` (Recomendado)` no fim do `label` |
   | `label` | De 1 a 5 palavras, o que a pessoa escolhe (ex.: `Pulso de opacidade`) |
   | `description` | Uma frase, até 25 palavras: o que acontece se ela escolher essa, e o porquê na recomendada |
   | `multiSelect` | `true` só quando as alternativas não se excluem |

   Não crie a alternativa "Outro": o compositor já é a resposta livre. Não use `preview`: o T3 descarta esse campo;
   um trecho de código curto vai na `question`.
4. **Confira antes de chamar:** grave o JSON da chamada num arquivo e rode `texto.py --tipo pergunta <arquivo>`.
   Ele valida a forma acima e os vícios de escrita de [`../escrita/ESCRITA.md`](../escrita/ESCRITA.md).
5. **Depois das respostas**, escreva uma linha por pergunta na conversa (`Spinner: pulso de opacidade`), marcando
   as respostas livres e as que contrariaram a recomendação. É o registro que o resumo final usa.

Se o usuário fechar o painel sem responder, a chamada volta como cancelada: pare e pergunte em uma linha se ele
quer seguir. Não aplique as recomendações em silêncio.

**Sem o painel** (o provedor não tem `AskUserQuestion`, ou a sabatina roda fora do T3), use a rodada em texto,
conferida com `texto.py --tipo sabatina`:

```text
❓ **P1** - **<título da pergunta>**: <corpo da pergunta e as alternativas numeradas>

➡️ <sua resposta recomendada, com o porquê em uma linha>
```

Cada rodada respondida remodela a árvore: decisões resolvidas empurram a fronteira para fora e liberam as perguntas
que dependiam delas. Recalcule a fronteira e faça a próxima rodada. Uma pergunta cuja resposta depende de outra
ainda aberta nesta rodada fica para uma rodada *seguinte*, não para esta.

## Fatos são seus; decisões são do usuário

Descobrir **fatos** é trabalho seu, nunca do usuário. Quando uma pergunta da fronteira precisa de um fato do
ambiente (código, arquivos, issues, ferramentas), despache um subagente para buscá-lo (Haiku 5.5: agente
`Explore` com `model: "haiku"`). Não pergunte ao usuário nada que você mesmo consiga verificar.

Não trave esperando: uma busca em andamento é um pré-requisito não resolvido. Só as perguntas que dependem dela
esperam o subagente voltar; faça o resto da fronteira agora.

As **decisões** são do usuário: leve cada uma até ele e espere.

## Fim

A sabatina termina quando a fronteira esvazia: todos os ramos da árvore visitados, nada assumido em silêncio. Não
aja sobre o resultado até o usuário confirmar que vocês chegaram a um entendimento comum.

Feche com um resumo curto: as decisões tomadas, os **não-objetivos** e o que ficou para depois. Esse resumo alimenta
o `PLANO.md` e o contrato de escopo das tarefas ([`ESCOPO.md`](../ESCOPO.md)).

## Ramos que não podem faltar

Numa ideia de produto ou feature:

- o problema e para quem; o que muda para essa pessoa quando estiver pronto;
- o "fim": o que precisa ser verdade para dizer que terminou;
- os **não-objetivos**: o que parece próximo e fica de fora, dito em voz alta;
- critérios de aceite verificáveis por comando, teste ou medição;
- restrições: prazos, compatibilidade, desempenho, segurança, dados, contratos com terceiros;
- riscos e o que fazer se cada um acontecer;
- o que já existe no código e na documentação (fatos: busque antes de perguntar).

Numa orquestração, os ramos da etapa 2 da [`MONTAGEM.md`](../MONTAGEM.md).

## Postura

- Recomende sempre: quem responde "não sei" precisa de uma opção concreta para aceitar ou recusar.
- Desafie respostas vagas ("rápido", "simples", "igual ao outro") até virarem algo verificável.
- Uma resposta que contradiz outra anterior reabre o ramo: aponte a contradição e pergunte qual vale.
- Rodadas curtas: no máximo 7 perguntas, em até 2 chamadas do painel. Se a fronteira tiver mais, faça primeiro as
  que destravam mais ramos.
- Uma resposta livre que não cabe em nenhuma alternativa vale como está. Se ela for vaga, a próxima chamada
  desafia com alternativas concretas.
