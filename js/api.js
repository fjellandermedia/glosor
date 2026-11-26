// Hämtar gloslistor och glosor från Power Automate-flödet (eller demodata).
import config from "./config.js";
import * as demo from "./demo.js";

const params = new URLSearchParams(location.search);
export const demolage = !config.apiUrl || params.has("demo");

async function anropa(kropp) {
  let svar;
  try {
    svar = await fetch(config.apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(kropp),
    });
  } catch {
    throw new Error("Kunde inte nå servern. Kontrollera internetuppkopplingen och försök igen.");
  }
  if (!svar.ok) throw new Error(`Servern svarade med felkod ${svar.status}.`);
  try {
    return await svar.json();
  } catch {
    throw new Error("Servern skickade ett svar som inte gick att läsa.");
  }
}

// "12;15;19" eller [12, 15, 19] -> ["12", "15", "19"]
export function tolkaIds(v) {
  const delar = Array.isArray(v) ? v : String(v ?? "").split(/[;,\s]+/);
  return [...new Set(delar.map((x) => String(x).trim()).filter(Boolean))];
}

function tolkaLista(l) {
  return {
    id: String(l.id ?? l.ID),
    titel: l.titel ?? l.Title ?? "Namnlös lista",
    beskrivning: l.beskrivning ?? "",
    larare: l.larare ?? "Okänd lärare",
    sprak: (l.sprak ?? "").trim(),
    glosaIds: tolkaIds(l.glosaIds ?? l.GlosaIDs),
  };
}

function tolkaGlosa(g) {
  return {
    id: String(g.id ?? g.ID),
    mal: String(g.mal ?? g.Title ?? "").trim(),
    sv: String(g.sv ?? g.Svenska ?? "").trim(),
    genus: tolkaGenus(g.genus ?? g.Genus),
    sprak: String(g.sprak ?? g.Sprak ?? "").trim(),
  };
}

export function tolkaGenus(v) {
  const s = String(v ?? "").trim().toLowerCase();
  if (s.startsWith("m")) return "m";
  if (s.startsWith("f")) return "f";
  if (s.startsWith("n")) return "n";
  return "";
}

export async function hamtaListor() {
  const data = demolage ? { listor: demo.listor } : await anropa({ action: "listor" });
  return (data.listor ?? []).map(tolkaLista);
}

// Flödet hämtar glosorna med ett filter på ID (ID eq 1 or ID eq 2 …). Ett litet filter per anrop
// håller SharePoint-frågan enkel och snabb oavsett hur många glosor som finns totalt.
export const GLOSOR_PER_ANROP = 30;

export async function hamtaGlosor(ids) {
  if (!ids.length) return [];
  if (demolage) {
    return demo.glosor
      .filter((g) => ids.includes(String(g.id)))
      .map(tolkaGlosa)
      .filter((g) => g.mal && g.sv);
  }
  const nummer = ids.map(Number).filter((x) => Number.isInteger(x) && x > 0);
  const omgangar = [];
  for (let i = 0; i < nummer.length; i += GLOSOR_PER_ANROP) omgangar.push(nummer.slice(i, i + GLOSOR_PER_ANROP));
  const svar = await Promise.all(omgangar.map((del) => anropa({ action: "glosor", ids: del })));
  const sedda = new Set();
  return svar
    .flatMap((data) => data.glosor ?? [])
    .map(tolkaGlosa)
    .filter((g) => g.mal && g.sv && !sedda.has(g.id) && sedda.add(g.id));
}
