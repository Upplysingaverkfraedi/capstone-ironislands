# Keyrsla á `app.py`

Höfum database-ið `f1db.db`. Höfum prófað að gera app með gröfum, alls ekki fullkomið hægt að sjá gróflega hvernig gögnin lýta út og hvernig þau eru upp sett.

Keyrðu eftirfarandi skipun til þess að vera í réttu umhverfi:

```bash
pip install -r requirements.txt
```

síðan getur keyrt annað hvort `appdb.py` eða `appgogn.db` með eftirfarandi skipun:

```bash
shiny run appdb.py
```

Ef þú ert með windows tölvu gæti verið að þú þurfir að keyra þessa skipun til þess að keyra app-ið:

```bash
python -m shiny run --reload appdb.py
```

# Ferli

## Skref 1, sækja gagnagrunn

### A. Sækja og Undirbúa Rétta Gagnagrunnsskrá

### Fara á Útgáfusíðuna

- Farðu á: [https://github.com/f1db/f1db/releases](https://github.com/f1db/f1db/releases).

### Sækja SQLite Gagnagrunnsskrána

- Undir nýjustu útgáfu, finndu og sæktu `f1db-sqlite.zip`.

### Afþjappa Gagnagrunnsskránni

- Notaðu þjappunarforrit til að afþjappa `f1db-sqlite.zip`.
- Eftir afþjöppun ættirðu að fá skrána `f1db.sqlite` eða `f1db.db`.

### Staðfesta Gagnagrunnsskrána

- Athugaðu skráarstærðina (hún ætti að vera nokkrar MB).
- Ekki opna skrána í textaritli, þar sem það getur eyðilagt tvíundargögnin.

## B. Tengja Gagnagrunninn í PyCharm

### Opna PyCharm og Fá Aðgang að Gagnagrunnsglugga Tólsins

- Í PyCharm, farðu í **View > Tool Windows > Database**.

### Bæta við Nýjum Gagnagrunni

1. Smelltu á + (Bæta við) táknið í gagnagrunnsglugganum.
2. Veldu **Data Source > SQLite**.

### Stilla Gagnagrunntenginguna

- **Database File**: Smelltu á möpputáknið og veldu afþjöppuðu `f1db.sqlite` skrána.
- **Driver**: Ef beðið er um það, leyfðu PyCharm að sækja nauðsynlega SQLite drivera.

### Prófa Tengingu

- Smelltu á **Test Connection** til að tryggja að PyCharm geti tengst gagnagrunninum.
- Þú ættir að sjá skilaboð um að tengingin hafi tekist.

### Vista Stillinguna

- Smelltu á **OK** til að vista gagnagrunninn.

### Skoða Gagnagrunninn

- Í gagnagrunnsglugganum, stækkaðu f1db gagnagrunninn.
- Nú ættirðu að sjá allar töflur (t.d. drivers, constructors, races, osfrv.).

## C. Bilanaúrræði ef Vandamál Halda Áfram

Ef þú stendur enn frammi fyrir sömu villu eftir að hafa fylgt ofangreindum skrefum, reyndu eftirfarandi:

### Staðfesta Heilleika Gagnagrunnsskrárinnar

- Reyndu að opna `f1db.sqlite` skrána í SQLiteStudio eða öðru SQLite-samhæfu tóli.
- Ef önnur tól geta ekki opnað gagnagrunninn gæti verið að skráin sé skemmd.

### Reyna Annað Þjappunarforrit

- Stundum mistekst þjappunarforritum þögult.
- Prófaðu annað forrit (t.d. ef þú notaðir innbyggða þjappunarforritið, prófaðu 7-Zip).

### Athuga Skrá fyrir Spillingu

- Berðu saman skráarstærðina á `f1db.sqlite` við það sem gefið er upp á útgáfusíðunni eða við aðra sem hafa náð að hlaða henni niður.
- Ef stærðirnar eru verulega ólíkar gæti niðurhal ekki verið fullkomið.

### Nota SQL Dump sem Valkost

Ef gagnagrunnsskráin veldur enn vandræðum, íhugaðu að nota SQL dump skrána.

#### Flytja SQL Dump Inn í Nýjan SQLite Gagnagrunn

##### Með Skipanalínu

- Búa til nýjan tóman gagnagrunn:
  
  ```bash
  sqlite3 new_f1db.dbß
  ```

## Skref 2, búa til nothæf gögn. `Max-Lewis-table.py`

Þessi kóði fer í upphaflega f1db.db gagnagrunninn og býr til 2x nýjar töflu sem heita:

- `hamilton_verstappen_all_time_data`
  - Þessi tafla hefur aðeins gögn um Lewis Hamilton og Max Verstappen
- `hamilton_verstappen_race_dara_2021`
  - Þessi hefur sömu gögn og í hinni töflunni nema aðeins fyrir árið 2021

## Skref 3, ná í staðsetningar 'location.py'

Þessi kóði fer inn í gagnagrunninn okkar og finnur staðsetningar fyrir öll keppnir í síuðu gögnunum. Hann gerir það í gégnum API hjá openstreetmap.org. Kóðinn geymir þessar upplýsingar í nýrri töflu sem heitir `race_locations`

## Skref 4, ná í upplýsingar um keppnir `f1_racedata.py`

Þessi kóði nær í nákvæmari upplýsingar um frammistöðu keppendana árið 2021 sem ekki eru í gagnagrunninum. Hann gerir það með því að nota reglulegar segðir og HTML kóða vefsíðunnar. Upplýsingarnar úr keyrslunni eru geymdar í nýrri töflu sem heitir `f1_racedata.py`.