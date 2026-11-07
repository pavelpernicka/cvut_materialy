from pathlib import Path
import fitz,json,subprocess,tempfile
fitz.TOOLS.set_small_glyph_heights(True)
R=Path(__file__).resolve().parents[1]
for folder in ['latex/obrazky','anki/media','output']:
 (R/folder).mkdir(parents=True,exist_ok=True)
data=json.loads((R/'scripts/metadata.json').read_text())
files={int(p.name.split()[1].split('_')[0]):p for p in R.glob('*.pdf')}
docs={n:fitz.open(p) for n,p in files.items()}
# Relativní hranice výřezů vybrané vizuální kontrolou zdrojových snímků.
C={(1, 13): (0.03, 0.265, 1, 0.94),
 (1, 15): (0.04, 0.23, 0.97, 0.89),
 (1, 26): (0.21, 0.18, 0.76, 0.875),
 (1, 30): (0.1, 0.235, 0.9, 0.92),
 (1, 39): (0.645, 0.685, 0.852, 0.96),
 (1, 46): (0.2, 0.44, 0.74, 0.875),
 (2, 9): (0.04, 0.28, 0.98, 0.93),
 (2, 20): (0, 0.208, 1, 0.88),
 (2, 29): (0, 0.22, 1, 0.915),
 (2, 33): (0, 0.118, 1, 0.91),
 (2, 36): (0.245, 0.195, 0.785, 0.87),
 (2, 53): (0.001, 0.22, 0.999, 0.88),
 (2, 54): (0.001, 0.22, 0.999, 0.88),
 (3, 21): (0.001, 0.23, 0.999, 0.9),
 (3, 23): (0, 0.218, 1, 0.9),
 (3, 30): (0.05, 0.33, 0.97, 0.86),
 (3, 34): (0, 0.212, 1, 0.89),
 (3, 41): (0.04, 0.3, 0.99, 0.9),
 (3, 53): (0.04, 0.24, 0.96, 0.97),
 (3, 57): (0.05, 0.44, 0.51, 0.98),
 (3, 61): (0.001, 0.25, 0.999, 0.9),
 (3, 62): (0.001, 0.24, 0.999, 0.9),
 (3, 66): (0.001, 0.23, 0.999, 0.88),
 (4, 13): (0.065, 0.275, 0.87, 0.84),
 (4, 16): (0.14, 0.55, 0.98, 0.9),
 (4, 29): (0.05, 0.29, 0.96, 0.9),
 (4, 31): (0.54, 0.3, 0.99, 0.98),
 (4, 38): (0.175, 0.285, 0.84, 0.855),
 (4, 41): (0.001, 0.21, 0.999, 0.89),
 (4, 52): (0.65, 0.16, 0.96, 0.955),
 (4, 53): (0.02, 0.18, 0.94, 0.97),
 (4, 59): (0.07, 0.29, 0.655, 0.92),
 (4, 70): (0.1, 0.29, 0.9, 0.74),
 (4, 77): (0.04, 0.36, 0.43, 0.87),
 (4, 79): (0.07, 0.235, 0.91, 0.92),
 (5, 11): (0.24, 0.43, 0.83, 0.9),
 (5, 16): (0.03, 0.52, 0.35, 0.91),
 (5, 22): (0.2, 0.18, 0.79, 0.835),
 (5, 31): (0.64, 0.33, 0.96, 0.73),
 (6, 5): (0.49, 0.25, 0.8, 0.88),
 (6, 6): (0.125, 0.635, 0.91, 0.9),
 (6, 7): (0.65, 0.178, 0.998, 0.28),
 (6, 8): (0.035, 0.605, 0.95, 1),
 (6, 15): (0.085, 0.45, 0.9, 0.925),
 (6, 16): (0.15, 0.62, 0.81, 0.88),
 (6, 32): (0.575, 0.32, 0.825, 0.495),
 (7, 11): (0.18, 0.53, 0.79, 0.925),
 (7, 13): (0.205, 0.6, 0.69, 0.925),
 (7, 37): (0.02, 0.37, 0.545, 0.855),
 (7, 39): (0.1, 0.25, 0.9, 0.88),
 (7, 42): (0.3, 0.24, 0.765, 0.85),
 (7, 48): (0.08, 0.275, 0.97, 0.795),
 (7, 62): (0.11, 0.25, 0.86, 0.87),
 (7, 64): (0.115, 0.2, 0.85, 0.86)}
CAP={(1, 13): 'Tvary a kapacity orbitalů s, p, d, f.',
 (1, 15): 'Pořadí obsazování podslupek a energetické hladiny.',
 (1, 26): 'Vznik iontové vazby přenosem elektronů.',
 (1, 30): 'Sdílení elektronů v kovalentní vazbě.',
 (1, 39): 'Symetrické prostorové uspořádání SF₆.',
 (1, 46): 'Hromadění nábojů na nehomogenitách po přiložení pole.',
 (2, 9): 'Lokální pole a vztah mezi permitivitou a polarizovatelností.',
 (2, 20): 'Permitivita, ztrátové číslo a ztrátový činitel jedné relaxace.',
 (2, 29): 'Vliv šířky rozdělení relaxačních dob.',
 (2, 33): 'Porovnání Debyeova, Coleových a HN modelu.',
 (2, 36): 'Frekvenční oblasti polarizačních mechanismů.',
 (2, 53): 'Součet vodivostního a polarizačního příspěvku.',
 (2, 54): 'Posun relaxačních maxim při růstu teploty.',
 (3, 21): 'Dvě rovnocenné polohy bez vnějšího pole.',
 (3, 23): 'Elektrické pole sníží bariéru ve směru driftu.',
 (3, 30): 'Frenkelova a Schottkyho porucha krystalové mřížky.',
 (3, 34): 'Arrheniův graf; směrnice křivky je záporná.',
 (3, 41): 'Nárazový, fotoelektrický a tepelný ionizační mechanismus.',
 (3, 53): 'Násobení elektronů při průchodu plynem.',
 (3, 57): 'Zpětná vazba přes kladné ionty a katodu.',
 (3, 61): 'Čtyři oblasti vodivosti plynu podle přednášky.',
 (3, 62): 'Nesamostatný, doutnavý a obloukový průběh.',
 (3, 66): 'Paschenova křivka – schematicky překresleno podle přednášky.',
 (4, 13): 'Vláknitá struktura azbestu.',
 (4, 16): 'Vrstvy slídy a jejich propojení draselnými ionty.',
 (4, 29): 'Křemenná síť a síť modifikovaná ionty.',
 (4, 31): 'Teplotní oblasti nukleace a růstu krystalů.',
 (4, 38): 'Tavicí a čeřicí část vanové pece.',
 (4, 41): 'Viskozitní křivka; schematicky podle s. 40–41, názvy bodů podle s. 40.',
 (4, 52): 'Zvlákňovací tryska a nanášení apretury.',
 (4, 53): 'Tažení optického vlákna a jeho ochranné vrstvy.',
 (4, 59): 'Příklady výrobků ze speciálních silikátových keramik.',
 (4, 70): 'Vznik krčků, zhutňování a uzavírání pórů při slinování.',
 (4, 77): 'Feroelektrická hysterezní smyčka P(E).',
 (4, 79): 'Teplotní závislosti kapacit keramických hmot.',
 (5, 11): 'Vliv čistoty kovu na zbytkovou rezistivitu.',
 (5, 16): 'Odpor při přechodu do supravodivého stavu.',
 (5, 22): 'Kritická mez magnetického pole a teploty.',
 (5, 31): 'Kontakt v konstrukci spínacího přístroje.',
 (6, 5): 'Lineární řetězec (vlevo) a prostorová síť (vpravo).',
 (6, 6): 'Izotaktické, syndiotaktické a ataktické uspořádání.',
 (6, 7): 'Příčné propojení makromolekulárních řetězců.',
 (6, 8): 'Od řetězce přes lamelu a sférolit ke struktuře polymeru.',
 (6, 15): 'Částice a jednotlivé fáze emulzní polymerace.',
 (6, 16): 'Polyadiční vznik urethanové vazby.',
 (6, 32): 'Páteřní řetězec silikonů s vazbami Si–O.',
 (7, 11): 'Diamagnetická odezva proti působícímu poli.',
 (7, 13): 'Částečné souhlasné uspořádání paramagnetických momentů.',
 (7, 37): 'Čtyři oblasti prvotní magnetizace.',
 (7, 39): 'Smyčky magneticky tvrdého a měkkého materiálu.',
 (7, 42): 'Komutační křivka spojující vrcholy smyček.',
 (7, 48): 'Statická a dynamická smyčka při různých frekvencích.',
 (7, 62): 'Magnetit a jeho spinelová struktura.',
 (7, 64): 'Uspořádání momentů a teplotní zánik uspořádaného stavu.'}
# Odstranění pouze okolního textu, který přesahuje do obdélníku schématu.
# Obrázky a vektorová kresba zůstávají beze změny; zdrojové PDF se nepřepisuje.
REMOVE_TEXT = {
 (2,36): ['Komplexní permitivita:'],
 (4,29): ['Sktruktura oxidových skel', '•'],
 (4,59): ['Steatit –', 'Forsterit –', 'vysokých teplot', 'Kordierit –', 'teplotních šocích', 'Pyrostat – Hráz', 'tepla díky'],
 (6,7): ['Makromolekulární látky'],
 (7,11): ['Inertní plyny', '•'],
 (6,5): ['Podle tvaru a uspořádání'],
 (3,57): ['elektronů vyražených dopadem', '•', 'Celý proces emise', 'zpětnovazební mechanismus'],
 (4,53): ['B. Skleněná vlákna', 'vlnovody', 'Ochrana optického kabelu', 'mechanickým, klimatickým', 'vlivům při instalaci'],
 (6,8): ['Makromolekuly jsou střídavě', 'seskupují do tzv. sférolitů'],
}
manifest={}
crop_issues=[]
for n,p in sorted({tuple(f) for d in data for f in d['figs']}):
 source=fitz.open()
 source.insert_pdf(docs[n],from_page=p-1,to_page=p-1)
 page=source[0]
 for block in page.get_text('dict')['blocks']:
  for line in block.get('lines',[]):
   text=''.join(span['text'] for span in line['spans'])
   bbox=fitz.Rect(line['bbox'])
   footer=text.strip()==str(p) and bbox.y0>page.rect.height*.93
   if footer or any(text.startswith(prefix) for prefix in REMOVE_TEXT.get((n,p),[])):
    page.add_redact_annot(bbox,fill=None)
 page.apply_redactions(images=0,graphics=0)
 if (n,p)==(3,57):
  # Popisek E v originálu koliduje s posledním řádkem odstavce.
  # Po jeho odstranění obnovíme označení nad stejnou šipkou.
  page.insert_text((195.1,277.5),'E',fontname='tiit',fontsize=24)

 r=page.rect;a,b,c,d=C[n,p];clip=fitz.Rect(a*r.width,b*r.height,c*r.width,d*r.height)
 if (n,p) not in [(3,66),(4,41),(6,5)]:
  for word in page.get_text('words'):
   box=fitz.Rect(word[:4]);intersection=box & clip
   if not intersection.is_empty and intersection.get_area()/box.get_area()<.98:
    crop_issues.append({'figure':f'{n}:{p}','text':word[4]})
 name=f'emv1_p{n}_s{p:02}'
 out=fitz.open();op=out.new_page(width=clip.width,height=clip.height)
 if (n,p) in [(3,66),(4,41)]:
  # Čitelné schéma podle přednášky z editovatelného vektorového zdroje.
  with tempfile.TemporaryDirectory(prefix='emv1-paschen-') as td:
   subprocess.run(['xelatex','-interaction=nonstopmode','-halt-on-error',
                   '-output-directory='+td,str(R/f'latex/obrazky/{name}.tex')],
                  check=True,stdout=subprocess.DEVNULL)
   out=fitz.open(Path(td)/f'{name}.pdf')
   op=out[0]
   # Načtený dokument drží obsah i po odstranění dočasného adresáře.
 elif (n,p)==(6,5):
  out=fitz.open();op=out.new_page(width=510,height=205)
  op.show_pdf_page(fitz.Rect(0,65,270,94),source,0,clip=fitz.Rect(237,154,507,183))
  op.show_pdf_page(fitz.Rect(305,0,500,196),source,0,clip=fitz.Rect(225,310,420,506))
 else:
  op.show_pdf_page(op.rect,source,0,clip=clip)
 # Malý bezpečný okraj kolem celého výřezu také v PNG pro Anki.
 padded=fitz.open();pp=padded.new_page(width=op.rect.width+8,height=op.rect.height+8)
 pp.show_pdf_page(fitz.Rect(4,4,op.rect.width+4,op.rect.height+4),out,0)
 out=padded;op=out[0]
 out.save(R/f'latex/obrazky/{name}.pdf',garbage=4,deflate=True)
 # PNG is self-contained and portable in Anki; preserve adequate resolution.
 zoom=min(4,1800/op.rect.width)
 op.get_pixmap(matrix=fitz.Matrix(zoom,zoom),alpha=False).save(R/f'anki/media/{name}.png')
 manifest[f'{n}:{p}']={'name':name,'caption':CAP[n,p],'source':files[n].name,'page':p,'crop':C[n,p]}
 if (n,p) in REMOVE_TEXT:
  manifest[f'{n}:{p}']['removed_surrounding_text']=REMOVE_TEXT[n,p]
 if (n,p)==(3,57):
  manifest[f'{n}:{p}']['adaptation']='Odstranění okolního odstavce a obnova překrytého popisku E nad šipkou.'
 if (n,p)==(3,66):
  manifest[f'{n}:{p}']['adaptation']='Vektorové překreslení pro čitelnost; bez číselného měřítka.'
 if (n,p)==(4,41):
  manifest[f'{n}:{p}']['adaptation']='Vektorové schéma podle P4, s. 40–41; názvy teplot tvarování sjednoceny s tabulkou na s. 40. Osa teploty bez číselného měřítka.'
(R/'scripts/obrazky.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(R/'output/overeni_orezu.json').write_text(json.dumps({
 'figures':len(manifest),'partial_words_at_crop_boundary':crop_issues,
 'padding_pt':4,'visual_review':'Všechny výřezy porovnány s přednáškami.'
},ensure_ascii=False,indent=2))
if crop_issues:
 raise ValueError(f'Ořez protíná text: {crop_issues}')
print('Vytvořeno',len(manifest),'vektorových výřezů a PNG pro Anki.')
