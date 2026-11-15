#!/usr/bin/env bash
# Varredura de toda iteração: o que está em disco, no host de PRs e na máquina. O estado dos agentes no T3 o
# orquestrador lê com task_status (T3-V2.md); aqui ficam os agentes registrados para ele conferir um a um.
. "$(dirname "$0")/_comum.sh"
echo "--- controles"
for f in PAUSAR PAUSADO; do [ -e "$ORQ/$f" ] && echo "$f: $(head -c 200 "$ORQ/$f" | tr '\n' ' ')"; done
echo "heartbeat: $(cat "$ORQ/HEARTBEAT" 2>/dev/null || echo 'sem id (criar no passo 0)')"
[ -e "$ORQ/AGENDA" ] && echo "agenda: $(tr '\n' ' ' < "$ORQ/AGENDA")"
echo "--- agentes registrados (rodando/pausando) → confira cada um com task_status"
"$ORQ/bin/agentes.py" ativos
echo "--- PRs abertos para $BASE"
gh pr list -R "$REPO" --base "$BASE" --state open --json number,headRefName,headRefOid,mergeable \
  --jq '.[]|"\(.number) \(.headRefName) \(.headRefOid[0:9]) \(.mergeable)"'
echo "--- tarefas ativas no PAINEL × sinais em disco"
python3 - "$ORQ" <<'PY'
import os, re, sys, time, subprocess
O = sys.argv[1]
ativos = ('implementando', 'corrigindo', 'em revisão', 'aprovada', 'pausando', 'pausada')
idade = lambda p: f'{int((time.time() - os.path.getmtime(p)) // 60)} min' if os.path.exists(p) else '—'
for l in open(f'{O}/PAINEL.md'):
    c = [x.strip() for x in l.strip().strip('|').split('|')]
    if len(c) < 9 or not re.match(r'^[A-Za-z][\w.-]*$', c[0]) or c[0] == 'ID':
        continue
    tid, st, ciclo = c[0], c[5], c[8]
    if not st.startswith(ativos):
        continue
    d = f'{O}/tarefas/{tid}'; n = re.sub(r'\D', '', ciclo) or '0'
    sinais = []
    rev = f'{d}/revisao-c{n}.md'
    if st.startswith('em revisão') and os.path.exists(rev):
        cab = ' · '.join(x.strip() for x in open(rev).read().splitlines()[1:3])
        r = subprocess.run([sys.executable, f'{O}/bin/provas.py', tid, n], capture_output=True, text=True)
        prov = (re.findall(r'^Resultado: (\w+)', r.stdout, re.M) or ['sem manifesto'])[0]
        sinais.append(f'REVISÃO c{n} ESCRITA ({cab} · provas {prov}) — processar já')
    if os.path.exists(f'{d}/revisao-c{n}.parcial.md'):
        sinais.append(f'revisão parcial c{n}')
    sinais.append(f'relatório há {idade(d + "/relatorio.md")}')
    print(f'{tid} | {st} | c{n} | ' + ' · '.join(sinais))
PY
echo "--- limites e ambiente de teste"
"$ORQ/bin/guarda.py" checar 2>&1 | tail -1
"$ORQ/bin/hml" checar 2>&1 | tail -1
echo "--- processos órfãos nas worktrees"
"$ORQ/bin/orfaos.sh"
echo "--- carga"
"$ORQ/bin/capacidade.sh"
