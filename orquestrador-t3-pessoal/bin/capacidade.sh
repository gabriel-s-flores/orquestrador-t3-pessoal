#!/usr/bin/env bash
# Quantos agentes cabem agora sem travar a máquina. Lê load, memória, swap e PSI (/proc/pressure) e os agentes
# ativos registrados. Imprime uma linha de leitura e AGENTES=, VAGAS=, ABERTAS=, VAGAS_IMPL=, ESTADO=ok|apertado|critico
# e MOTIVO=. VAGAS vale para qualquer agente; VAGAS_IMPL, para implementação nova: zera quando os PRs abertos para o
# épico mais as implementações que ainda vão abrir PR chegam a MAX_PRS_ABERTOS (vazio = MAX_AGENTES + 1). Cada PR aberto
# a mais é um PR a mais para envelhecer atrás da base (INTEGRACAO.md).
# No Windows não há load nem PSI: o load vem da CPU ocupada × núcleos + a fila do processador (_orq.metricas).
# Uso: <estado>/bin/capacidade.sh            leitura para o despacho
#      <estado>/bin/capacidade.sh --sugerir  valores de paralelismo para o orq.env desta máquina
if [ "${1:-}" != "--sugerir" ]; then . "$(dirname "$0")/_comum.sh"; fi
export PYTHONUTF8=1
PRS=
if [ "${1:-}" != "--sugerir" ] && [ -n "${REPO:-}" ] && [ -n "${BASE:-}" ]; then
  # API REST: o limite dela é separado do GraphQL, que a vigília de PR já gasta.
  PRS=$(gh api --method GET "repos/$REPO/pulls" -f state=open -f base="$BASE" -f per_page=100 --jq length 2>/dev/null || true)
fi
PRS="$PRS" ORQ_BIN=$(cd "$(dirname "$0")" && (pwd -W 2>/dev/null || pwd)) \
ATIVOS=$("${ORQ:-.}/bin/agentes.py" ativos --contar 2>/dev/null || echo 0) MODO="${1:-}" exec python3 - <<'PY'
import os, sys, math, glob, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.environ['ORQ_BIN'])
from _orq import metricas
E = os.environ
def num(k, padrao):
    try: return float(E.get(k, '') or padrao)
    except ValueError: return float(padrao)
M = metricas()
total, livre, swap_usada, cpus = M['total'], M['livre'], M['swap'], M['cpus']
load1, load5 = M['load1'], M['load5']
cpu_some, mem_some, mem_full, io_some = M['cpu_some'], M['mem_some'], M['mem_full'], M['io_some']

if E.get('MODO') == '--sugerir':
    print('# sugestão para esta máquina:', cpus, 'CPUs,', round(total), 'GB')
    print(f'MAX_AGENTES={min(8, max(2, int(total // 5)))}')
    print(f'CARGA_MAX={round(cpus * 0.85, 1)}')
    print(f'CARGA_CRITICA={round(cpus * 1.5, 1)}')
    print(f'RESERVA_MEM_GB={max(4, round(total * 0.15))}')
    print(f'SLOTS_BUILD={max(1, cpus // 8)}')
    print(f'SLOTS_TEST={max(1, cpus // 4)}')
    print(f'SLOTS_BROWSER={1 if total < 24 else 2}')
    print('SLOTS_INSTALL=1')
    print(f'SLOT_MEM_MAX="{max(2, int(total * 0.2))}G"')
    raise SystemExit

maxag = int(num('MAX_AGENTES', 6)); ativos = int(num('ATIVOS', 0))
carga_max, carga_crit = num('CARGA_MAX', cpus * 0.85), num('CARGA_CRITICA', cpus * 1.5)
reserva, por_agente = num('RESERVA_MEM_GB', 5), num('MEM_POR_AGENTE_GB', 2.5)
psi_cpu, psi_mem = num('PSI_CPU_MAX', 40), num('PSI_MEM_MAX', 10)
motivos_crit, motivos = [], []
if livre < reserva / 2: motivos_crit.append(f'memória livre {livre:.1f} GB < metade da reserva')
if mem_full > 5: motivos_crit.append(f'PSI memória full {mem_full:.0f}%')
if load1 > carga_crit: motivos_crit.append(f'load {load1:.1f} > crítico {carga_crit:g}')
if load1 > carga_max: motivos.append(f'load {load1:.1f} > teto {carga_max:g}')
if cpu_some > psi_cpu: motivos.append(f'PSI CPU {cpu_some:.0f}% > {psi_cpu:g}%')
if mem_some > psi_mem: motivos.append(f'PSI memória {mem_some:.0f}% > {psi_mem:g}%')
vagas_mem = math.floor((livre - reserva) / por_agente)
if vagas_mem <= 0: motivos.append(f'memória livre {livre:.1f} GB sem folga além da reserva {reserva:g}')
estado = 'critico' if motivos_crit else ('apertado' if motivos else 'ok')
vagas = 0 if estado != 'ok' else max(0, min(maxag - ativos, vagas_mem, int(num('DESPACHO_POR_ITERACAO', 2))))
if estado == 'ok' and vagas == 0:
    motivos.append(f'teto de agentes {ativos}/{maxag}')
# Implementações que ainda vão abrir PR: implementador rodando numa tarefa sem evento "pronto".
sem_pr = 0
for f in glob.glob(os.path.join(E.get('ORQ', '.'), 'tarefas', '*', 'agentes.json')):
    try:
        impl = json.load(open(f, encoding='utf-8')).get('impl', {})
        ev = os.path.join(os.path.dirname(f), 'eventos.jsonl')
        pronto = os.path.exists(ev) and '"evento": "pronto"' in open(ev, encoding='utf-8').read()
    except (OSError, ValueError):
        continue
    if impl.get('estado') in ('rodando', 'pausando') and not pronto:
        sem_pr += 1
teto = int(num('MAX_PRS_ABERTOS', maxag + 1)); prs = E.get('PRS', '').strip()
if prs.isdigit():
    abertas = int(prs) + sem_pr
    vagas_impl = max(0, min(vagas, teto - abertas))
    linha_abertas = f'ABERTAS={abertas}/{teto} ({prs} PR(s) aberto(s) + {sem_pr} implementação(ões) sem PR)'
    if vagas > 0 and vagas_impl == 0:
        motivos.append(f'teto de PRs abertos {abertas}/{teto}: vaga só para integração e revisão')
else:
    vagas_impl = vagas
    linha_abertas = f'ABERTAS=?/{teto} (o gh não respondeu: sem teto de PRs nesta leitura)'
psi = (f'PSI cpu {cpu_some:.0f}% mem {mem_some:.0f}%/{mem_full:.0f}% io {io_some:.0f}%' if M['psi']
       else (f'CPU ocupada {M["cpu_uso"]:.0f}% · sem PSI no Windows' if 'cpu_uso' in M else 'sem PSI'))
print(f'CPU {cpus} · load {load1:.2f}/{load5:.2f} (teto {carga_max:g}, crítico {carga_crit:g}) · memória livre {livre:.1f} '
      f'de {total:.0f} GB (reserva {reserva:g}) · swap {swap_usada:.1f} GB · {psi}')
print(f'AGENTES={ativos}/{maxag}')
print(f'VAGAS={vagas}')
print(linha_abertas)
print(f'VAGAS_IMPL={vagas_impl}')
print(f'ESTADO={estado}')
print('MOTIVO=' + ('; '.join(motivos_crit + motivos) or '—'))
PY
