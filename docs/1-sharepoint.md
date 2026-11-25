# 1. SharePoint-listorna

Allt material ligger i fyra listor på **en** SharePoint-webbplats, till exempel språklärarnas Teams-webbplats.
Lärarna behöver redigeringsrätt (medlem) på webbplatsen. Eleverna behöver ingen behörighet alls: de hämtar glosorna via Power Automate-flödet.

```
glosor_bocker ──< glosor_kapitel ──< glosor_glosor >── (GlosaIDs) ── glosor_gloslistor
  ID         BokID        BokID, KapitelID       "12;15;19;…"
```

- En **bok** har flera **kapitel**.
- En **glosa** hör till en bok och ett kapitel. Fristående glosor har `BokID = 0` och `KapitelID = 0`.
- En **gloslista** är det som delas ut till eleverna. Den pekar på glosor med deras ID, i kolumnen `GlosaIDs` (`12;15;19`).
  Därför kan en lista blanda kapitel, böcker och fristående glosor. När listor slås ihop återanvänds glosorna, inget dupliceras.
  Om någon rättar ett stavfel i en glosa syns rättelsen i alla listor som använder den.

## Viktigt innan du börjar

1. **Skriv kolumnnamnen exakt som här**, utan å, ä och ö, med samma stora och små bokstäver.
   Power Apps och flödet använder namnen. (Du kan byta visningsnamn efteråt, men då måste du ändra i formlerna också. Låt bli.)
2. **Titelkolumnen ska heta `Title`.** På en svenskspråkig webbplats heter den ofta *Rubrik*.
   Byt namn på den till `Title` i varje lista: *Listinställningar → klicka på Rubrik → Kolumnnamn: Title*.
   Power Apps använder visningsnamnet, så formlerna fungerar bara om den heter Title.
3. Skapa kolumnerna via **Listinställningar → Skapa kolumn**. Då blir det interna namnet samma som namnet du skriver.
   Om du i stället använder *+ Lägg till kolumn* direkt i listvyn kan det interna namnet bli något annat.

## Lista 1: `glosor_bocker`

| Kolumn | Typ | Obligatorisk | Kommentar |
| --- | --- | --- | --- |
| `Title` | (finns redan) | Ja | Bokens namn, t.ex. *Caminando 1* |
| `Sprak` | En textrad | Ja | Språkkod: `es`, `de`, `fr`, `en`, `it`, `pt`, `la`, `fi` |

## Lista 2: `glosor_kapitel`

| Kolumn | Typ | Obligatorisk | Kommentar |
| --- | --- | --- | --- |
| `Title` | (finns redan) | Ja | Kapitlets namn, t.ex. *Kapitel 4* |
| `BokID` | Tal, 0 decimaler | Ja | ID för boken i `glosor_bocker` |
| `Ordning` | Tal, 0 decimaler | Nej | Sorteringsordning, sätts automatiskt av appen |

## Lista 3: `glosor_glosor`

| Kolumn | Typ | Obligatorisk | Kommentar |
| --- | --- | --- | --- |
| `Title` | (finns redan) | Ja | Ordet på **målspråket**, t.ex. *la casa* |
| `Svenska` | En textrad | Ja | Översättningen, t.ex. *huset* |
| `Genus` | En textrad | Nej | `m`, `f`, `n` eller tom |
| `Sprak` | En textrad | Ja | Språkkod, t.ex. `es` |
| `BokID` | Tal, 0 decimaler | Nej | Standardvärde **0**. 0 betyder fristående glosa |
| `KapitelID` | Tal, 0 decimaler | Nej | Standardvärde **0** |
| `SkapadAv` | En textrad | Nej | Lärarens namn, fylls i av appen |
| `SkapadAvEpost` | En textrad | Nej | Lärarens e-post, fylls i av appen. Bara den som skapat glosan kan ta bort den |

**Indexera** `KapitelID`, `BokID` och `Sprak`. Det gör att filtren fungerar även när listan växer förbi 5 000 glosor:
*Listinställningar → Indexerade kolumner → Skapa nytt index*, ett index per kolumn.

## Lista 4: `glosor_gloslistor`

| Kolumn | Typ | Obligatorisk | Kommentar |
| --- | --- | --- | --- |
| `Title` | (finns redan) | Ja | Listans namn, t.ex. *Repetition inför prov* |
| `Beskrivning` | En textrad | Nej | Visas för eleverna |
| `Sprak` | En textrad | Nej | Språkkod, sätts av appen |
| `LarareNamn` | En textrad | Ja | Eleverna väljer lärare utifrån detta namn |
| `LarareEpost` | En textrad | Ja | Används för *Mina listor* i appen. Visas aldrig för elever |
| `GlosaIDs` | **Flera textrader**, *oformaterad text* | Nej | `12;15;19`. Välj **Oformaterad text** (inte RTF/utökad text) och **Nej** på *Lägg till ändringar i befintlig text* |
| `Aktiv` | Ja/Nej | – | Standardvärde **Ja**. Dolda listor (Nej) syns inte för eleverna |

Indexera gärna `LarareEpost` och `Aktiv`.

## Snabbtest

Lägg in en bok, ett kapitel och några glosor för hand. Skapa sedan en gloslista med `GlosaIDs` = glosornas ID med semikolon emellan.
Kolumnen ID visar du via *Redigera aktuell vy → bocka för ID*.
Då kan du testa flödet och webbsidan innan Power Apps-appen är klar.
