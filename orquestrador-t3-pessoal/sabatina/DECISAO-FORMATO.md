# Formato de uma decisão

Adaptação de `ADR-FORMAT.md` (Matt Pocock). A decisão vai para `$E/DECISOES.md`, numerada (`D-001`, `D-002`…).

## Modelo

```md
### D-00N · {Título curto da decisão}

{1–3 frases: o contexto, o que foi decidido e por quê.}
```

Só isso. Uma decisão pode ser um parágrafo. O valor está em registrar *que* foi decidido e *por quê*, não em
preencher seções.

## Seções opcionais

Só quando acrescentam algo. A maioria das decisões não precisa delas.

- **Status** (`proposta | aceita | obsoleta | substituída por D-00M`): quando a decisão é revisitada.
- **Alternativas consideradas:** só quando as recusadas merecem ser lembradas.
- **Consequências:** só quando há efeitos não óbvios que precisam ser ditos.

## O que costuma merecer registro

- **Forma da arquitetura.** "Monorepo." "Escrita orientada a eventos, leitura projetada no Postgres."
- **Integração entre contextos.** "Pedidos e Cobrança conversam por eventos, não por HTTP síncrono."
- **Tecnologia com aprisionamento.** Banco, fila, provedor de autenticação, alvo de deploy. Não toda biblioteca: só
  as que levariam um trimestre para trocar.
- **Fronteira e escopo.** "Os dados do Cliente são do contexto de Clientes; os outros guardam só o id." Os não valem
  tanto quanto os sim.
- **Desvios deliberados do caminho óbvio.** "SQL à mão em vez de ORM por causa de X." Evita que o próximo "conserte"
  algo que foi de propósito.
- **Restrições que o código não mostra.** "Nada de AWS por compliance." "Resposta abaixo de 200 ms por contrato com o
  parceiro."
- **Alternativas recusadas por motivo não óbvio.** Se GraphQL foi considerado e REST venceu por motivos sutis,
  registre; senão alguém sugere GraphQL de novo em seis meses.
