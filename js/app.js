import * as api from "./api.js";
import * as lager from "./lagring.js";
import * as M from "./motor.js";

// ---------- Språk ----------

const SPRAK = {
  en: { namn: "engelska", tecken: [] },
  es: { namn: "spanska", tecken: ["á", "é", "í", "ó", "ú", "ü", "ñ", "¿", "¡"] },
  fr: { namn: "franska", tecken: ["à", "â", "æ", "ç", "é", "è", "ê", "ë", "î", "ï", "ô", "œ", "ù", "û", "ü"] },
  de: { namn: "tyska", tecken: ["ä", "ö", "ü", "ß"] },
  it: { namn: "italienska", tecken: ["à", "è", "é", "ì", "ò", "ù"] },
  pt: { namn: "portugisiska", tecken: ["á", "â", "ã", "à", "ç", "é", "ê", "í", "ó", "ô", "õ", "ú"] },
  la: { namn: "latin", tecken: [] },
  fi: { namn: "finska", tecken: ["ä", "ö"] },
  sv: { namn: "svenska", tecken: ["å", "ä", "ö"] },
};

function sprakKod(v) {
  const s = String(v ?? "").trim().toLowerCase();
  if (SPRAK[s]) return s;
  return Object.keys(SPRAK).find((k) => SPRAK[k].namn === s || (s.length > 2 && SPRAK[k].namn.startsWith(s))) ?? s;
}
const sprakNamn = (v) => SPRAK[sprakKod(v)]?.namn ?? (v ? String(v) : "");

const GENUS = { m: "maskulinum", f: "femininum", n: "neutrum" };
const BEROM = ["Rätt!", "Snyggt!", "Bra jobbat!", "Helt rätt!", "Perfekt!", "Toppen!", "Kanon!"];
const slumpa = (lista) => lista[Math.floor(Math.random() * lista.length)];

// ---------- DOM-hjälp ----------

const app = document.getElementById("app");

function h(tag, attrs, ...barn) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, "");
    else el.setAttribute(k, v);
  }
  for (const b of barn.flat(Infinity)) {
    if (b == null || b === false) continue;
    el.append(b instanceof Node ? b : document.createTextNode(String(b)));
  }
  return el;
}

function visa(...noder) {
  app.replaceChildren(...noder.flat().filter(Boolean));
  window.scrollTo(0, 0);
  const fokus = app.querySelector("[data-fokus]");
  if (fokus) fokus.focus();
}

// Ordet på målspråket, i genusfärg.
function malOrd(g, extraKlass = "") {
  return h("span", { class: `mal genus-${g.genus || "x"} ${extraKlass}`.trim(), lang: sprakKod(g.sprak) || null }, g.mal);
}

function datumFint(d) {
  const [y, m, dag] = d.split("-").map(Number);
  return new Date(y, m - 1, dag).toLocaleDateString("sv-SE", { day: "numeric", month: "long" });
}

function laddar(text = "Hämtar…") {
  visa(h("div", { class: "laddar" }, h("div", { class: "snurra", "aria-hidden": "true" }), text));
}

function felruta(fel, tillbaka) {
  visa(
    sidhuvud(),
    h(
      "div",
      { class: "kort fel-kort" },
      h("h2", {}, "Något gick fel"),
      h("p", {}, fel.message || String(fel)),
      h("button", { class: "knapp", onclick: tillbaka, "data-fokus": true }, "Tillbaka"),
    ),
  );
}

function sidhuvud(...hoger) {
  return h(
    "header",
    { class: "sidhuvud" },
    h("a", { class: "logga", href: "./", onclick: (e) => (e.preventDefault(), lamnaPass(visaStart)) }, "Glosträning"),
    api.demolage ? h("span", { class: "demo", title: "Ingen API-adress är inställd. Sidan visar exempelglosor." }, "Demoläge") : null,
    h("span", { class: "fyll" }),
    ...hoger,
  );
}

// ---------- Status för en lista (lokalt) ----------

function listStatus(glosaIds) {
  const dag = M.idag();
  let nya = 0;
  let dags = 0;
  let nasta = null;
  for (const id of glosaIds) {
    const s = lager.ordStat(id);
    if (M.arNytt(s)) nya++;
    else if (M.arDags(s, dag)) dags++;
    else if (!nasta || s.nasta < nasta) nasta = s.nasta;
  }
  return { nya, dags, nasta };
}

function statusText(st) {
  const delar = [];
  if (st.nya) delar.push(`${st.nya} nya ord`);
  if (st.dags) delar.push(`${st.dags} ord att repetera`);
  if (delar.length) return h("span", { class: "dags" }, delar.join(" · "));
  if (st.nasta) return h("span", { class: "klar-idag" }, `✓ Klar för idag – nästa repetition ${datumFint(st.nasta)}`);
  return h("span", {}, "Inga ord i listan");
}

// ---------- Startsidan: mina listor ----------

function visaStart() {
  history.replaceState(null, "", location.pathname + (api.demolage && location.search.includes("demo") ? "?demo=1" : ""));
  const listor = lager.minaListor();
  const valda = new Set();
  const ovaKnapp = h("button", { class: "knapp", disabled: true, onclick: () => visaForbered([...valda]) }, "Öva valda");
  const uppdatera = () => {
    ovaKnapp.disabled = valda.size === 0;
    ovaKnapp.textContent = valda.size > 1 ? `Öva valda tillsammans (${valda.size})` : "Öva vald lista";
  };

  const kort = (l) => {
    const st = listStatus(l.glosaIds);
    const aktiv = l.status === "aktiv";
    const meny = h(
      "details",
      { class: "meny" },
      h("summary", { "aria-label": "Fler val" }, "⋯"),
      h(
        "div",
        { class: "meny-val" },
        l.status !== "aktiv" && h("button", { onclick: () => (lager.sattStatus(l.id, "aktiv"), visaStart()) }, "Aktivera igen"),
        l.status === "aktiv" && h("button", { onclick: () => (lager.sattStatus(l.id, "pausad"), visaStart()) }, "Pausa listan"),
        l.status !== "arkiverad" &&
          h("button", { onclick: () => (lager.sattStatus(l.id, "arkiverad"), visaStart()) }, "Markera som avslutad (arkivera)"),
        h(
          "button",
          {
            class: "farlig",
            onclick: () => {
              if (confirm(`Ta bort "${l.titel}" från dina listor? Statistiken för orden finns kvar om du lägger till listan igen.`)) {
                lager.taBortLista(l.id);
                visaStart();
              }
            },
          },
          "Ta bort från mina listor",
        ),
      ),
    );
    return h(
      "div",
      { class: `kort lista-kort ${aktiv ? "" : "inaktiv"}` },
      aktiv &&
        h("input", {
          type: "checkbox",
          class: "valj",
          "aria-label": `Välj ${l.titel}`,
          onchange: (e) => (e.target.checked ? valda.add(l.id) : valda.delete(l.id), uppdatera()),
        }),
      h(
        "div",
        { class: "lista-info" },
        h("h3", {}, l.titel),
        h("div", { class: "meta" }, [l.larare, sprakNamn(l.sprak), `${l.glosaIds.length} ord`].filter(Boolean).join(" · ")),
        h("div", { class: "status" }, aktiv ? statusText(st) : lager.STATUS[l.status]),
      ),
      h("div", { class: "lista-knappar" }, aktiv && h("button", { class: "knapp liten", onclick: () => visaForbered([l.id]) }, "Öva"), meny),
    );
  };

  const aktiva = listor.filter((l) => l.status === "aktiv");
  const pausade = listor.filter((l) => l.status === "pausad");
  const arkiv = listor.filter((l) => l.status === "arkiverad");

  visa(
    sidhuvud(),
    h("h1", {}, "Mina gloslistor"),
    listor.length === 0 &&
      h(
        "div",
        { class: "kort tom" },
        h("p", {}, "Du har inga gloslistor än."),
        h("p", {}, "Öppna länken som din lärare har delat, eller leta upp listan här:"),
      ),
    aktiva.length > 0 && h("p", { class: "tips" }, "Bocka för flera listor för att träna alla glosor blandat."),
    aktiva.map(kort),
    aktiva.length > 0 && h("div", { class: "knapprad" }, ovaKnapp),
    h(
      "div",
      { class: "knapprad" },
      h("button", { class: "knapp sekundar", onclick: visaHitta, "data-fokus": listor.length === 0 || null }, "Hitta gloslistor"),
    ),
    pausade.length > 0 && h("details", { class: "grupp" }, h("summary", {}, `Pausade listor (${pausade.length})`), pausade.map(kort)),
    arkiv.length > 0 && h("details", { class: "grupp" }, h("summary", {}, `Avslutade listor (${arkiv.length})`), arkiv.map(kort)),
  );
}

// ---------- Hitta listor ----------

let listCache = null;

async function hamtaAllaListor() {
  if (!listCache) listCache = await api.hamtaListor();
  return listCache;
}

async function visaHitta() {
  laddar("Hämtar gloslistor…");
  let listor;
  try {
    listor = await hamtaAllaListor();
  } catch (e) {
    return felruta(e, visaStart);
  }
  const larare = new Map();
  for (const l of listor) larare.set(l.larare, (larare.get(l.larare) ?? 0) + 1);
  const namn = [...larare.keys()].sort((a, b) => a.localeCompare(b, "sv"));
  visa(
    sidhuvud(h("button", { class: "knapp sekundar liten", onclick: visaStart }, "← Mina listor")),
    h("h1", {}, "Välj lärare"),
    namn.length === 0 && h("p", {}, "Det finns inga gloslistor att visa."),
    h(
      "div",
      { class: "rutnat" },
      namn.map((n) =>
        h(
          "button",
          { class: "kort larare-knapp", onclick: () => visaLarare(n, listor) },
          h("strong", {}, n),
          h("span", { class: "meta" }, `${larare.get(n)} ${larare.get(n) === 1 ? "lista" : "listor"}`),
        ),
      ),
    ),
  );
}

function visaLarare(namn, allaListor) {
  const listor = allaListor.filter((l) => l.larare === namn).sort((a, b) => a.titel.localeCompare(b.titel, "sv", { numeric: true }));
  const valda = new Set();
  const laggTill = h("button", { class: "knapp sekundar", disabled: true }, "Lägg till i mina listor");
  const ova = h("button", { class: "knapp", disabled: true }, "Öva valda nu");
  const uppdatera = () => {
    laggTill.disabled = ova.disabled = valda.size === 0;
    ova.textContent = valda.size > 1 ? `Öva valda tillsammans (${valda.size})` : "Öva vald lista nu";
  };
  const spara = () => {
    for (const l of listor) if (valda.has(l.id)) lager.sparaLista(l, { aktivera: true });
  };
  laggTill.onclick = () => (spara(), visaStart());
  ova.onclick = () => (spara(), visaForbered([...valda]));

  visa(
    sidhuvud(h("button", { class: "knapp sekundar liten", onclick: visaHitta }, "← Lärare")),
    h("h1", {}, namn),
    h("p", { class: "tips" }, "Bocka för en eller flera listor."),
    listor.map((l) =>
      h(
        "label",
        { class: "kort lista-kort valbar" },
        h("input", {
          type: "checkbox",
          class: "valj",
          onchange: (e) => (e.target.checked ? valda.add(l.id) : valda.delete(l.id), uppdatera()),
        }),
        h(
          "div",
          { class: "lista-info" },
          h("h3", {}, l.titel),
          l.beskrivning && h("div", { class: "beskrivning" }, l.beskrivning),
          h("div", { class: "meta" }, [sprakNamn(l.sprak), `${l.glosaIds.length} ord`].filter(Boolean).join(" · ")),
          lager.lista(l.id) && h("div", { class: "status" }, "Finns redan i dina listor"),
        ),
      ),
    ),
    h("div", { class: "knapprad" }, laggTill, ova),
  );
}

// ---------- Direktlänk ----------

async function oppnaDirektlank(ids) {
  laddar("Hämtar gloslistan…");
  let listor;
  try {
    listor = await hamtaAllaListor();
  } catch (e) {
    return felruta(e, visaStart);
  }
  const hittade = listor.filter((l) => ids.includes(l.id));
  if (!hittade.length) {
    return felruta(new Error("Gloslistan finns inte, eller så har läraren gjort den inaktiv."), visaStart);
  }
  for (const l of hittade) lager.sparaLista(l, { aktivera: true });
  visaForbered(hittade.map((l) => l.id));
}

// ---------- Före passet ----------

async function visaForbered(listIds) {
  laddar("Hämtar glosor…");
  // Uppdatera listornas innehåll om läraren ändrat dem.
  try {
    const fardiga = await hamtaAllaListor();
    for (const l of fardiga) if (listIds.includes(l.id) && lager.lista(l.id)) lager.sparaLista(l);
  } catch {
    // Använd sparad version av listan.
  }
  const listor = listIds.map(lager.lista).filter(Boolean);
  const ids = [...new Set(listor.flatMap((l) => l.glosaIds))];
  let glosor;
  try {
    glosor = await api.hamtaGlosor(ids);
  } catch (e) {
    return felruta(e, visaStart);
  }
  const reservSprak = listor[0]?.sprak ?? "";
  for (const g of glosor) if (!g.sprak) g.sprak = listor.find((l) => l.glosaIds.includes(g.id))?.sprak ?? reservSprak;

  const dag = M.idag();
  const nya = glosor.filter((g) => M.arNytt(lager.ordStat(g.id))).map((g) => g.id);
  const dags = glosor.filter((g) => !nya.includes(g.id) && M.arDags(lager.ordStat(g.id), dag)).map((g) => g.id);
  const vila = glosor.filter((g) => !nya.includes(g.id) && !dags.includes(g.id)).map((g) => g.id);
  const nasta = vila.map((id) => lager.ordStat(id).nasta).sort()[0];
  const titel = listor.map((l) => l.titel).join(" + ");

  const start = (repetera) => startaPass({ glosor, nya, repetera, listIds });

  visa(
    sidhuvud(h("button", { class: "knapp sekundar liten", onclick: visaStart }, "← Mina listor")),
    h("h1", {}, titel),
    h(
      "div",
      { class: "kort" },
      glosor.length === 0
        ? h("p", {}, "Listan innehåller inga glosor ännu.")
        : h(
            "ul",
            { class: "sammanfattning" },
            h("li", {}, h("strong", {}, nya.length), " nya ord"),
            h("li", {}, h("strong", {}, dags.length), " ord att repetera idag"),
            vila.length > 0 && h("li", {}, h("strong", {}, vila.length), ` ord som vilar (nästa repetition ${datumFint(nasta)})`),
          ),
      nya.length > 0 &&
        h(
          "ol",
          { class: "flode" },
          h("li", {}, h("strong", {}, "Introduktion: "), "nya ord i grupper om fem. Först matchar du, sedan skriver du."),
          h("li", {}, h("strong", {}, "Matchning: "), "en frivillig matchningsövning med alla ord."),
          h("li", {}, h("strong", {}, "Repetition: "), "du skriver alla ord tills du kan dem. Svåra ord kommer tillbaka oftare."),
        ),
      nya.length === 0 && dags.length > 0 && h("p", {}, "Dags att repetera! Skriv orden tills du kan dem."),
      nya.length === 0 && dags.length === 0 && glosor.length > 0 && h("p", {}, `Du har inget att öva idag. Nästa repetition: ${datumFint(nasta)}.`),
    ),
    h(
      "div",
      { class: "knapprad" },
      nya.length + dags.length > 0 && h("button", { class: "knapp", onclick: () => start(dags), "data-fokus": true }, "Starta"),
      vila.length > 0 &&
        h(
          "button",
          { class: `knapp ${nya.length + dags.length > 0 ? "sekundar" : ""}`, onclick: () => start(dags.concat(vila)) },
          nya.length + dags.length > 0 ? "Öva alla ord" : "Öva ändå",
        ),
    ),
  );
}

// ---------- Träningspasset ----------

let aktivtPass = null;

window.addEventListener("beforeunload", (e) => {
  if (aktivtPass) {
    e.preventDefault();
    e.returnValue = "";
  }
});

function lamnaPass(dit) {
  if (aktivtPass && !confirm("Vill du avsluta passet? Det du har övat nu sparas inte.")) return;
  aktivtPass = null;
  dit();
}

function startaPass({ glosor, nya, repetera, listIds }) {
  const P = {
    ord: new Map(glosor.map((g) => [g.id, g])),
    nya: M.blanda(nya),
    repetera,
    listIds,
    loggar: {},
    repLogg: {},
    harGenus: glosor.some((g) => g.genus),
    faser: [],
  };
  P.grupper = M.delaIGrupper(P.nya);
  if (P.nya.length) P.faser.push("intro", "matchning");
  P.faser.push("repetition");
  aktivtPass = P;
  if (P.grupper.length) introGrupp(P, 0);
  else repetition(P);
}

function logg(P, id) {
  return (P.loggar[id] ??= { forsok: 0, fel: 0, ledtradar: 0, repriser: 0, valkant: undefined });
}

const FASNAMN = { intro: "Introduktion", matchning: "Matchning", repetition: "Repetition" };

// Översta delen under passet: vilka delar som finns och var eleven är.
function passHuvud(P, fas, ...under) {
  const nu = P.faser.indexOf(fas);
  return [
    sidhuvud(h("button", { class: "knapp sekundar liten", onclick: () => lamnaPass(visaStart) }, "Avsluta")),
    P.faser.length > 1 &&
      h(
        "ol",
        { class: "stegvisare", "aria-label": "Passets delar" },
        P.faser.map((f, i) =>
          h("li", { class: i < nu ? "gjord" : i === nu ? "nu" : "", "aria-current": i === nu ? "step" : null }, i < nu ? "✓ " : "", FASNAMN[f]),
        ),
      ),
    ...under,
  ];
}

function introHuvud(P, gi, delsteg) {
  const n = P.grupper.length;
  const DELAR = ["Matcha", "Skriv", "Repetera"];
  return passHuvud(
    P,
    "intro",
    h(
      "div",
      { class: "fasinfo" },
      h("div", { class: "fastext" }, `Introduktion: fas ${gi + 1} av ${n}`),
      h(
        "div",
        { class: "segment", role: "progressbar", "aria-valuemin": 1, "aria-valuemax": n, "aria-valuenow": gi + 1 },
        Array.from({ length: n }, (_, i) => h("span", { class: i < gi ? "gjord" : i === gi ? "nu" : "" })),
      ),
      h(
        "div",
        { class: "delsteg" },
        DELAR.map((d, i) => h("span", { class: i < delsteg ? "gjord" : i === delsteg ? "nu" : "" }, d)),
      ),
    ),
  );
}

// ---------- Introduktion ----------

function introGrupp(P, gi) {
  const tidigare = P.grupper.slice(0, gi).flat();
  const { grupp, fyllnad } = M.fyllGrupp(P.grupper[gi], tidigare, P.loggar);
  const nasta = () => (gi + 1 < P.grupper.length ? introGrupp(P, gi + 1) : oversikt(P));

  matchning(P, grupp, { huvud: () => introHuvud(P, gi, 0) }, () => {
    skrivSerie(P, grupp, { huvud: () => introHuvud(P, gi, 1), rubrik: "Skriv orden" }, (id, res) => {
      const l = logg(P, id);
      l.forsok += res.forsok;
      l.fel += res.fel;
      l.ledtradar += res.ledtradar;
      if (fyllnad.includes(id) || l.valkant !== undefined) l.repriser++;
      else l.valkant = M.valkant(res);
    }, () => {
      const svara = M.blanda(grupp.filter((id) => !fyllnad.includes(id) && !P.loggar[id].valkant));
      if (!svara.length) return nasta();
      skrivSerie(P, svara, { huvud: () => introHuvud(P, gi, 2), rubrik: "Repetera de ord som var svåra" }, (id, res) => {
        const l = logg(P, id);
        l.forsok += res.forsok;
        l.fel += res.fel;
        l.ledtradar += res.ledtradar;
        l.repriser++;
      }, nasta);
    });
  });
}

function skrivSerie(P, ids, ram, efterOrd, klar) {
  let i = 0;
  const nasta = () => {
    if (i >= ids.length) return klar();
    const id = ids[i];
    const nr = i + 1;
    skrivFraga(P, id, { huvud: ram.huvud, rubrik: `${ram.rubrik} – ord ${nr} av ${ids.length}` }, (res) => {
      efterOrd(id, res);
      i++;
      nasta();
    });
  };
  nasta();
}

// ---------- Matchning ----------

function matchning(P, ids, { huvud, stor = false, rubrik }, klar) {
  const antalPlatser = stor ? Math.min(6, ids.length) : ids.length;
  const ko = M.blanda(ids);
  const vanster = ko.splice(0, antalPlatser);
  const hoger = M.blanda(vanster);
  let valdV = null;
  let valdH = null;
  let klara = 0;
  let upptagen = false;
  const klaraV = new Set();
  const klaraH = new Set();
  // Två glosor med samma svenska ord (eller samma målord) får paras ihop åt båda hållen.
  const passar = (a, b) => {
    const ga = P.ord.get(a);
    const gb = P.ord.get(b);
    return a === b || ga.sv === gb.sv || ga.mal === gb.mal;
  };

  const bradet = h("div", { class: "matchning" });
  const raknare = h("div", { class: "raknare", "aria-live": "polite" });
  const meddelande = h("div", { class: "meddelande", "aria-live": "polite" });

  function rita() {
    raknare.textContent = `${klara} av ${ids.length} par`;
    const knapp = (sida, id, i) => {
      if (id === null) return h("div", { class: "match-tom" });
      const g = P.ord.get(id);
      const klarad = !stor && (sida === "v" ? klaraV : klaraH).has(id);
      const vald = sida === "v" ? valdV?.i === i : valdH?.i === i;
      return h(
        "button",
        {
          class: `match ${vald ? "vald" : ""} ${klarad ? "klarad" : ""}`,
          disabled: klarad,
          "data-sida": sida,
          "data-i": i,
          onclick: () => klick(sida, id, i),
        },
        sida === "v" ? malOrd(g) : h("span", { lang: "sv" }, g.sv),
      );
    };
    bradet.replaceChildren(
      h("div", { class: "kolumn" }, vanster.map((id, i) => knapp("v", id, i))),
      h("div", { class: "kolumn" }, hoger.map((id, i) => knapp("h", id, i))),
    );
  }

  function klick(sida, id, i) {
    if (upptagen) return;
    if (sida === "v") valdV = valdV?.i === i ? null : { id, i };
    else valdH = valdH?.i === i ? null : { id, i };
    if (valdV && valdH) {
      if (passar(valdV.id, valdH.id)) return paratRatt();
      upptagen = true;
      for (const [s, v] of [["v", valdV], ["h", valdH]]) bradet.querySelector(`[data-sida="${s}"][data-i="${v.i}"]`)?.classList.add("skaka");
      setTimeout(() => {
        valdV = valdH = null;
        upptagen = false;
        rita();
      }, 550);
      return;
    }
    rita();
  }

  function paratRatt() {
    klara++;
    klaraV.add(valdV.id);
    klaraH.add(valdH.id);
    if (stor) {
      const iv = valdV.i;
      const ih = valdH.i;
      const ny = ko.shift();
      if (ny !== undefined) {
        vanster[iv] = ny;
        // Lägg det nya svenska ordet på en slumpad plats så att paret inte syns direkt.
        const andra = hoger.map((x, j) => j).filter((j) => j !== ih && hoger[j] !== null);
        if (andra.length) {
          const j = andra[Math.floor(Math.random() * andra.length)];
          hoger[ih] = hoger[j];
          hoger[j] = ny;
        } else hoger[ih] = ny;
      } else {
        vanster[iv] = null;
        hoger[ih] = null;
      }
    }
    valdV = valdH = null;
    rita();
    if (klara === ids.length) {
      meddelande.textContent = slumpa(["Snyggt! Alla par är klara.", "Bra! Alla par hittade.", "Perfekt matchat!"]);
      upptagen = true;
      setTimeout(klar, 900);
    }
  }

  rita();
  visa(
    huvud(),
    h(
      "section",
      { class: "kort ovning" },
      h("h2", {}, rubrik ?? "Para ihop orden"),
      h("p", { class: "tips" }, "Klicka på ett ord i varje kolumn som betyder samma sak."),
      raknare,
      bradet,
      meddelande,
      P.harGenus && genusForklaring(),
    ),
    stor && h("div", { class: "knapprad" }, h("button", { class: "knapp sekundar", onclick: klar }, "Hoppa över matchningen")),
  );
}

function genusForklaring() {
  return h(
    "p",
    { class: "genusforklaring" },
    h("span", { class: "genus-f" }, "■ femininum"),
    h("span", { class: "genus-m" }, "■ maskulinum"),
    h("span", { class: "genus-n" }, "■ neutrum"),
  );
}

// ---------- Skrivfråga ----------

// Visar ett svenskt ord och låter eleven skriva det på målspråket.
// klar(res) anropas med { forsok, fel, ledtradar, forstaRatt }.
function skrivFraga(P, id, { huvud, rubrik, extra }, klar) {
  const g = P.ord.get(id);
  const kod = sprakKod(g.sprak);
  const max = M.maxLedtradar(g.mal);
  const res = { forsok: 0, fel: 0, ledtradar: 0, forstaRatt: null };
  let lage = "fraga"; // fraga | skrivAv | klar
  let fardig = false;

  const input = h("input", {
    type: "text",
    class: "svar",
    autocomplete: "off",
    autocapitalize: "off",
    autocorrect: "off",
    spellcheck: "false",
    lang: kod || null,
    "aria-label": `Skriv ordet på ${sprakNamn(kod) || "målspråket"}`,
    "data-fokus": true,
  });
  const feedback = h("div", { class: "feedback", "aria-live": "polite" });
  const facit = h("div", { class: "facit", hidden: true });
  const ledtradKnapp = h("button", { type: "button", class: "knapp sekundar", disabled: max === 0 }, "Ledtråd");
  const svaraKnapp = h("button", { type: "submit", class: "knapp" }, "Svara");
  const tecken = SPRAK[kod]?.tecken ?? [];

  const uppdateraLedtrad = () => {
    const kvar = max - res.ledtradar;
    ledtradKnapp.textContent = max === 0 ? "Ledtråd" : `Ledtråd (${kvar} kvar)`;
    ledtradKnapp.disabled = kvar <= 0 || lage !== "fraga";
  };
  uppdateraLedtrad();

  ledtradKnapp.onclick = () => {
    if (res.ledtradar >= max || lage !== "fraga") return;
    res.ledtradar++;
    const text = M.ledtrad(g.mal, res.ledtradar);
    input.value = text;
    feedback.className = "feedback info";
    feedback.textContent = `Ledtråd: ${text}…`;
    uppdateraLedtrad();
    input.focus();
    input.setSelectionRange(text.length, text.length);
  };

  const fortsatt = () => {
    if (fardig) return;
    fardig = true;
    document.removeEventListener("keydown", enterFortsatt);
    klar(res);
  };
  const enterFortsatt = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      fortsatt();
    }
  };

  function visaRatt() {
    lage = "klar";
    input.disabled = true;
    input.classList.add("ratt");
    feedback.className = "feedback ratt";
    feedback.replaceChildren(h("strong", {}, slumpa(BEROM)), " ", malOrd(g));
    facit.hidden = true;
    uppdateraLedtrad();
    svaraKnapp.textContent = "Nästa →";
    svaraKnapp.onclick = (e) => (e.preventDefault(), fortsatt());
    svaraKnapp.focus();
    setTimeout(() => document.addEventListener("keydown", enterFortsatt), 60);
    setTimeout(fortsatt, res.fel === 0 ? 1100 : 1600);
  }

  function svara(e) {
    e.preventDefault();
    if (lage === "klar") return fortsatt();
    const varde = input.value;
    if (!varde.trim()) return input.focus();
    res.forsok++;
    const r = M.ratta(varde, g.mal);
    if (r.ratt) {
      if (res.forstaRatt === null) res.forstaRatt = res.ledtradar === 0;
      return visaRatt();
    }
    res.fel++;
    res.forstaRatt = false;
    input.classList.remove("skaka");
    void input.offsetWidth;
    input.classList.add("skaka");
    if (lage === "fraga") {
      lage = "skrivAv";
      uppdateraLedtrad();
      feedback.className = "feedback fel";
      feedback.textContent = r.nastan ? "Nästan! Kolla accenter och stora/små bokstäver." : "Inte riktigt.";
      facit.hidden = false;
      facit.replaceChildren(h("span", { class: "facit-etikett" }, "Rätt svar:"), malOrd(g, "stor"), h("span", { class: "facit-uppmaning" }, "Skriv ordet igen."));
      input.value = "";
    } else {
      feedback.className = "feedback fel";
      feedback.textContent = "Inte riktigt – skriv av ordet precis som det står.";
      input.select();
    }
    input.focus();
  }

  const infoga = (t) => {
    if (input.disabled) return;
    const a = input.selectionStart ?? input.value.length;
    const b = input.selectionEnd ?? input.value.length;
    input.value = input.value.slice(0, a) + t + input.value.slice(b);
    input.focus();
    input.setSelectionRange(a + t.length, a + t.length);
  };

  visa(
    huvud(),
    extra,
    h(
      "section",
      { class: "kort ovning" },
      h("h2", { class: "rubrik-liten" }, rubrik),
      h("div", { class: "fraga" }, h("span", { class: "uppmaning" }, `Skriv på ${sprakNamn(kod) || "målspråket"}:`), h("span", { class: "svenska", lang: "sv" }, g.sv)),
      h(
        "form",
        { class: "svarform", onsubmit: svara },
        input,
        tecken.length > 0 &&
          h(
            "div",
            { class: "tecken" },
            tecken.map((t) => h("button", { type: "button", tabindex: "-1", onmousedown: (e) => e.preventDefault(), onclick: () => infoga(t) }, t)),
          ),
        facit,
        feedback,
        h("div", { class: "knapprad" }, ledtradKnapp, svaraKnapp),
      ),
    ),
  );
}

// ---------- Översikt efter introduktionen ----------

function oversikt(P) {
  const ids = P.nya;
  const antal = { gron: 0, gul: 0, rod: 0 };
  const plattor = ids.map((id) => {
    const g = P.ord.get(id);
    const l = logg(P, id);
    const farg = M.platta(l);
    antal[farg]++;
    return h(
      "div",
      { class: `platta ${farg}` },
      malOrd(g),
      h("span", { class: "sv" }, g.sv),
      h("span", { class: "plattstat" }, `Försök ${l.forsok} · Fel ${l.fel} · Ledtrådar ${l.ledtradar}`),
    );
  });
  const summa = (k) => ids.reduce((s, id) => s + (P.loggar[id]?.[k] ?? 0), 0);

  visa(
    passHuvud(P, "matchning"),
    h("h1", {}, "Introduktionen är klar!"),
    h(
      "div",
      { class: "kort" },
      h(
        "ul",
        { class: "sammanfattning" },
        h("li", { class: "gron-text" }, h("strong", {}, antal.gron), " ord kunde du direkt"),
        h("li", { class: "gul-text" }, h("strong", {}, antal.gul), " ord var lite kluriga"),
        h("li", { class: "rod-text" }, h("strong", {}, antal.rod), " ord var svåra"),
      ),
      h("p", { class: "meta" }, `Totalt: ${summa("forsok")} försök · ${summa("fel")} fel · ${summa("ledtradar")} ledtrådar`),
    ),
    h("div", { class: "plattor" }, plattor),
    P.harGenus && genusForklaring(),
    h("h2", {}, "Vill du göra en stor matchningsövning?"),
    h("p", {}, "Alla ord blandas. Det är frivilligt – du kan gå direkt till repetitionen."),
    h(
      "div",
      { class: "knapprad" },
      h(
        "button",
        {
          class: "knapp",
          "data-fokus": true,
          onclick: () =>
            matchning(P, ids, { huvud: () => passHuvud(P, "matchning"), stor: true, rubrik: "Stor matchning" }, () => repetition(P)),
        },
        "Ja, matcha alla ord",
      ),
      h("button", { class: "knapp sekundar", onclick: () => repetition(P) }, "Hoppa över"),
    ),
  );
}

// ---------- Slutlig repetition ----------

function repetition(P) {
  const start = {};
  for (const id of P.nya) start[id] = M.startniva(P.loggar[id]);
  for (const id of P.repetera) start[id] = 0;
  const R = new M.Repetition(start);
  P.R = R;

  const huvud = () => {
    const klara = R.antalKlara;
    return passHuvud(
      P,
      "repetition",
      h(
        "div",
        { class: "fasinfo" },
        h("div", { class: "fastext" }, `Repetition: ${klara} av ${R.antal} ord avklarade`),
        h(
          "div",
          { class: "stapel", role: "progressbar", "aria-valuemin": 0, "aria-valuemax": R.antal, "aria-valuenow": klara },
          h("span", { style: `width:${(100 * klara) / R.antal}%` }),
        ),
      ),
    );
  };

  const nasta = () => {
    const id = R.nasta();
    if (id === null) return slut(P);
    const niva = R.niva[id];
    const prickar = h(
      "div",
      { class: "nivaprickar", title: "Två rätt i rad så är ordet klart", "aria-label": `Nivå ${niva}` },
      h("span", { class: niva >= 1 ? "fylld" : niva < 0 ? "svar-ord" : "" }),
      h("span", { class: niva >= 2 ? "fylld" : "" }),
    );
    skrivFraga(P, id, { huvud, rubrik: "Skriv ordet", extra: null }, (res) => {
      const l = (P.repLogg[id] ??= { ratt: 0, fel: 0, ledtradar: 0 });
      if (res.forstaRatt) l.ratt++;
      l.fel += res.fel;
      l.ledtradar += res.ledtradar;
      R.svara(id, res.forstaRatt);
      nasta();
    });
    app.querySelector(".fraga")?.append(prickar);
  };
  nasta();
}

// ---------- Avslut ----------

function slut(P) {
  aktivtPass = null;
  const dag = M.idag();
  const ids = [...new Set([...P.nya, ...P.repetera])];
  const nya = {};
  let totFel = 0;
  let totLed = 0;
  let totFragor = 0;
  for (const id of ids) {
    const i = P.loggar[id] ?? { fel: 0, ledtradar: 0, forsok: 0 };
    const r = P.repLogg[id] ?? { ratt: 0, fel: 0, ledtradar: 0 };
    const pass = {
      ratt: (i.valkant ? 1 : 0) + r.ratt,
      fel: i.fel + r.fel,
      ledtradar: i.ledtradar + r.ledtradar,
      tillNiva2: P.R?.klarEfter[id],
    };
    totFel += pass.fel;
    totLed += pass.ledtradar;
    totFragor += (P.R?.fragorPerOrd[id] ?? 0) + i.forsok;
    nya[id] = M.schemalagg(lager.ordStat(id), pass, dag);
  }
  lager.sparaAllaOrd(nya);
  lager.markeraOvad(P.listIds);

  // Nästa repetitionsdatum för listorna som övades.
  const allaIds = [...new Set(P.listIds.flatMap((lid) => lager.lista(lid)?.glosaIds ?? []))];
  const datum = allaIds
    .map((id) => lager.ordStat(id))
    .filter((s) => s && s.nasta)
    .map((s) => s.nasta)
    .sort()[0];
  const imorgon = M.plusDagar(dag, 1);
  const nastaText = !datum
    ? null
    : datum <= imorgon
      ? "Kom tillbaka i morgon och öva igen."
      : `Nästa repetition: ${datumFint(datum)}.`;

  visa(
    sidhuvud(),
    h(
      "div",
      { class: "kort klart" },
      h("div", { class: "konfetti", "aria-hidden": "true" }, "🎉"),
      h("h1", {}, "Bra gjort! Nu har du övat klart för denna gång."),
      nastaText && h("p", { class: "nasta" }, nastaText),
      h("p", { class: "meta" }, `${ids.length} ord · ${totFragor} svar · ${totFel} fel · ${totLed} ledtrådar`),
      h("div", { class: "knapprad" }, h("button", { class: "knapp", onclick: visaStart, "data-fokus": true }, "Till mina listor")),
    ),
  );
}

// ---------- Start ----------

const params = new URLSearchParams(location.search);
const direkt = api.tolkaIds(params.get("lista") ?? params.get("listor") ?? "");
if (direkt.length) oppnaDirektlank(direkt);
else visaStart();
