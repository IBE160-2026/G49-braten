# Databaser: normalisering
Forelesningsnotater i emnet databaser, del 4.
Normalisering er en metode for å strukturere tabeller i en relasjonsdatabase.
Målet er at hvert faktum lagres ett sted, slik at dataene holder seg konsistente.
I denne forelesningen går vi fra en uryddig tabell til tredje normalform og BCNF.
Underveis ser vi på funksjonelle avhengigheter, nøkler og dekomponering.

Utgitt av forfatteren som CC0 1.0: fritt til bruk uten vilkår.

# Hvorfor normalisere?
- En tabell som blander flere temaer, lagrer de samme opplysningene mange ganger.
- Redundans gjør databasen større enn den trenger å være.
- Verre er det at kopier av samme opplysning kan bli forskjellige over tid.
- Normalisering deler tabellen opp i mindre tabeller som hver beskriver én ting.
- Resultatet er færre feil ved endringer og enklere regler for dataene.

# Anomalier
- En oppdateringsanomali oppstår når samme faktum må endres i mange rader.
- Glemmer vi én rad, viser databasen to ulike svar på samme spørsmål.
- En innsettingsanomali betyr at vi ikke kan lagre et faktum uten et annet.
- Eksempel: et nytt emne kan ikke registreres før en student har meldt seg opp.
- En slettingsanomali betyr at vi mister et faktum når vi sletter et annet.
- Eksempel: sletter vi siste oppmelding, forsvinner også opplysningene om emnet.

# Eksempel: tabellen Oppmelding
Oppmelding(studentnr, navn, emnekode, emnenavn, foreleser, karakter)
- Én rad per student per emne.
- Navnet til studenten gjentas i hver rad der studenten tar et emne.
- Emnenavn og foreleser gjentas for hver student som tar emnet.
- Bytter emnet foreleser, må vi oppdatere alle radene for det emnet.
- Denne tabellen bruker vi som gjennomgående eksempel i resten av forelesningen.

# Funksjonelle avhengigheter
- En funksjonell avhengighet skrives X -> Y og leses «X bestemmer Y».
- Den betyr at to rader med lik verdi for X alltid har lik verdi for Y.
- I Oppmelding gjelder studentnr -> navn og emnekode -> emnenavn, foreleser.
- Videre gjelder studentnr, emnekode -> karakter.
- Avhengighetene kommer fra virkeligheten vi modellerer, ikke fra dataene i tabellen.
- Én tabell med data kan motbevise en avhengighet, men aldri bevise den.

# Nøkler
- En supernøkkel er en mengde attributter som bestemmer alle attributtene i tabellen.
- En kandidatnøkkel er en minimal supernøkkel: ingen attributter kan fjernes.
- Primærnøkkelen er den kandidatnøkkelen vi velger å bruke.
- Et nøkkelattributt er et attributt som inngår i minst én kandidatnøkkel.
- I Oppmelding er (studentnr, emnekode) den eneste kandidatnøkkelen.

# Første normalform (1NF)
- En tabell er på første normalform når hver celle inneholder én atomær verdi.
- Det skal ikke finnes lister, mengder eller gjentatte grupper i en celle.
- Hver rad må kunne identifiseres entydig av en nøkkel.
- Et felt som «telefoner: 900 11 222, 911 22 333» bryter med 1NF.
- Relasjonsmodellen forutsetter 1NF, så de fleste tabeller oppfyller den allerede.

# Fra unormalisert til 1NF
- Anta at én rad per student lister alle emnene studenten tar i én kolonne.
- Løsningen er å lage én rad per kombinasjon av student og emne.
- Alternativt flyttes den gjentatte gruppen ut i en egen tabell med fremmednøkkel.
- Etter dette steget har vi tabellen Oppmelding slik den ble vist tidligere.
- Tabellen er nå på 1NF, men har fortsatt mye redundans.

# Andre normalform (2NF)
- En tabell er på andre normalform når den er på 1NF og har ingen partielle avhengigheter.
- En partiell avhengighet betyr at et ikke-nøkkelattributt avhenger av bare en del av nøkkelen.
- 2NF er bare et tema når kandidatnøkkelen består av flere attributter.
- Har tabellen en nøkkel med ett attributt, er den automatisk på 2NF hvis den er på 1NF.

# Partielle avhengigheter i Oppmelding
- Nøkkelen er (studentnr, emnekode).
- navn avhenger bare av studentnr, altså av en del av nøkkelen.
- emnenavn og foreleser avhenger bare av emnekode.
- Vi dekomponerer derfor i tre tabeller:
Student(studentnr, navn)
Emne(emnekode, emnenavn, foreleser)
Oppmelding(studentnr, emnekode, karakter)
- Nå lagres navnet til hver student bare én gang.

# Tredje normalform (3NF)
- En tabell er på tredje normalform når den er på 2NF og har ingen transitive avhengigheter.
- En transitiv avhengighet går fra nøkkelen via et annet ikke-nøkkelattributt.
- Formelt: for hver avhengighet X -> A er X en supernøkkel eller A et nøkkelattributt.
- Huskeregel: hvert attributt skal avhenge av nøkkelen, hele nøkkelen og bare nøkkelen.

# Transitive avhengigheter i Emne
- Anta at Emne også lagrer kontoret til foreleseren:
Emne(emnekode, emnenavn, foreleser, kontor)
- Her gjelder emnekode -> foreleser og foreleser -> kontor.
- Dermed avhenger kontor transitivt av emnekode via foreleser.
- Løsningen er å flytte kontoret til en egen tabell:
Foreleser(foreleser, kontor)
- Når en foreleser bytter kontor, endrer vi nå bare én rad.

# Boyce-Codd normalform (BCNF)
- En tabell er på BCNF når venstresiden i hver ikke-triviell avhengighet er en supernøkkel.
- BCNF er strengere enn 3NF fordi unntaket for nøkkelattributter er fjernet.
- Forskjellen viser seg bare når tabellen har flere overlappende kandidatnøkler.
- De fleste tabeller som er på 3NF, er også på BCNF.

# 3NF mot BCNF: et eksempel
Veiledning(student, fag, veileder)
- Hver veileder veileder i nøyaktig ett fag: veileder -> fag.
- En student har én veileder per fag: student, fag -> veileder.
- Kandidatnøklene er (student, fag) og (student, veileder).
- Tabellen er på 3NF fordi fag er et nøkkelattributt.
- Den er ikke på BCNF fordi veileder ikke er en supernøkkel.

# Dekomponering uten tap
- Når vi deler en tabell, må vi kunne sette den sammen igjen med en naturlig join.
- En dekomponering er tapsfri når joinen gir nøyaktig de opprinnelige radene.
- En tapsfri join gir verken færre rader eller falske ekstra rader.
- Regel for to deler: det felles attributtet må være en nøkkel i minst én av delene.
- Student og Oppmelding har studentnr felles, og studentnr er nøkkel i Student.

# Bevaring av avhengigheter
- En dekomponering bevarer avhengighetene når hver av dem kan sjekkes i én tabell.
- Da kan databasen håndheve reglene uten å gjøre joins ved hver endring.
- Til 3NF finnes det alltid en dekomponering som er både tapsfri og bevarer avhengighetene.
- Til BCNF er det ikke alltid mulig å bevare alle avhengighetene.
- I Veiledning går avhengigheten student, fag -> veileder tapt ved BCNF-dekomponering.

# Fjerde normalform (4NF)
- Fjerde normalform handler om flerverdiavhengigheter, skrevet X ->> Y.
- En flerverdiavhengighet betyr at X bestemmer en mengde verdier av Y uavhengig av resten.
- Eksempel: en foreleser har flere kurs og flere hobbyer som ikke henger sammen.
- Lagres begge i én tabell, må alle kombinasjoner av kurs og hobby lagres.
- Løsningen er to tabeller: én for kurs og én for hobbyer.

# Denormalisering
- Denormalisering betyr å innføre redundans med vilje, for eksempel for å få raskere spørringer.
- Det brukes ofte i rapporter og datavarehus der dataene sjelden endres.
- Prisen er at programmet selv må holde kopiene like.
- Normaliser først, og denormaliser bare når målinger viser at det trengs.

# Framgangsmåte i praksis
- 1. Skriv opp attributtene og de funksjonelle avhengighetene.
- 2. Finn kandidatnøklene ved å se hvilke attributter som bestemmer alle de andre.
- 3. Sjekk 1NF: fjern lister og gjentatte grupper.
- 4. Fjern partielle avhengigheter for å nå 2NF.
- 5. Fjern transitive avhengigheter for å nå 3NF, og vurder BCNF.
- 6. Kontroller at dekomponeringen er tapsfri og bevarer avhengighetene.

# Oppsummering
- Normalisering fjerner redundans og hindrer anomalier ved endringer.
- 1NF krever atomære verdier, 2NF fjerner partielle og 3NF transitive avhengigheter.
- BCNF krever at hver determinant er en supernøkkel.
- Dekomponeringer skal være tapsfrie og helst bevare avhengighetene.
- Neste forelesning: indekser og hvordan databasen finner radene raskt.
