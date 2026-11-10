# raw.json (из extract.py) -> words.json: карточки для трёх вкладок
import json, re, sys
raw = json.load(open(sys.argv[1])); out_path = sys.argv[2]
VOW = 'аеёиоуыэюя'
yo = lambda s: s.replace('ё', 'е').replace('Ё', 'Е')
caps = lambda w, m: ''.join(c.upper() if x == '1' else c for c, x in zip(w, m))

def split_forms(w, m):
    """делит 'занять; занял, заняла' на формы, сохраняя маску"""
    res = []; start = 0
    for i, c in enumerate(w + ';'):
        if c in ';,':
            seg, sm = w[start:i], m[start:i]
            l = len(seg) - len(seg.lstrip()); r = len(seg.rstrip())
            if seg.strip(): res.append((seg[l:r], sm[l:r]))
            start = i + 1
    return res

# ---------- ударения ----------
POS = [('Имена существительные', 'Существительные'), ('Имена прилагательные', 'Прилагательные'), ('Глаголы', 'Глаголы'),
       ('Причастия и отглагольные прилагательные', 'Причастия'), ('Деепричастия', 'Деепричастия'), ('Наречия', 'Наречия')]
pos_idx = {a: i for i, (a, b) in enumerate(POS)}
udar = []
for r in raw['udar']:
    forms = split_forms(r['w'], r['m'])
    row = yo(caps(r['w'], r['m'])) if len(forms) > 1 else ''
    for w, m in forms:
        assert m.count('1') == 1, (w, m)
        s = m.index('1'); w2 = yo(w.lower())
        assert w[s].lower() in VOW and sum(c in VOW for c in w2) >= 2, w
        card = {'w': w2, 's': s, 'p': pos_idx[r['sec']]}
        if r['p']: card['c'] = yo(r['p'])
        if r['h']: card['x'] = yo(r['h'])
        if row: card['r'] = row
        udar.append(card)
# одинаковые слова из разных частей речи (красивее) — подписываем, чтобы не выглядели повтором
from collections import Counter as _C
_dup = {k for k, v in _C((c['w'], c['s']) for c in udar).items() if v > 1}
_names = ['существительное', 'прилагательное', 'глагол', 'причастие', 'деепричастие', 'наречие']
for c in udar:
    if (c['w'], c['s']) in _dup and 'c' not in c: c['c'] = '(' + _names[c['p']] + ')'

# ---------- пре- / при- ----------
prepri = []
for r in raw['prepri']:
    for w, m in split_forms(r['w'], r['m']):
        assert m.count('1') == 1 and w[m.index('1')].lower() in 'еи', w
        g = m.index('1')
        assert w[g-2:g].lower() == 'пр'
        prepri.append({'w': yo(w.lower()), 'g': g})

# ---------- словарные ----------
MANUAL_GAPS = {'грамота': [4], 'грамотный': [4], 'иней': [2], 'панцирь': [4]}      # в PDF у этих трёх слов гласная не выделена
PAIR_FIX = {('бюллетень', 1): 'ию', ('жюри', 1): 'ую'}
def pair(word, i):
    c = word[i]; prev = word[i-1] if i else ''
    if (word, i) in PAIR_FIX: return PAIR_FIX[(word, i)]
    if c in 'ао': return 'ёо' if (c == 'о' and prev in 'жш') else 'ао'
    if c == 'и' and prev == 'ц': return 'иы'
    if c in 'еи': return 'еи'
    if c == 'я': return 'ея'
    if c == 'у': return 'оу'
    raise ValueError((word, i))
slov = []
for r in raw['slov']:
    forms = split_forms(r['w'], r['m'])
    w, m = forms[0]
    gaps = [i for i, x in enumerate(m) if x == '1'] or MANUAL_GAPS[w]
    w2 = yo(w)
    card = {'w': w2, 'g': gaps, 'o': [pair(w, i) for i in gaps]}
    for i, o in zip(gaps, card['o']): assert w2[i] in o, (w2, i, o)
    if r['p'] and len(forms) == 1: card['c'] = r['p']
    if len(forms) > 1:
        rest = []
        for fw, fm in forms[1:]:
            fg = [i for i, x in enumerate(fm) if x == '1'] or MANUAL_GAPS.get(fw, [])
            rest.append({'w': yo(fw) + ('(ка)' if fw == 'фигурист' else ''), 'g': fg})
        card['d'] = rest
    slov.append(card)

json.dump({'pos': [b for a, b in POS], 'udar': udar, 'prepri': prepri, 'slov': slov},
          open(out_path, 'w'), ensure_ascii=False, separators=(',', ':'))
from collections import Counter
print('ударения:', len(udar), Counter(c['p'] for c in udar))
print('пре-/при-:', len(prepri), Counter(c['w'][c['g']] for c in prepri))
print('словарные:', len(slov), Counter(len(c['g']) for c in slov))
