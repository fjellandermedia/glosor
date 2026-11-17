(function () {
  "use strict";

  // ---------- Inställningar ----------
  const cfg = window.GLOSOR_CONFIG || {};
  const params = new URLSearchParams(location.search);
  const skola = params.get("skola") || cfg.skola || "";
  const kurs = params.get("kurs") || cfg.kurs || "";

  const SPRAK = {
    sv: ["svenska", "sv-SE"],
    en: ["engelska", "en-GB"],
    de: ["tyska", "de-DE"],
    fr: ["franska", "fr-FR"],
    es: ["spanska", "es-ES"],
    it: ["italienska", "it-IT"],
    fi: ["finska", "fi-FI"],
    no: ["norska", "nb-NO"],
    da: ["danska", "da-DK"],
  };
  // Småord som får utelämnas framför verb ("to drink" = "drink").
  const INFINITIVMARKER = { en: "to", sv: "att" };

  const sprakNamn = (kod) => (SPRAK[kod] ? SPRAK[kod][0] : String(kod).toUpperCase());
  const stor = (s) => s.charAt(0).toUpperCase() + s.slice(1);

  const app = document.getElementById("app");
  const state = {
    lista: null,
    glosor: [],
    fran: "sv", // listans "fransprak" (språket i fältet fraga)
    till: "en", // listans "tillsprak" (språket i fältet svar)
    lage: null, // aktuell övning
    ko: [], // glosor i den här omgången
    pos: 0,
    resultat: [],
    svarat: false,
  };

  // ---------- Hjälpfunktioner ----------
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

  const visa = (...noder) => {
    app.replaceChildren(...noder.flat().filter(Boolean));
    window.scrollTo(0, 0);
  };

  const IKONER = {
    hogtalare:
      '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M18.5 5.5a9 9 0 0 1 0 13"/></svg>',
    valj:
      '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><path d="m14.5 17.5 2 2 4-4"/></svg>',
    skriv:
      '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>',
  };
  function ikon(namn) {
    const span = h("span", { class: "ikon" });
    span.innerHTML = IKONER[namn];
    return span;
  }

  function blanda(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function somLista(v) {
    if (Array.isArray(v)) return v.map((x) => String(x).trim()).filter(Boolean);
    if (v == null) return [];
    const s = String(v).trim();
    return s ? [s] : [];
  }

  // Gör svar jämförbara: små bokstäver, inga skiljetecken, enkla mellanslag.
  function norm(s) {
    return String(s)
      .normalize("NFC")
      .toLowerCase()
      .replace(/[’`´]/g, "'")
      .replace(/[.,!?;:"“”„()]/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function varianter(s, sprak) {
    const n = norm(s);
    const ut = [n];
    const m = INFINITIVMARKER[sprak];
    if (m && n.startsWith(m + " ")) ut.push(n.slice(m.length + 1));
    return ut;
  }

  // Levenshtein-avstånd plus en bokstav-för-bokstav-jämförelse.
  function jamforBokstaver(skrivet, ratt) {
    const A = Array.from(skrivet);
    const B = Array.from(ratt);
    const n = A.length;
    const m = B.length;
    const d = [];
    for (let i = 0; i <= n; i++) {
      d.push(new Array(m + 1).fill(0));
      d[i][0] = i;
    }
    for (let j = 0; j <= m; j++) d[0][j] = j;
    for (let i = 1; i <= n; i++) {
      for (let j = 1; j <= m; j++) {
        const kostnad = A[i - 1] === B[j - 1] ? 0 : 1;
        d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + kostnad);
      }
    }
    const steg = [];
    let i = n;
    let j = m;
    while (i > 0 || j > 0) {
      if (i > 0 && j > 0 && d[i][j] === d[i - 1][j - 1] + (A[i - 1] === B[j - 1] ? 0 : 1)) {
        steg.push({ typ: A[i - 1] === B[j - 1] ? "ratt" : "fel", tecken: A[i - 1] });
        i--;
        j--;
      } else if (i > 0 && d[i][j] === d[i - 1][j] + 1) {
        steg.push({ typ: "extra", tecken: A[i - 1] });
        i--;
      } else {
        steg.push({ typ: "saknas" });
        j--;
      }
    }
    return { avstand: d[n][m], steg: steg.reverse(), langd: Math.max(n, m) };
  }

  // Hittar det godkända svar som ligger närmast det eleven skrivit.
  function narmasteSvar(glosa, skrivet) {
    const sprak = state.lage.till;
    let bast = null;
    for (const r of glosa.ord[sprak]) {
      for (const rv of varianter(r, sprak)) {
        for (const sv of varianter(skrivet, sprak)) {
          const j = jamforBokstaver(sv, rv);
          if (!bast || j.avstand < bast.avstand) bast = j;
        }
      }
    }
    return bast;
  }

  function talKnapp(text, sprak) {
    if (!("speechSynthesis" in window)) return null;
    return h(
      "button",
      {
        type: "button",
        class: "ikon-knapp",
        title: "Lyssna",
        "aria-label": "Lyssna på " + text,
        onclick: () => {
          const u = new SpeechSynthesisUtterance(text);
          u.lang = (SPRAK[sprak] || [])[1] || sprak;
          speechSynthesis.cancel();
          speechSynthesis.speak(u);
        },
      },
      ikon("hogtalare")
    );
  }

  const lageTitel = (l) => stor(sprakNamn(l.fran)) + " → " + sprakNamn(l.till);

  // ---------- Hämta glosor ----------
  async function ladda() {
    visa(
      h(
        "div",
        { class: "center" },
        h("div", { class: "spinner", "aria-hidden": "true" }),
        h("p", { class: "muted" }, "Hämtar glosor…")
      )
    );
    try {
      if (!cfg.apiUrl) throw new Error("Ingen API-adress är inställd i js/config.js.");
      const svar = await fetch(cfg.apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ skola, kurs }),
      });
      if (!svar.ok) throw new Error("Servern svarade med felkod " + svar.status + ".");
      let data = await svar.json();
      if (typeof data === "string") data = JSON.parse(data);
      if (Array.isArray(data)) data = data.length && data[0].glosor ? data[0] : { glosor: data };
      tolka(data || {});
      visaStart();
    } catch (fel) {
      visa(
        h(
          "section",
          { class: "card center" },
          h("h1", null, "Kunde inte hämta glosorna"),
          h("p", { class: "muted" }, fel && fel.message ? fel.message : String(fel)),
          h("button", { class: "btn primary", onclick: ladda }, "Försök igen")
        )
      );
    }
  }

  function tolka(data) {
    state.lista = data;
    state.fran = String(data.fransprak || "sv").toLowerCase();
    state.till = String(data.tillsprak || "en").toLowerCase();
    state.glosor = (data.glosor || [])
      .map((g, i) => {
        const fragor = somLista(g.fraga);
        const svar = somLista(g.svar);
        if (!fragor.length || !svar.length) return null;
        return {
          id: g.id != null ? String(g.id) : "g" + i,
          ord: { [state.fran]: fragor, [state.till]: svar },
          ordklass: g.ordklass,
          exempel: g.exempelmening,
          ledtrad: g.ledtrad,
          bild: typeof g.bild === "string" && /^https?:\/\//.test(g.bild) ? g.bild : null,
          bojningar: somLista(g.bojningar),
        };
      })
      .filter(Boolean);
  }

  // ---------- Startsida ----------
  function lagen() {
    const a = state.till;
    const b = state.fran;
    return [
      { fran: a, till: b, typ: "valj" },
      { fran: a, till: b, typ: "skriv" },
      { fran: b, till: a, typ: "valj" },
      { fran: b, till: a, typ: "skriv" },
    ];
  }

  function visaStart() {
    state.lage = null;
    const L = state.lista || {};
    const antal = state.glosor.length;
    visa(
      h(
        "header",
        { class: "top" },
        (skola || kurs) && h("p", { class: "eyebrow" }, [skola, kurs].filter(Boolean).join(" · ")),
        h("h1", null, L.titel || "Glosor"),
        L.beskrivning && h("p", { class: "muted" }, L.beskrivning),
        h("p", { class: "pill" }, antal + (antal === 1 ? " glosa" : " glosor"))
      ),
      antal === 0
        ? h("p", { class: "card center muted" }, "Listan innehåller inga glosor ännu.")
        : h(
            "section",
            { class: "modes", "aria-label": "Välj övning" },
            lagen().map((l) =>
              h(
                "button",
                {
                  class: "mode",
                  disabled: l.typ === "valj" && antal < 2,
                  onclick: () => starta(l, blanda(state.glosor)),
                },
                h("span", { class: "mode-dir" }, lageTitel(l)),
                h(
                  "span",
                  { class: "mode-type" },
                  ikon(l.typ),
                  l.typ === "valj" ? "Välj rätt ord" : "Skriv ordet"
                )
              )
            )
          )
    );
  }

  // ---------- Övning ----------
  function starta(lage, glosor) {
    state.lage = lage;
    state.ko = glosor;
    state.pos = 0;
    state.resultat = [];
    visaFraga();
  }

  function visaFraga() {
    const g = state.ko[state.pos];
    const l = state.lage;
    state.svarat = false;
    const fraga = g.ord[l.fran][0];

    const kort = h(
      "section",
      { class: "card", id: "kort", tabindex: "-1" },
      h(
        "p",
        { class: "lang" },
        stor(sprakNamn(l.fran)),
        g.ordklass && h("span", { class: "tag" }, g.ordklass)
      ),
      h(
        "div",
        { class: "prompt-row" },
        h("h2", { class: "prompt", lang: l.fran }, fraga),
        talKnapp(fraga, l.fran)
      ),
      g.bild &&
        h("img", {
          class: "bild",
          src: g.bild,
          alt: "",
          loading: "lazy",
          onerror: (e) => e.currentTarget.remove(),
        }),
      h("p", { class: "ask" }, "Vad heter det på " + sprakNamn(l.till) + "?"),
      l.typ === "valj" ? valjDel(g) : skrivDel(g),
      h("div", { class: "feedback", id: "feedback", "aria-live": "polite" })
    );

    visa(
      h(
        "div",
        { class: "quiz-head" },
        h("button", { class: "link", onclick: visaStart }, "← Byt övning"),
        h("span", { class: "muted" }, lageTitel(l)),
        h("span", { class: "progress-text" }, state.pos + 1 + " / " + state.ko.length)
      ),
      h(
        "div",
        { class: "bar", role: "progressbar", "aria-valuemin": "0", "aria-valuemax": String(state.ko.length), "aria-valuenow": String(state.pos) },
        h("div", { class: "bar-fill", style: "width:" + (state.pos / state.ko.length) * 100 + "%" })
      ),
      kort
    );

    const input = document.getElementById("svar");
    if (input) input.focus();
  }

  // --- Välj ord ---
  function valjDel(g) {
    const l = state.lage;
    const ratt = g.ord[l.till];
    const rattNorm = new Set(ratt.map(norm));
    const alternativ = [];
    const sett = new Set();
    for (const annan of blanda(state.glosor)) {
      if (annan.id === g.id) continue;
      const ord = annan.ord[l.till][0];
      const n = norm(ord);
      if (rattNorm.has(n) || sett.has(n)) continue;
      sett.add(n);
      alternativ.push(ord);
      if (alternativ.length === 3) break;
    }
    const knappar = blanda([ratt[0], ...alternativ]);
    const grid = h("div", { class: "choices" });
    knappar.forEach((text, i) => {
      grid.append(
        h(
          "button",
          {
            class: "choice",
            lang: l.till,
            "data-ratt": rattNorm.has(norm(text)) ? "1" : null,
            onclick: (e) => valj(e.currentTarget, grid, g, text),
          },
          h("span", { class: "key", "aria-hidden": "true" }, String(i + 1)),
          h("span", null, text)
        )
      );
    });
    return grid;
  }

  function valj(knapp, grid, g, text) {
    if (state.svarat) return;
    const ratt = knapp.dataset.ratt === "1";
    for (const b of grid.children) {
      b.disabled = true;
      if (b.dataset.ratt === "1") b.classList.add("correct");
    }
    if (!ratt) knapp.classList.add("wrong");
    besvara(g, ratt, text);
  }

  // --- Skriv ord ---
  function skrivDel(g) {
    const l = state.lage;
    const input = h("input", {
      type: "text",
      id: "svar",
      class: "input",
      lang: l.till,
      autocomplete: "off",
      autocapitalize: "off",
      autocorrect: "off",
      spellcheck: "false",
      enterkeyhint: "done",
      placeholder: "Skriv på " + sprakNamn(l.till) + "…",
      "aria-label": "Ditt svar",
    });
    const naraUt = h("div", { class: "near", id: "nara", "aria-live": "polite" });
    const visaLedtrad = g.ledtrad && l.till === state.till;

    const specialTecken =
      l.till === "sv"
        ? h(
            "div",
            { class: "chars", "aria-label": "Specialtecken" },
            ["å", "ä", "ö"].map((t) =>
              h(
                "button",
                {
                  type: "button",
                  class: "char",
                  onclick: () => {
                    const s = input.selectionStart ?? input.value.length;
                    const e = input.selectionEnd ?? input.value.length;
                    input.value = input.value.slice(0, s) + t + input.value.slice(e);
                    input.focus();
                    input.setSelectionRange(s + 1, s + 1);
                  },
                },
                t
              )
            )
          )
        : null;

    return h(
      "form",
      {
        class: "write",
        onsubmit: (e) => {
          e.preventDefault();
          kolla(g, input, false);
        },
      },
      h(
        "fieldset",
        { class: "plain", id: "skriv-falt" },
        h("div", { class: "input-row" }, input, specialTecken),
        h(
          "div",
          { class: "actions" },
          h("button", { type: "button", class: "btn secondary", onclick: () => naraKoll(g, input, naraUt) }, "Är jag nära?"),
          h("button", { type: "submit", class: "btn primary" }, "Kolla svar")
        ),
        h(
          "div",
          { class: "actions small" },
          visaLedtrad &&
            h(
              "button",
              {
                type: "button",
                class: "link",
                onclick: (e) => e.currentTarget.replaceWith(h("p", { class: "hint" }, "Ledtråd: " + g.ledtrad)),
              },
              "Visa ledtråd"
            ),
          h("button", { type: "button", class: "link", onclick: () => kolla(g, input, true) }, "Jag vet inte")
        )
      ),
      naraUt
    );
  }

  function bokstavsVy(steg) {
    return h(
      "p",
      { class: "diff", "aria-label": "Jämförelse bokstav för bokstav" },
      steg.map((s) => {
        if (s.typ === "saknas") return h("span", { class: "d-saknas", title: "Här saknas en bokstav" }, "_");
        const t = s.tecken === " " ? " " : s.tecken;
        const titel = { ratt: "Rätt", fel: "Fel bokstav", extra: "Ska bort" }[s.typ];
        return h("span", { class: "d-" + s.typ, title: titel }, t);
      })
    );
  }

  const forklaring = () =>
    h(
      "p",
      { class: "legend" },
      h("span", { class: "d-ratt" }, "a"), " rätt  ",
      h("span", { class: "d-fel" }, "a"), " fel bokstav  ",
      h("span", { class: "d-extra" }, "a"), " ska bort  ",
      h("span", { class: "d-saknas" }, "_"), " saknas"
    );

  function naraKoll(g, input, ut) {
    if (state.svarat) return;
    if (!norm(input.value)) {
      ut.className = "near";
      ut.replaceChildren(h("p", { class: "muted" }, "Skriv något först."));
      input.focus();
      return;
    }
    const b = narmasteSvar(g, input.value);
    const procent = Math.max(0, Math.round((1 - b.avstand / Math.max(1, b.langd)) * 100));
    let text;
    let niva;
    if (b.avstand === 0) {
      text = "Det där ser rätt ut! Tryck på Kolla svar.";
      niva = "ok";
    } else if (b.avstand === 1) {
      text = "Jättenära – bara en bokstav skiljer.";
      niva = "close";
    } else if (b.avstand === 2) {
      text = "Nära – två bokstäver skiljer.";
      niva = "close";
    } else if (b.avstand <= Math.max(3, Math.ceil(b.langd * 0.4))) {
      text = "Du är på rätt spår, men " + b.avstand + " bokstäver skiljer.";
      niva = "warm";
    } else {
      text = "Inte så nära ännu. Försök igen!";
      niva = "cold";
    }
    const visaBokstaver = b.avstand > 0 && niva !== "cold";
    ut.className = "near " + niva;
    ut.replaceChildren(
      ...[
        h(
          "div",
          { class: "meter", "aria-hidden": "true" },
          h("div", { class: "meter-fill", style: "width:" + procent + "%" })
        ),
        h("p", { class: "near-text" }, text),
        visaBokstaver && bokstavsVy(b.steg),
        visaBokstaver && forklaring(),
      ].filter(Boolean)
    );
    input.focus();
  }

  function kolla(g, input, gavUpp) {
    if (state.svarat) return;
    const skrivet = input.value;
    if (!gavUpp && !norm(skrivet)) {
      input.focus();
      return;
    }
    const b = gavUpp ? null : narmasteSvar(g, skrivet);
    const ratt = !!b && b.avstand === 0;
    input.classList.add(ratt ? "correct" : "wrong");
    document.getElementById("skriv-falt").disabled = true;
    document.getElementById("nara").replaceChildren();
    document.getElementById("nara").className = "near";
    const extra =
      b && !ratt
        ? h("div", { class: "your-answer" }, h("p", { class: "label" }, "Ditt svar jämfört med rätt svar:"), bokstavsVy(b.steg))
        : null;
    besvara(g, ratt, gavUpp ? "" : skrivet, extra);
  }

  // --- Gemensamt efter svar ---
  function besvara(g, ratt, givet, extra) {
    state.svarat = true;
    state.resultat.push({ g, ratt, givet });
    const l = state.lage;
    const svar = g.ord[l.till];
    const sista = state.pos + 1 >= state.ko.length;
    const fb = document.getElementById("feedback");
    fb.className = "feedback " + (ratt ? "ok" : "bad");
    fb.replaceChildren(
      ...[
      h("p", { class: "verdict" }, ratt ? "Rätt!" : givet === "" && l.typ === "skriv" ? "Så här heter det:" : "Inte riktigt."),
      extra,
      h(
        "div",
        { class: "answer-row" },
        h(
          "p",
          { class: "answer" },
          ratt ? null : h("span", { class: "label" }, "Rätt svar: "),
          h("strong", { lang: l.till }, svar[0]),
          svar.length > 1 && h("span", { class: "muted" }, " (även: " + svar.slice(1).join(", ") + ")")
        ),
        talKnapp(svar[0], l.till)
      ),
      g.bojningar.length > 0 && h("p", { class: "extra" }, h("span", { class: "label" }, "Böjningar: "), g.bojningar.join(" – ")),
      g.exempel && h("p", { class: "example", lang: state.till }, "”" + g.exempel + "”"),
      h(
        "button",
        { class: "btn primary next", onclick: nasta },
        sista ? "Se resultat" : "Nästa →"
      ),
      ].filter(Boolean)
    );
    const kort = document.getElementById("kort");
    if (kort) kort.focus({ preventScroll: true });
    fb.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  function nasta() {
    state.pos++;
    if (state.pos >= state.ko.length) visaResultat();
    else visaFraga();
  }

  // ---------- Resultat ----------
  function visaResultat() {
    const l = state.lage;
    const r = state.resultat;
    const antalRatt = r.filter((x) => x.ratt).length;
    const fel = r.filter((x) => !x.ratt);
    const procent = Math.round((antalRatt / r.length) * 100);
    const omdome =
      procent === 100
        ? "Alla rätt – snyggt!"
        : procent >= 80
          ? "Riktigt bra!"
          : procent >= 50
            ? "Bra jobbat – fortsätt öva!"
            : "Fortsätt öva, det kommer!";

    state.svarat = false;
    visa(
      h(
        "section",
        { class: "card result" },
        h("p", { class: "eyebrow" }, lageTitel(l) + " · " + (l.typ === "valj" ? "välj ord" : "skriv ord")),
        h("p", { class: "score" }, antalRatt + " av " + r.length),
        h("div", { class: "meter big", "aria-hidden": "true" }, h("div", { class: "meter-fill", style: "width:" + procent + "%" })),
        h("p", { class: "muted" }, omdome),
        fel.length > 0 &&
          h(
            "div",
            { class: "wrong-list" },
            h("h3", null, "Öva mer på"),
            h(
              "ul",
              null,
              fel.map((x) =>
                h(
                  "li",
                  null,
                  h("span", { lang: l.fran }, x.g.ord[l.fran][0]),
                  h("span", { class: "muted" }, " → "),
                  h("strong", { lang: l.till }, x.g.ord[l.till][0])
                )
              )
            )
          ),
        h(
          "div",
          { class: "actions" },
          fel.length > 0 &&
            h("button", { class: "btn primary", onclick: () => starta(l, blanda(fel.map((x) => x.g))) }, "Öva på felen (" + fel.length + ")"),
          h("button", { class: "btn " + (fel.length ? "secondary" : "primary"), onclick: () => starta(l, blanda(state.glosor)) }, "Öva igen"),
          h("button", { class: "btn secondary", onclick: visaStart }, "Byt övning")
        )
      )
    );
  }

  // ---------- Tangentbord ----------
  document.addEventListener("keydown", (e) => {
    if (!state.lage || !document.getElementById("kort")) return;
    if (state.svarat && e.key === "Enter" && !(e.target instanceof HTMLButtonElement)) {
      e.preventDefault();
      nasta();
      return;
    }
    if (!state.svarat && state.lage.typ === "valj" && /^[1-4]$/.test(e.key)) {
      const b = document.querySelectorAll(".choice")[Number(e.key) - 1];
      if (b) b.click();
    }
  });

  ladda();
})();
