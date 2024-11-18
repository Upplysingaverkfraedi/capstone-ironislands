<center>

# Capstone verkefni um Formúlu 1 - Upplýsingaverkfræði
## Iron Islands

</center>

# Samantekt.

Þetta Capstone verkefni beindist að því að svara rannsóknarspurningunni: „Hvor er betri Formúlu 1 kappakstursmaður, Max Verstappen eða Lewis Hamilton?“, með hjálp gagnadrifs mælaborðs, byggðu á gögnum úr opinberum Formúlu 1 gagnagrunni (`f1db.db`) til að bera saman frammistöðu þeirra á öllum keppnistímabilum og sérstaklega árið 2021.

Gögnin voru sótt, hreinsuð og greind með Python, SQL og reglulegum segðum (regex). 
Verkefnið bjó til sérsniðnar töflur og mælaborð með Shiny, sem sýnir lykilþætti eins og uppsöfnuð stig, hröðustu hringi, pit stop, og staðsetningargögn.

Niðurstöður sýna að þrátt fyrir yfirburði Hamiltons í heildartölfræði, eins og heildarfjölda stiga og sigra, skarar Verstappen fram úr í lykilþáttum sem benda til að hann sé betri ökumaður.
Á jafnstöðu ári, eins og 2021, sýndi Verstappen að hann er hæfari í að hámarka frammistöðu sína í aðstæðum þar sem smáatriði gera gæfumuninn.

Verkefnið byggði á þekkingu úr námsefni í SQL, gagnavinnslu og myndrænni framsetningu og nýtir þetta til að draga fram mikilvægar niðurstöður á myndrænan og notendavænan hátt.
Niðurstaðan staðfestir að Max Verstappen er betri kappakstursmaður.

# Inngangur.

Í þessari skýrslu er fjallað um lokaverkefnið "Capstone" sem snýr að greiningu gagna úr Formúlu 1 kappakstursheiminum. 
Verkefnið beinist að því að byggja upp gagnadrifið mælaborð sem veitir innsýn í einvígi á milli ökumannanna Lewis Hamilton og Max Verstappen á tímabilinu 2021, 
með það að markmiði að svara fyrir hvor þeirra er betri kappakstursmaður.
Með þessu mælaborði er stefnt að því að draga fram upplýsingar sem varpa ljósi á stigakeppni þeirra yfir kappaksturstímabilið 2021, með áherslu á uppsöfnuð stig í hverri keppni.

Markmið skýrslunnar er að útskýra þau skref sem tekin voru í vinnslu verkefnisins, allt frá gagnaöflun og vinnslu yfir í að birta niðurstöður og setja þær í fræðilegt samhengi við námsefni. 
Í gegnum þetta verkefni nýtum við þá þekkingu sem hefur verið aflað í námskeiðum í upplýsinga- og gagnasafnsfræði, þar á meðal aðferðir við greiningu gagna, gagnasafnsstjórnun og framsetningu upplýsinga.

Áður en áfram er haldið í skýrsluna er vert að athuga að gögnin fyrir þetta verkefni voru fengin með gagnagrunninum [f1db.db](https://github.com/f1db/f1db/releases), 
frá GitHub aðganginum [F1DB](https://github.com/f1db/f1db), sem er opinn og aðgengilegur GitHub aðgangur sem veitir gagnasöfn fyrir Formúlu 1 keppnir. 
Þessi gögn eru dreifð undir [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) leyfinu. 

# Lýsing á gagnaöflun.

Við öflun gagna fyrir verkefnið nýttum við okkur opinberan gagnagrunninn f1db.db, áskorunarlaust, af GitHub aðganginum F1DB. 
Gagnagrunnurinn er aðgengilegur á GitHub undir notandanafninu F1DB og er opinn og frjáls gagnagrunnur sem inniheldur ítarlegar upplýsingar um Formúlu 1 keppnir, þar á meðal ökumenn, lið, vélar, dekkjaframleiðendur, brautir og keppnir frá upphafi Formúlu 1 árið 1950 til dagsins í dag.

Gagnagrunnurinn er uppfærður reglulega, af Marcelo Overdijk, eftir hverja keppni til að tryggja að nýjustu upplýsingar séu tiltækar. 
Gögnin eru fáanleg í ýmsum sniðum, þar á meðal CSV, JSON, Smile (óhefðbundin útgáfa af JSON), SQL (MySQL, PostgreSQL eða SQLite ásamt .sql dump skrár) og SQLite gagnagrunnsformi. 
Ákveðið var að nota SQLite útgáfuna, þar sem hópurinn hafði reynslu af útgáfunni, uppfyllir okkar þarfir og er auðveld í notkun með Python.

Varðandi leyfisskilmála, þá er F1DB dreift undir Creative "Commons Attribution 4.0 International" (CC BY 4.0) leyfi. 
Þetta tiltekna leyfi býður notendum að deila, afrita og dreifa efninu á hvaða formi sem er; aðlaga, breyta og byggja ofan á efnið, jafnvel í viðskiptalegum tilgangi, að því tilskildu að viðeigandi heiður sé veittur, tengill á leyfið sé gefinn og bent sé á ef breytingar hafi verið gerðar.

Við sóttum SQLite útgáfuna af gagnagrunninum beint af GitHub síðu gagnagrunnsins. 
Þar sem gögnin eru opin og frjáls til notkunar. 
Þetta auðveldaði okkur að hefja gagnavinnslu og greiningu án tafar, þó þurftum við að búa til nýjar töflur út frá gagnagrunninum en umjföllun um þær framkvæmdir má finna í næsta kafla "Gagnavinnsla".

# Gagnavinnsla.

## Undirbúningur gagna.

Í upphafi voru gögnin greind og síuð til að draga út aðeins þau gögn sem tengjast Hamilton og Verstappen. Fyrst var unnið með töflurnar í gagnagrunninum til að búa til nýjar sérsniðnar töflur, sem einungis innihalda viðeigandi gögn fyrir keppnistímabilið 2021 og allar keppnir þar sem báðir ökumenn tóku þátt.

Python skráin [`Max-Lewis-table.py`]() var notuð í þessum tilgangi:

**Taflan `hamilton_verstappen_race_data_2021`:** Þessi tafla var búin til með því að sækja gögn úr `race_data` töflunni fyrir allar keppnir árið 2021 þar sem bæði Hamilton og Verstappen voru til staðar.
Gögnin voru síuð þannig að einungis niðurstöður fyrir þessa tvo keppendur voru tekin fyrir.

**Taflan `hamilton_verstappen_all_time_data`:** Önnur tafla var búin fyrir allar keppnir þar sem Hamilton og Verstappen tóku þátt yfir allan feril þeirra, óháð keppnisári.
Til að framkvæma þessar breytingar voru SQL fyrirspurnir notaðar í gegnum Python, með því að tengjast gagnagrunninum með SQLite. 
Þetta tryggði að gögnin væru einfölduð og aðeins viðeigandi gögn væru meðhöndluð.

## Að vinna með hröðusta hringi og pit stop gögn

Til viðbótar við ofangreindar aðgerðir var kóðinn [`f1_racedata.py`]() notaður til að safna gögnum um "fastest laps" (hraðasta hringi) og "pit stop" (viðkomu í pitt) fyrir báða ökumenn. 
Þessi gögn voru sótt frá opinberri vefsíðu Formúlu 1 með hjálp `Selenium`, `BeautifulSoup`, og REGEX. 
Gögnin voru síðan vistuð í töflunni `f1_racedata`.

Kóðinn framkvæmir eftirfarandi:

**Sækir gögn með vafraeftirlíkingu:** 
Með `Selenium` var vafri settur upp til að fara á vefsíður sem innihalda "fastest laps" og "pit stop" gögn fyrir tilteknar keppnir.

**Notkun á REGEX til að vinna með HTML:** 
Þegar HTML-innihaldið var sótt, var reglulegum segðum (REGEX) beitt til að draga út gögn úr töflum, svo sem ökumannanöfn, tíma, meðaltalshraða, og hringi.

**Flokkun gagna eftir ökumönnum:** 
Gögnin voru síuð eftir því hvort þau tengdust Hamilton eða Verstappen, og hverri færslu var úthlutað réttum race_id.

**Vista gögn í gagnagrunninum:** 
Gögnin voru síðan vistuð í töflu þar sem hvert atriði var skipulagt eftir upplýsingum um hraðasta hring, viðkomu í pitt, meðaltalshraða og fleira.

Þessi gögn eru sótt vegna þess að gögn um hröðustu hringi og pit stopp eru mikilvægar breytur sem gefa betri innsýn í frammistöðu ökumanna. 
Þau hjálpa okkur að bera saman Hamilton og Verstappen, ekki bara út frá stigum og sigrum, heldur einnig út frá þeirra hæfni til að bæta tíma í keppni.

## Staðsetningarupplýsingum bætt við gagnagrunninn.

Til að bæta við myndræna framsetningu á mælaborðinu var unnið með gögn um brautirnar þar sem keppnirnar fóru fram. 
Python skráin [`location.py`]() var notuð til að sækja og tengja staðsetningarhnit (breiddar- og lengdargráður) við hverja braut. 
Þetta var gert með því að tengjast OpenStreetMap Nominatim API, sem leitar að hnitum miðað við nöfn staða eða brauta.

Ferlið fól í sér:

Að sækja upplýsingar úr töflunni `hamilton_verstappen_all_time_data`, þar sem brautir og keppnir voru tengdar. 
Að senda fyrirspurnir til Nominatim API með nöfnum brautanna til að fá hnit.
Að bæta þessum upplýsingum við nýja töflu sem kallast `race_locations`, sem inniheldur `race_id`, `grand_prix_id`, `circuit_id`, og staðsetningarhnit (breiddar- og lengdargráður).
Við notkun API var sérstaklega hugað að reglum OpenStreetMap, og 1 sekúndu töf var bætt við milli fyrirspurna til að forðast að of mikið álag á þjónustuna.

## Hreinsun og umbreyting gagna.

Við hreinsun og umbreytingu gagna voru notaðar ýmsar tækni og aðferðir, þar á meðal:

**SQL síun:** Gögn voru síuð eftir ár, keppendum og stöðu þeirra til að tryggja að þau væru viðeigandi fyrir verkefnið.
**Python og SQLite:** Gögnin voru meðhöndluð og umbreytt með Python og SQLite, sem gerði okkur kleift að framkvæma flóknar SQL fyrirspurnir og framkvæma beinar breytingar á gagnagrunninum.
**Regex og textameðhöndlun:** Regex var notað til að sækja viðbótarupplýsingar fyrir töfluna `race_data`.

Eftirfarandi mynd (Mynd 1.) sýnir uppbyggingu gagnagrunnsins eftir lagfæringar og uppfærslur.

![DBDiagram.jpeg](www/DBDiagram.jpeg)
*Mynd 1. Uppbygging gagnagrunnsins.*

## Lokavinnsla og frágangur.

Lokavinnsla verkefnisins fól í sér að nýta öll unnin gögn til að smíða notendavænt og gagnvirkt mælaborð sem veitir innsýn í frammistöðu og einvígi Lewis Hamilton og Max Verstappen í Formúlu 1. 
Í þessum hluta var smíðuð Python skrá að nafni [`app.py`](), sem byggir á Shiny fyrir Python til að búa til mælaborðið.

Mælaborðið nýtir sér gögn úr sérsniðnum töflum, sem voru gerðar í undirbúningnum, í gagnagrunninum [`f1db.db`]() og tengir þau við gagnvirka myndræna framsetningu. 
Meðal lykilatriða í lokavinnslunni voru:

### Uppsetning mælaborðs.

Kóðinn í [`app.py`]() býr til mælaborð með notkun Shiny-viðmóts fyrir Python. 
Hann inniheldur:

Forsíðu með myndefni (skraut til að gera mælaborðið flott) sem tengist Hamilton og Verstappen, ásamt Formúlu 1 merki.
Valmyndir og yfirlit sem gefa notendum möguleika á að velja gögn eftir tímabilum, keppnum eða framleiðendum (vélar, lið og dekk).
Mismunandi glugga fyrir yfirlit, samanburð tímabila og frammistöðu framleiðenda.

### Gagnvirkni og myndræn framsetning.

Gögnin voru tengd við fjölbreytt myndræn tól, þar á meðal:

**Línurit fyrir uppsöfnuð stig:** 
Samanburður á stigum Hamiltons og Verstappens yfir tímabilið 2021.

**Kortlagning frammistöðu:**
Með staðsetningarupplýsingum úr töflunni `race_locations` var búið til gagnvirkt kort sem sýnir meðalstig ökumanna eftir brautum.

**Súlurit fyrir frammistöðu:** 
Samanburður á fjölda sigra, pallastöðum og öðrum þáttum.

**Spider Chart:**
Útfært til að sýna umfangsmikinn samanburð á frammistöðu yfir allan feril ökumanna.

**Hitakort:**
Sýnir hraðasta hring ökumanna á öllum brautum keppninar í tímaröð.


### Gagnabreytingar og hreinsanir.

Mælaborðið nýtir sér gögn sem voru hreinsuð og umbreytt í fyrri skrefum. 
Til viðbótar var:

Notast við gagnahreinsun til að tryggja samræmi í dálkum, meðhöndlað gögn eins og hnit, stig og tíma með Python-föllum. útbúin gagnvirk valmynd þar sem notendur geta valið keppnir eða flokkað gögnin.

### Samþætting korta.

Kortin voru byggð með notkun Mapbox API og staðsetningargagna úr töflunni `race_locations`. 
Þessi hluti tryggði að gögn um staðsetningu voru rétt tengd við viðeigandi upplýsingar um stig.

# Markverðustu niðurstöður.

Í samanburði milli Lewis Hamilton og Max Verstappen kemur í ljós að Max Verstappen er betri kappakstursmaður þegar bæði gögn frá öllum keppnum þeirra og sérstaklega árið 2021 eru skoðuð. 
Gögnin undirstrika hæfni þeirra beggja, en hápunkta Verstappens má sjá í mikilvægum þáttum sem gera hann fremri kappaksturmann.

## Samanburður á Lewis Hamilton og Max Verstappen fyrir öll tímabil.

**Fjöldi Stiga:**
Lewis Hamilton hefur safnað 4829,5 stigum yfir feril sinn, samanborið við 2979,5 stig hjá Verstappen (sjá mynd 2.). 
Þetta endurspeglar lengri feril Hamiltons, en Verstappen hefur náð sambærilegum árangri á styttri tíma.

**Fjöldi Keppnissigra:**
Hamilton er með 657 sigra, en Verstappen hefur 365 sigra. 
Þetta sýnir yfirburði Hamiltons þar sem Hamilton hefur varið meiri tíma í íþróttina.

**Hröðustu hringir:**
Hamilton hefur náð 67 hröðustu hringjum, samanborið við 33 hjá Verstappen. 
Hins vegar er bilið á milli þeirra minna en gæti verið miðað við lengd ferla þeirra.

**Staðabætur:** Verstappen hefur bætti upp 221 staði í keppnum, sem er aðeins 20 færri en Hamiltons 241, þrátt fyrir styttri feril.

**Grand Slams:** Hamilton hefur 6 „grand slams“ (keppnir þar sem ökumaður byrjar í fyrsta sæti, leiðir alla hringi og vinnur með hraðasta hring), en Verstappen hefur 5.

![Stigathroun.jpeg](www/Stigathroun.jpeg)
*Mynd 2. Stigaþróunarkúrfur fyrir kappakstursmennina.*

## Samanburður Lewis Hamilton og Max Verstappen fyrir tímabilið 2021.

Á tímabilinu 2021, þar sem bílarnir voru tæknilega jafnir, skar Verstappen sig úr.

**Fjöldi stiga:** 
Verstappen safnaði 395,5 stigum, samanborið við 387,5 stig Hamiltons, þrátt fyrir mjög jafna samkeppni (sjá mynd 3.).

**Fjöldi sigra:** 
Verstappen vann fleiri sigrar á tímabilinu, 65 gegn 45 Hamiltons.

**Grand Slams:** 
Verstappen vann eitt „grand slam,“ meðan Hamilton náði engu á þessu tímabili.

Gögnin sýna að þótt Hamilton hafi meiri reynslu og hafi náð framúrskarandi árangri yfir lengri tíma, sýnir Verstappen ótrúlega mikinn árangurs á styttri tíma.
Árið 2021, þegar kappaksturbílarnir voru sambærilegir, sannaði Verstappen sig með því að nýta færni sína til að vinna í lykilaðstæðum.
Þrátt fyrir styttri feril, hefur V erstappen sýnt framúrskarandi árangur sem undirstrikar að hann er betri kappakstursmaður.

![Stigathroun2021.jpeg](www/Stigathroun2021.jpeg)
*Mynd 3. Stigaþróunarkúrfa fyrir kappakstursmennina tímabilið 2021.*

![Braut.jpeg](www/Braut.jpeg)
*Mynd 4. Sýnidæmi um einstaka keppni fyrir tímabilið 2021.*

# Tengsl við námsefni.

## Stakræn stærðfræði

Með regex tókst að finna og sía mikilvægar upplýsingar, svo sem hraðasta hringi, nöfn ökumanna, hringatíma og pit stop gögn, úr flóknu uppsettu texta.
Í námsefninu lærðum við að reglulegar segðir nýtast vel í sjálfvirkri textavinnslu og til að einfalda ferlið við að vinna með stór gagnasöfn. 
Þessi þekking var beitt í verkefninu til að auka nákvæmni og draga út gögn hratt og örugglega. 
Með regex var hægt að greina mynstur í gögnum og tryggja að einungis rétt gögn voru vistuð í gagnagrunninn. 
Þetta sýnir hvernig reglulegar segðir eru hagnýtar í raunverulegum verkefnum og mikilvægt tæki í gagnavinnslu.

## SQL (gagnagrunnsvinna)

Í verkefninu notuðum við SQL í til þess að búa til flestallar þær töflur sem notaðar voru í gerð mælaborðsins.
Töflurnar voru annaðhvort búnar til útfrá stærri töflum [`f1db.db`]() eða myndaðar með regex vef-sköpun.
[`Max-Lewis-table.py`]() býr til þær samanburðartöflur sem mynda grunninn að markmiði verkefnisins og inniheldur nær eingöngu SQL skipanir.
SQL var líka grunntólið í myndun og lagfæringum á `race_data` og `race-location`.

## Myndræn framsetning og gagnafrásögn

Helstu gröf og töflur:

Verkefnið notaði helst línurit og stöplarit til að sýna samanburð á stigum og frammistöðu. 
Stöplarit eru mjög þægileg þegar á að bera saman töluleg gildi flokkabreyta (ekki of margar) og það hentar einmitt mjög vel til að bera saman frammistöður Hamiltons og Verstappen. 
Línurit eru góð til að sýna þróun tölulegra gilda sem hentaði vel fyrir samanburð ökumannanna á tímabilinu 2021, líka til að sýna stigasöfnun þeirra í gegnum árin.
Við notuðum radar-kort (spider-chart) til að sýna myndrænan samanburð í mörgum (ótengdum) atriðum

Gagnvirkt mælaborð, Shiny:

Í verkefninu var notað Shiny fyrir Python til að útbúa gagnvirka mælaborðið sem er undirstaðan í verkefninu.
Shiny hentaði vel því að það er notendavænt og við í hópnum höfðum allir reynslu af python og shiny úr fyrri verkefnum.
