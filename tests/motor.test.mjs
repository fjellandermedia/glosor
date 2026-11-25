// Kör med: node --test tests/
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  ratta,
  alternativ,
  ledtrad,
  maxLedtradar,
  fordelaJamnt,
  Repetition,
  schemalagg,
  plusDagar,
  delaIGrupper,
  fyllGrupp,
  platta,
  valkant,
} from "../js/motor.js";

function seedad(seed = 1) {
  return () => {
    seed = (seed * 16807) % 2147483647;
    return (seed - 1) / 2147483646;
  };
}

test("rättning: exakt, extra mellanslag, versal först, alternativ, parentes", () => {
  assert.equal(ratta("la casa", "la casa").ratt, true);
  assert.equal(ratta("  la   casa ", "la casa").ratt, true);
  assert.equal(ratta("La casa", "la casa").ratt, true, "mobilens autoversal godkänns");
  assert.equal(ratta("der hund", "der Hund").ratt, false, "versal mitt i räknas");
  assert.equal(ratta("hund", "Hund").ratt, false, "versal som ska vara där räknas");
  assert.equal(ratta("el hogar", "la casa / el hogar").ratt, true);
  assert.equal(ratta("llamar", "(se) llamar").ratt, true);
  assert.equal(ratta("se llamar", "(se) llamar").ratt, true);
  assert.equal(ratta("que tal", "¿Qué tal?").ratt, false);
  assert.equal(ratta("que tal", "¿Qué tal?").nastan, true);
  assert.equal(ratta("Qué tal", "¿Qué tal?").ratt, true);
  assert.equal(ratta("", "x").ratt, false);
  assert.deepEqual(alternativ("a / b"), ["a", "b"]);
});

test("ledtrådar: högst halva ordet, mellanslag följer med", () => {
  assert.equal(maxLedtradar("la casa"), 3);
  assert.equal(ledtrad("la casa", 1), "l");
  assert.equal(ledtrad("la casa", 2), "la ");
  assert.equal(ledtrad("la casa", 3), "la c");
  assert.equal(maxLedtradar("dog"), 1);
  assert.equal(ledtrad("x", 0), "");
});

test("introduktion: grupper om fem och utfyllnad med svåra ord", () => {
  const ord = ["a", "b", "c", "d", "e", "f", "g"];
  const g = delaIGrupper(ord);
  assert.deepEqual(g, [["a", "b", "c", "d", "e"], ["f", "g"]]);
  const loggar = { a: { fel: 0, ledtradar: 0 }, b: { fel: 2, ledtradar: 0 }, c: { fel: 0, ledtradar: 1 }, d: { fel: 0, ledtradar: 0 }, e: { fel: 5, ledtradar: 0 } };
  const { grupp, fyllnad } = fyllGrupp(g[1], g[0], loggar, 5, seedad());
  assert.equal(grupp.length, 5);
  assert.deepEqual(fyllnad, ["e", "b", "c"]);
  assert.equal(platta({ fel: 0, ledtradar: 0 }), "gron");
  assert.equal(platta({ fel: 1, ledtradar: 1 }), "gul");
  assert.equal(platta({ fel: 3, ledtradar: 1 }), "rod");
  assert.equal(valkant({ forsok: 1, fel: 0, ledtradar: 0 }), true);
  assert.equal(valkant({ forsok: 2, fel: 1, ledtradar: 0 }), false);
});

test("fördela nivå 1-ord jämnt bland nivå 0-ord", () => {
  const ut = fordelaJamnt(["a", "b", "c", "d", "e", "f"], ["X", "Y"]);
  assert.equal(ut.length, 8);
  const pos = ["X", "Y"].map((x) => ut.indexOf(x));
  assert.ok(pos[1] - pos[0] >= 3, `för tätt: ${ut.join(" ")}`);
});

test("repetition: alla rätt -> nivå 1-ord klara efter en fråga, nivå 0 efter två", () => {
  const r = new Repetition({ a: 0, b: 1, c: 0 }, seedad(3));
  const fragor = [];
  let id;
  while ((id = r.nasta()) !== null) {
    fragor.push(id);
    r.svara(id, true);
    assert.ok(fragor.length < 50);
  }
  assert.equal(fragor.length, 5);
  assert.equal(fragor.filter((x) => x === "b").length, 1);
  for (let i = 1; i < fragor.length; i++) assert.notEqual(fragor[i], fragor[i - 1]);
});

test("repetition: felkön får var tredje fråga och ord kommer inte två gånger i rad", () => {
  const ids = ["a", "b", "c", "d", "e", "f"];
  const r = new Repetition(Object.fromEntries(ids.map((x) => [x, 0])), seedad(7));
  // Svara fel på "a" tills det hamnar i felkön.
  const log = [];
  let id;
  let felA = 0;
  while (!r.klar) {
    const kvar = r.antal - r.antalKlara;
    id = r.nasta();
    log.push({ id, felko: r.aktuell.franFelko, nr: r.antalFragor + 1, kvar });
    const ratt = !(id === "a" && felA < 3);
    if (id === "a" && !ratt) felA++;
    r.svara(id, ratt);
    assert.ok(log.length < 200);
  }
  for (let i = 1; i < log.length; i++) if (log[i].kvar > 1) assert.notEqual(log[i].id, log[i - 1].id);
  const felkoFragor = log.filter((x) => x.felko);
  assert.ok(felkoFragor.length >= 1);
  // Felkö-frågor ställs på var tredje fråga så länge huvudlistan har ord.
  for (const f of felkoFragor) {
    const huvudKvar = log.slice(log.indexOf(f) + 1).some((x) => x.id !== "a");
    if (huvudKvar) assert.equal(f.nr % 3, 0, `felköfråga på nr ${f.nr}`);
  }
  assert.ok(r.klar);
});

test("repetition: nivån går aldrig under -1 och felkö-ord som klaras får nivå 0", () => {
  const r = new Repetition({ a: 0, b: 0 }, seedad(2));
  let id = r.nasta();
  r.svara(id, false);
  assert.equal(r.niva[id], -1);
  assert.deepEqual(r.felko, [id]);
  // Bara b i huvudlistan, a i felkön.
  const andra = r.nasta();
  assert.notEqual(andra, id);
  r.svara(andra, false);
  r.svara(r.nasta(), false);
  assert.ok(Object.values(r.niva).every((n) => n >= -1));
  let varv = 0;
  while ((id = r.nasta()) !== null && varv++ < 100) {
    const fore = r.niva[id];
    const franFelko = r.aktuell.franFelko;
    r.svara(id, true);
    if (franFelko) assert.equal(r.niva[id], fore + 1);
  }
  assert.ok(r.klar);
});

test("spaced repetition: 1, 3, 7 dagar och kortare vid fel", () => {
  const dag = "2026-12-01";
  let s = schemalagg(undefined, { ratt: 2, fel: 1, ledtradar: 0, tillNiva2: 3 }, dag);
  assert.equal(s.nasta, "2026-12-02");
  s = schemalagg(s, { ratt: 2, fel: 0, ledtradar: 0 }, "2026-12-02");
  assert.equal(s.nasta, "2026-12-05");
  s = schemalagg(s, { ratt: 2, fel: 0, ledtradar: 0 }, "2026-12-05");
  assert.equal(s.nasta, "2026-12-12");
  s = schemalagg(s, { ratt: 2, fel: 1, ledtradar: 0 }, "2026-12-12");
  assert.equal(s.nasta, "2026-12-15", "ett fel kortar ett steg");
  s = schemalagg(s, { ratt: 2, fel: 3, ledtradar: 1 }, "2026-12-15");
  assert.equal(s.nasta, "2026-12-16", "många fel börjar om");
  assert.equal(s.pass, 5);
  assert.equal(plusDagar("2026-12-31", 1), "2027-01-01");
});
