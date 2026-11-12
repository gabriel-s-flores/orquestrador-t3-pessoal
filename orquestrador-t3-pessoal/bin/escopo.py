#!/usr/bin/env python3
# Conferência mecânica do contrato de escopo (ESCOPO.md): compara o diff da tarefa com os campos Arquivos e
# Orçamento do BACKLOG e com o Mapa de escopo do relatório. Aponta arquivos fora das áreas permitidas, manifestos de
# dependência, CI e configuração, migrações, remoções e o tamanho do diff.
# Uso: <estado>/bin/escopo.py <ID> [--repo DIR] [--head REF] [--base REF]
#   --repo: checkout com o head disponível (padrão: CHECKOUT do orq.env) · --base: padrão origin/$BASE
# Saída: markdown. Código 0 = dentro do contrato, 1 = alertas, 2 = erro.
import sys, os, re, fnmatch, subprocess
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from _orq import estado, params, Entrada
O = estado(); P = params(O)
args = sys.argv[1:]
def opt(nome, padrao):
    if nome in args:
        i = args.index(nome); v = args[i + 1]; del args[i:i + 2]; return v
    return padrao
repo = opt('--repo', P.get('CHECKOUT', '.')); head = opt('--head', 'HEAD'); base = opt('--base', f"origin/{P['BASE']}")
if len(args) != 1:
    sys.exit('uso: escopo.py <ID> [--repo DIR] [--head REF] [--base REF]')
tid = args[0]; e = Entrada(O, tid)
def git(*a):
    r = subprocess.run(['git', '-C', repo, *a], capture_output=True, text=True)
    if r.returncode:
        print(f'escopo: git {" ".join(a)} falhou: {r.stderr.strip()} (faltou git fetch origin?)', file=sys.stderr); sys.exit(2)
    return r.stdout
num = {}
for l in git('diff', '--numstat', '--no-renames', f'{base}...{head}').splitlines():
    a, d, f = l.split('\t', 2)
    num[f] = (0 if a == '-' else int(a), 0 if d == '-' else int(d), a == '-')
removidos = [l.split('\t', 1)[1] for l in git('diff', '--name-status', '--no-renames', f'{base}...{head}').splitlines() if l.startswith('D\t')]
sha = git('rev-parse', '--short', head).strip()

globs = e.globs()
def casa(f, padroes):
    for g in padroes:
        g2 = g.rstrip('/')
        if fnmatch.fnmatch(f, g2) or (g2.endswith('/**') and f.startswith(g2[:-3] + '/')) or f.startswith(g2 + '/'):
            return True
    return False
mapa = {}
rel = f'{O}/tarefas/{tid}/relatorio.md'
if os.path.exists(rel):
    sec = re.search(r'^## Mapa de escopo\n(.*?)(?=^## |\Z)', open(rel).read(), re.S | re.M)
    for l in (sec.group(1).splitlines() if sec else []):
        c = [x.strip() for x in l.strip().strip('|').split('|')]
        if len(c) >= 2 and c[0] and not set(c[0]) <= set('-: ') and c[0].lower() not in ('arquivo', 'arquivo (ou grupo)'):
            for item in re.split(r'[,\s]+', c[0].replace('`', '')):
                if item: mapa[item] = c[1]
def justificativa(f):
    for k, v in mapa.items():
        if casa(f, [k]): return v
    return None

MANIFESTOS = ['package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'npm-shrinkwrap.json', 'go.mod', 'go.sum',
              'pom.xml', 'build.gradle', 'build.gradle.kts', 'settings.gradle', 'gradle.properties', 'requirements*.txt',
              'pyproject.toml', 'poetry.lock', 'uv.lock', 'Pipfile', 'Pipfile.lock', 'Cargo.toml', 'Cargo.lock', 'Gemfile',
              'Gemfile.lock', 'composer.json', 'composer.lock', '*.csproj']
LOCKS = {'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'npm-shrinkwrap.json', 'go.sum', 'poetry.lock', 'uv.lock',
         'Pipfile.lock', 'Cargo.lock', 'Gemfile.lock', 'composer.lock'}
CI = ['.github/**', '.gitlab-ci.yml', 'Jenkinsfile', '.circleci/**', 'Dockerfile*',
      'docker-compose*.yml', '*.env', '.env*', 'Makefile', '.eslintrc*', 'eslint.config.*', 'tsconfig*.json',
      '.golangci*', 'sonar-project.properties', '.husky/**']
MIGR = ['**/migrations/**', '**/migration/**', 'db/migrate/**', '**/*.sql', '**/flyway/**', '**/liquibase/**', '**/changelog/**']
nome = lambda f: f.rsplit('/', 1)[-1]
def grupo(padroes, por_nome=False):
    return [f for f in num if (casa(nome(f), padroes) if por_nome else casa(f, padroes) or casa(nome(f), padroes))]

alertas = []; L = []
def secao(titulo, arquivos, alerta_sem_mapa=True):
    if not arquivos: return
    L.append(f'\n## {titulo}')
    for f in sorted(arquivos):
        a, d, b = num.get(f, (0, 0, False)); j = justificativa(f)
        permitido = globs and casa(f, globs)
        if j: marca = f'justificado no Mapa: "{j[:120]}"'
        elif permitido: marca = 'dentro dos arquivos permitidos'
        else:
            marca = '⚠ sem linha no Mapa de escopo'
            if alerta_sem_mapa: alertas.append(f)
        L.append(f'- `{f}` ({"binário" if b else f"+{a} −{d}"}) — {marca}')

fora = [f for f in num if globs and not casa(f, globs)]
manif = grupo(MANIFESTOS, por_nome=True); ci = grupo(CI); migr = grupo(MIGR)
total = sum(a + d for f, (a, d, b) in num.items() if nome(f) not in LOCKS)
orc = e.orcamento()
secao('Fora dos arquivos permitidos', [f for f in fora if f not in manif + ci + migr])
secao('Dependências e manifestos', manif)
secao('CI, build e configuração', ci)
secao('Migrações e dados', migr)
if removidos:
    L.append('\n## Removidos'); L += [f'- `{f}`' for f in removidos]
tam = f'{len(num)} arquivo(s), {total} linhas alteradas sem lockfiles'
if orc:
    razao = total / orc if orc else 0
    tam += f' · orçamento ~{orc} → {razao:.1f}×'
    if razao > 2: alertas.append('tamanho'); tam += ' ⚠ mais que o dobro do orçamento'
if not globs:
    L.insert(0, '\n_Sem **Arquivos:** no BACKLOG: só os alertas de manifesto, CI, migração e tamanho._')
res = 'ALERTA' if alertas else 'DENTRO'
print(f'# Escopo {tid} · head {sha} · base {base}\nResultado: {res}\n- {tam}' + '\n'.join([''] + L) if L else
      f'# Escopo {tid} · head {sha} · base {base}\nResultado: {res}\n- {tam}')
sys.exit(1 if alertas else 0)
