# Достаёт слова и красное выделение из трёх PDF -> ../data/raw.json
import pdfplumber, sys, json, re
RED=(0.88,0.19,0.19)
def klass(ch):
    col=tuple(round(x,2) for x in (ch.get('non_stroking_color') or ()))
    size=round(ch['size'],1); font=ch['fontname']
    if col==RED and size>9.2: return 'R'
    if col==(0.12,0.15,0.2) and size in (10.5,9.6): return 'W'
    if col==(0.6,0.64,0.71): return 'N'
    if col==(0.23,0.36,0.86) and size>10: return 'H'
    if col==(0.48,0.51,0.59): return 'P'
    if col==(0.76,0.15,0.36): return 'S'
    if 'Italic' in font: return 'I'
    return 'O'
def rows(p):
    out=[]; row=None; sec=None; prevk=None; headbuf=''
    with pdfplumber.open(p) as pdf:
        for pi,pg in enumerate(pdf.pages):
            for ch in pg.chars:
                k=klass(ch); t=ch['text']
                if ch['top']>pg.height-45 and k=='N': prevk=None; continue   # номер страницы
                if k=='N':
                    if prevk!='N':
                        row={'n':'','sec':sec,'f':{'w':[], 'p':[], 'h':[]},'order':[]}; out.append(row)
                    row['n']+=t.strip()
                elif k=='H':
                    if prevk!='H': sec=''
                    sec+=t; row=None
                elif k=='O': 
                    if t.strip(): row=None if round(ch['size'],1)!=9.0 or True else row
                elif row is not None:
                    fld={'W':'w','R':'w','P':'p','I':'h','S':'h'}[k]
                    lst=row['f'][fld]
                    if lst and ch['top']-lst[-1][2]>3 and lst[-1][0]!=' ': lst.append((' ',0,ch['top']))
                    lst.append((t,1 if k=='R' else 0,ch['top']))
                    if not row['order'] or row['order'][-1]!=fld: row['order'].append(fld)
                prevk=k
    res=[]
    for r in out:
        d={'n':int(r['n']),'sec':(r['sec'] or '').strip()}
        for fld in 'wph':
            txt=''.join(c for c,_,_ in r['f'][fld]); mask=''.join(str(m) for _,m,_ in r['f'][fld])
            # trim
            l=len(txt)-len(txt.lstrip()); rr=len(txt.rstrip())
            d[fld]=txt[l:rr]; 
            if fld=='w': d['m']=mask[l:rr]
        res.append(d)
    return res
if __name__=='__main__':
    U,P,S=sys.argv[1:4]
    data={'udar':rows(U),'prepri':rows(P),'slov':rows(S)}
    json.dump(data,open(sys.argv[4],'w'),ensure_ascii=False,indent=0)
    for k,v in data.items(): print(k,len(v))
