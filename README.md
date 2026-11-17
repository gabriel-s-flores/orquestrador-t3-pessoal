# orquestrador-t3-pessoal

Skill para Claude Code / T3 Code: orquestração AFK de agentes com o Orchestrator V2 em projetos pessoais no GitHub
(sabatina no planejamento, implementador + revisor adversarial por tarefa, provas antes do merge, branch de épico,
guarda contra scope creep, pausa segura, painel e diário).

## Instalação

```bash
git clone https://github.com/gabriel-s-flores/orquestrador-t3-pessoal.git
ln -s "$PWD/orquestrador-t3-pessoal/orquestrador-t3-pessoal" ~/.claude/skills/orquestrador-t3-pessoal
```

Pede `git` 2.38 ou mais novo (o `bin/base.py` usa `git merge-tree --write-tree`), `python3` 3.10+ e o `gh` autenticado.

No Windows (Git Bash, com o Modo de Desenvolvedor ligado para os links simbólicos):

```bash
git clone -c core.autocrlf=false https://github.com/gabriel-s-flores/orquestrador-t3-pessoal.git ~/.claude/repos/orquestrador-t3-pessoal
MSYS=winsymlinks:nativestrict ln -s ~/.claude/repos/orquestrador-t3-pessoal/orquestrador-t3-pessoal ~/.claude/skills/orquestrador-t3-pessoal
python3 -m pip install --user psutil
```

Detalhes em [`orquestrador-t3-pessoal/WINDOWS.md`](orquestrador-t3-pessoal/WINDOWS.md).

Comece por [`orquestrador-t3-pessoal/SKILL.md`](orquestrador-t3-pessoal/SKILL.md).
