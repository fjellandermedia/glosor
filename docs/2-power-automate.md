# 2. Power Automate-flödet (API:t till webbsidan)

Webbsidan anropar **ett** flöde med `POST` och JSON. Flödet läser SharePoint med *din* anslutning och svarar med JSON.
Eleverna loggar alltså inte in, och de kommer bara åt det flödet lämnar ut: aktiva gloslistor och glosor.

> Triggern *När en HTTP-begäran tas emot* kräver en Premium-licens för Power Automate (du har redan ett sådant flöde till den gamla sidan).

## API:t

| Anrop (body) | Svar |
| --- | --- |
| `{"action": "listor"}` | `{"listor": [{"id": 5, "titel": "Kapitel 3", "beskrivning": "", "larare": "Anna Andersson", "sprak": "es", "glosaIds": "12;15;19"}]}` |
| `{"action": "glosor", "ids": [12, 15, 19]}` | `{"glosor": [{"id": 12, "mal": "la casa", "sv": "huset", "genus": "f", "sprak": "es"}]}` |

## Bygg flödet

Skapa ett **Direktflöde (Instant cloud flow)** med triggern **När en HTTP-begäran tas emot** (*When an HTTP request is received*).
Byt namn på åtgärderna **exakt** som i fetstilen nedan (klicka på åtgärdens rubrik). Uttrycken refererar till namnen.

### Trigger: När en HTTP-begäran tas emot

- **Vem kan utlösa flödet:** *Vem som helst* (Anyone)
- **Metod:** `POST`
- **JSON-schema för begärandetext:**

```json
{
  "type": "object",
  "properties": {
    "action": { "type": "string" },
    "ids": { "type": "array", "items": { "type": "integer" } }
  }
}
```

### Växel (Switch): **Vaxel**

- **På:** uttrycket `triggerBody()?['action']`

#### Fall 1: Lika med `listor`

1. **SharePoint → Hämta objekt** (*Get items*), namn: **Hamta_listor**
   - Webbplats: din webbplats, Lista: `glosor_gloslistor`
   - Filterfråga: `Aktiv eq 1`
   - Högsta antal (Top count): `5000`
2. **Dataåtgärd → Välj** (*Select*), namn: **Valj_listor**
   - Från: uttrycket `body('Hamta_listor')?['value']`
   - Mappa (nyckel → värde, alla värden är uttryck):

     | Nyckel | Värde (uttryck) |
     | --- | --- |
     | `id` | `item()?['ID']` |
     | `titel` | `item()?['Title']` |
     | `beskrivning` | `item()?['Beskrivning']` |
     | `larare` | `item()?['LarareNamn']` |
     | `sprak` | `item()?['Sprak']` |
     | `glosaIds` | `item()?['GlosaIDs']` |

3. **Begäran → Svar** (*Response*), namn: **Svar_listor**
   - Statuskod: `200`
   - Rubriker: `Content-Type` = `application/json` och `Access-Control-Allow-Origin` = `*`
   - Brödtext: uttrycket `setProperty(json('{}'), 'listor', body('Valj_listor'))`

#### Fall 2: Lika med `glosor`

Flödet hämtar bara de glosor som efterfrågas, med ett filter på ID. Webbsidan skickar högst 30 ID per anrop
(flera anrop parallellt om listan är längre). Det fungerar lika snabbt oavsett hur många glosor som finns i SharePoint,
eftersom ID alltid är indexerat. Någon gräns på 5 000 glosor finns alltså inte.

1. **Dataåtgärd → Välj** (*Select*), namn: **Valj_filter**
   - Från: `take(coalesce(triggerBody()?['ids'], json('[]')), 100)`
   - Växla till textläge (ikonen till höger om *Mappa*) och skriv uttrycket `concat('ID eq ', string(item()))`
   - Resultat: `["ID eq 12", "ID eq 15", …]`
2. **SharePoint → Hämta objekt**, namn: **Hamta_glosor**
   - Lista: `glosor_glosor`
   - Filterfråga, som uttryck: `if(empty(body('Valj_filter')), 'ID eq 0', join(body('Valj_filter'), ' or '))`
   - Högsta antal: `100`. Ingen sidnumrering behövs.
3. **Dataåtgärd → Välj**, namn: **Valj_glosor**
   - Från: `body('Hamta_glosor')?['value']`
   - Mappa:

     | Nyckel | Värde (uttryck) |
     | --- | --- |
     | `id` | `item()?['ID']` |
     | `mal` | `item()?['Title']` |
     | `sv` | `item()?['Svenska']` |
     | `genus` | `item()?['Genus']` |
     | `sprak` | `item()?['Sprak']` |

4. **Svar**, namn: **Svar_glosor**
   - Statuskod `200`, samma rubriker som ovan
   - Brödtext: `setProperty(json('{}'), 'glosor', body('Valj_glosor'))`

#### Standard (Default)

**Svar** med statuskod `400` och brödtext `{"fel": "Okänd action"}`.

### Spara och koppla till webbsidan

1. Spara flödet. Kopiera **HTTP-URL:en** från triggern.
2. Klistra in den i [`js/config.js`](../js/config.js):

   ```js
   export default {
     apiUrl: "https://…/triggers/manual/paths/invoke?api-version=1&sp=…&sv=1.0&sig=…",
   };
   ```

3. Committa och pusha. Sidan lämnar demoläget när `apiUrl` är ifylld.

## Testa

```bash
curl -s -X POST -H "Content-Type: application/json" -d '{"action":"listor"}' "DIN_FLÖDES_URL"
```

```bash
curl -s -X POST -H "Content-Type: application/json" -d '{"action":"glosor","ids":[1,2,3]}' "DIN_FLÖDES_URL"
```

## Bra att veta

- **Säkerhet:** URL:en innehåller en nyckel (`sig=`) och syns i webbsidans kod. Den som har den kan läsa aktiva gloslistor och glosor, men inget annat. `LarareEpost` och `SkapadAvEpost` skickas aldrig ut.
- **Fart och storlek:** *glosor* gör ett litet anrop till SharePoint per 30 glosor, så det skalar till hela kommunen.
  *listor* hämtar alla aktiva gloslistor (högst 5 000). Dölj gamla listor i appen, så räcker det länge.
- **Den gamla sidan** använde ett annat flöde med `{"skola": …, "kurs": …}`. Det kan stängas av när det här fungerar.
