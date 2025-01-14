def reverze(n, s):
    if n<len(s):
        print(n)
        return reverze(n+1,s)+s[n]
    else:
        return ''
    
print(reverze(0,'ahoj'))

str = '''Babička měla syna a dvě dcery. Nejstarší žila mnoho let ve Vídni u přátel, od nichž se vdala. Druhá dcera šla pak na její místo. Syn řemeslník též byl již samostatným a přiženil se do městského domku. Babička bydlela v pohorské vesničce na slezských hranicích, žila spokojeně v malé chaloupce se starou Bětkou, která byla její vrstevnice a již u rodičů sloužila.

Nežila osamotnělá ve své chaloupce; všickni obyvatelé vesničtí byli bratřími jí a sestrami, ona jim byla matkou, rádkyní, bez ní se neskončil ani křest, ani svatba, ani pohřeb.

Tu najednou přišel babičce list z Vídně od nejstarší dcery, v němž jí vědomost dávala, že manžel její službu přijal u jedné kněžny, která má velké panství v Čechách, a sice jen několik mil vzdálenosti od pohorské vesničky, kde babička bydlí. Tam že se nyní s rodinou odstěhuje, manžel pak vždy jen přes léto že tam bude, když i paní kněžna se tam zdržuje. Ke konci listu stála vroucí prosba, aby babička k nim se odebrala navždy a živobytí svoje u dcery a vnoučat strávila, kteří se již na ni těší. Babička se rozplakala; nevěděla, co má dělat! Srdce ji táhlo k dceři a k vnoučátkům, jichž neznala ještě, dávný zvyk poutal ji k malé chaloupce a k dobrým přátelům! Ale krev není voda, touha přemohla dávný zvyk, babička se rozmyslila, že pojede. Chaloupku se vším, co v ní, odevzdala staré Bětce s doložením: „Nevím, jak se mi tam líbit bude a jestli přece zde neumřu mezi vámi." Když jednoho dne vozík u chaloupky se zastavil, naložil naň kočí Václav babiččinu malovanou truhlu, kolovrat, bez něhož být nemohla, košík, v němž byla čtyry chocholatá kuřátka, pytlík s dvěma čtverobarevnými koťaty a pak babičku, která pro pláč ani neviděla před sebe. Požehnáním přátel provázena odejela k novému domovu.'''

print(reverze(0,str))
