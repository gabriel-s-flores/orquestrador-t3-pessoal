# Backlog

Cada tarefa tem um ID curto (ex.: `T1.2`), dependências, classe, contrato de escopo, critérios de aceite
verificáveis e as provas que o revisor produz. A fase é a seção `## ` em que a tarefa está. Todas as branches
saem da branch do épico e voltam para ela por PR. Gates (`G1`…) são pontos de avaliação: as tarefas depois deles
dependem do gate aprovado. Classes, effort e modelos em `MODELOS.md`; escopo em `ESCOPO.md`; provas em `PROVAS.md`.
A classe escolhe o modelo. O `Effort` é opcional (`medium` ou `high`): `—` vale o padrão da classe.

## Fase 1 — <nome>

### T1.1 · <título curto>
- **Issue:** <#número da issue no GitHub ou —> · **Origem:** <requisito R<n> do PLANO.md ou critério que esta tarefa atende>
- **Depende de:** — · **Classe:** M · **Effort:** —
- **Escopo:** <o que fazer e onde>
- **Fora do escopo:** <o que parece próximo e não entra>
- **Arquivos:** <globs das áreas permitidas, ex.: src/auth/**, test/auth/**>
- **Orçamento:** <tamanho esperado do diff, ex.: ~300 linhas>
- **Aceite:** <condições checáveis, uma por linha e numeradas (1.1, 1.2…): comandos que passam, números medidos, cenários. O caso que cada regra nega (entrada inválida, sem permissão, repetição, vazio) entra como item próprio>
- **Evidências:** <o que o implementador entrega em evidencias/>
- **Provas:** <tipos que o revisor precisa produzir: log, print, vídeo, medição, requisição; tela → print, vídeo>
- **Branch:** <PREFIXO/id-da-tarefa-descricao, a partir da branch do épico>

## Propostas

Ideias fora do escopo vindas do implementador, do revisor ou do orquestrador. Nenhuma é despachada sem o "pode" do
usuário; aprovada, vira tarefa acima.

| Proposta | Origem | Motivo | Status |
|---|---|---|---|
