# Incluído pelos scripts Python do orquestrador: pasta de estado, parâmetros de orq.env e entradas do BACKLOG.
import os, re, sys, shlex

def estado():
    if os.environ.get('ORQ'):
        return os.environ['ORQ']
    # <estado>/bin é um link para a pasta da skill: use o caminho chamado, sem resolver o link.
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), '..'))

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
