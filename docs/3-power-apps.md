# 3. Lärarappen i Power Apps

Appen är en arbetsyteapp (canvas app) med fyra skärmar:

| Skärm | Fil | Gör |
| --- | --- | --- |
| `scrStart` | [`1-scrStart.yaml`](../powerapps/1-scrStart.yaml) | Startsida med tre val |
| `scrGlosor` | [`2-scrGlosor.yaml`](../powerapps/2-scrGlosor.yaml) | Lägga in glosor: en i taget eller inklistrade (tabb, `;` eller ` - ` mellan orden), byta plats på språken, färgmarkera genus, skapa böcker och kapitel, se och rätta glosor som redan finns i kapitlet |
| `scrNyLista` | [`3-scrNyLista.yaml`](../powerapps/3-scrNyLista.yaml) | Skapa eller redigera en gloslista: välj bok och kapitel och bocka för glosor, ta med fristående glosor, slå ihop befintliga listor, spara och kopiera elevlänken |
| `scrListor` | [`4-scrListor.yaml`](../powerapps/4-scrListor.yaml) | Mina (eller allas) gloslistor: kopiera länk, redigera, använd som mall, dölj för elever, ta bort |

## Steg för steg

1. **Skapa appen.** *make.powerapps.com → Skapa → Tom app → Tom arbetsyteapp*, format **Surfplatta**.
2. **Lägg till data.** *Data → Lägg till data → SharePoint →* din webbplats → bocka för `glosor_bocker`, `glosor_kapitel`, `glosor_glosor` och `glosor_gloslistor`.
   Heter listorna något annat hos er, ändra `DATAKALLOR` överst i utskriftsdelen av [`tools/generera_powerapps.py`](../tools/generera_powerapps.py) och generera om filerna.
   Gör detta **innan** du klistrar in skärmarna, annars blir formlerna röda.
3. **Named formulas.** Markera **App** i trädvyn, välj egenskapen **Formulas** och klistra in hela [`App.Formulas.txt`](../powerapps/App.Formulas.txt).
   Om Power Apps är på svenska, använd i stället [`App.Formulas.sv.txt`](../powerapps/App.Formulas.sv.txt) (semikolon mellan argument).
   Ändra `WebbAdress` om elevsidan inte ligger på `https://fjellandermedia.github.io/glosor/`.
4. **Klistra in skärmarna.** Öppna en YAML-fil på GitHub och klicka på kopieraknappen ("Copy raw file"). I Power Apps Studio:
   högerklicka i **trädvyn** → **Klistra in** → **Klistra in kod** (*Paste code*). Gör så för alla fyra filerna, i ordning.
5. **Ta bort** den tomma `Screen1` och dra `scrStart` överst, så att appen startar där.
6. Kontrollera att inga formler är röda (*App checker*, stetoskopet uppe till höger). Spara och publicera.
7. Dela appen med lärarna och ge dem redigeringsrätt på SharePoint-webbplatsen.

### Om skärmen inte går att klistra in

Vissa versioner av Studio tar bara emot kontroller, inte hela skärmar. Gör då så här för varje skärm:

1. Lägg till en tom skärm och döp om den till exakt namnet ovan, till exempel `scrGlosor`.
2. Sätt skärmens **Fill** till `RGBA(244, 246, 251, 1)` och, för `scrNyLista` och `scrListor`, egenskapen **OnVisible**. Den står överst i skärmens YAML-fil.
3. Kopiera motsvarande fil i [`powerapps/kontroller/`](../powerapps/kontroller). Högerklicka på skärmen i trädvyn → **Klistra in kod**.

### Svenska eller engelska formler?

YAML-koden använder engelsk formelsyntax (`,` mellan argument och `;` mellan formler). Studio översätter den när du klistrar in.
Om Power Apps är på svenska skriver du formler för hand med `;` mellan argument och `;;` mellan formler.
För `App.Formulas` finns en färdig svensk version: [`App.Formulas.sv.txt`](../powerapps/App.Formulas.sv.txt).
Det enklaste är att tillfälligt byta Power Apps till engelska (kugghjulet → Språk) medan du bygger.

## Så fungerar det för lärarna

**Lägga in glosor (`scrGlosor`)**

1. Välj bok och kapitel. Finns de inte, skriv namnet och klicka på *Skapa bok* eller *Skapa kapitel*.
   För fristående glosor lämnar du boken tom och väljer språk.
2. Klistra in en lista (t.ex. två kolumner från Word eller Excel, `house⇥hus`) och klicka på *Lägg till raderna*, eller skriv en glosa i taget.
3. Kontrollera raderna. Rätta direkt i rutorna. Klicka på genusknappen för att växla färg: *genus → mask. → fem. → neutr.*
   Appen föreslår genus utifrån artikeln (el/la, le/la, der/die/das, il/la, o/a).
4. Hamnade språken åt fel håll? Klicka på **⇄ Byt plats på språken**.
5. Klicka på **Spara N glosor**. Glosorna syns direkt i högerkolumnen, *Redan inlagda här*. Där kan alla lärare fylla på samma kapitel och rätta stavfel.

**Skapa gloslista (`scrNyLista`)**

1. Välj bok och kapitel och bocka för glosor (eller *Markera alla*). Byt kapitel eller bok och fortsätt bocka. Allt samlas i högerkolumnen.
2. Vill du slå ihop listor, välj dem under *…eller slå ihop befintliga gloslistor* och klicka på *Lägg till glosorna*.
3. Ge listan ett namn och klicka på **Spara gloslista**. Kopiera länken (`…/glosor/?lista=17`) och dela den med eleverna.

**Gloslistor (`scrListor`)**: *Dölj* gör att eleverna inte längre ser listan. *Använd som mall* gör en ny lista med samma glosor.

## Bra att veta

- Glosor och listor kopplas med ID-nummer. Gloslistan sparar `GlosaIDs = "12;15;19"`, så en glosa finns bara en gång även om den ingår i många listor.
- Bara den som skapat en glosa kan ta bort den i appen. Alla kan rätta stavning och genus.
- Om en glosa tas bort hoppar webbsidan bara över den i listorna där den ingick.
- YAML-filerna genereras av [`tools/generera_powerapps.py`](../tools/generera_powerapps.py). Ändra där och kör `python3 tools/generera_powerapps.py` om du vill göra större ändringar.
