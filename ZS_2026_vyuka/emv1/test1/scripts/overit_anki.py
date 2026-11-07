from pathlib import Path
import json,re,tempfile
from anki.collection import Collection
from anki.import_export_pb2 import ImportAnkiPackageRequest
R=Path(__file__).resolve().parents[1]
metadata=json.loads((R/'scripts/metadata.json').read_text())
expected_images={f"{q['n']:02}":{f'emv1_p{l}_s{p:02}.png' for l,p in q['figs']} for q in metadata}
tempdir=tempfile.TemporaryDirectory(prefix='emv1-anki-test-')
tmp=Path(tempdir.name)
col=Collection(str(tmp/'collection.anki2'))
result=col.import_anki_package(ImportAnkiPackageRequest(package_path=str(R/'anki/EMV1_Test1.apkg')))
assert col.note_count()==66,(col.note_count(),str(result))
assert col.card_count()==66,col.card_count()
missing=[];math=0;image_refs=set();fronts=[]
for cid in col.find_cards(''):
 card=col.get_card(cid);n=card.note();front=card.question();back=card.answer()
 assert n['Otazka'] and n['Odpoved']
 assert set(re.findall(r'<img[^>]+src="([^"]+)"',n['Obrazky']))==expected_images[n['ID']]
 assert 'id="answer"' in back
 assert n['Odpoved'] in back
 assert '\\begin{itemize}' not in back
 for f in re.findall(r'<img[^>]+src="([^"]+)"',back):
  image_refs.add(f)
  if not (Path(col.media.dir())/f).is_file():missing.append(f)
 math+=n['Odpoved'].count('\\(')+n['Odpoved'].count('\\[')
 fronts.append(n['ID'])
assert not missing,missing
assert image_refs==set().union(*expected_images.values())
assert sorted(fronts)==[f'{n:02}' for n in range(1,67)]
check=col.media.check()
print('Media check:',check)
assert not check.missing and not check.unused
report={'import_backend':'installed Anki Python backend','notes':col.note_count(),'cards':col.card_count(),'referenced_media':len(image_refs),'math_expressions':math,'missing_media':missing,'unused_media':list(check.unused),'question_numbers_complete':True}
(R/'output').mkdir(exist_ok=True)
(R/'output/overeni_anki.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
col.close()
tempdir.cleanup()
print(json.dumps(report,ensure_ascii=False))
