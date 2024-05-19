### Latviešu valodas pareizrakstības un pareizrunas vārdnīcas (LVPPV) datu pārveidošana uz modificēto SAMPA pierakstu.
---
Šajā repozitorijā fails "read_dict.py" veic visu analīzes loģiku.<br>
Ievaddatos tiek saņemta mape, kurā ir ".txt" failu formātā caurskatītas LVPPV lapaspuses ar vārdu un izrunu informāciju.<br>
Izvadā tiek izvadītas leksēmas, kas satur gan ortogrāfisko pierakstu, gan fonētisko izrunu LVTagger rīkam vēlamajā pierakstā.<br>
___
Papildus, turpmākā šī koda izstrādē būtu nepieciešams integrēt, šos datus iekš "tezaurs_lexemes.json" datiem.<br>
Kā arī izstrādāt metodi kā automātiski nošķirt starp vārdiem ar vairākiem izrunu variantiem priekš atsevisķām leksēmām, kas rakstās vienādi.<br>
