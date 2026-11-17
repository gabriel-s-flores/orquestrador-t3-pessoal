#!/usr/bin/env bash
# Cria a pasta de estado de uma orquestração nova com os modelos da skill e, se existir, os seus padrões
# (~/.config/orquestrador-t3-pessoal/perfil.env: linhas CHAVE=valor que substituem as do orq.env). A pasta fica fora de qualquer repositório.
# No Git Bash (Windows) os links são links simbólicos nativos (Modo de Desenvolvedor ligado); sem permissão, a pasta
# vira junção e o arquivo vira cópia (WINDOWS.md).
# Uso: <skill>/bin/nova-orquestracao.sh <pasta-de-estado>
set -euo pipefail
case "$(uname -s 2>/dev/null)" in MINGW*|MSYS*|CYGWIN*) WIN=1; export MSYS=winsymlinks:nativestrict PYTHONUTF8=1 ;; *) WIN= ;; esac
S=$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)
E=${1:?uso: nova-orquestracao.sh <pasta-de-estado>}
PERFIL=${ORQ_PERFIL:-$HOME/.config/orquestrador-t3-pessoal/perfil.env}
[ -e "$E/orq.env" ] && { echo "nova-orquestracao: $E/orq.env já existe" >&2; exit 1; }
pai=$E; while [ ! -d "$pai" ]; do pai=$(dirname "$pai"); done
if git -C "$pai" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "nova-orquestracao: $E fica dentro de um repositório git; use uma pasta fora dele" >&2; exit 1
fi
mkdir -p "$E/tarefas" "$E/modelos"; E=$(cd "$E" && pwd)
ligar() {  # ligar <origem> <destino>
  if [ -z "$WIN" ]; then ln -sfn "$1" "$2"; return; fi
  rm -rf "$2" 2>/dev/null || true
  ln -s "$1" "$2" 2>/dev/null && return
  if [ -d "$1" ]; then
    cmd //c mklink //J "$(cygpath -w "$2")" "$(cygpath -w "$1")" >/dev/null && return
  fi
  echo "nova-orquestracao: sem link simbólico (ligue o Modo de Desenvolvedor do Windows); copiei $2" >&2
  cp -r "$1" "$2"
}
ligar "$S/bin" "$E/bin"; ligar "$S/escrita" "$E/escrita"
ligar "$S/PROVAS.md" "$E/PROVAS.md"; ligar "$S/AMBIENTE.md" "$E/AMBIENTE.md"
ligar "$S/MODELOS.md" "$E/MODELOS.md"; ligar "$S/ESCOPO.md" "$E/ESCOPO.md"
ligar "$S/REVISAO.md" "$E/REVISAO.md"; ligar "$S/INTEGRACAO.md" "$E/INTEGRACAO.md"
cp "$S"/modelos/{PAINEL.md,DIARIO.md,BACKLOG.md} "$E/"
cp "$S"/modelos/{brief-implementador.md,brief-revisor.md,brief-revisor-rodada.md,brief-revisao-final.md,achados.md,relatorio.md} "$E/modelos/"
python3 - "$S/modelos/orq.env" "$PERFIL" "$E/orq.env" <<'PY'
import os, re, sys, shlex
modelo, perfil, saida = sys.argv[1:]
valores = {}
if os.path.exists(perfil):
    for l in open(perfil, encoding='utf-8'):
        m = re.match(r'^([A-Z_][A-Z0-9_]*)=(.*)$', l.strip())
        if m: valores[m.group(1)] = (shlex.split(m.group(2), comments=True) or [''])[0]
out, aplicados = [], 0
for l in open(modelo, encoding='utf-8'):
    m = re.match(r'^([A-Z_][A-Z0-9_]*)=("[^"]*"|\S*)(\s*#.*)?$', l.rstrip('\r\n'))
    if m and m.group(1) in valores:
        l = f'{m.group(1)}="{valores[m.group(1)]}"{m.group(3) or ""}\n'; aplicados += 1
    out.append(l)
with open(saida, 'w', encoding='utf-8', newline='\n') as f:  # LF: o bash lê o orq.env
    f.write(''.join(out))
faltam = [re.match(r'^([A-Z_]+)=', l).group(1) for l in out if re.match(r'^[A-Z_]+="?<', l)]
print(f'orq.env: {aplicados} valor(es) do perfil aplicados' + (f'; preencha: {", ".join(faltam)}' if faltam else ''))
PY
if [ -n "$WIN" ]; then E=$(cygpath -m "$E"); fi
echo "pasta de estado pronta: $E"
