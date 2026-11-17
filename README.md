# Glosträning

En statisk webbsida för att öva glosor. Sidan hämtar glosorna från ett API och erbjuder fyra övningar:

| Övning | Hur |
| --- | --- |
| Engelska → svenska | Välj rätt ord bland fyra alternativ |
| Engelska → svenska | Skriv ordet |
| Svenska → engelska | Välj rätt ord bland fyra alternativ |
| Svenska → engelska | Skriv ordet |

Riktningarna styrs av listans `fransprak` och `tillsprak`, så samma sida fungerar även för t.ex. tyska.

## Skriv-läget

- **Är jag nära?** jämför det du skrivit med rätt svar, bokstav för bokstav (Levenshtein-avstånd), utan att avslöja svaret. Den visar hur många bokstäver som skiljer och markerar vilka bokstäver som är rätt, fel, ska bort eller saknas.
- **Kolla svar** rättar. Stora och små bokstäver, extra mellanslag och skiljetecken spelar ingen roll. "to" och "att" framför verb får utelämnas ("drink" godkänns för "to drink").
- Alla svar i `svar`-listan godkänns.
- Knappar för å, ä och ö visas när man skriver på svenska.
- **Visa ledtråd** visas om glosan har en `ledtrad`.

Tangentbord: <kbd>Enter</kbd> rättar och går vidare, <kbd>1</kbd>–<kbd>4</kbd> väljer alternativ.

## Inställningar

API-adress, skola och kurs finns i [`js/config.js`](js/config.js). Skola och kurs kan också anges i adressen:

```
index.html?skola=Testskolan&kurs=Engelska%207
```

Sidan skickar `POST` med `{"skola": "...", "kurs": "..."}` och förväntar sig ett svar som:

```json
{
  "id": "lista-42",
  "titel": "Vecka 12 – Mat och dryck",
  "beskrivning": "Glosor till provet på fredag",
  "fransprak": "sv",
  "tillsprak": "en",
  "glosor": [
    {
      "id": "g1",
      "fraga": "äpple",
      "svar": ["apple"],
      "ordklass": "substantiv",
      "exempelmening": "I eat an apple every day.",
      "ledtrad": "Börjar på a",
      "bild": "https://…/apple.png",
      "bojningar": ["…"]
    }
  ]
}
```

Bara `glosor[].fraga` och `glosor[].svar` är obligatoriska. `svar` får vara en sträng eller en lista.

## Köra lokalt

```bash
python3 -m http.server 8000
```

Öppna sedan http://localhost:8000.

## Publicera med GitHub Pages

Settings → Pages → *Deploy from a branch* → `main` / `(root)`.

> **Obs:** API-adressen (inklusive `sig`-nyckeln) ligger i `js/config.js` och syns för alla som kan se sidan eller repot. Den som har adressen kan anropa flödet.
