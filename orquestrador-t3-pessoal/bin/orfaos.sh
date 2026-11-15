#!/usr/bin/env bash
# Processos órfãos nas worktrees das tarefas: servidores, watchers, navegadores e builds que sobreviveram ao agente.
# Órfão = diretório atual dentro de uma worktree e nenhum ancestral é uma sessão de agente viva (claude, codex,
# t3code). Assim as ferramentas, os servidores MCP e as tarefas de fundo de um agente vivo nunca entram na lista.
# Lê /proc no Linux; com o psutil instalado (obrigatório no Windows: python3 -m pip install --user psutil), usa ele.
# Uso: <estado>/bin/orfaos.sh [--matar] [<worktree>...]   (sem worktree: todas as registradas em agentes.json)
. "$(dirname "$0")/_comum.sh"
MATAR=0; [ "${1:-}" = "--matar" ] && { MATAR=1; shift; }
if [ $# -gt 0 ]; then WTS=("$@"); else mapfile -t WTS < <("$ORQ/bin/agentes.py" worktrees | tr -d '\r'); fi
[ ${#WTS[@]} -gt 0 ] || { echo "orfaos: nenhuma worktree registrada"; exit 0; }
if [ -n "$ORQ_WIN" ]; then for i in "${!WTS[@]}"; do WTS[$i]=$(cygpath -m "${WTS[$i]}" 2>/dev/null || echo "${WTS[$i]}"); done; fi
MATAR=$MATAR exec python3 - "${WTS[@]}" <<'PY'
import os, re, sys, time, signal
SESSAO = re.compile(r'(?i)(^|[/\\])(claude|codex|t3code|t3 code)(\.exe)?("|\s|$)|claude-agent-sdk|claude-code|@openai[/\\]codex|[/\\]codex-')
norm = lambda p: os.path.normcase(os.path.realpath(p)).rstrip('/\\') + os.sep
wts = {norm(w): w.rstrip('/\\') for w in sys.argv[1:] if os.path.isdir(w)}  # chave para comparar, valor para mostrar
eu = {os.getpid(), os.getppid()}
try:
    import psutil
except ImportError:
    psutil = None
    if os.name == 'nt' or not os.path.isdir('/proc'):
        sys.exit('orfaos: falta o psutil (python3 -m pip install --user psutil)')
achados = []
if psutil:
    for p in psutil.process_iter(['pid', 'cmdline', 'create_time']):
        if p.pid in eu:
            continue
        try:
            cwd = norm(p.cwd())
        except (psutil.Error, OSError):
            continue
        wt = next((w for w in wts if cwd.startswith(w)), None)
        if not wt:
            continue
        try:
            cadeia = [p] + p.parents()
            if any(SESSAO.search(' '.join(x.cmdline() or [x.name()])) for x in cadeia):
                continue
            args = ' '.join(p.info['cmdline'] or [p.name()])
        except (psutil.Error, OSError):
            continue
        achados.append((p.pid, int(time.time() - p.info['create_time']), wts[wt], args[:160]))
else:
    TICK = os.sysconf('SC_CLK_TCK'); UPTIME = float(open('/proc/uptime').read().split()[0])
    def idade_s(pid):
        campos = open(f'/proc/{pid}/stat').read().rsplit(')', 1)[1].split()
        return int(UPTIME - int(campos[19]) / TICK)
    def info(pid):
        try:
            st = open(f'/proc/{pid}/stat').read()
            ppid = int(st.rsplit(')', 1)[1].split()[1])
            args = open(f'/proc/{pid}/cmdline', 'rb').read().replace(b'\0', b' ').decode(errors='replace').strip()
            return ppid, args
        except OSError:
            return None, ''
    def sob_sessao(pid):
        vistos = 0
        while pid and pid > 1 and vistos < 64:
            ppid, args = info(pid)
            if SESSAO.search(args):
                return True
            pid, vistos = ppid, vistos + 1
        return False
    for d in os.listdir('/proc'):
        if not d.isdigit() or int(d) in eu:
            continue
        pid = int(d)
        try:
            cwd = norm(os.readlink(f'/proc/{pid}/cwd'))
        except OSError:
            continue
        wt = next((w for w in wts if cwd.startswith(w)), None)
        if not wt or sob_sessao(pid):
            continue
        _, args = info(pid)
        try: idade = idade_s(pid)
        except OSError: continue
        achados.append((pid, idade, wts[wt], args[:160]))
if not achados:
    print('orfaos: nenhum'); raise SystemExit
for pid, idade, wt, args in achados:
    print(f'ÓRFÃO pid {pid} · {idade // 60} min · {wt} · {args}')
if os.environ.get('MATAR') == '1':
    if psutil:
        procs = []
        for pid, *_ in achados:
            try: pr = psutil.Process(pid); pr.terminate(); procs.append(pr)
            except psutil.Error: pass
        _, vivos = psutil.wait_procs(procs, timeout=5)
        for pr in vivos:
            try: pr.kill(); print(f'orfaos: pid {pr.pid} não saiu com TERM; KILL')
            except psutil.Error: pass
    else:
        for pid, *_ in achados:
            try: os.kill(pid, signal.SIGTERM)
            except OSError: pass
        time.sleep(5)
        for pid, *_ in achados:
            try: os.kill(pid, signal.SIGKILL); print(f'orfaos: pid {pid} não saiu com TERM; KILL')
            except OSError: pass
    print(f'orfaos: {len(achados)} encerrado(s)')
PY
