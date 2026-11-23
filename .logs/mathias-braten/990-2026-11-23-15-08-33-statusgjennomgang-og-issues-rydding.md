# Statusgjennomgang og rydding i issues.md

## 2026-11-23 kl. 15:08 — Mathias Bråten

### Oppgave
Mathias spurte hvordan prosjektet ligger an, og ba deretter om at utdaterte punkter i issues.md ble ryddet.

### Plan
- Les sprint-status.yaml, issues.md, PRD §7.1 (kuttlinjer og levering 7.12) og retroene for epic 1 og 2.
- Kjør testene.
- Sjekk hvert åpne punkt mot repoet, og kryss av punktene som er løst eller som går igjen to ganger.

### Resultat
- Status: epic 1 er ferdig bortsett fra 1-9b (backlog). Epic 2 er ferdig bortsett fra 13b og 13c (backlog). Epic 3 er ikke startet og er utenfor Must. Ingen av kuttlinjene 20.11 og 30.11 slår inn.
- Testene: 897 bestått (pytest, 3 min 34 s).
- issues.md: fem punkter er krysset av med løsningsdato 2026-11-23:
  - PDF-test før stakkvalg: følges nå opp som retrotiltak OQ-1.
  - De 18 UX-antakelsene: erstattet av punktet om 29 antakelser.
  - Kuttlinja 20.11: ikke brukt, trinn 1 ble ferdig 18.11.
  - Kuttlinja 30.11: FR-14–17 er levert i story 11, 11b og 12.
  - Neste steg bmad-spec: spec og stories finnes.
- Sjekket at disse fortsatt er åpne: PRODUCT.md sier fortsatt «Stack: Undecided». Unntaket i AD-13 dekker bare en Grade-celle som venter, ikke en kilderad som venter. BMad-konfigen har fortsatt communication_language: English.

### Åpne punkter
- Ingen nye. OQ-2 (målinger i Real mode «før 20.11») står fortsatt åpen selv om datoen er passert. Den henger sammen med retrotiltak 3 og målingene før levering.
