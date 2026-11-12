#!/usr/bin/env python3
# Confere um texto em português antes de ele chegar ao operador: vícios de escrita de IA, forma e tamanho por tipo.
# Adaptação para PT-BR do catálogo do unslop (cujos scanners recusam texto que não seja inglês). Regras em
# escrita/ESCRITA.md; explicação dos vícios em escrita/VICIOS.md.
# Uso: texto.py [--tipo TIPO] [--estrito] [arquivo | -]      texto.py --catalogo
#   TIPO: push | thread | decisao | diario | pausa | final | devolutiva | relatorio | revisao | sabatina | livre
#   pergunta: o arquivo é o JSON do AskUserQuestion ({"questions": [...]}); confere a forma do painel do T3
#   (sabatina/SABATINA.md) e os vícios de cada pergunta, etiqueta e alternativa.
# Saída: uma linha por achado (GRAVE ou LEVE) e o resultado. Código 1 = há achado grave (ou leve, com --estrito).
# Achado é candidato: termo de domínio, citação e nome próprio ficam. Código, URLs e trechos entre aspas são ignorados.
import json, re, sys, unicodedata

G, L = 'GRAVE', 'LEVE'
CATALOGO = {
    'abertura que atrasa': (G, 'corte e comece pelo fato', [
        r'vale (a pena )?(ressaltar|destacar|lembrar|mencionar|notar|frisar|salientar)( que)?',
        r'é (importante|fundamental|essencial|válido|interessante|bom) (ressaltar|destacar|lembrar|mencionar|notar|frisar|salientar|observar|dizer)( que)?',
        r'(cabe|convém) (ressaltar|destacar|lembrar|mencionar|salientar)( que)?',
        r'antes de mais nada', r'\bvamos lá\b', r'sem mais delongas',
        r'vamos (mergulhar|explorar|analisar|destrinchar|desvendar|dar uma olhada)',
        r'\b(a verdade|o fato) é que\b', r'como (é )?sabido', r'não é segredo (que|para ninguém)',
        r'(aqui|eis) (está|vai) o (ponto|segredo|pulo do gato)',
    ]),
    'ênfase fabricada': (G, 'corte; o fato mostra a importância', [
        r'isso é (muito|extremamente|super|realmente) importante', r'faz toda a diferença', r'ponto final\.',
        r'leia (isso )?de novo', r'não se engane', r'sem sombra de dúvidas?', r'sem dúvida alguma',
        r'com certeza absoluta', r'não pode ser subestimad[oa]', r'isso muda tudo', r'divisor de águas', r'game.?changer',
    ]),
    'resto de chatbot': (G, 'corte', [
        r'(ótima|excelente|boa) pergunta', r'^\s*(claro|com certeza|perfeito|entendido|beleza|ótimo)!',
        r'espero (ter ajudado|que (isso )?(ajude|tenha ajudado))', r'fico à disposição',
        r'(qualquer|em caso de) dúvida,? (é só|fico|estou)', r'se precisar de (algo|mais alguma coisa)',
        r'estou aqui para (ajudar|o que precisar)', r'fico feliz em ajudar', r'posso ajudar em (algo|mais alguma coisa)',
        r'como (um )?(modelo de linguagem|assistente de ia|uma ia)',
    ]),
    'meta-comentário': (G, 'corte; diga direto', [
        r'neste (relatório|documento|texto|resumo),? (vou|irei|apresento|apresentarei|veremos)',
        r'a seguir,? (apresento|veremos|vou apresentar|segue)', r'(abaixo segue|segue abaixo)',
        r'(conforme|como) (mencionado|dito|citado|explicado|vimos) (anteriormente|acima|antes)',
        r'\bem (suma|síntese)\b', r'\bpara concluir\b', r'por fim,? mas não menos importante',
        r'\b(dito isso|posto isso|isto posto)\b', r'resumindo o que foi (dito|visto)',
    ]),
    'raciocínio vazado': (G, 'dê a conclusão, depois a evidência', [
        r'vamos pensar passo a passo', r'(analisando|pensando) passo a passo', r'meu raciocínio (é|foi)',
        r'deix(a|e)(-me)? (eu )?(ver|pensar|verificar)',
    ]),
    'conclusão genérica': (G, 'diga o resultado medido', [
        r'(foi|é) um (grande )?sucesso', r'tudo (está|ficou|segue) funcionando perfeitamente',
        r'(um|mais um) (passo|marco) (importante|significativo|fundamental|decisivo)', r'abre caminho para',
        r'eleva o nível', r'com isso,? (garantimos|asseguramos)', r'(qualidade|eficiência) e (eficiência|qualidade)',
    ]),
    'contraste dramático': (L, 'diga o ponto positivo direto', [
        r'não é (só|apenas|somente) [^.\n]{1,60}, (é|mas)', r'não se trata (só |apenas )?de [^.\n]{1,60}, mas',
        r'mais do que [^.\n]{1,40}, é\b',
    ]),
    'atribuição vaga': (L, 'diga quem, onde ou o número', [
        r'especialistas (dizem|afirmam|apontam)', r'é amplamente (reconhecido|aceito|sabido)',
        r'estudos (mostram|indicam|apontam)', r'muitos (acreditam|dizem|afirmam)', r'tudo indica que',
    ]),
    'intensificador': (L, 'corte ou troque por um número', [
        r'\b(extremamente|incrivelmente|altamente|absolutamente|verdadeiramente|perfeitamente|simplesmente|realmente|efetivamente|definitivamente)\b',
        r'\bde fato\b', r'\b(crucial|cruciais|primordial|primordiais|imprescindíve(l|is))\b',
        r'\b(robust[oa]s?|abrangentes?|holístic[oa]s?|poderos[oa]s?|inovador(a|es|as)?|revolucionári[oa]s?|disruptiv[oa]s?|de ponta(?! a ponta)|de excelência|impressionantes?|notáve(l|is))\b',
        r'\bsignificativ(o|a|os|as|amente)\b', r'\b(fundamental|fundamentais|essencial|essenciais)\b',
    ]),
    'jargão': (L, 'use a palavra comum', [
        r'\balavanc(ar|a|am|ando|ou)\b', r'\bpotencializ(ar|a|am|ando|ou)\b', r'agreg(ar|a|am|ando|ou) valor',
        r'\bsinergias?\b', r'\bjornadas?\b', r'\bmergulh(ar|a|amos|ando|ou) (em|no|na|nos|nas)\b',
        r'naveg(ar|a|ando) (por |pelos |pelas |entre )?(os |as )?(desafios|complexidades)', r'\bdesbloque(ar|ia|ou|ando)\b',
        r'\bendere[çc](ar|a|ou|ando)\b', r'\bperform(ar|a|ou|ando)\b', r'\bempoder(ar|a|ou|ando)\b', r'\bparadigmas?\b',
        r'\bmindset\b', r'\bdeep dive\b', r'\binsights?\b', r'no fim do dia\b',
    ]),
    'enchimento': (L, 'use o verbo direto ou a preposição simples', [
        r'\b(realiz|efetu)(ar|a|ou|ei|amos|ando|ada|ado) (a|o|uma|um) \w+(ção|são|mento)\b',
        r'\b(faz(er|endo|emos)?|fez|fizemos|fiz) (a|o|uma|um) (validação|verificação|análise|correção|implementação|alteração|atualização|revisão|configuração|integração|migração|instalação)\b',
        r'\bproced(er|a|eu|endo) (com|à|ao)\b', r'\bno sentido de\b', r'\b(a|em) nível de\b',
        r'\bvisando( a)?\b', r'\bcom (o intuito|o objetivo|a finalidade) de\b', r'\ba fim de\b', r'\bsendo que\b',
        r'(?<!\bé )(?<!são )(?<!foi )(?<!era )(?<!ficou )(?<!segue )(?<!continua )\b(o|a|os|as|do|da|dos|das|no|na|nos|nas|ao|à|pelo|pela)\s+mesm[oa]s?\s*[.,;:)]',
        r'\b(o|a|os|as) mesm[oa]s? (foi|foram|é|são|está|estão|será|serão|tem|têm|deve|devem|pode|podem)\b',
        r'\b(vou|vamos|vai|vão|irei|iremos) estar \w+ndo\b', r'\bno que (diz respeito|tange|se refere) (a|ao|à|aos|às)\b',
        r'\bno tocante a\b', r'\btendo em vista que\b', r'\bdevido ao fato de( que)?\b',
        r'\bé possível (observar|notar|perceber|verificar) que\b', r'\bpode-se (dizer|afirmar|observar) que\b',
        r'\bde forma a\b', r'\bde (forma|maneira) (eficiente|eficaz|robusta|adequada|otimizada|significativa)\b',
        r'\batravés d(e|o|a|os|as)\b',
    ]),
    'falso cognato': (L, 'confira o sentido em português', [
        r'\beventualmente\b', r'\bassum(ir|o|imos|indo|iu) que\b', r'\brealizei que\b', r'\bsuport(ar|a|am) (o|a|os|as) (formato|versão|arquivo|protocolo)',
    ]),
}
LIMITES = {  # linhas não vazias e palavras, fora de código (e de tabelas, onde dito)
    'push': {'chars': 120},
    'thread': {'linhas': 6, 'palavras': 90},
    'decisao': {'linhas': 10, 'palavras': 140},
    'diario': {'linhas': 4, 'palavras': 60},
    'pausa': {'linhas': 15, 'palavras': 200, 'sem_tabela': True},
    'final': {'linhas': 20, 'palavras': 250, 'sem_tabela': True},
    'devolutiva': {'itens': 12, 'palavras_item': 40},
    'relatorio': {'palavras': 450, 'sem_tabela': True},
    'revisao': {'palavras': 550, 'sem_tabela': True},
    'sabatina': {'perguntas': 7, 'palavras_pergunta': 70},
    'pergunta': {'perguntas': 4, 'palavras_pergunta': 70, 'opcoes': '2-4', 'header': 12, 'palavras_label': 5, 'palavras_descricao': 25},
    'livre': {},
}
CURTOS = {'push', 'thread', 'decisao', 'diario'}
EMOJI_OK = set('✅⚠⛔⏸🔨🔍🎛❓➡️') | {'️'}

def norm(s):
    return unicodedata.normalize('NFC', s)

def catalogo_md():
    out = ['| Categoria | Severidade | Troque por | Padrões |', '|---|---|---|---|']
    for cat, (sev, dica, pads) in CATALOGO.items():
        out.append(f'| {cat} | {sev.lower()} | {dica} | ' + ' · '.join(f'`{p}`' for p in pads).replace('|', '\\|') + ' |')
    return '\n'.join(out)

def limpar(linha):
    linha = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', linha)   # link e imagem: só o texto visível conta
    linha = re.sub(r'`[^`]*`', ' ', linha)
    linha = re.sub(r'https?://\S+', ' ', linha)
    return re.sub(r'"[^"\n]*"|“[^”\n]*”', ' ', linha)

def palavras(s):
    return len(re.findall(r'\w+', limpar(s)))

OUTRO = re.compile(r'^\s*(outr[oa]s?|other|nenhuma das anteriores)\b', re.I)

def checar_pergunta(texto, lim):
    """Forma do painel do AskUserQuestion no T3 (sabatina/SABATINA.md) e vícios de cada campo."""
    achados = []
    try:
        dado = json.loads(texto)
    except json.JSONDecodeError as e:
        return [(G, 'JSON', 'json inválido', str(e)[:60], 'grave o input da chamada como JSON')], '0 perguntas'
    qs = dado.get('questions') if isinstance(dado, dict) else dado
    if not isinstance(qs, list) or not qs:
        return [(G, 'JSON', 'forma', 'sem "questions"', 'o JSON precisa de {"questions": [...]}')], '0 perguntas'
    if len(qs) > lim['perguntas']:
        achados.append((G, 'chamada', 'tamanho', f'{len(qs)} perguntas', f'no máximo {lim["perguntas"]} por chamada; o resto vai numa chamada seguinte'))
    vistas = set(); n_opc = 0
    for i, q in enumerate(qs, 1):
        onde = f'P{i}'
        if not isinstance(q, dict):
            achados.append((G, onde, 'forma', 'não é objeto', 'cada pergunta é um objeto')); continue
        pergunta = str(q.get('question') or '').strip(); header = str(q.get('header') or '').strip()
        opcoes = q.get('options') if isinstance(q.get('options'), list) else []
        if not pergunta:
            achados.append((G, onde, 'forma', 'sem question', 'escreva a pergunta'))
        elif pergunta in vistas:
            achados.append((G, onde, 'forma', 'pergunta repetida', 'o T3 usa o texto como chave: as respostas se sobrepõem'))
        vistas.add(pergunta)
        if pergunta and not pergunta.rstrip('`*_ ').endswith('?'):
            achados.append((L, onde, 'forma', pergunta[-30:], 'termine a pergunta em "?"'))
        if palavras(pergunta) > lim['palavras_pergunta']:
            achados.append((L, onde, 'tamanho', f'pergunta com {palavras(pergunta)} palavras', f'no máximo {lim["palavras_pergunta"]}'))
        if not header:
            achados.append((G, onde, 'forma', 'sem header', f'etiqueta de até {lim["header"]} caracteres'))
        elif len(header) > lim['header']:
            achados.append((G, onde, 'tamanho', f'header "{header}" com {len(header)} caracteres', f'no máximo {lim["header"]}'))
        if 'preview' in q or any(isinstance(o, dict) and 'preview' in o for o in opcoes):
            achados.append((L, onde, 'forma', 'preview', 'o T3 descarta o preview; ponha o trecho na pergunta'))
        if not 2 <= len(opcoes) <= 4:
            achados.append((G, onde, 'tamanho', f'{len(opcoes)} alternativas', 'de 2 a 4 alternativas'))
        rotulos, recomendadas = [], []
        for k, o in enumerate(opcoes, 1):
            n_opc += 1; ondo = f'{onde}.{k}'
            label = str((o or {}).get('label') or '').strip() if isinstance(o, dict) else ''
            desc = str((o or {}).get('description') or '').strip() if isinstance(o, dict) else ''
            if not label:
                achados.append((G, ondo, 'forma', 'sem label', 'escreva a alternativa')); continue
            base = re.sub(r'\s*\(recomendad[oa]\)\s*$', '', label, flags=re.I)
            if re.search(r'\(recomendad[oa]\)', label, re.I):
                recomendadas.append(k)
            if base.lower() in rotulos:
                achados.append((G, ondo, 'forma', f'"{base}" repetida', 'alternativas diferentes'))
            rotulos.append(base.lower())
            if palavras(base) > lim['palavras_label']:
                achados.append((L, ondo, 'tamanho', f'label com {palavras(base)} palavras', f'de 1 a {lim["palavras_label"]} palavras'))
            if OUTRO.match(base):
                achados.append((G, ondo, 'forma', base, 'não crie "Outro": o compositor já é a resposta livre'))
            if not desc:
                achados.append((L, ondo, 'forma', 'sem description', 'diga o que acontece com essa escolha'))
            elif palavras(desc) > lim['palavras_descricao']:
                achados.append((L, ondo, 'tamanho', f'description com {palavras(desc)} palavras', f'no máximo {lim["palavras_descricao"]}'))
            for campo in (base, desc):
                achados += [(sev, ondo, cat, trecho, dica) for sev, cat, trecho, dica in achados_linha(campo)]
        if not recomendadas:
            achados.append((L, onde, 'recomendação', 'nenhuma "(Recomendado)"', 'marque a sua recomendação'))
        elif len(recomendadas) > 1:
            achados.append((G, onde, 'recomendação', f'{len(recomendadas)} recomendadas', 'recomende uma só'))
        elif recomendadas[0] != 1:
            achados.append((L, onde, 'recomendação', f'recomendada na posição {recomendadas[0]}', 'a recomendada vem primeiro'))
        for campo in (header, pergunta):
            achados += [(sev, onde, cat, trecho, dica) for sev, cat, trecho, dica in achados_linha(campo)]
    return achados, f'{len(qs)} perguntas, {n_opc} alternativas'

def achados_linha(l):
    """Vícios e forma de uma linha: [(severidade, categoria, trecho, dica)]."""
    t = limpar(l); out = []
    for cat, (sev, dica, pads) in CATALOGO.items():
        for p in pads:
            for m in re.finditer(p, t, re.I | re.M):
                out.append((sev, cat, m.group(0).strip(), dica))
    if '!' in t and not re.search(r'!\[|!=', t):
        out.append((L, 'forma', '!', 'sem exclamação'))
    if '...' in t or '…' in t:
        out.append((L, 'forma', 'reticências', 'termine a frase'))
    if re.search(r'\betc\.?', t, re.I):
        out.append((L, 'forma', 'etc.', 'liste tudo ou diga "entre outros" com o total'))
    for ch in t:
        if ord(ch) > 0x2600 and ch not in EMOJI_OK and unicodedata.category(ch) in ('So', 'Sk'):
            out.append((L, 'forma', ch, 'emoji decorativo: use só os ícones de status')); break
    neg = re.findall(r'\*\*([^*]+)\*\*', t); visivel = len(re.sub(r'[*#|>-]', '', t).strip())
    if neg and visivel and sum(len(x) for x in neg) / visivel > 0.5 and visivel > 40:
        out.append((L, 'forma', 'negrito', 'negrito só no rótulo, não na frase inteira'))
    cab = re.sub(r'^#+\s*', '', t).strip()
    pal = re.findall(r'[A-Za-zÀ-ÿ]+', cab)
    if len(pal) >= 4 and all(p[0].isupper() for p in pal) and any(p in ('Da', 'De', 'Do', 'Das', 'Dos', 'Para', 'Com', 'Em', 'No', 'Na') for p in pal):
        out.append((L, 'forma', cab[:40], 'maiúscula só no início'))
    for frase in re.split(r'(?<=[.!?])\s+', t):
        if palavras(frase) > 35:
            out.append((L, 'frase longa', f'{palavras(frase)} palavras', 'divida em duas')); break
    return out

def main():
    a = sys.argv[1:]
    if '--catalogo' in a:
        print(catalogo_md()); return 0
    tipo = 'livre'
    if '--tipo' in a:
        i = a.index('--tipo'); tipo = a[i + 1]; del a[i:i + 2]
    estrito = '--estrito' in a
    a = [x for x in a if x != '--estrito']
    if tipo not in LIMITES:
        print(f'texto.py: tipo desconhecido "{tipo}" ({", ".join(LIMITES)})', file=sys.stderr); return 2
    fonte = a[0] if a else '-'
    texto = norm(sys.stdin.read() if fonte == '-' else open(fonte).read())
    lim = LIMITES[tipo]; achados = []
    if tipo == 'pergunta':
        achados, resumo = checar_pergunta(texto, lim)
        achados.sort(key=lambda x: (x[0] != G, x[1]))
        print(f'texto.py · tipo pergunta · {resumo} (limites: 4 perguntas, 2 a 4 alternativas, header 12 caracteres, label 5 palavras)')
        for sev, onde, cat, trecho, dica in achados:
            print(f'{sev:<5} {onde} · {cat} · "{str(trecho)[:60]}" → {dica}')
        graves = sum(1 for x in achados if x[0] == G); leves = len(achados) - graves
        print(f'Resultado: {"AJUSTAR" if graves or (estrito and leves) else "LIMPO"} ({graves} grave(s), {leves} leve(s))')
        return 1 if graves or (estrito and leves) else 0
    texto = re.sub(r'<!--.*?-->', lambda m: '\n' * m.group(0).count('\n'), texto, flags=re.S)  # comentários HTML
    linhas, em_codigo = [], False
    for n, l in enumerate(texto.splitlines(), 1):
        if l.strip().startswith('```'):
            em_codigo = not em_codigo; continue
        if not em_codigo:
            linhas.append((n, l))
    uteis = [(n, l) for n, l in linhas if l.strip() and not l.lstrip().startswith('>')]
    corpo = [(n, l) for n, l in uteis if not (lim.get('sem_tabela') and l.lstrip().startswith('|'))]
    palavras = lambda s: len(re.findall(r'\w+', limpar(s)))

    for n, l in uteis:
        achados += [(sev, n, cat, trecho, dica) for sev, cat, trecho, dica in achados_linha(l)]
    paras, atual = [], []
    for n, l in linhas:
        if l.strip() and not re.match(r'\s*([-*+|#>]|\d+[.)])', l):
            atual.append((n, l))
        else:
            if atual: paras.append(atual)
            atual = []
    if atual: paras.append(atual)
    for p in paras:
        tr = sum(limpar(l).count('—') for _, l in p)
        if tr > 1:
            achados.append((G if tipo in CURTOS else L, p[0][0], 'forma', f'{tr} travessões', 'troque por vírgula, ponto ou dois-pontos'))
        if tipo not in ('relatorio', 'revisao', 'livre') and len(p) > 3:
            achados.append((L, p[0][0], 'parágrafo longo', f'{len(p)} linhas', 'no máximo 3 linhas por parágrafo'))

    total_pal = sum(palavras(l) for _, l in corpo)
    resumo = [f'{len(corpo)} linhas', f'{total_pal} palavras']
    if 'chars' in lim:
        c = len(' '.join(l.strip() for _, l in uteis)); resumo = [f'{c} caracteres']
        if c > lim['chars']:
            achados.append((G, 1, 'tamanho', f'{c} caracteres', f'no máximo {lim["chars"]}'))
    if 'linhas' in lim and len(corpo) > lim['linhas']:
        achados.append((G, corpo[0][0], 'tamanho', f'{len(corpo)} linhas', f'no máximo {lim["linhas"]}' + (' fora das tabelas' if lim.get('sem_tabela') else '')))
    if 'palavras' in lim and total_pal > lim['palavras']:
        achados.append((G, corpo[0][0], 'tamanho', f'{total_pal} palavras', f'no máximo {lim["palavras"]}' + (' fora das tabelas' if lim.get('sem_tabela') else '')))
    if 'itens' in lim:
        itens = [(n, l) for n, l in uteis if re.match(r'\s*(\d+[.)]|[-*])\s', l)]
        if len(itens) > lim['itens']:
            achados.append((G, itens[0][0], 'tamanho', f'{len(itens)} itens', f'no máximo {lim["itens"]}; o resto vai para Propostas'))
        for n, l in itens:
            if palavras(l) > lim['palavras_item']:
                achados.append((L, n, 'tamanho', f'item com {palavras(l)} palavras', f'no máximo {lim["palavras_item"]}'))
    if 'perguntas' in lim:
        qs = [(n, l) for n, l in uteis if '❓' in l]
        if len(qs) > lim['perguntas']:
            achados.append((G, qs[0][0], 'tamanho', f'{len(qs)} perguntas', f'no máximo {lim["perguntas"]} por rodada'))
        for n, l in qs:
            if palavras(l) > lim['palavras_pergunta']:
                achados.append((L, n, 'tamanho', f'pergunta com {palavras(l)} palavras', f'no máximo {lim["palavras_pergunta"]}'))
    if tipo in CURTOS and corpo and palavras(corpo[0][1]) > 25:
        achados.append((L, corpo[0][0], 'primeira linha', f'{palavras(corpo[0][1])} palavras', 'a primeira linha diz o essencial em até 25 palavras'))

    achados.sort(key=lambda x: (x[0] != G, x[1]))
    lim_txt = ', '.join(f'{k} {v}' for k, v in lim.items() if not isinstance(v, bool))
    print(f'texto.py · tipo {tipo} · ' + ', '.join(resumo) + (f' (limites: {lim_txt})' if lim_txt else ''))
    for sev, n, cat, trecho, dica in achados:
        print(f'{sev:<5} linha {n} · {cat} · "{trecho[:60]}" → {dica}')
    graves = sum(1 for x in achados if x[0] == G); leves = len(achados) - graves
    print(f'Resultado: {"AJUSTAR" if graves or (estrito and leves) else "LIMPO"} ({graves} grave(s), {leves} leve(s))')
    return 1 if graves or (estrito and leves) else 0

if __name__ == '__main__':
    sys.exit(main())
