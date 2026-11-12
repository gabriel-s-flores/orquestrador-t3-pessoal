#!/usr/bin/env bash
# Quantos agentes cabem agora sem travar a máquina. Lê load, memória, swap e PSI (/proc/pressure) e os agentes
# ativos registrados. Imprime uma linha de leitura e AGENTES=, VAGAS=, ESTADO=ok|apertado|critico e MOTIVO=.
# Uso: <estado>/bin/capacidade.sh            leitura para o despacho
#      <estado>/bin/capacidade.sh --sugerir  valores de paralelismo para o orq.env desta máquina
if [ "${1:-}" != "--sugerir" ]; then . "$(dirname "$0")/_comum.sh"; fi
ATIVOS=$("${ORQ:-.}/bin/agentes.py" ativos --contar 2>/dev/null || echo 0) MODO="${1:-}" exec python3 - <<'PY'
import os, math
E = os.environ
def num(k, padrao):
    try: return float(E.get(k, '') or padrao)
    except ValueError: return float(padrao)
mem = {}
for l in open('/proc/meminfo'):
    k, v = l.split(':', 1); mem[k] = int(v.split()[0]) / 1048576  # GB
total, livre = mem['MemTotal'], mem['MemAvailable']
swap_usada = mem.get('SwapTotal', 0) - mem.get('SwapFree', 0)
cpus = os.cpu_count() or 1
load1, load5 = (float(x) for x in open('/proc/loadavg').read().split()[:2])
def psi(nome):
    try:
        r = {}
        for l in open(f'/proc/pressure/{nome}'):
            tipo, *campos = l.split()
            r[tipo] = float(dict(c.split('=') for c in campos)['avg10'])
        return r.get('some', 0.0), r.get('full', 0.0)
    except OSError:
        return 0.0, 0.0
cpu_some, _ = psi('cpu'); mem_some, mem_full = psi('memory'); io_some, _ = psi('io')

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
print(f'CPU {cpus} · load {load1:.2f}/{load5:.2f} (teto {carga_max:g}, crítico {carga_crit:g}) · memória livre {livre:.1f} '
      f'de {total:.0f} GB (reserva {reserva:g}) · swap {swap_usada:.1f} GB · PSI cpu {cpu_some:.0f}% '
      f'mem {mem_some:.0f}%/{mem_full:.0f}% io {io_some:.0f}%')
print(f'AGENTES={ativos}/{maxag}')
print(f'VAGAS={vagas}')
print(f'ESTADO={estado}')
print('MOTIVO=' + ('; '.join(motivos_crit + motivos) or '—'))
PY
