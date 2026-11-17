# Incluído pelos scripts Python do orquestrador: pasta de estado, parâmetros de orq.env e entradas do BACKLOG.
# No Windows também: modo UTF-8, caminhos com barras normais, o bash do Git, travas, árvore de processos e a carga da
# máquina (WINDOWS.md).
import os, re, sys, shlex, shutil, subprocess

WIN = os.name == 'nt'
if WIN and not sys.flags.utf8_mode:
    # Os arquivos de estado são UTF-8; sem o modo UTF-8 o Python do Windows lê e escreve em cp1252. Roda o mesmo
    # script de novo com -X utf8 (uma vez só). Script vindo do stdin (python3 -) não pode ser relido: só ajusta o stdio.
    if sys.argv and sys.argv[0] not in ('', '-', '-c') and not os.environ.get('ORQ_UTF8_REEXEC'):
        os.environ['ORQ_UTF8_REEXEC'] = '1'; os.environ['PYTHONUTF8'] = '1'
        try:
            _rc = subprocess.call([sys.executable, '-X', 'utf8', *sys.orig_argv[1:]])
        except KeyboardInterrupt:
            _rc = 130
        sys.exit(_rc)
    for _s in (sys.stdout, sys.stderr):
        try: _s.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError): pass

def caminho(p):
    """No Windows, /c/x vira C:/x e as barras ficam normais: o Git Bash come as invertidas fora de aspas."""
    if WIN and p:
        m = re.match(r'^/([a-zA-Z])(/|$)', p)
        if m:
            p = m.group(1).upper() + ':/' + p[3:]
        p = p.replace('\\', '/')
    return p

def estado():
    if os.environ.get('ORQ'):
        return caminho(os.environ['ORQ'])
    # <estado>/bin é um link para a pasta da skill: use o caminho chamado, sem resolver o link.
    return caminho(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), '..')))

def params(orq):
    p = {}
    f = os.path.join(orq, 'orq.env')
    if not os.path.exists(f):
        sys.exit(f'orquestrador: {f} não existe')
    for linha in open(f):
        linha = linha.strip()
        if not linha or linha.startswith('#') or '=' not in linha:
            continue
        k, v = linha.split('=', 1)
        p[k.strip()] = (shlex.split(v, comments=True) or [''])[0]
    return p

def preencher(texto, valores):
    for k, v in valores.items():
        texto = texto.replace('{' + k + '}', v)
    return texto

class Entrada:
    """Uma tarefa do BACKLOG: "### <ID> · <título>" seguida de linhas "- **Campo:** valor"."""

    def __init__(self, orq, tid):
        bl = open(os.path.join(orq, 'BACKLOG.md')).read()
        m = re.search(r'^### ' + re.escape(tid) + r' · (.+?)\n(.*?)(?=^### |^## |\Z)', bl, re.S | re.M)
        if not m:
            sys.exit(f'{tid} não está no BACKLOG.md')
        self.id, self.titulo, self.corpo = tid, m.group(1).strip(), m.group(2)
        fases = [f for f in re.finditer(r'^## (.+)$', bl, re.M) if f.start() < m.start()]
        self.fase = fases[-1].group(1).strip() if fases else '—'

    def bloco(self, nome):
        """Campo que ocupa a linha inteira e pode continuar nas linhas seguintes (Escopo, Aceite…)."""
        mm = re.search(r'- \*\*' + re.escape(nome) + r':\*\*(.*?)(?=\n- \*\*|\Z)', self.corpo, re.S)
        return mm.group(1).strip() if mm else ''

    def linha(self, nome):
        """Campo curto que divide a linha com outros, separados por "·" (Issue, Origem, Depende de, Classe)."""
        mm = re.search(r'\*\*' + re.escape(nome) + r':\*\*\s*(.*?)\s*(?:·|$)', self.corpo, re.M)
        return mm.group(1).strip() if mm else ''

    def globs(self):
        bruto = self.bloco('Arquivos')
        return [g.strip().strip('`') for g in re.split(r'[,\n]', bruto) if g.strip().strip('`') and g.strip() not in ('—', '-')]

    def orcamento(self):
        mm = re.search(r'(\d[\d.]*)', self.bloco('Orçamento').replace('.', ''))
        return int(mm.group(1)) if mm else None

    def classe(self):
        c = self.linha('Classe').upper()
        return c if c in ('P', 'M', 'G', 'GG') else ''

    def effort(self):
        """Effort declarado na tarefa (campo opcional **Effort:**); vazio = o padrão da classe."""
        x = self.linha('Effort').lower().strip('`')
        return x if x in EFFORTS else ''

    def criterios(self):
        """Itens do aceite, com id: o X.Y do item, se houver; senão C1, C2… na ordem."""
        itens = []
        for linha in (self.bloco('Aceite') or '').splitlines():
            t = linha.strip().lstrip('-*').strip()
            if not t:
                continue
            m = re.match(r'(\d+(?:\.\d+)*)[.)]?\s+(.*)', t)
            itens.append((m.group(1), m.group(2)) if m else (f'C{len(itens) + 1}', t))
        return itens

    def provas_exigidas(self):
        """Tipos de prova exigidos: os do campo Provas, mais log sempre e mutação fora da classe P."""
        txt = self.bloco('Provas').lower()
        mapa = {'print': 'print', 'captura': 'print', 'vídeo': 'video', 'video': 'video', 'log': 'log',
                'medição': 'medicao', 'medicao': 'medicao', 'requisição': 'requisicao', 'requisicao': 'requisicao',
                'mutação': 'mutacao', 'mutacao': 'mutacao'}
        tipos = {v for k, v in mapa.items() if re.search(r'\b' + k + r'\b', txt)} | {'log'}
        if self.classe() in ('M', 'G', 'GG', '') and not re.search(r'sem muta[çc][ãa]o', txt):
            tipos.add('mutacao')
        if re.search(r'sem muta[çc][ãa]o', txt):
            tipos.discard('mutacao')
        return sorted(tipos)

# Segredos e dados pessoais que não podem ir para provas nem para o comentário do PR.
SEGREDOS = [
    (re.compile(r'(?i)\b(authorization|x-api-key|api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|secret|password|passwd|senha|token)\b(\s*[:=]\s*|"\s*:\s*")("?)(?!«)([^\s"\',;]{8,})'), r'\1\2\3«mascarado»'),
    (re.compile(r'(?i)\bbearer\s+[A-Za-z0-9._~+/-]{16,}=*'), 'Bearer «mascarado»'),
    (re.compile(r'\b(gh[pousr]_[A-Za-z0-9]{30,}|xox[abpr]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|ATATT[A-Za-z0-9_=-]{20,}|sk-[A-Za-z0-9_-]{20,})\b'), '«mascarado»'),
    (re.compile(r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b'), '«jwt mascarado»'),
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----', re.S), '«chave privada mascarada»'),
    (re.compile(r'(://)[^/\s:@]+:[^/\s@]+@'), r'\1«credencial»@'),
    (re.compile(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b'), '«cpf»'),
]

def mascarar(texto):
    for padrao, troca in SEGREDOS:
        texto = padrao.sub(troca, texto)
    return texto

def tem_segredo(texto):
    return [p.pattern[:40] for p, _ in SEGREDOS if p.search(texto)]

# Limites do fluxo: branches protegidas e hosts permitidos (AMBIENTE.md).
import fnmatch
from urllib.parse import urlsplit

def lista(P, chave, padrao=''):
    return [x for x in re.split(r'[\s,]+', P.get(chave, padrao) or padrao) if x]

def branch_protegida(P, nome):
    nome = re.sub(r'^refs/heads/', '', nome or '')
    return any(fnmatch.fnmatchcase(nome, p) for p in lista(P, 'BRANCHES_PROTEGIDAS', 'main master develop'))

def host_de(url):
    u = url if '://' in url else 'http://' + url
    return (urlsplit(u).hostname or '').lower()

def url_permitida(P, url):
    """Default-deny: só hosts de HOSTS_PERMITIDOS. Devolve (ok, motivo)."""
    h = host_de(url)
    if not h:
        return False, f'URL sem host: {url}'
    if any(fnmatch.fnmatchcase(h, p.lower()) for p in lista(P, 'HOSTS_PERMITIDOS', 'localhost 127.0.0.1 ::1')):
        return True, f'{h} está em HOSTS_PERMITIDOS'
    if any(fnmatch.fnmatchcase(h, p.lower()) for p in lista(P, 'HOSTS_PROIBIDOS')):
        return False, f'{h} é produção (HOSTS_PROIBIDOS)'
    return False, f'{h} não está em HOSTS_PERMITIDOS'

# Alvos de modelo (MODELOS.md): "provedor:modelo:effort" no orq.env, por papel; a tarefa pode declarar o effort.
EFFORTS = ('low', 'medium', 'high', 'xhigh', 'max')
PAPEIS = {'P': 'MODELO_P', 'M': 'MODELO_M', 'G': 'MODELO_G', 'GG': 'MODELO_GG'}
ESCADA_PADRAO = ('claudeAgent:claude-sonnet-5-5:medium claudeAgent:claude-sonnet-5-5:high '
                 'claudeAgent:claude-opus-5-5:medium claudeAgent:claude-opus-5-5:high '
                 'claudeAgent:claude-fable-5-2:medium claudeAgent:claude-fable-5-2:high')

def spec_de(P, papel):
    """Papel (P, M, G, GG, REVISOR, ORQUESTRADOR…) ou alvo literal provedor:modelo[:effort] → (provedor, modelo, effort)."""
    if ':' in papel:
        chave, valor = 'alvo', papel
    else:
        chave = PAPEIS.get(papel.upper(), papel.upper())
        valor = P.get(chave, '')
        if chave == 'REVISOR_CRITICO' and not valor:
            valor = P.get('REVISOR', '')
        if not valor:
            sys.exit(f'alvo: {chave} vazio ou ausente no orq.env')
    partes = valor.split(':')
    if len(partes) not in (2, 3) or not all(partes):
        sys.exit(f'alvo: {chave}="{valor}" não está no formato provedor:modelo:effort')
    return partes[0], partes[1], (partes[2] if len(partes) == 3 else '')

def opcao_effort(P, prov):
    """Nome da opção de effort no target de um provedor: EFFORT_OPCAO="codex=reasoningEffort outro=thinking";
    sem entrada, reasoningEffort no Codex e effort nos demais."""
    mapa = {'codex': 'reasoningEffort'}
    for par in lista(P, 'EFFORT_OPCAO'):
        if '=' in par:
            k, v = par.split('=', 1); mapa[k] = v
    return mapa.get(prov, 'effort')

def spec_txt(spec):
    return ':'.join(x for x in spec if x)

def alvo_tarefa(orq, P, tid, revisor=False):
    """Alvo de uma tarefa do BACKLOG. Implementador: o modelo da classe, com o **Effort:** da tarefa se houver.
    Revisor: REVISOR_CRITICO nas classes G e GG, REVISOR nas outras."""
    e = Entrada(orq, tid)
    classe = e.classe() or 'M'
    if revisor:
        return spec_de(P, 'REVISOR_CRITICO' if classe in ('G', 'GG') else 'REVISOR')
    prov, modelo, effort = spec_de(P, classe)
    return prov, modelo, e.effort() or effort

def acima(P, spec, so_modelo=False):
    """Próximo degrau da ESCADA. so_modelo=True: o primeiro degrau do modelo seguinte (falha de capacidade, não
    de cuidado). Devolve None no topo ou quando o modelo não está na escada."""
    escada = [spec_de(P, x) for x in lista(P, 'ESCADA', ESCADA_PADRAO)]
    modelos = []
    for d in escada:
        if d[1] not in modelos:
            modelos.append(d[1])
    if spec[1] not in modelos:
        return None
    if not so_modelo:
        if spec in escada:
            i = escada.index(spec)
            return escada[i + 1] if i + 1 < len(escada) else None
        # effort fora da escada (xhigh, max, low): sobe dentro do modelo se houver degrau acima; senão, troca de modelo
        ordem = {x: i for i, x in enumerate(EFFORTS)}
        maiores = [d for d in escada if d[1] == spec[1] and ordem.get(d[2], -1) > ordem.get(spec[2], 99)]
        if maiores:
            return maiores[0]
    i = modelos.index(spec[1])
    if i + 1 >= len(modelos):
        return None
    return next(d for d in escada if d[1] == modelos[i + 1])

def familia(modelo):
    m = modelo.lower()
    for f in ('fable', 'mythos', 'opus', 'sonnet', 'haiku'):
        if f in m:
            return 'fable' if f == 'mythos' else f
    return 'outro'

def bloco(orq, papel, modelo):
    """Texto de prompts/<papel>-<família>.md (papel: impl | rev), o trecho do brief que muda com o modelo
    (PROMPTS.md). A pasta de estado pode ter a sua versão em modelos/prompts/. Sem arquivo, devolve ''."""
    skill = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    fam = familia(modelo)
    for nome in [fam] + (['sonnet'] if fam == 'haiku' else []) + ['outro']:
        for pasta in (os.path.join(orq, 'modelos', 'prompts'), os.path.join(skill, 'prompts')):
            f = os.path.join(pasta, f'{papel}-{nome}.md')
            if os.path.exists(f):
                return open(f).read().strip()
    return ''

# ---------------------------------------------------------------------------------------------------------------------
# Portabilidade Linux × Windows (WINDOWS.md)

def bash_exe():
    """O bash do Git for Windows. No PowerShell e no PATH do Windows, "bash" costuma ser o do WSL: nunca use esse."""
    if not WIN:
        return shutil.which('bash') or '/bin/bash'
    cands = [os.environ.get('ORQ_BASH')]
    git = shutil.which('git')
    if git:  # ...\Git\cmd\git.exe ou ...\Git\mingw64\bin\git.exe
        d = os.path.dirname(os.path.dirname(git))
        cands += [os.path.join(d, 'bin', 'bash.exe'), os.path.join(os.path.dirname(d), 'bin', 'bash.exe'),
                  os.path.join(d, 'usr', 'bin', 'bash.exe')]
    for base in (os.environ.get('ProgramFiles'), os.environ.get('ProgramW6432'), os.environ.get('LOCALAPPDATA') and
                 os.path.join(os.environ['LOCALAPPDATA'], 'Programs')):
        if base:
            cands.append(os.path.join(base, 'Git', 'bin', 'bash.exe'))
    for c in cands:
        if c and os.path.isfile(c) and 'windowsapps' not in c.lower() and 'system32' not in c.lower():
            return c
    return shutil.which('bash') or 'bash'

def comando(cmd):
    """Lista pronta para o subprocess. No Windows o CreateProcess não lê shebang nem acha .cmd sem a extensão:
    resolve npx → npx.cmd, script sem extensão pelo shebang (python, node, bash) e "bash" → o bash do Git."""
    cmd = list(cmd)
    if not WIN or not cmd:
        return cmd
    c0, resto = cmd[0], cmd[1:]
    if not os.path.dirname(c0) and c0.lower() in ('bash', 'sh', 'bash.exe', 'sh.exe'):
        return [bash_exe(), *resto]
    achado = c0 if (os.path.dirname(c0) and os.path.isfile(c0)) else shutil.which(c0)
    if not achado:
        return cmd
    ext = os.path.splitext(achado)[1].lower()
    if ext in ('.exe', '.com', '.bat', '.cmd'):
        return [achado, *resto]
    if ext == '.ps1':
        return ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', achado, *resto]
    if ext == '.py':
        return [sys.executable, achado, *resto]
    if ext in ('.js', '.cjs', '.mjs'):
        return [shutil.which('node') or 'node', achado, *resto]
    try:
        primeira = open(achado, 'rb').readline().decode('utf-8', 'replace')
    except OSError:
        return cmd
    if primeira.startswith('#!'):
        if 'python' in primeira:
            return [sys.executable, achado, *resto]
        if 'node' in primeira:
            return [shutil.which('node') or 'node', achado, *resto]
        return [bash_exe(), achado, *resto]
    return [achado, *resto]

def travar(arquivo):
    """Trava exclusiva sem esperar. Devolve o arquivo aberto (segure-o enquanto precisar) ou None se ocupada.
    O sistema solta a trava quando o processo morre, nos dois sistemas."""
    os.makedirs(os.path.dirname(os.path.abspath(arquivo)), exist_ok=True)
    f = open(arquivo, 'a+')
    try:
        if WIN:
            import msvcrt
            f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except OSError:
        f.close()
        return None

def novo_grupo():
    """kwargs do Popen para o filho ficar num grupo próprio (para matar_arvore)."""
    return {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if WIN else {'start_new_session': True}

def matar_arvore(pid, forca=False):
    """Encerra o processo e os filhos dele. No Windows não há TERM para programa de console: é sempre taskkill /F."""
    if WIN:
        r = subprocess.run(['taskkill', '/T', '/F', '/PID', str(pid)], capture_output=True)
        if r.returncode not in (0, 128, 255):
            raise ProcessLookupError(pid)
    else:
        import signal
        os.killpg(pid, signal.SIGKILL if forca else signal.SIGTERM)

def _psi(nome):
    try:
        r = {}
        for l in open(f'/proc/pressure/{nome}'):
            tipo, *campos = l.split()
            r[tipo] = float(dict(c.split('=') for c in campos)['avg10'])
        return r.get('some', 0.0), r.get('full', 0.0)
    except OSError:
        return 0.0, 0.0

def metricas(amostra_s=1.0):
    """Carga da máquina: memória total e livre e swap em GB, CPUs, load de 1 e 5 min e PSI (0 onde não há).
    No Windows não há load nem PSI: o load é a CPU ocupada × núcleos + a fila do processador (como o Cygwin faz),
    medida numa amostra de amostra_s segundos; o de 5 min repete o de 1 min."""
    cpus = os.cpu_count() or 1
    m = {'cpus': cpus, 'psi': False, 'cpu_some': 0.0, 'mem_some': 0.0, 'mem_full': 0.0, 'io_some': 0.0}
    if not WIN:
        mem = {}
        for l in open('/proc/meminfo'):
            k, v = l.split(':', 1); mem[k] = int(v.split()[0]) / 1048576  # GB
        m['total'], m['livre'] = mem['MemTotal'], mem.get('MemAvailable', mem.get('MemFree', 0))
        m['swap'] = mem.get('SwapTotal', 0) - mem.get('SwapFree', 0)
        m['load1'], m['load5'] = (float(x) for x in open('/proc/loadavg').read().split()[:2])
        if os.path.isdir('/proc/pressure'):
            m['psi'] = True
            m['cpu_some'], _ = _psi('cpu'); m['mem_some'], m['mem_full'] = _psi('memory'); m['io_some'], _ = _psi('io')
        return m
    import ctypes, time
    from ctypes import wintypes
    GB = 1024 ** 3
    class MEMSTAT(ctypes.Structure):
        _fields_ = [('dwLength', wintypes.DWORD), ('dwMemoryLoad', wintypes.DWORD)] + \
                   [(n, ctypes.c_ulonglong) for n in ('total', 'livre', 'pf_total', 'pf_livre', 'v_total', 'v_livre', 'v_ext')]
    st = MEMSTAT(); st.dwLength = ctypes.sizeof(MEMSTAT)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
    m['total'], m['livre'] = st.total / GB, st.livre / GB
    try:
        import psutil
        m['swap'] = psutil.swap_memory().used / GB
    except Exception:  # sem psutil: o que o arquivo de paginação guarda além da RAM em uso
        m['swap'] = max(0, (st.pf_total - st.pf_livre) - (st.total - st.livre)) / GB
    def tempos():
        ft = [wintypes.FILETIME() for _ in range(3)]
        ctypes.windll.kernel32.GetSystemTimes(*(ctypes.byref(x) for x in ft))
        return [(x.dwHighDateTime << 32) | x.dwLowDateTime for x in ft]  # ocioso, kernel (com o ocioso), usuário
    a = tempos(); time.sleep(amostra_s); b = tempos()
    ocioso, total = b[0] - a[0], (b[1] - a[1]) + (b[2] - a[2])
    uso = max(0.0, min(1.0, 1 - ocioso / total)) if total else 0.0
    fila = 0.0
    try:
        pdh = ctypes.WinDLL('pdh')
        class VALOR(ctypes.Structure):
            _fields_ = [('status', wintypes.DWORD), ('valor', ctypes.c_double)]
        q, c, v = ctypes.c_void_p(), ctypes.c_void_p(), VALOR()
        if pdh.PdhOpenQueryW(None, None, ctypes.byref(q)) == 0:
            if (pdh.PdhAddEnglishCounterW(q, ctypes.c_wchar_p(r'\System\Processor Queue Length'), None, ctypes.byref(c)) == 0
                    and pdh.PdhCollectQueryData(q) == 0
                    and pdh.PdhGetFormattedCounterValue(c, 0x200, None, ctypes.byref(v)) == 0):
                fila = max(0.0, v.valor)
            pdh.PdhCloseQuery(q)
    except (OSError, AttributeError):
        pass
    m['load1'] = m['load5'] = uso * cpus + fila
    m['cpu_uso'] = uso * 100
    return m

def nota_windows():
    """Trecho dos briefs no Windows: onde rodar os scripts de bin/ (WINDOWS.md). Vazio fora do Windows."""
    if not WIN:
        return ''
    b = bash_exe().replace('\\', '/')
    return ('## Esta máquina é Windows\n'
            '- Os comandos `.../bin/...` deste brief são scripts bash e Python: rode-os no Git Bash (a ferramenta Bash), '
            'com os caminhos como estão escritos aqui (`C:/...`, barras normais).\n'
            f'- No PowerShell, passe pelo bash do Git: `& "{b}" -lc \'<comando>\'`. O `bash` sozinho no PowerShell é o '
            'do WSL e não enxerga estes arquivos.\n'
            '- Pipe, redirecionamento e variável no começo do comando (`PORT=3000 yarn start`) são sintaxe do bash: '
            'no `bin/prova` e no `bin/slot`, use `-- bash -c \'<comando>\'`.')
