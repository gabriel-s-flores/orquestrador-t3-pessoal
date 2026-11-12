# Vícios de escrita de IA em português

Adaptação do catálogo do `unslop` (`references/taboo-phrases.md`) para o português do Brasil. A lista exata de
padrões que o verificador usa sai de `<estado>/bin/texto.py --catalogo`. Lista nenhuma é completa: reconheça pela
função o vício escrito de outro jeito.

**Grave** bloqueia o envio. **Leve** pede um olhar: é vício quando a frase perde nada sem ele.

## Graves

| Vício | Exemplos | Conserto |
|---|---|---|
| Abertura que atrasa | "Vale ressaltar que", "É importante destacar que", "Cabe lembrar", "Vamos lá", "A verdade é que", "Antes de mais nada" | Corte e comece pelo fato |
| Ênfase fabricada | "Isso é muito importante", "Faz toda a diferença", "Não se engane", "Sem sombra de dúvida", "Divisor de águas" | Corte; o fato mostra a importância |
| Resto de chatbot | "Ótima pergunta!", "Claro!", "Espero ter ajudado", "Fico à disposição", "Qualquer dúvida, é só chamar" | Corte |
| Meta-comentário | "Neste relatório vou apresentar", "A seguir, apresento", "Conforme mencionado anteriormente", "Em suma", "Dito isso" | Corte; diga direto |
| Raciocínio vazado | "Vamos pensar passo a passo", "Deixa eu ver", "Meu raciocínio foi" | Dê a conclusão, depois a evidência |
| Conclusão genérica | "Foi um grande sucesso", "Tudo está funcionando perfeitamente", "Um passo importante", "Abre caminho para", "Garantimos qualidade e eficiência" | Diga o resultado medido: testes, números, o que entrou |
| Tamanho acima do limite | ver os formatos em [`ESCRITA.md`](ESCRITA.md) | Mova o detalhe para um arquivo e aponte o caminho |
| Travessões em série em texto curto | "a entrega — que potencializa — e garante" | Vírgula, ponto ou dois-pontos |

## Leves

| Vício | Exemplos | Conserto |
|---|---|---|
| Intensificador e adjetivo inflado | "extremamente", "realmente", "de fato", "crucial", "robusto", "abrangente", "significativo", "fundamental" | Corte, ou troque por um número |
| Jargão corporativo | "alavancar", "potencializar", "agregar valor", "sinergia", "jornada", "endereçar", "performar", "insights", "mindset" | Usar, aumentar, resolver, funcionar, conclusões |
| Enchimento | "realizar a implementação", "fez a validação", "no sentido de", "a nível de", "visando", "com o objetivo de", "sendo que", "através de" | Implementar, validou, para, em, por |
| "O mesmo" como pronome | "verifique o arquivo e edite o mesmo", "o mesmo foi aprovado" | Ele, ela, isso, ou repita o nome |
| Gerundismo | "vou estar enviando" | Vou enviar, envio |
| Rodeio formal | "no que diz respeito a", "tendo em vista que", "devido ao fato de que", "é possível observar que" | Sobre, como, porque, (corte) |
| Contraste dramático | "Não é só X, é Y", "Não se trata de X, mas de Y" | Diga Y |
| Atribuição vaga | "especialistas dizem", "estudos mostram", "tudo indica que" | Quem, onde, qual número |
| Falso cognato | "eventualmente" (no sentido de "no fim"), "assumir que" (supor), "realizei que" (percebi) | Por fim, supor, percebi |
| Forma | exclamação, reticências, "etc.", negrito na frase inteira, Título Com Maiúsculas, emoji decorativo, frase com mais de 35 palavras, parágrafo com mais de 3 linhas | Ver as regras de forma em [`ESCRITA.md`](ESCRITA.md) |

## Protegidos

Não são vícios, mesmo que o script aponte:

- termos técnicos do dia a dia: PR, merge, branch, commit, rebase, worktree, CI, deploy, build, lint, feature flag;
- nomes de tarefas, títulos de issue, nomes de arquivos, comandos e mensagens de erro;
- citações entre aspas e trechos de código;
- "fundamental" e "essencial" quando dizem o que depende de quê ("a migração é pré-requisito da T2.1");
- "nunca", "sempre", "obrigatório" e "todos" em regras de segurança, de escopo ou do projeto.
