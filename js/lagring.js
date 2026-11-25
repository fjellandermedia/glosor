// All elevdata sparas lokalt i webbläsaren (localStorage).
const NYCKEL = "glosor.v1";

let data = las();

function las() {
  try {
    const d = JSON.parse(localStorage.getItem(NYCKEL) || "{}");
    return { ord: d.ord ?? {}, listor: d.listor ?? {} };
  } catch {
    return { ord: {}, listor: {} };
  }
}

function spara() {
  try {
    localStorage.setItem(NYCKEL, JSON.stringify(data));
  } catch {
    // Privat läge eller full lagring: träningen fungerar ändå, men sparas inte.
  }
}

// ---------- Listor ----------

export const STATUS = { aktiv: "Aktiv", pausad: "Pausad", arkiverad: "Arkiverad" };

export function minaListor() {
  return Object.values(data.listor).sort((a, b) => (b.senastOvad ?? b.tillagd).localeCompare(a.senastOvad ?? a.tillagd));
}

export function lista(id) {
  return data.listor[id];
}

// Lägger till eller uppdaterar en lista. Status behålls om listan redan finns,
// men en borttagen eller arkiverad lista som öppnas via länk blir aktiv igen.
export function sparaLista(info, { aktivera = false } = {}) {
  const fore = data.listor[info.id];
  data.listor[info.id] = {
    ...fore,
    id: info.id,
    titel: info.titel,
    beskrivning: info.beskrivning,
    larare: info.larare,
    sprak: info.sprak,
    glosaIds: info.glosaIds,
    status: aktivera || !fore ? "aktiv" : fore.status,
    tillagd: fore?.tillagd ?? new Date().toISOString(),
  };
  spara();
}

export function sattStatus(id, status) {
  if (!data.listor[id]) return;
  data.listor[id].status = status;
  spara();
}

export function taBortLista(id) {
  delete data.listor[id];
  spara();
}

export function markeraOvad(ids) {
  const nu = new Date().toISOString();
  for (const id of ids) if (data.listor[id]) data.listor[id].senastOvad = nu;
  spara();
}

// ---------- Ord ----------

export function ordStat(id) {
  return data.ord[id];
}

export function sparaOrdStat(id, stat) {
  data.ord[id] = stat;
  spara();
}

export function sparaAllaOrd(stats) {
  Object.assign(data.ord, stats);
  spara();
}

export function rensaAllt() {
  data = { ord: {}, listor: {} };
  spara();
}
