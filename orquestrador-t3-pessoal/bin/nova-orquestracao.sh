#!/usr/bin/env bash
# Cria a pasta de estado de uma orquestração nova com os modelos da skill e, se existir, os seus padrões
# (~/.config/orquestrador-t3-pessoal/perfil.env: linhas CHAVE=valor que substituem as do orq.env). A pasta fica fora de qualquer repositório.
# Uso: <skill>/bin/nova-orquestracao.sh <pasta-de-estado>
set -euo pipefail
S=$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)
E=${1:?uso: nova-orquestracao.sh <pasta-de-estado>}
PERFIL=${ORQ_PERFIL:-$HOME/.config/orquestrador-t3-pessoal/perfil.env}
[ -e "$E/orq.env" ] && { echo "nova-orquestracao: $E/orq.env já existe" >&2; exit 1; }
pai=$E; while [ ! -d "$pai" ]; do pai=$(dirname "$pai"); done
if git -C "$pai" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "nova-orquestracao: $E fica dentro de um repositório git; use uma pasta fora dele" >&2; exit 1
fi
mkdir -p "$E/tarefas" "$E/modelos"; E=$(cd "$E" && pwd)
ln -sfn "$S/bin" "$E/bin"; ln -sfn "$S/escrita" "$E/escrita"
ln -sfn "$S/PROVAS.md" "$E/PROVAS.md"; ln -sfn "$S/AMBIENTE.md" "$E/AMBIENTE.md"
ln -sfn "$S/MODELOS.md" "$E/MODELOS.md"; ln -sfn "$S/ESCOPO.md" "$E/ESCOPO.md"
cp "$S"/modelos/{PAINEL.md,DIARIO.md,BACKLOG.md} "$E/"
cp "$S"/modelos/{brief-implementador.md,brief-revisor.md,relatorio.md} "$E/modelos/"
python3 - "$S/modelos/orq.env" "$PERFIL" "$E/orq.env" <<'PY'
import os, re, sys, shlex
modelo, perfil, saida = sys.argv[1:]
valores = {}
if os.path.exists(perfil):
    for l in open(perfil):
        m = re.match(r'^([A-Z_][A-Z0-9_]*)=(.*)$', l.strip())
        if m: valores[m.group(1)] = (shlex.split(m.group(2), comments=True) or [''])[0]
out, aplicados = [], 0
for l in open(modelo):
    m = re.match(r'^([A-Z_][A-Z0-9_]*)=("[^"]*"|\S*)(\s*#.*)?$', l.rstrip('\n'))
    if m and m.group(1) in valores:
        l = f'{m.group(1)}="{valores[m.group(1)]}"{m.group(3) or ""}\n'; aplicados += 1
    out.append(l)
open(saida, 'w').write(''.join(out))
faltam = [re.match(r'^([A-Z_]+)=', l).group(1) for l in out if re.match(r'^[A-Z_]+="?<', l)]
print(f'orq.env: {aplicados} valor(es) do perfil aplicados' + (f'; preencha: {", ".join(faltam)}' if faltam else ''))
PY
echo "pasta de estado pronta: $E"
