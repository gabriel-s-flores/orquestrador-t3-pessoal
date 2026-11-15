#!/usr/bin/env python3
# Limites do fluxo (AMBIENTE.md): branches protegidas nunca recebem push, merge nem PR; tudo se consolida na branch do
# épico por PR; testes só em hosts permitidos.
# Uso: guarda.py checar                         confere o orq.env (épico, prefixo, protegidas, HML_URL)
#      guarda.py instalar <worktree>            hook pre-push só nesta worktree (encadeia os hooks do repositório)
#      guarda.py instalado <worktree>           código 0 se o hook está ativo nesta worktree
#      guarda.py pr <número> [--base B --head H] antes do merge: base = branch do épico, head fora das protegidas
#      guarda.py url <url>...                   a URL pode ser usada nos testes? (código 1 = não)
#      guarda.py texto <arquivo>...             hosts de produção em .env e configurações usados para subir o ambiente
#      guarda.py hook <nome> [args]             chamado pelos hooks instalados
import os, re, sys, json, subprocess
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from _orq import estado, params, lista, branch_protegida, url_permitida, host_de, WIN, bash_exe
import fnmatch
O = estado(); P = params(O)
pasta_hooks = lambda: os.path.join(O, 'hooks').replace('\\', '/')
ZERO = '0' * 40
HOOKS = ['applypatch-msg', 'pre-applypatch', 'post-applypatch', 'pre-commit', 'pre-merge-commit', 'prepare-commit-msg',
         'commit-msg', 'post-commit', 'pre-rebase', 'post-checkout', 'post-merge', 'pre-push', 'pre-receive', 'update',
         'post-receive', 'post-update', 'reference-transaction', 'push-to-checkout', 'pre-auto-gc', 'post-rewrite',
         'sendemail-validate', 'fsmonitor-watchman', 'post-index-change']

def git(*a, cwd=None, check=True):
    r = subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f'guarda: git {" ".join(a)}: {r.stderr.strip()}')
    return r.stdout.strip()

def negar(msg):
    print(f'⛔ guarda: {msg}', file=sys.stderr); sys.exit(1)

def checar():
    erros = []
    base, prefixo = P.get('BASE', ''), P.get('PREFIXO', '')
    if not base or base.startswith('<'): erros.append('BASE vazia: deve ser a branch do épico (ex.: epico-login)')
    elif branch_protegida(P, base): erros.append(f'BASE "{base}" é protegida: o épico precisa de branch própria')
    if prefixo and branch_protegida(P, prefixo + '/x'): erros.append(f'PREFIXO "{prefixo}" cai numa branch protegida')
    if base and prefixo and (prefixo == base or base.startswith(prefixo + '/')):
        erros.append('PREFIXO e BASE se sobrepõem (o git não aceita X e X/y juntos)')
    if P.get('HML_URL'):
        ok, motivo = url_permitida(P, P['HML_URL'])
        if not ok: erros.append(f'HML_URL {P["HML_URL"]}: {motivo}')
    for e in erros: print(f'- {e}')
    print('Resultado: ' + ('PROBLEMA' if erros else 'OK') + f' · épico {base} · protegidas {" ".join(lista(P, "BRANCHES_PROTEGIDAS", "main master develop"))}')
    return 1 if erros else 0

def instalar(wt):
    wt = os.path.abspath(wt); top = git('rev-parse', '--show-toplevel', cwd=wt)
    if git('config', '--get', 'extensions.worktreeConfig', cwd=top, check=False) != 'true':
        git('config', 'extensions.worktreeConfig', 'true', cwd=top)
    atual = git('config', '--worktree', '--get', 'core.hooksPath', cwd=top, check=False)
    hooks = pasta_hooks()
    if atual != hooks:
        original = git('config', '--get', 'core.hooksPath', cwd=top, check=False) or os.path.join(git('rev-parse', '--git-common-dir', cwd=top), 'hooks')
        if not os.path.isabs(original): original = os.path.join(top, original)
        git('config', '--worktree', 'orq.hooksOriginal', original, cwd=top)
        git('config', '--worktree', 'core.hooksPath', hooks, cwd=top)
    os.makedirs(hooks, exist_ok=True)
    me = os.path.join(O, 'bin', 'guarda.py').replace('\\', '/')
    # No Windows o git roda o hook pelo sh dele: caminhos com barras normais, o python deste comando (o "python3" do
    # PATH pode ser o atalho da Loja) e fim de linha LF (CRLF quebra o script).
    py = sys.executable.replace('\\', '/') if WIN else 'python3'
    for h in HOOKS:
        f = os.path.join(hooks, h)
        with open(f, 'w', newline='\n') as arq:
            arq.write(f'#!/usr/bin/env bash\n# gerado por guarda.py: limites do fluxo + o hook original desta worktree\nexec "{py}" "{me}" hook {h} "$@"\n')
        os.chmod(f, 0o755)
    print(f'guarda: hook ativo em {top} (hooks originais: {git("config", "--worktree", "--get", "orq.hooksOriginal", cwd=top, check=False)})')
    return 0

def instalado(wt):
    ok = git('config', '--worktree', '--get', 'core.hooksPath', cwd=os.path.abspath(wt), check=False) == pasta_hooks()
    print('guarda: hook ' + ('ativo' if ok else 'AUSENTE') + f' em {wt}')
    return 0 if ok else 1

def hook(nome, args):
    entrada = sys.stdin.read() if nome in ('pre-push', 'pre-receive', 'post-rewrite', 'reference-transaction', 'post-receive') else ''
    if nome == 'pre-push':
        base = P.get('BASE', '')
        for linha in entrada.splitlines():
            partes = linha.split()
            if len(partes) != 4 or not partes[2].startswith('refs/heads/'): continue
            local_sha, ref, remoto_sha = partes[1], partes[2][len('refs/heads/'):], partes[3]
            if branch_protegida(P, ref):
                negar(f'push para "{ref}" bloqueado: {", ".join(lista(P, "BRANCHES_PROTEGIDAS", "main master develop"))} ficam fora deste fluxo')
            if ref == base:
                if local_sha == ZERO: negar(f'apagar a branch do épico "{base}" é proibido')
                if remoto_sha != ZERO: negar(f'push direto em "{base}" bloqueado: o épico só recebe código por PR revisado')
    original = git('config', '--get', 'orq.hooksOriginal', check=False)
    alvo = os.path.join(original, nome) if original else ''
    if alvo and os.path.isfile(alvo) and os.access(alvo, os.X_OK):
        # Windows: o hook é script sh sem extensão (husky inclusive); o CreateProcess não lê shebang, o bash do Git lê.
        r = subprocess.run(([bash_exe()] if WIN else []) + [alvo, *args], input=entrada, text=True)
        sys.exit(r.returncode)
    sys.exit(0)

def pr(numero, base, head):
    if not (base and head):
        d = json.loads(git_out(['gh', 'pr', 'view', numero, '-R', P['REPO'], '--json', 'baseRefName,headRefName,state']))
        base, head = d['baseRefName'], d['headRefName']
    erros = []
    if base != P.get('BASE'): erros.append(f'base do PR é "{base}", não a branch do épico "{P.get("BASE")}"')
    if branch_protegida(P, base): erros.append(f'base "{base}" é protegida')
    if branch_protegida(P, head): erros.append(f'head "{head}" é protegida')
    for e in erros: print(f'- {e}')
    print(f'Resultado: {"BLOQUEADO" if erros else "OK"} · PR {numero} · {head} → {base}')
    return 1 if erros else 0

def git_out(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit(f'guarda: {" ".join(cmd[:3])}: {r.stderr.strip()[:200]}')
    return r.stdout

def texto(arquivos):
    proibidos = [p.lower() for p in lista(P, 'HOSTS_PROIBIDOS')]
    achados = []
    for f in arquivos:
        for n, l in enumerate(open(f, errors='replace'), 1):
            for m in re.finditer(r'(?i)\b(?:https?|wss?)://[^\s"\'<>]+|\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b', l):
                h = host_de(m.group(0))
                if any(fnmatch.fnmatchcase(h, p) for p in proibidos) and not url_permitida(P, m.group(0))[0]:
                    achados.append(f'{f}:{n} · {m.group(0)[:80]}')
    for a in achados: print(f'- produção: {a}')
    print('Resultado: ' + ('PRODUÇÃO REFERENCIADA' if achados else 'OK') + f' · {len(arquivos)} arquivo(s)')
    return 1 if achados else 0

a = sys.argv[1:]
cmd = a[0] if a else ''
def opt(nome):
    return a[a.index(nome) + 1] if nome in a else None
if cmd == 'checar': sys.exit(checar())
if cmd == 'instalar' and len(a) == 2: sys.exit(instalar(a[1]))
if cmd == 'instalado' and len(a) == 2: sys.exit(instalado(a[1]))
if cmd == 'hook' and len(a) >= 2: hook(a[1], a[2:])
if cmd == 'pr' and len(a) >= 2: sys.exit(pr(a[1], opt('--base'), opt('--head')))
if cmd == 'url' and len(a) >= 2:
    rc = 0
    for u in a[1:]:
        ok, motivo = url_permitida(P, u); print(f'{"permitida" if ok else "PROIBIDA"} · {u} · {motivo}'); rc |= 0 if ok else 1
    sys.exit(rc)
if cmd == 'texto' and len(a) >= 2: sys.exit(texto(a[1:]))
sys.exit(open(os.path.realpath(__file__)).read().split('\nimport ')[0].replace('#!/usr/bin/env python3\n', ''))
