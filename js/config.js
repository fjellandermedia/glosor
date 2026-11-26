// Inställningar för glosträningen.
//
// apiUrl: adressen till Power Automate-flödet ("HTTP URL" i triggern "När en HTTP-begäran tas emot").
// Lämna tom för att köra sidan i demoläge med inbyggda exempelglosor.
// Demoläget kan också tvingas fram med ?demo=1 i adressen.
//
// Obs! Adressen innehåller en nyckel (sig=...) och syns för alla som kan se sidan.
// Flödet lämnar bara ut gloslistor och glosor, aldrig något annat från SharePoint.
export default {
  apiUrl:
    "https://default947897c4c0034f3692b855ac5ab353.54.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/14/workflows/f77c9dea8d4a43208bc088a97e22d8e0/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=wrGI8VE0HGZx0lgZx4I1q5X7b5E5-t3rJinvbYyd8eY",
};
