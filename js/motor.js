// Ren logik utan DOM: rättning, ledtrådar, repetitionsalgoritm och spaced repetition.
// Filen används både av webbsidan och av testerna i tests/.

// ---------- Slump ----------

export function blanda(lista, slump = Math.random) {
  const a = lista.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(slump() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// ---------- Rättning ----------

const SKILJETECKEN = /[.,!?;:¿¡"«»“”„]/g;

function grundform(s) {
  return String(s ?? "")
    .normalize("NFC")
    .replace(/[’‘`´]/g, "'")
    .replace(SKILJETECKEN, "")
    .replace(/\s+/g, " ")
    .trim();
}

function utanAccenter(s) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ß/g, "ss").normalize("NFC");
}

// Alla svar som godkänns för en glosa.
// "la casa / el hogar" ger två alternativ. "(se) llamar" godkänns både med och utan "se".
export function alternativ(mal) {
  const ut = new Set();
  for (const del of String(mal ?? "").split("/")) {
    const a = grundform(del);
    if (!a) continue;
    ut.add(grundform(a.replace(/[()]/g, "")));
    ut.add(grundform(a.replace(/\([^)]*\)/g, " ")));
  }
  return [...ut].filter(Boolean);
}

// Texten som visas och som ledtrådar tas från: första alternativet, med parenteser.
export function visningsform(mal) {
  const forsta = String(mal ?? "").split("/")[0];
  return forsta.replace(/\s+/g, " ").trim();
}

// Liten versal i början godkänns om mobilen själv gjort stor bokstav ("La casa" för "la casa").
// I övrigt räknas stora och små bokstäver, eftersom läraren bara skriver versal när den ska vara där.
function lika(svar, facit) {
  if (svar === facit) return true;
  if (!svar || !facit) return false;
  const f0 = facit[0];
  if (f0 === f0.toLowerCase() && f0 !== f0.toUpperCase()) {
    return svar[0].toLowerCase() === f0 && svar.slice(1) === facit.slice(1);
  }
  return false;
}

// Returnerar { ratt, nastan } där nastan är true om bara accenter eller versaler skiljer.
export function ratta(svar, mal) {
  const s = grundform(svar);
  const alla = alternativ(mal);
  if (!s) return { ratt: false, nastan: false };
  if (alla.some((a) => lika(s, a))) return { ratt: true, nastan: false };
  const enkel = (x) => utanAccenter(x).toLowerCase();
  return { ratt: false, nastan: alla.some((a) => enkel(a) === enkel(s)) };
}

// ---------- Ledtrådar ----------

const ARBOKSTAV = (t) => t.trim() !== "";

// Högst halva ordet (räknat i bokstäver, inte mellanslag) får visas.
export function maxLedtradar(mal) {
  const tecken = [...visningsform(mal)].filter(ARBOKSTAV).length;
  return Math.floor(tecken / 2);
}

// De första n bokstäverna. Mellanslag före nästa bokstav tas med automatiskt.
export function ledtrad(mal, n) {
  const tecken = [...visningsform(mal)];
  let ut = "";
  let bokstaver = 0;
  for (const t of tecken) {
    if (ARBOKSTAV(t)) {
      if (bokstaver >= n) break;
      bokstaver++;
    }
    ut += t;
  }
  return n > 0 ? ut : "";
}

// ---------- Introduktionsdelen ----------

export const GRUPPSTORLEK = 5;

// Ett ord räknas som välkänt om det skrevs rätt på första försöket utan fel och ledtråd.
// Anropas när ordet skrivits klart första gången i introduktionen.
export function valkant(logg) {
  return !!logg && logg.forsok === 1 && logg.fel === 0 && logg.ledtradar === 0;
}

// Platta efter introduktionen: gron, gul eller rod.
export function platta(logg) {
  const problem = (logg?.fel ?? 0) + (logg?.ledtradar ?? 0);
  if (problem === 0) return "gron";
  if (problem <= 2) return "gul";
  return "rod";
}

// Delar nya ord i grupper om fem. Sista gruppen fylls senare med ord eleven gjort fel på
// (se fyllGrupp), därför returneras den som den är.
export function delaIGrupper(ord, storlek = GRUPPSTORLEK) {
  const grupper = [];
  for (let i = 0; i < ord.length; i += storlek) grupper.push(ord.slice(i, i + storlek));
  return grupper;
}

// Fyller en för liten grupp med redan övade ord, svåraste först.
// tidigare: id:n som redan övats, loggar: { id: logg }.
export function fyllGrupp(grupp, tidigare, loggar, storlek = GRUPPSTORLEK, slump = Math.random) {
  if (grupp.length >= storlek) return { grupp, fyllnad: [] };
  const problem = (id) => (loggar[id]?.fel ?? 0) + (loggar[id]?.ledtradar ?? 0);
  const kandidater = blanda(
    tidigare.filter((id) => !grupp.includes(id) && problem(id) > 0),
    slump,
  ).sort((a, b) => problem(b) - problem(a));
  const fyllnad = kandidater.slice(0, storlek - grupp.length);
  return { grupp: grupp.concat(fyllnad), fyllnad };
}

// ---------- Slutlig repetitionsdel ----------

export const MIN_NIVA = -1;
export const KLAR_NIVA = 2;

// Lägger ut ord1 jämnt bland ord0, t.ex. 6 nivå 0-ord och 2 nivå 1-ord:
// 0 0 0 1 0 0 0 1
export function fordelaJamnt(ord0, ord1) {
  if (!ord1.length) return ord0.slice();
  if (!ord0.length) return ord1.slice();
  const ut = [];
  const total = ord0.length + ord1.length;
  let i0 = 0;
  let i1 = 0;
  for (let pos = 0; pos < total; pos++) {
    // Var ska nästa nivå 1-ord ligga för att de ska bli jämnt utspridda?
    const malPos = Math.floor(((i1 + 0.5) * total) / ord1.length);
    if (i1 < ord1.length && (pos >= malPos || i0 >= ord0.length)) ut.push(ord1[i1++]);
    else ut.push(ord0[i0++]);
  }
  return ut;
}

export class Repetition {
  // startnivaer: { id: 0 | 1 }
  constructor(startnivaer, slump = Math.random) {
    this.niva = { ...startnivaer };
    this.slump = slump;
    this.felko = [];
    this.antalFragor = 0;
    this.senaste = null;
    this.fragorPerOrd = {};
    this.klarEfter = {}; // id -> antal frågor om ordet innan nivå 2
    const ej = Object.keys(this.niva).filter((id) => this.niva[id] < KLAR_NIVA);
    for (const id of ej) if (this.niva[id] <= MIN_NIVA) this.felko.push(id);
    const noll = blanda(ej.filter((id) => this.niva[id] === 0), slump);
    const ett = blanda(ej.filter((id) => this.niva[id] === 1), slump);
    this.ordning = fordelaJamnt(noll, ett).concat(ej.filter((id) => this.niva[id] <= MIN_NIVA));
    this.pos = 0;
  }

  get antal() {
    return Object.keys(this.niva).length;
  }

  get antalKlara() {
    return Object.values(this.niva).filter((n) => n >= KLAR_NIVA).length;
  }

  get klar() {
    return this.antalKlara === this.antal;
  }

  _iHuvudlistan(id) {
    return this.niva[id] < KLAR_NIVA && !this.felko.includes(id);
  }

  _franHuvudlistan(undvik) {
    const n = this.ordning.length;
    let reserv = null;
    for (let steg = 0; steg < n; steg++) {
      const i = (this.pos + steg) % n;
      const id = this.ordning[i];
      if (!this._iHuvudlistan(id)) continue;
      if (id === undvik) {
        if (reserv === null) reserv = i;
        continue;
      }
      this.pos = (i + 1) % n;
      return id;
    }
    if (reserv !== null) {
      this.pos = (reserv + 1) % n;
      return this.ordning[reserv];
    }
    return null;
  }

  _franFelkon(undvik) {
    const i = this.felko.findIndex((id) => id !== undvik);
    if (i === -1) return null;
    return this.felko.splice(i, 1)[0];
  }

  // Nästa ord att fråga om, eller null när alla nått nivå 2.
  // Var tredje fråga tas från felkön om den innehåller ord.
  nasta() {
    if (this.klar) return null;
    const felkoTur = (this.antalFragor + 1) % 3 === 0;
    let id = null;
    let franFelko = false;
    if (felkoTur && this.felko.length) {
      id = this._franFelkon(this.senaste);
      franFelko = id !== null;
    }
    if (id === null) id = this._franHuvudlistan(this.senaste);
    if (id === null && this.felko.length) {
      // Bara felkö-ord kvar.
      id = this._franFelkon(this.senaste) ?? this.felko.shift();
      franFelko = true;
    }
    this.aktuell = { id, franFelko };
    return id;
  }

  // Registrerar svaret på frågan som nasta() senast gav.
  // ratt = rätt på första försöket utan ledtråd.
  svara(id, ratt) {
    this.antalFragor++;
    this.senaste = id;
    this.fragorPerOrd[id] = (this.fragorPerOrd[id] ?? 0) + 1;
    const franFelko = this.aktuell?.id === id && this.aktuell.franFelko;
    const fore = this.niva[id];
    if (ratt) {
      this.niva[id] = Math.min(KLAR_NIVA, fore + 1);
      if (this.niva[id] >= KLAR_NIVA && this.klarEfter[id] === undefined) {
        this.klarEfter[id] = this.fragorPerOrd[id];
      }
      // Ett felkö-ord som klaras får nivå 0 och går tillbaka till huvudlistan.
    } else {
      this.niva[id] = Math.max(MIN_NIVA, fore - 1);
      if (this.niva[id] === MIN_NIVA && !this.felko.includes(id)) this.felko.push(id);
    }
    if (franFelko && !ratt && !this.felko.includes(id)) this.felko.push(id);
    this.aktuell = null;
    return this.niva[id];
  }
}

// ---------- Spaced repetition mellan dagar ----------

export const INTERVALL = [1, 3, 7, 14, 30, 60];

export function datumText(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const dag = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${dag}`;
}

export function idag(nu = new Date()) {
  return datumText(nu);
}

export function plusDagar(datum, dagar) {
  const [y, m, d] = datum.split("-").map(Number);
  return datumText(new Date(y, m - 1, d + dagar));
}

export function nyStatistik() {
  return {
    pass: 0,
    ratt: 0,
    fel: 0,
    ledtradar: 0,
    senast: null,
    nasta: null,
    steg: 0,
    tillNiva2: [], // antal frågor i repetitionsdelen som krävdes för att nå nivå 2, per pass
  };
}

// Är ordet dags att repetera?
export function arDags(stat, dag = idag()) {
  return !stat || !stat.nasta || stat.nasta <= dag;
}

export function arNytt(stat) {
  return !stat || !stat.pass;
}

// Uppdaterar ett ords långtidsstatistik efter ett genomfört pass.
// pass: { ratt, fel, ledtradar, tillNiva2 }
export function schemalagg(stat, pass, dag = idag()) {
  const s = { ...nyStatistik(), ...stat };
  const forsta = !s.pass;
  const problem = pass.fel + pass.ledtradar;
  s.pass += 1;
  s.ratt += pass.ratt;
  s.fel += pass.fel;
  s.ledtradar += pass.ledtradar;
  if (pass.tillNiva2 != null) s.tillNiva2 = [...s.tillNiva2, pass.tillNiva2].slice(-10);
  if (forsta) s.steg = 0;
  else if (problem === 0) s.steg = Math.min(s.steg + 1, INTERVALL.length - 1);
  else if (problem <= 2) s.steg = Math.max(s.steg - 1, 0);
  else s.steg = 0;
  s.senast = dag;
  s.nasta = plusDagar(dag, INTERVALL[s.steg]);
  return s;
}

// Startnivå i repetitionsdelen.
// Ord som introducerats i passet: välkänt -> 1, annars 0. Ord som repeteras från tidigare pass: 0.
export function startniva(introLogg) {
  return introLogg && introLogg.valkant ? 1 : 0;
}
