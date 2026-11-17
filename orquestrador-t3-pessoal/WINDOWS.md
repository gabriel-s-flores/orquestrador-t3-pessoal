# Rodando no Windows

A skill roda no Windows pelo **Git Bash**: os comandos dos documentos (`$E/bin/...`, `$S/bin/...`) valem como estão,
na ferramenta Bash. Os scripts detectam o Windows e trocam sozinhos o que só existe no Linux.

## Pré-requisitos

| Peça | Para quê | Conferir |
|---|---|---|
| Git for Windows 2.38+ | o bash que roda os scripts e os hooks; o `bin/base.py` usa `git merge-tree --write-tree` | `git --version` |
| Python 3.10+ no PATH como `python3` | todos os scripts de `bin/` | `python3 --version` |
| `psutil` | `orfaos.sh` (diretório atual de cada processo) | `python3 -m pip install --user psutil` |
| Modo de Desenvolvedor ligado | links simbólicos da pasta de estado para a skill | Configurações › Sistema › Para desenvolvedores |
| Node.js, `gh` autenticado, Chrome | `hml vivo`, PRs e provas, como no Linux | `node -v`, `gh auth status` |

## Instalação

```bash
git clone -c core.autocrlf=false https://github.com/gabriel-s-flores/orquestrador-t3-pessoal.git ~/.claude/repos/orquestrador-t3-pessoal
MSYS=winsymlinks:nativestrict ln -s ~/.claude/repos/orquestrador-t3-pessoal/orquestrador-t3-pessoal ~/.claude/skills/orquestrador-t3-pessoal
python3 -m pip install --user psutil
```

O `core.autocrlf=false` mantém os scripts com fim de linha LF: com CRLF o bash quebra. O `.gitattributes` do
repositório garante o mesmo num clone comum.

## O que muda por baixo

| Peça | Linux | Windows |
|---|---|---|
| Caminhos | `/home/...` | `C:/...` com barras normais (`ORQ`, briefs, hooks). Barra invertida fora de aspas some no bash |
| Python | UTF-8 por padrão | os scripts se reabrem com `-X utf8` (sem isso o Python lê e escreve em cp1252) |
| `capacidade.sh` | `/proc/loadavg`, `/proc/meminfo`, PSI | load = CPU ocupada × núcleos + fila do processador (amostra de 1 s); memória pela API do Windows; sem PSI |
| `slot` | `flock`, `nice`/`ionice`, `systemd-run` com `MemoryMax` | trava de arquivo do Windows, prioridade abaixo do normal, Job Object com `SLOT_MEM_MAX` (o comando que passa do teto recebe erro de memória) |
| `orfaos.sh` | `/proc/<pid>/cwd` | `psutil` |
| `hml`, cofre | `secret-tool` | Gerenciador de Credenciais, alvos `orq-hml-pessoal/<conta>/<campo>` |
| `hml`, sessão e arquivo | `~/.local/share/orquestrador-t3-pessoal/hml/<conta>/` | `%LOCALAPPDATA%\orquestrador-t3-pessoal\hml\<conta>\` |
| `hml`, Chrome | `google-chrome-stable` no PATH | `Program Files\Google\Chrome\Application\chrome.exe`, ou `HML_CHROME` no `orq.env` |
| `hml vivo`, `HML_SERVIDOR` | `bash -c` | o bash do Git (nunca o do WSL) e `taskkill /T` para derrubar o app |
| Hooks do `guarda.py` | `python3` | o caminho do Python que instalou o hook; hooks originais (husky) rodam pelo bash do Git |
| `nova-orquestracao.sh` | `ln -s` | link simbólico nativo; sem o Modo de Desenvolvedor, junção para pasta e cópia para arquivo |

## Agentes no PowerShell

O Codex e outros agentes podem rodar comandos no PowerShell. Lá, `bash` é o do WSL e não enxerga estes arquivos, e
script sem extensão não roda. Os briefs gerados no Windows já trazem uma seção "Esta máquina é Windows" com o caminho:

```powershell
& "C:/Program Files/Git/bin/bash.exe" -lc '<estado>/bin/slot test -- npm test'
```

Comando com pipe, redirecionamento ou `VAR=valor` na frente, dentro do `slot` ou da `prova`: `-- bash -c '<comando>'`.
O `bash` ali é resolvido para o do Git.

## Limites conhecidos

- O load do Windows sai de uma amostra curta, não de uma média de 1 e 5 minutos: os dois números são iguais.
  `CARGA_MAX` e `CARGA_CRITICA` continuam valendo (`capacidade.sh --sugerir`).
- `PSI_CPU_MAX` e `PSI_MEM_MAX` não têm efeito: o Windows não tem PSI. A memória livre e o load seguram o despacho.
- `nova-orquestracao.sh` sem o Modo de Desenvolvedor copia `PROVAS.md`, `AMBIENTE.md`, `MODELOS.md`, `ESCOPO.md`,
  `REVISAO.md` e `INTEGRACAO.md`: depois de atualizar a skill, copie de novo.
