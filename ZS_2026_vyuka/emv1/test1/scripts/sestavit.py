#!/usr/bin/env python3
"""Sazba a Anki export z editovatelných latex/otazky/qNN.tex."""
from pathlib import Path
import json, subprocess, html, re, csv, genanki
R=Path(__file__).resolve().parents[1]
for folder in ['anki','output']:
 (R/folder).mkdir(parents=True,exist_ok=True)
D=json.loads((R/'scripts/metadata.json').read_text());F=json.loads((R/'scripts/obrazky.json').read_text())
for d in D:
 if not re.fullmatch(r'P[1-7]: [0-9, –-]+(?:; P[1-7]: [0-9, –-]+)*',d['refs']):
  raise ValueError(f"Otázka {d['n']}: povoleny jsou pouze odkazy na přednášky P1–P7.")
 d['body']=(R/'latex/otazky'/f"q{d['n']:02}.tex").read_text()
def esc(s):
 s=s.replace('₆','6').replace('₂','2').replace('₃','3').replace('₄','4').replace('–','--').replace('—','---')
 return ''.join({'&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','\\':r'\textbackslash{}'}.get(c,c) for c in s)
def htex(s):
 p=subprocess.run(['pandoc','-f','latex','-t','html5','--mathjax','--wrap=none'],input=s,text=True,capture_output=True,check=True)
 if p.stderr:print(p.stderr)
 return p.stdout.strip()
header=r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=16mm,top=15mm,bottom=17mm]{geometry}
\usepackage{fontspec}\setmainfont{TeX Gyre Pagella}\setsansfont{Lato}
\usepackage[czech]{babel}
\usepackage{amsmath,amssymb,graphicx,xcolor,enumitem}
\usepackage{titlesec,hyperref}
\definecolor{ink}{HTML}{173B4A}\definecolor{muted}{HTML}{526773}
\hypersetup{colorlinks=true,linkcolor=ink,urlcolor=ink,pdftitle={EMV1: otázky a stručné odpovědi}}
\titleformat{\section}{\normalsize\sffamily\bfseries\color{ink}}{}{0pt}{}
\titlespacing*{\section}{0pt}{0pt}{5pt}
\setlist{nosep,leftmargin=1.35em,topsep=3pt,itemsep=2pt}
\setlength{\parindent}{0pt}\setlength{\parskip}{4pt}\setlength{\emergencystretch}{2em}
\setlength{\abovedisplayskip}{5pt}\setlength{\belowdisplayskip}{5pt}
\pagestyle{plain}
\begin{document}
'''
parts=[header]
for d in D:
 n=d['n']
 parts += [r'\noindent\begin{minipage}[b]{\linewidth}',r'\section*{'+str(n)+'. '+esc(d['question'].strip())+'}',r'\input{otazky/q'+f'{n:02}'+'.tex}']
 if d['figs']:parts.append(r'\par\vspace{2mm}')
 width='.48' if len(d['figs'])>1 else '.94'
 for i,(lec,pg) in enumerate(d['figs']):
  f=F[f'{lec}:{pg}'];parts += [r'\begin{minipage}[t]{'+width+r'\linewidth}\centering',r'\includegraphics[width=\linewidth,height=52mm,keepaspectratio]{obrazky/'+f['name']+'.pdf}',r'\par\vspace{1mm}{\scriptsize\sffamily\color{muted} '+esc(f['caption'])+' '+esc(f'P{lec}, s. {pg}.')+r'\par}',r'\end{minipage}'+(r'\hfill' if i==0 and len(d['figs'])>1 else '')]
 parts += [r'\par\end{minipage}\par\vspace{6mm}']
parts += [r'\end{document}']
(R/'latex/emv1_otazky.tex').write_text('\n'.join(parts)+'\n')
css='''body{margin:0}.card{font-family:Arial,sans-serif;font-size:19px;line-height:1.5;text-align:left;color:#182b34;background:#fff;padding:18px;max-width:880px;margin:auto}.label{font-size:13px;color:#526773;letter-spacing:.03em}.question{font-size:22px;font-weight:600;margin:10px 0 18px}p{margin:.65em 0}li{margin:.3em 0}ul,ol{padding-left:1.4em}img{max-width:100%;height:auto;background:white}figure{margin:18px 0}figcaption,.sources{font-size:13px;color:#526773}table{border-collapse:collapse;width:100%;font-size:.95em}td,th{border-bottom:1px solid #cdd5d8;padding:5px}hr{border:0;border-top:1px solid #ccd7da;margin:22px 0}mjx-container[display=true]{overflow-x:auto;overflow-y:hidden;padding:4px 0}.nightMode.card{background:#202327;color:#e5e9ec}.nightMode .label,.nightMode .sources,.nightMode figcaption{color:#b4c1cb}a{color:#286681}@media(max-width:500px){.card{font-size:17px;padding:12px}.question{font-size:20px}}'''
model=genanki.Model(1826011061,'EMV1 – otázka, LaTeX/MathJax a obrázky',fields=[{'name':s} for s in ['ID','Tema','Otazka','Odpoved','Obrazky','Zdroje']],templates=[{'name':'Otázka → odpověď','qfmt':'<div class="label">EMV1 · {{ID}} · {{Tema}}</div><div class="question">{{Otazka}}</div>','afmt':'{{FrontSide}}<hr id="answer"><div class="answer">{{Odpoved}}</div>{{Obrazky}}<hr><div class="sources">{{Zdroje}}</div>'}],css=css,sort_field_index=0)
themes=['Stavba látek a polarizace','Permitivita a dielektrické ztráty','Vodivost izolantů a výboje','Anorganické materiály','Vodivé a odporové materiály','Plasty a elastomery','Magnetické materiály'];bounds=[8,15,25,40,49,57,66]
decks={i:genanki.Deck(1826011100+i,f'EMV1 – Test 1::{i:02} {t}') for i,t in enumerate(themes,1)}
rows=[];used=set()
for d in D:
 n=d['n'];lec=next(i+1 for i,b in enumerate(bounds) if n<=b);body=htex(d['body']);question=html.escape(d['question']);figs=''
 for l,p in d['figs']:
  f=F[f'{l}:{p}'];name=f['name']+'.png';used.add(name)
  figs+=f'<figure><img src="{name}" alt="{html.escape(f["caption"],quote=True)}"><figcaption>{html.escape(f["caption"])} P{l}, PDF s. {p}.</figcaption></figure>'
 refs=html.escape(d['refs'])+'. Čísla stran označují pořadí v původním PDF.'
 fields=[f'{n:02}',themes[lec-1],question,body,figs,refs];tags=[f'EMV1::otazka_{n:02}',f'EMV1::prednaska_{lec}']
 decks[lec].add_note(genanki.Note(model=model,fields=fields,tags=tags,guid=genanki.guid_for(f'emv1-test1-2026-question-{n}'),due=n));rows.append(fields+[' '.join(tags)])
package=genanki.Package(list(decks.values()));package.media_files=[str(R/'anki/media'/n) for n in sorted(used)];package.write_to_file(str(R/'anki/EMV1_Test1.apkg'))
with (R/'anki/EMV1_Test1.tsv').open('w',newline='') as f:
 f.write('#separator:Tab\n#html:true\n#columns:ID\tTema\tOtazka\tOdpoved\tObrazky\tZdroje\tTags\n#tags column:7\n');csv.writer(f,delimiter='\t').writerows(rows)
(R/'output/export_audit.json').write_text(json.dumps({'notes':len(rows),'cards':len(rows),'media':len(used),'deck_names':[d.name for d in decks.values()],'source_policy':'Pouze dodané přednášky P1–P7','external_sources':{}},ensure_ascii=False,indent=2))
print(f'Vytvořen LaTeX, APKG: {len(rows)} karet a {len(used)} médií, TSV.')
