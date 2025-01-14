def preskoc_komentare(line):
  # vytiskne obsah souboru 'f' s vynechanymi komentari
  stav=0          # počáteční stav automatu
  for c in line:  # přečti jeden znak
    if stav==0:   # počáteční stav
      if c=="#":  # začátek komentáře
        stav=1
        continue        
      elif c=='\"':
        stav=2    # začátek řetězce
    elif stav==1: # 1="komentar"
      continue
    elif stav==2:
      if c=='\"':
        stav=0
    print(c,end="") # vytiskni znak
 
i=input()
preskoc_komentare(i)  # nacti radku a preskakuj
