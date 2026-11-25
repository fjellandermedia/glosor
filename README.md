# Glosträning

Glosträning med matchning, skrivövningar, adaptiv repetition och spaced repetition. Systemet har två delar:

```
 Lärare                                                     Elever
 ┌──────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐   ┌──────────────────────┐
 │ Power Apps       │──▶│ SharePoint-listor   │◀──│ Power Automate-flöde │◀──│ Webbsida (det här    │
 │ (lägger in och   │   │ glosor_bocker, …    │   │ "När en HTTP-begäran │   │ repot, GitHub Pages) │
 │ delar glosor)    │   │ glosor_gloslistor   │   │ tas emot" → JSON     │   │ statistik i webbläs. │
 └──────────────────┘   └─────────────────────┘   └─────────────────────┘   └──────────────────────┘
```

| Del | Instruktion |
| --- | --- |
| SharePoint-listorna | [docs/1-sharepoint.md](docs/1-sharepoint.md) |
| Power Automate-flödet (API) | [docs/2-power-automate.md](docs/2-power-automate.md) |
| Lärarappen i Power Apps (YAML) | [docs/3-power-apps.md](docs/3-power-apps.md), koden i [powerapps/](powerapps) |
| Elevernas webbsida | den här filen |

Bygg i den ordningen. Webbsidan fungerar redan nu i **demoläge** med exempelglosor, så länge `apiUrl` i [`js/config.js`](js/config.js) är tom.

## Elevernas webbsida

### Hitta listor

- **Direktlänk** från läraren: `https://fjellandermedia.github.io/glosor/?lista=17`. Flera listor går också: `?listor=17,18,19`.
- **Hitta gloslistor** → välj lärare → bocka för en eller flera listor.
- **Mina gloslistor**: listor som eleven lagt till. Eleven kan bocka för flera och träna dem blandat.
  Under ⋯ kan en lista pausas, markeras som avslutad (arkiveras) eller tas bort. Den kan aktiveras igen senare.

### Ett träningspass

1. **Introduktion** av nya ord i grupper om fem, med *Introduktion: fas 2 av 4* och en stapel:
   - **Matcha:** para ihop målspråk (i genusfärg) med svenska.
   - **Skriv:** svenska visas, eleven skriver på målspråket. *Ledtråd* visar en bokstav i taget, högst halva ordet.
     Vid fel visas rätt svar (i genusfärg) och eleven skriver av det tills det blir rätt.
   - **Repetera:** ord som inte satt direkt skrivs en gång till.
   - Sista gruppen fylls ut till fem med ord som eleven redan gjort fel på.
2. **Översikt:** varje ord på en grön, gul eller röd platta med försök, fel och ledtrådar.
3. **Stor matchning** (frivillig) med alla ord. Högst sex par syns samtidigt, nya fylls på när par klaras.
4. **Repetition** med den adaptiva algoritmen tills alla ord är klara (*12 av 30 ord avklarade*).
5. **Avslut:** "Bra gjort! Nu har du övat klart för denna gång." och *Kom tillbaka i morgon* eller *Nästa repetition: 7 december*.

Stegvisaren överst visar *Introduktion → Matchning → Repetition*. Vid senare tillfällen repeteras bara ord som är dags att repetera, plus nya ord som läraren lagt till.

### Repetitionsalgoritmen ([`js/motor.js`](js/motor.js))

| Regel | Implementation |
| --- | --- |
| Nivåer −1, 0, 1, 2 | `Repetition.niva`. Klar vid nivå 2 |
| Startnivå | Nya ord: 1 om skrivet direkt utan fel, ledtråd eller extraförsök i introduktionen, annars 0. Ord som repeteras från tidigare dagar: 0 |
| Rätt svar | +1 |
| Fel svar **eller ledtråd** | −1, aldrig under −1. Eleven får ändå beröm om ordet till slut blir rätt |
| Felkö | Ord som når −1 läggs sist i felkön. Var tredje fråga tas från felkön. Felkö-ord som klaras får nivå 0 och går tillbaka till huvudlistan |
| Ordning | Slumpad. Nivå 1-ord sprids jämnt bland nivå 0-ord. Samma ord kommer aldrig två gånger i rad (om andra ord finns kvar). Listan börjar om från början, och klara ord hoppas över |

### Spaced repetition

All statistik sparas i webbläsaren (`localStorage`, nyckeln `glosor.v1`), per glosa. Samma glosa i flera listor delar alltså statistik.
För varje ord sparas antal pass, rätt, fel, ledtrådar, senast tränad, nästa repetition, intervallsteg och hur många frågor ordet behövde för att nå nivå 2.

Intervall: **1 → 3 → 7 → 14 → 30 → 60 dagar.** Ett pass utan fel och ledtrådar tar ordet ett steg upp.
1–2 fel eller ledtrådar tar det ett steg ned, fler än så börjar om på 1 dag. Nya ord repeteras alltid dagen efter.

Statistiken följer webbläsaren, inte eleven. Byter eleven dator börjar statistiken om.

### Rättning

- Mellanslag och skiljetecken (`.,!?¿¡`) spelar ingen roll.
- Accenter räknas (`é` ≠ `e`). Om bara accenter eller stora/små bokstäver skiljer får eleven tipset *Kolla accenter och stora/små bokstäver*.
- Versaler räknas, eftersom läraren bara skriver versal där den ska vara. Undantag: stor första bokstav godkänns om facit börjar med liten, eftersom mobiler gör så automatiskt.
- `la casa / el hogar` godkänner båda. `(se) llamar` godkänner både *llamar* och *se llamar*.
- Knappar för specialtecken visas för spanska, franska, tyska, italienska, portugisiska och finska.

## Filer

```
index.html            sidan
css/style.css         utseende (ljust och mörkt läge)
js/config.js          API-adress (tom = demoläge)
js/app.js             skärmar och övningsflöde
js/motor.js           rättning, ledtrådar, repetitionsalgoritm, spaced repetition (utan DOM)
js/api.js             anrop till Power Automate
js/lagring.js         elevens data i localStorage
js/demo.js            exempeldata i samma format som flödet svarar med
tests/                tester för motor.js
powerapps/            YAML till Power Apps (genereras av tools/generera_powerapps.py)
docs/                 instruktioner för SharePoint, Power Automate och Power Apps
```

## Köra lokalt och testa

```bash
python3 -m http.server 8000
```

Öppna http://localhost:8000. Sidan använder JavaScript-moduler och måste därför köras via en webbserver, inte som fil.

```bash
node --test tests/*.test.mjs
```

## Publicera

*Settings → Pages → Deploy from a branch → `main` / `(root)`*. Sidan hamnar på `https://fjellandermedia.github.io/glosor/`.
Samma adress står som `WebbAdress` i Power Apps ([`powerapps/App.Formulas.txt`](powerapps/App.Formulas.txt)), och därifrån bygger appen länkarna.
