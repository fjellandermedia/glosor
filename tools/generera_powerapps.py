#!/usr/bin/env python3
"""Genererar lärarappen i Power Apps: YAML för skärmarna och App.Formulas.

Kör:  python3 tools/generera_powerapps.py

Skriver:
  powerapps/<n>-<skärm>.yaml            hela skärmen ("Screens: ..."), klistras in i trädvyn
  powerapps/kontroller/<n>-<skärm>.yaml bara kontrollerna, om Studio inte tar emot hela skärmar
  powerapps/App.Formulas.txt            named formulas, engelsk formelsyntax (, och ;)
  powerapps/App.Formulas.sv.txt         samma med svensk syntax (; och ;;)

Appen använder moderna kontroller och containrar med automatisk layout.
Alla färger kommer från den namngivna formeln Tema i App.Formulas.
"""
import re
from pathlib import Path

ROT = Path(__file__).resolve().parent.parent
UT = ROT / "powerapps"

# ---------- Kontrolltyper (som Power Apps Studio i er miljö skriver dem) ----------
CONTAINER = "GroupContainer@1.5.0"
TEXT = "ModernText@1.0.0"
KNAPP = "ModernButton@1.0.0"
INMATNING = "ModernTextInput@1.1.2"
KOMBO = "ModernCombobox@1.1.2"
KRYSS = "ModernCheckbox@1.0.2"
GALLERI = "Gallery@2.15.0"
GALLERI_VARIANT = "BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0"
REKTANGEL = "Rectangle@2.3.0"

# ---------- Namnen på SharePoint-listorna ----------
# Formlerna nedan skrivs med de korta namnen till vänster. De byts ut mot namnen till höger
# överallt utom inuti textsträngar ("...").
DATAKALLOR = {
    "Bocker": "glosor_bocker",
    "Kapitel": "glosor_kapitel",
    "Glosor": "glosor_glosor",
    "Gloslistor": "glosor_gloslistor",
}

# ---------- Färgschemat ----------
# Ändra här (och generera om), eller direkt i App.Formulas i appen.
TEMA = [
    ("Primar", "#2F5BD3", "knappar, sidhuvud, länkar"),
    ("PrimarLjus", "#E7EDFC", "tipsruta, markeringar"),
    ("Bakgrund", "#F4F6FB", "skärmarnas bakgrund"),
    ("Yta", "#FFFFFF", "kort/paneler"),
    ("Linje", "#DDE2EC", "ramar och avdelare"),
    ("Brodtext", "#1C2333", "vanlig text"),
    ("TextDampad", "#5B6578", "hjälptexter"),
    ("TextPaPrimar", "#FFFFFF", "text på sidhuvudet"),
    ("Fel", "#C62828", "varningar"),
    ("GenusF", "#D32F2F", "femininum"),
    ("GenusM", "#1F5FD1", "maskulinum"),
    ("GenusN", "#168A3D", "neutrum"),
]

SPRAKVAL = [
    ("en", "Engelska"),
    ("es", "Spanska"),
    ("fr", "Franska"),
    ("de", "Tyska"),
    ("it", "Italienska"),
    ("pt", "Portugisiska"),
    ("la", "Latin"),
    ("fi", "Finska"),
]

GENUS_ARTIKLAR = [
    ("es", ["el", "los", "un"], ["la", "las", "una"], []),
    ("fr", ["le", "un"], ["la", "une"], []),
    ("de", ["der"], ["die", "eine"], ["das"]),
    ("it", ["il", "lo", "un", "uno"], ["la", "una"], []),
    ("pt", ["o", "um"], ["a", "uma"], []),
]


# ---------- Formel-hjälp ----------


def genusfarg(x, standard="Tema.Brodtext"):
    return f'Switch({x}, "f", Tema.GenusF, "m", Tema.GenusM, "n", Tema.GenusN, {standard})'


def genustext(x):
    return f'Switch({x}, "m", "mask.", "f", "fem.", "n", "neutr.", "genus")'


def nasta_genus(x):
    return f'Switch({x}, "m", "f", "f", "n", "n", "", "m")'


def genusforslag(ord_x, sprak_x):
    return (
        f"Coalesce(LookUp(GenusArtiklar, Sprak = {sprak_x} && "
        f'Artikel = Lower(First(Split(Trim({ord_x}), " ")).Value), Genus), "")'
    )


# ---------- Kontroller ----------


def ctl(namn, typ, props, children=None, variant=None):
    return {"namn": namn, "typ": typ, "variant": variant, "props": props, "children": children or []}


def behallare(namn, riktning, children, **p):
    """Container med automatisk layout. riktning: 'v' (lodrät) eller 'h' (vågrät)."""
    props = {
        "LayoutDirection": "LayoutDirection.Vertical" if riktning == "v" else "LayoutDirection.Horizontal",
        "LayoutAlignItems": "LayoutAlignItems.Stretch",
        "LayoutGap": 8,
        "Fill": "RGBA(0, 0, 0, 0)",
        "DropShadow": "DropShadow.None",
    }
    props.update(p)
    return ctl(namn, CONTAINER, props, children, variant="AutoLayout")


def kort(namn, children, **p):
    """Vit panel med ram och rundade hörn."""
    props = dict(
        Fill="Tema.Yta",
        BorderColor="Tema.Linje",
        BorderThickness=1,
        RadiusTopLeft=12,
        RadiusTopRight=12,
        RadiusBottomLeft=12,
        RadiusBottomRight=12,
        PaddingTop=16,
        PaddingBottom=16,
        PaddingLeft=16,
        PaddingRight=16,
        LayoutGap=8,
        LayoutOverflowY="LayoutOverflow.Scroll",
    )
    props.update(p)
    return behallare(namn, "v", children, **props)


def rad(namn, children, hojd=40, **p):
    return behallare(namn, "h", children, Height=hojd, **p)


def text(namn, txt, hojd=28, storlek=12, fet=False, farg="Tema.Brodtext", **p):
    props = {"Text": txt, "Size": storlek, "Color": farg, "Height": hojd}
    if fet:
        props["FontWeight"] = "FontWeight.Semibold" if fet is True else fet
    props.update(p)
    return ctl(namn, TEXT, props)


def rubrik(namn, txt, **p):
    return text(namn, txt, hojd=30, storlek=14, fet=True, **p)


def hjalptext(namn, txt, **p):
    return text(namn, txt, hojd=22, storlek=10, farg="Tema.TextDampad", **p)


def knapp(namn, txt, onselect, sekundar=False, **p):
    props = {
        "Text": txt,
        "OnSelect": onselect,
        "Appearance": "ButtonAppearance.Secondary" if sekundar else "ButtonAppearance.Primary",
        "BasePaletteColor": "Tema.Primar",
        "Height": 40,
    }
    props.update(p)
    return ctl(namn, KNAPP, props)


def inmatning(namn, platshallare="", varde='""', **p):
    props = {"Default": varde, "Placeholder": f'"{platshallare}"', "Height": 40}
    props.update(p)
    return ctl(namn, INMATNING, props)


def kombo(namn, items, visa, platshallare="", flera=False, **p):
    props = {
        "Items": items,
        "ItemDisplayText": visa,
        "SelectMultiple": "true" if flera else "false",
        "InputTextPlaceholder": f'"{platshallare}"',
        "Height": 40,
    }
    props.update(p)
    return ctl(namn, KOMBO, props)


def kryss(namn, etikett, **p):
    props = {"Label": etikett, "Height": 36}
    props.update(p)
    return ctl(namn, KRYSS, props)


def galleri(namn, items, mallhojd, children, **p):
    props = {
        "Items": items,
        "TemplateSize": mallhojd,
        "TemplatePadding": 0,
        "FillPortions": 1,
        "LayoutMinHeight": 160,
        "Fill": "RGBA(0, 0, 0, 0)",
        "BorderThickness": 0,
        "ShowScrollbar": "true",
    }
    props.update(p)
    return ctl(namn, GALLERI, props, children, variant=GALLERI_VARIANT)


def avdelare(namn):
    return ctl(
        namn,
        REKTANGEL,
        {
            "X": 0,
            "Y": "Parent.TemplateHeight - 1",
            "Width": "Parent.TemplateWidth",
            "Height": 1,
            "Fill": "Tema.Linje",
        },
    )


def pos(x, y, w, h):
    return {"X": x, "Y": y, "Width": w, "Height": h}


def skarm(prefix, titel, innehall, hem=True):
    """Hela skärmen: en container som fyller skärmen, med sidhuvud och innehåll."""
    huvud = rad(
        f"con{prefix}Huvud",
        [
            text(
                f"txt{prefix}Titel",
                titel,
                hojd=36,
                storlek=20,
                fet="FontWeight.Bold",
                farg="Tema.TextPaPrimar",
                FillPortions=1,
            ),
            hem
            and knapp(
                f"btn{prefix}Hem",
                '"Start"',
                "Navigate(scrStart, ScreenTransition.None)",
                sekundar=True,
                Width=120,
            ),
        ],
        hojd=64,
        Fill="Tema.Primar",
        LayoutAlignItems="LayoutAlignItems.Center",
        PaddingLeft=24,
        PaddingRight=24,
        LayoutGap=12,
    )
    huvud["children"] = [c for c in huvud["children"] if c]
    return behallare(
        f"con{prefix}",
        "v",
        [huvud, innehall],
        X=0,
        Y=0,
        Width="Parent.Width",
        Height="Parent.Height",
        Fill="Tema.Bakgrund",
        LayoutGap=0,
    )


def kropp(namn, children, riktning="h", **p):
    props = dict(
        FillPortions=1,
        PaddingTop=16,
        PaddingBottom=16,
        PaddingLeft=16,
        PaddingRight=16,
        LayoutGap=16,
    )
    props.update(p)
    return behallare(namn, riktning, children, **props)


# ---------- Skärm 1: Start ----------


def skarm_start():
    val = [
        (
            "Glosor",
            '"Lägg in glosor"',
            '"Skriv in eller klistra in glosor till en bok och ett kapitel. Flera lärare kan fylla på samma kapitel."',
            "Navigate(scrGlosor, ScreenTransition.None)",
        ),
        (
            "NyLista",
            '"Skapa gloslista"',
            '"Välj glosor ur böcker och kapitel, eller slå ihop befintliga listor, och dela listan med eleverna."',
            'Set(varRedigeraLista, Blank());\nSet(varMallNamn, "");\nClear(colValda);\nNavigate(scrNyLista, ScreenTransition.None)',
        ),
        (
            "Listor",
            '"Gloslistor"',
            '"Se dina och andras gloslistor, kopiera länkar till eleverna, redigera eller dölj listor."',
            "Navigate(scrListor, ScreenTransition.None)",
        ),
    ]
    korten = [
        kort(
            f"conStart{n}",
            [
                text(f"txtStart{n}Rubrik", titel, hojd=36, storlek=18, fet="FontWeight.Bold"),
                text(f"txtStart{n}Text", beskr, farg="Tema.TextDampad", FillPortions=1),
                knapp(f"btnStart{n}", '"Öppna"', onselect, Width=150, AlignInContainer="AlignInContainer.Start"),
            ],
            FillPortions=1,
            LayoutMinWidth=220,
            LayoutOverflowY="LayoutOverflow.Hide",
        )
        for n, titel, beskr, onselect in val
    ]
    innehall = kropp(
        "conStartKropp",
        [
            text("txtStartHej", '"Hej " & User().FullName & "! Vad vill du göra?"', hojd=40, storlek=16),
            rad("conStartKort", korten, hojd=240, LayoutGap=16),
            hjalptext("txtStartWebb", '"Elevernas övningssida: " & WebbAdress'),
        ],
        riktning="v",
        PaddingTop=24,
        PaddingLeft=32,
        PaddingRight=32,
    )
    return "scrStart", {"Fill": "Tema.Bakgrund"}, [skarm("Start", '"Glosor – lärarverktyg"', innehall, hem=False)]


# ---------- Skärm 2: Lägg in glosor ----------

TIPS = (
    '"Tips när du skriver glosor' + "\n\n"
    "• Skriv grundform om inget annat ska tränas.\n"
    "• Använd versal i början bara om ordet alltid skrivs så (der Hund).\n"
    "• Skriv gärna artikel på substantiv: la casa, der Hund, das Haus – inte bara casa, Hund, Haus.\n"
    "• Färgmarkera genus med knappen efter ordet: röd = femininum, blå = maskulinum, grön = neutrum. "
    "Appen föreslår färg utifrån artikeln.\n"
    "• Flera godkända svar: skriv / mellan (la casa / el hogar). Valfri del inom parentes: (se) llamar."
    '"'
)

TOLKA = """With(
    {
        rader: Filter(
            Split(Substitute(txtImport.Text, Char(13), ""), Char(10)),
            !IsBlank(Trim(Value))
        ),
        start: Coalesce(Max(colImport, Nr), 0),
        valtSprak: txtGlosSprak.Text
    },
    Collect(
        colImport,
        ForAll(
            Sequence(CountRows(rader)) As n,
            With(
                { rad: Index(rader, n.Value).Value },
                With(
                    {
                        delar: If(
                            !IsBlank(Find(Char(9), rad)), Split(rad, Char(9)),
                            !IsBlank(Find(";", rad)), Split(rad, ";"),
                            !IsBlank(Find(" - ", rad)), Split(rad, " - "),
                            !IsBlank(Find(" = ", rad)), Split(rad, " = "),
                            Split(rad, Char(9))
                        )
                    },
                    With(
                        {
                            mal: Trim(First(delar).Value),
                            sv: If(CountRows(delar) > 1, Trim(Last(delar).Value), "")
                        },
                        {
                            Nr: start + n.Value,
                            Mal: mal,
                            Svenska: sv,
                            Genus: %GENUS%
                        }
                    )
                )
            )
        )
    )
);
Reset(txtImport)""".replace("%GENUS%", genusforslag("mal", "valtSprak"))

LAGG_TILL_EN = """If(
    !IsBlank(Trim(txtMal.Text)),
    Collect(
        colImport,
        {
            Nr: Coalesce(Max(colImport, Nr), 0) + 1,
            Mal: Trim(txtMal.Text),
            Svenska: Trim(txtSv.Text),
            Genus: %GENUS%
        }
    );
    Reset(txtMal);
    Reset(txtSv);
    SetFocus(txtMal)
)""".replace("%GENUS%", genusforslag("txtMal.Text", "txtGlosSprak.Text"))

BYT = """ClearCollect(colImportTmp, colImport);
ClearCollect(
    colImport,
    ForAll(
        colImportTmp As r,
        {
            Nr: r.Nr,
            Mal: r.Svenska,
            Svenska: r.Mal,
            Genus: %GENUS%
        }
    )
);
Clear(colImportTmp)""".replace("%GENUS%", genusforslag("r.Svenska", "txtGlosSprak.Text"))

SPARA_GLOSOR = """With(
    {
        bok: Coalesce(cmbBok.Selected.ID, 0),
        kap: Coalesce(cmbKapitel.Selected.ID, 0),
        valtSprak: txtGlosSprak.Text,
        antal: CountRows(colImport)
    },
    Collect(
        Glosor,
        ForAll(
            colImport As r,
            {
                Title: Trim(r.Mal),
                Svenska: Trim(r.Svenska),
                Genus: r.Genus,
                Sprak: valtSprak,
                BokID: bok,
                KapitelID: kap,
                SkapadAv: User().FullName,
                SkapadAvEpost: User().Email
            }
        )
    );
    If(
        IsEmpty(Errors(Glosor)),
        Notify(antal & " glosor sparades.", NotificationType.Success);
        Clear(colImport),
        Notify("Något gick fel: " & First(Errors(Glosor)).Message, NotificationType.Error)
    )
)"""

SKAPA_BOK = """If(
    !IsBlank(Trim(txtNyBok.Text)) && !IsBlank(cmbNyBokSprak.Selected.Kod),
    Set(
        varBokID,
        Patch(Bocker, Defaults(Bocker), { Title: Trim(txtNyBok.Text), Sprak: cmbNyBokSprak.Selected.Kod }).ID
    );
    Set(varKapitelID, 0);
    Reset(txtNyBok);
    Reset(cmbNyBokSprak);
    Reset(cmbBok);
    Reset(cmbKapitel),
    Notify("Skriv bokens namn och välj språk.", NotificationType.Warning)
)"""

SKAPA_KAPITEL = """If(
    !IsBlank(Trim(txtNyttKapitel.Text)) && !IsBlank(cmbBok.Selected.ID),
    Set(
        varKapitelID,
        Patch(
            Kapitel,
            Defaults(Kapitel),
            {
                Title: Trim(txtNyttKapitel.Text),
                BokID: cmbBok.Selected.ID,
                Ordning: Coalesce(
                    First(Sort(Filter(Kapitel, BokID = cmbBok.Selected.ID), Ordning, SortOrder.Descending)).Ordning,
                    0
                ) + 1
            }
        ).ID
    );
    Reset(txtNyttKapitel);
    Reset(cmbKapitel),
    Notify("Välj bok och skriv kapitlets namn.", NotificationType.Warning)
)"""

BEFINTLIGA = """If(
    !IsBlank(cmbKapitel.Selected.ID),
    Filter(Glosor, KapitelID = cmbKapitel.Selected.ID),
    IsBlank(cmbBok.Selected.ID) && !IsBlank(cmbSprak.Selected.Kod),
    Filter(Glosor, BokID = 0, Sprak = cmbSprak.Selected.Kod),
    Filter(Glosor, ID = -1)
)"""

UTAN_BOK = "IsBlank(cmbBok.Selected.ID)"
KRAVER_BOK = f"If({UTAN_BOK}, DisplayMode.Disabled, DisplayMode.Edit)"


def genusknapp(namn, genus_x, onselect, **p):
    return knapp(
        namn,
        genustext(genus_x),
        onselect,
        Appearance=f"If(IsBlank({genus_x}), ButtonAppearance.Secondary, ButtonAppearance.Primary)",
        BasePaletteColor=genusfarg(genus_x, "Tema.Primar"),
        **p,
    )


def taBortKnapp(namn, onselect, **p):
    return knapp(namn, '"✕"', onselect, Appearance="ButtonAppearance.Subtle", **p)


def skarm_glosor():
    w = "Parent.TemplateWidth"
    bred = f"({w} - 140) / 2"
    imp_rad = [
        inmatning(
            "txtRadMal",
            varde="ThisItem.Mal",
            Color=genusfarg("ThisItem.Genus"),
            OnChange="Patch(colImport, LookUp(colImport, Nr = ThisItem.Nr), { Mal: Self.Text })",
            **pos(4, 4, bred, 40),
        ),
        inmatning(
            "txtRadSv",
            varde="ThisItem.Svenska",
            OnChange="Patch(colImport, LookUp(colImport, Nr = ThisItem.Nr), { Svenska: Self.Text })",
            **pos(f"8 + {bred}", 4, bred, 40),
        ),
        genusknapp(
            "btnRadGenus",
            "ThisItem.Genus",
            f"Patch(colImport, LookUp(colImport, Nr = ThisItem.Nr), {{ Genus: {nasta_genus('ThisItem.Genus')} }})",
            **pos(f"{w} - 124", 6, 78, 36),
        ),
        taBortKnapp(
            "btnRadTaBort",
            "Remove(colImport, LookUp(colImport, Nr = ThisItem.Nr))",
            **pos(f"{w} - 42", 6, 38, 36),
        ),
        avdelare("rectRadLinje"),
    ]
    bef_rad = [
        inmatning(
            "txtBefMal",
            varde="ThisItem.Title",
            Color=genusfarg("ThisItem.Genus"),
            OnChange="Patch(Glosor, ThisItem, { Title: Trim(Self.Text) })",
            **pos(4, 4, bred, 40),
        ),
        inmatning(
            "txtBefSv",
            varde="ThisItem.Svenska",
            OnChange="Patch(Glosor, ThisItem, { Svenska: Trim(Self.Text) })",
            **pos(f"8 + {bred}", 4, bred, 40),
        ),
        genusknapp(
            "btnBefGenus",
            "ThisItem.Genus",
            f"Patch(Glosor, ThisItem, {{ Genus: {nasta_genus('ThisItem.Genus')} }})",
            **pos(f"{w} - 124", 6, 78, 36),
        ),
        taBortKnapp(
            "btnBefTaBort",
            "Remove(Glosor, ThisItem)",
            Visible="ThisItem.SkapadAvEpost = User().Email",
            **pos(f"{w} - 42", 6, 38, 36),
        ),
        avdelare("rectBefLinje"),
    ]

    vanster = kort(
        "conGlosVal",
        [
            # Dold text som håller språkkoden för glosorna som läggs in.
            text(
                "txtGlosSprak",
                f"If({UTAN_BOK}, cmbSprak.Selected.Kod, cmbBok.Selected.Sprak)",
                Visible="false",
            ),
            rubrik("txtBok", '"1. Bok"'),
            kombo(
                "cmbBok",
                "Sort(Bocker, Title)",
                "ThisItem.Title",
                "Välj bok – tomt = fristående glosor",
                DefaultSelectedItems="Filter(Bocker, ID = varBokID)",
                OnChange="Set(varKapitelID, 0);\nReset(cmbKapitel)",
            ),
            rad(
                "conNyBok",
                [
                    inmatning("txtNyBok", "Ny bok…", FillPortions=2),
                    kombo("cmbNyBokSprak", "Sprakval", "ThisItem.Namn", "Språk", FillPortions=1, LayoutMinWidth=110),
                    knapp("btnNyBok", '"Skapa bok"', SKAPA_BOK, sekundar=True, Width=110),
                ],
            ),
            hjalptext(
                "txtBokSprak",
                '"Språk: " & Coalesce(LookUp(Sprakval, Kod = cmbBok.Selected.Sprak).Namn, cmbBok.Selected.Sprak)',
                Visible=f"!{UTAN_BOK}",
            ),
            rubrik("txtKapitel", '"2. Kapitel"'),
            kombo(
                "cmbKapitel",
                "Sort(Filter(Kapitel, BokID = Coalesce(cmbBok.Selected.ID, -1)), Ordning)",
                "ThisItem.Title",
                "Välj kapitel",
                DefaultSelectedItems="Filter(Kapitel, ID = varKapitelID)",
                DisplayMode=KRAVER_BOK,
            ),
            rad(
                "conNyttKapitel",
                [
                    inmatning("txtNyttKapitel", "Nytt kapitel…", FillPortions=1, DisplayMode=KRAVER_BOK),
                    knapp(
                        "btnNyttKapitel",
                        '"Skapa kapitel"',
                        SKAPA_KAPITEL,
                        sekundar=True,
                        Width=130,
                        DisplayMode=KRAVER_BOK,
                    ),
                ],
            ),
            rubrik("txtSprak", '"Språk för fristående glosor"', Visible=UTAN_BOK),
            kombo("cmbSprak", "Sprakval", "ThisItem.Namn", "Välj språk", Visible=UTAN_BOK),
            behallare(
                "conTips",
                "v",
                [text("txtTips", TIPS, storlek=11, FillPortions=1)],
                Height=300,
                Fill="Tema.PrimarLjus",
                PaddingTop=12,
                PaddingBottom=12,
                PaddingLeft=14,
                PaddingRight=14,
                RadiusTopLeft=8,
                RadiusTopRight=8,
                RadiusBottomLeft=8,
                RadiusBottomRight=8,
            ),
        ],
        FillPortions=3,
        LayoutMinWidth=300,
    )

    mitten = kort(
        "conGlosImport",
        [
            rubrik("txtImportRubrik", '"3. Klistra in glosor – en per rad, tabb mellan orden"'),
            inmatning(
                "txtImport",
                "house ⇥ hus (tabb, ; eller - mellan orden)",
                Type="TextInputType.Multiline",
                Height=100,
            ),
            rad(
                "conImportKnappar",
                [
                    knapp("btnTolka", '"Lägg till raderna ↓"', TOLKA, FillPortions=1),
                    knapp("btnByt", '"⇄ Byt plats på språken"', BYT, sekundar=True, FillPortions=1),
                ],
            ),
            rad(
                "conEnGlosa",
                [
                    inmatning("txtMal", "Målspråk, t.ex. la casa", FillPortions=1),
                    inmatning("txtSv", "Svenska, t.ex. huset", FillPortions=1),
                    knapp("btnLaggTill", '"+ Lägg till"', LAGG_TILL_EN, Width=110),
                ],
            ),
            rad(
                "conImportRubriker",
                [
                    hjalptext("txtImpRubMal", '"Målspråk"', FillPortions=1),
                    hjalptext("txtImpRubSv", '"Svenska"', FillPortions=1),
                    hjalptext("txtImpRubGenus", '"Genus"', Width=120),
                ],
                hojd=22,
            ),
            galleri("galImport", "colImport", 48, imp_rad),
            text(
                "txtImportVarning",
                'If(CountRows(Filter(colImport, IsBlank(Trim(Svenska)) || IsBlank(Trim(Mal)))) > 0, "Någon rad saknar ord.", '
                'IsBlank(txtGlosSprak.Text), "Välj bok eller språk först.", '
                f'!{UTAN_BOK} && IsBlank(cmbKapitel.Selected.ID), "Välj kapitel först.", "")',
                hojd=22,
                storlek=10,
                farg="Tema.Fel",
            ),
            knapp(
                "btnSparaGlosor",
                '"Spara " & CountRows(colImport) & " glosor"',
                SPARA_GLOSOR,
                Height=48,
                DisplayMode="If(CountRows(colImport) > 0 && IsBlank(txtImportVarning.Text), DisplayMode.Edit, DisplayMode.Disabled)",
            ),
        ],
        FillPortions=4,
        LayoutMinWidth=380,
    )

    hoger = kort(
        "conGlosBefintliga",
        [
            rubrik("txtBefintliga", '"Redan inlagda här (" & CountRows(galBefintliga.AllItems) & ")"'),
            hjalptext("txtBefintligaInfo", '"Alla lärare kan fylla på samma kapitel. Ändringar sparas direkt."'),
            galleri("galBefintliga", BEFINTLIGA, 48, bef_rad),
        ],
        FillPortions=3,
        LayoutMinWidth=320,
    )

    innehall = kropp("conGlosKropp", [vanster, mitten, hoger])
    return "scrGlosor", {"Fill": "Tema.Bakgrund"}, [skarm("Glos", '"Lägg in glosor"', innehall)]


# ---------- Skärm 3: Skapa / redigera gloslista ----------


def vald_post(x):
    return f"{{ ID: {x}.ID, Title: {x}.Title, Svenska: {x}.Svenska, Genus: {x}.Genus, Sprak: {x}.Sprak }}"


KALLA = """If(
    chkFristaende.Checked,
    Filter(Glosor, BokID = 0, Sprak = cmbLSprak.Selected.Kod),
    Filter(Glosor, KapitelID = Coalesce(cmbLKapitel.Selected.ID, -1))
)"""

LAGG_TILL_LISTOR = """ForAll(
    cmbListor.SelectedItems As lista,
    ForAll(
        Split(lista.GlosaIDs, ";") As idText,
        If(
            !IsBlank(Trim(idText.Value)) && IsBlank(LookUp(colValda, ID = Value(idText.Value))),
            With(
                { g: LookUp(Glosor, ID = Value(idText.Value)) },
                If(!IsBlank(g.ID), Collect(colValda, %POST%))
            )
        )
    )
);
Reset(cmbListor)""".replace("%POST%", vald_post("g"))

SPARA_LISTA = """If(
    IsBlank(varRedigeraLista),
    Set(
        varSparadLista,
        Patch(
            Gloslistor,
            Defaults(Gloslistor),
            {
                Title: Trim(txtListNamn.Text),
                Beskrivning: txtListBeskr.Text,
                Sprak: First(colValda).Sprak,
                LarareNamn: User().FullName,
                LarareEpost: User().Email,
                GlosaIDs: Concat(colValda, Text(ID), ";"),
                Aktiv: true
            }
        )
    ),
    Set(
        varSparadLista,
        Patch(
            Gloslistor,
            LookUp(Gloslistor, ID = varRedigeraLista.ID),
            {
                Title: Trim(txtListNamn.Text),
                Beskrivning: txtListBeskr.Text,
                Sprak: First(colValda).Sprak,
                GlosaIDs: Concat(colValda, Text(ID), ";")
            }
        )
    )
);
If(
    IsEmpty(Errors(Gloslistor)),
    Set(varRedigeraLista, varSparadLista);
    Notify("Gloslistan sparades. Kopiera länken och dela med eleverna.", NotificationType.Success),
    Notify("Något gick fel: " & First(Errors(Gloslistor)).Message, NotificationType.Error)
)"""


def skarm_ny_lista():
    w = "Parent.TemplateWidth"
    kalla_rad = [
        kryss(
            "chkGlosa",
            '""',
            Checked="!IsBlank(LookUp(colValda, ID = ThisItem.ID))",
            OnCheck=f"If(IsBlank(LookUp(colValda, ID = ThisItem.ID)), Collect(colValda, {vald_post('ThisItem')}))",
            OnUncheck="RemoveIf(colValda, ID = ThisItem.ID)",
            **pos(8, 6, 40, 36),
        ),
        text(
            "txtKMal",
            "ThisItem.Title",
            fet=True,
            farg=genusfarg("ThisItem.Genus"),
            **pos(52, 10, f"({w} - 60) / 2", 28),
        ),
        text("txtKSv", "ThisItem.Svenska", **pos(f"56 + ({w} - 60) / 2", 10, f"({w} - 60) / 2", 28)),
        avdelare("rectKLinje"),
    ]
    vald_rad = [
        text(
            "txtVMal",
            "ThisItem.Title",
            fet=True,
            farg=genusfarg("ThisItem.Genus"),
            **pos(8, 8, f"({w} - 60) / 2", 28),
        ),
        text("txtVSv", "ThisItem.Svenska", **pos(f"12 + ({w} - 60) / 2", 8, f"({w} - 60) / 2", 28)),
        taBortKnapp("btnVTaBort", "RemoveIf(colValda, ID = ThisItem.ID)", **pos(f"{w} - 42", 4, 38, 36)),
        avdelare("rectVLinje"),
    ]
    lank = 'WebbAdress & "?lista=" & varSparadLista.ID'
    fristaende = "chkFristaende.Checked"
    ej_fristaende = f"If({fristaende}, DisplayMode.Disabled, DisplayMode.Edit)"

    vanster = kort(
        "conNyLKalla",
        [
            rubrik("txtNyLSteg1", '"1. Välj glosor"'),
            rad(
                "conNyLBokKapitel",
                [
                    kombo(
                        "cmbLBok",
                        "Sort(Bocker, Title)",
                        "ThisItem.Title",
                        "Bok",
                        FillPortions=1,
                        OnChange="Reset(cmbLKapitel)",
                        DisplayMode=ej_fristaende,
                    ),
                    kombo(
                        "cmbLKapitel",
                        "Sort(Filter(Kapitel, BokID = Coalesce(cmbLBok.Selected.ID, -1)), Ordning)",
                        "ThisItem.Title",
                        "Kapitel",
                        FillPortions=1,
                        DisplayMode=ej_fristaende,
                    ),
                ],
            ),
            rad(
                "conNyLFristaende",
                [
                    kryss("chkFristaende", '"Fristående glosor (utan bok)"', FillPortions=1),
                    kombo("cmbLSprak", "Sprakval", "ThisItem.Namn", "Språk", FillPortions=1, Visible=fristaende),
                ],
            ),
            rad(
                "conNyLMarkera",
                [
                    knapp(
                        "btnMarkeraAlla",
                        '"Markera alla"',
                        f"Collect(colValda, ForAll(Filter(galKalla.AllItems, !(ID in colValda.ID)) As g, {vald_post('g')}))",
                        sekundar=True,
                        Width=150,
                    ),
                    knapp(
                        "btnAvmarkeraAlla",
                        '"Avmarkera alla"',
                        "RemoveIf(colValda, ID in galKalla.AllItems.ID)",
                        sekundar=True,
                        Width=150,
                    ),
                ],
            ),
            galleri("galKalla", KALLA, 48, kalla_rad),
            rubrik("txtNyLListor", '"…eller slå ihop befintliga gloslistor"'),
            rad(
                "conNyLListor",
                [
                    kombo(
                        "cmbListor",
                        "Sort(Gloslistor, Title)",
                        "ThisItem.Title",
                        "Välj en eller flera listor",
                        flera=True,
                        FillPortions=1,
                    ),
                    knapp("btnLaggTillListor", '"Lägg till glosorna"', LAGG_TILL_LISTOR, sekundar=True, Width=170),
                ],
            ),
            hjalptext(
                "txtNyLListorInfo",
                '"Glosorna återanvänds – inget dupliceras. Samma glosa läggs bara till en gång."',
            ),
        ],
        FillPortions=1,
        LayoutMinWidth=420,
    )

    hoger = kort(
        "conNyLLista",
        [
            rubrik("txtNyLSteg2", '"2. Din gloslista"'),
            inmatning(
                "txtListNamn",
                "Namn, t.ex. Kapitel 3 glosor",
                varde="If(IsBlank(varRedigeraLista), varMallNamn, varRedigeraLista.Title)",
            ),
            inmatning(
                "txtListBeskr",
                "Beskrivning (valfri), t.ex. Prov fredag v. 12",
                varde='If(IsBlank(varRedigeraLista), "", varRedigeraLista.Beskrivning)',
            ),
            rad(
                "conNyLValdaRubrik",
                [
                    rubrik("txtValda", '"Valda glosor (" & CountRows(colValda) & ")"', FillPortions=1),
                    knapp("btnTomLista", '"Töm"', "Clear(colValda)", sekundar=True, Width=90),
                ],
            ),
            galleri("galValda", "colValda", 44, vald_rad),
            knapp(
                "btnSparaLista",
                'If(IsBlank(varRedigeraLista), "Spara gloslista", "Spara ändringar")',
                SPARA_LISTA,
                Height=48,
                DisplayMode="If(CountRows(colValda) > 0 && !IsBlank(Trim(txtListNamn.Text)), DisplayMode.Edit, DisplayMode.Disabled)",
            ),
            rad(
                "conNyLLank",
                [
                    text("txtLank", '"Länk till eleverna: " & ' + lank, hojd=40, farg="Tema.Primar", FillPortions=1),
                    knapp(
                        "btnKopieraLank",
                        '"Kopiera länk"',
                        f'Copy({lank});\nNotify("Länken är kopierad.", NotificationType.Success)',
                        sekundar=True,
                        Width=140,
                    ),
                ],
                Visible="!IsBlank(varSparadLista)",
            ),
        ],
        FillPortions=1,
        LayoutMinWidth=420,
    )

    innehall = kropp("conNyLKropp", [vanster, hoger])
    return (
        "scrNyLista",
        {
            "Fill": "Tema.Bakgrund",
            "OnVisible": "Set(varSparadLista, varRedigeraLista);\nReset(txtListNamn);\nReset(txtListBeskr)",
        },
        [skarm("NyL", 'If(IsBlank(varRedigeraLista), "Skapa gloslista", "Redigera gloslista")', innehall)],
    )


# ---------- Skärm 4: Gloslistor ----------

LADDA_VALDA = """Clear(colValda);
ForAll(
    Split(ThisItem.GlosaIDs, ";") As idText,
    If(
        !IsBlank(Trim(idText.Value)) && IsBlank(LookUp(colValda, ID = Value(idText.Value))),
        With(
            { g: LookUp(Glosor, ID = Value(idText.Value)) },
            If(!IsBlank(g.ID), Collect(colValda, %POST%))
        )
    )
);""".replace("%POST%", vald_post("g"))


def skarm_listor():
    w = "Parent.TemplateWidth"
    egen = "ThisItem.LarareEpost = User().Email"
    antal = 'CountRows(Filter(Split(ThisItem.GlosaIDs, ";"), !IsBlank(Trim(Value))))'
    lank = 'WebbAdress & "?lista=" & ThisItem.ID'
    textbredd = f"Max(200, {w} - 720)"
    rad_ = [
        text(
            "txtLTitel",
            "ThisItem.Title",
            storlek=14,
            fet="FontWeight.Bold",
            farg="If(ThisItem.Aktiv, Tema.Brodtext, Tema.TextDampad)",
            **pos(16, 10, textbredd, 30),
        ),
        text(
            "txtLMeta",
            f'ThisItem.LarareNamn & " · " & {antal} & " glosor · " & '
            "Coalesce(LookUp(Sprakval, Kod = ThisItem.Sprak).Namn, ThisItem.Sprak) & "
            'If(ThisItem.Aktiv, "", " · DOLD för eleverna")'
            ' & If(IsBlank(ThisItem.Beskrivning), "", " · " & ThisItem.Beskrivning)',
            storlek=11,
            farg="Tema.TextDampad",
            **pos(16, 40, textbredd, 24),
        ),
        text("txtLLank", lank, storlek=10, farg="Tema.Primar", **pos(16, 64, textbredd, 22)),
        knapp(
            "btnLKopiera",
            '"Kopiera länk"',
            f'Copy({lank});\nNotify("Länken är kopierad.", NotificationType.Success)',
            sekundar=True,
            **pos(f"{w} - 690", 26, 125, 40),
        ),
        knapp(
            "btnLRedigera",
            '"Redigera"',
            LADDA_VALDA + "\nSet(varRedigeraLista, ThisItem);\nNavigate(scrNyLista, ScreenTransition.None)",
            sekundar=True,
            Visible=egen,
            **pos(f"{w} - 555", 26, 105, 40),
        ),
        knapp(
            "btnLMall",
            '"Använd som mall"',
            LADDA_VALDA
            + '\nSet(varRedigeraLista, Blank());\nSet(varMallNamn, "Kopia av " & ThisItem.Title);\n'
            "Navigate(scrNyLista, ScreenTransition.None)",
            sekundar=True,
            **pos(f"{w} - 440", 26, 140, 40),
        ),
        knapp(
            "btnLAktiv",
            'If(ThisItem.Aktiv, "Dölj", "Visa")',
            "Patch(Gloslistor, ThisItem, { Aktiv: !ThisItem.Aktiv })",
            sekundar=True,
            Visible=egen,
            **pos(f"{w} - 290", 26, 90, 40),
        ),
        knapp(
            "btnLTaBort",
            'If(varTaBortID = ThisItem.ID, "Bekräfta!", "Ta bort")',
            "If(\n    varTaBortID = ThisItem.ID,\n    Remove(Gloslistor, ThisItem);\n    Set(varTaBortID, 0),\n"
            "    Set(varTaBortID, ThisItem.ID)\n)",
            Appearance='If(varTaBortID = ThisItem.ID, ButtonAppearance.Primary, ButtonAppearance.Secondary)',
            BasePaletteColor="Tema.Fel",
            Visible=egen,
            **pos(f"{w} - 190", 26, 170, 40),
        ),
        avdelare("rectLLinje"),
    ]
    innehall = kropp(
        "conLisKropp",
        [
            rad(
                "conLisVerktyg",
                [
                    kryss("chkAllaListor", '"Visa alla lärares listor"', FillPortions=1),
                    knapp(
                        "btnLisNy",
                        '"+ Ny gloslista"',
                        'Set(varRedigeraLista, Blank());\nSet(varMallNamn, "");\nClear(colValda);\n'
                        "Navigate(scrNyLista, ScreenTransition.None)",
                        Width=180,
                    ),
                ],
                LayoutAlignItems="LayoutAlignItems.Center",
            ),
            kort(
                "conLisLista",
                [
                    galleri(
                        "galListor",
                        "Sort(\n    If(chkAllaListor.Checked, Gloslistor, Filter(Gloslistor, LarareEpost = User().Email)),\n"
                        "    ID,\n    SortOrder.Descending\n)",
                        92,
                        rad_,
                    )
                ],
                FillPortions=1,
                PaddingTop=4,
                PaddingBottom=4,
            ),
        ],
        riktning="v",
    )
    return "scrListor", {"Fill": "Tema.Bakgrund", "OnVisible": "Set(varTaBortID, 0)"}, [
        skarm("Lis", '"Gloslistor"', innehall)
    ]


# ---------- App.Formulas ----------


def app_formulas():
    r = [
        "// Klistra in i App → egenskapen Formulas (välj App i trädvyn, sedan Formulas i listan uppe till vänster).",
        "",
        "// Adressen till elevernas övningssida. Används för länkarna till gloslistorna.",
        'WebbAdress = "https://fjellandermedia.github.io/glosor/";',
        "",
        "// Färgschemat. Alla färger i appen hämtas härifrån – ändra en färgkod så ändras hela appen.",
        "Tema = {",
    ]
    for i, (namn, hex_, beskr) in enumerate(TEMA):
        komma = "," if i < len(TEMA) - 1 else ""
        r.append(f'    {namn}: ColorValue("{hex_}"){komma}    // {beskr}')
    r += ["};", "", "Sprakval = Table("]
    for i, (kod, namn) in enumerate(SPRAKVAL):
        komma = "," if i < len(SPRAKVAL) - 1 else ""
        r.append(f'    {{ Kod: "{kod}", Namn: "{namn}" }}{komma}')
    r += [
        ");",
        "",
        "// Förslag på genus utifrån språk och artikel. m = maskulinum, f = femininum, n = neutrum.",
        "GenusArtiklar = Table(",
    ]
    poster = []
    for sprak, m, f, n in GENUS_ARTIKLAR:
        for genus, artiklar in (("m", m), ("f", f), ("n", n)):
            for a in artiklar:
                poster.append(f'    {{ Sprak: "{sprak}", Artikel: "{a}", Genus: "{genus}" }}')
    r += [p + ("," if i < len(poster) - 1 else "") for i, p in enumerate(poster)]
    r += [");"]
    return "\n".join(r) + "\n"


def till_svensk_syntax(kod):
    """, -> ; och ; -> ;; utanför kommentarer och textsträngar."""
    ut = []
    for rad_ in kod.split("\n"):
        if rad_.lstrip().startswith("//"):
            ut.append(rad_)
            continue
        kodbit, sep, kommentar = rad_.partition("    //")
        delar = re.split(r'("(?:[^"]|"")*")', kodbit)
        for i in range(0, len(delar), 2):
            delar[i] = delar[i].replace(";", ";;").replace(",", ";")
        ut.append("".join(delar) + sep + kommentar)
    return "\n".join(ut)


# ---------- YAML-utskrift ----------

_STRANG = re.compile(r'"(?:[^"]|"")*"')
_KALLA = re.compile(r"\b(" + "|".join(DATAKALLOR) + r")\b")


def byt_datakallor(formel):
    delar = []
    pos_ = 0
    for m in _STRANG.finditer(formel):
        delar.append(_KALLA.sub(lambda x: DATAKALLOR[x.group(1)], formel[pos_ : m.start()]))
        delar.append(m.group(0))
        pos_ = m.end()
    delar.append(_KALLA.sub(lambda x: DATAKALLOR[x.group(1)], formel[pos_:]))
    return "".join(delar)


def varde(v):
    return "=" + byt_datakallor(str(v))


def skriv_varde(rader, nyckel, v, indrag):
    s = varde(v)
    pad = " " * indrag
    if "\n" in s or any(t in s for t in (": ", " #", "\t")) or s.endswith(":"):
        rader.append(f"{pad}{nyckel}: |-")
        for r in s.split("\n"):
            rader.append(f"{pad}  {r}" if r else "")
    else:
        rader.append(f"{pad}{nyckel}: {s}")


def skriv_kontroll(rader, k, indrag):
    pad = " " * indrag
    rader.append(f"{pad}- {k['namn']}:")
    rader.append(f"{pad}    Control: {k['typ']}")
    if k["variant"]:
        rader.append(f"{pad}    Variant: {k['variant']}")
    rader.append(f"{pad}    Properties:")
    for nyckel, v in k["props"].items():
        skriv_varde(rader, nyckel, v, indrag + 6)
    if k["children"]:
        rader.append(f"{pad}    Children:")
        for barn in k["children"]:
            skriv_kontroll(rader, barn, indrag + 6)


def skriv_skarm(namn, props, kontroller):
    rader = ["Screens:", f"  {namn}:", "    Properties:"]
    for nyckel, v in props.items():
        skriv_varde(rader, nyckel, v, 6)
    rader.append("    Children:")
    for k in kontroller:
        skriv_kontroll(rader, k, 6)
    return "\n".join(rader) + "\n"


def skriv_kontroller(kontroller):
    rader = []
    for k in kontroller:
        skriv_kontroll(rader, k, 0)
    return "\n".join(rader) + "\n"


def kontrollera_unika(skarmar):
    sedda = {}

    def ga(k, skarm_):
        if k["namn"] in sedda:
            raise SystemExit(f"Dubbelt kontrollnamn: {k['namn']} ({skarm_} och {sedda[k['namn']]})")
        sedda[k["namn"]] = skarm_
        for b in k["children"]:
            ga(b, skarm_)

    for namn, _, kontroller in skarmar:
        if namn in sedda:
            raise SystemExit(f"Dubbelt namn: {namn}")
        sedda[namn] = namn
        for k in kontroller:
            ga(k, namn)


def main():
    skarmar = [skarm_start(), skarm_glosor(), skarm_ny_lista(), skarm_listor()]
    kontrollera_unika(skarmar)
    (UT / "kontroller").mkdir(parents=True, exist_ok=True)
    for i, (namn, props, kontroller) in enumerate(skarmar, 1):
        fil = UT / f"{i}-{namn}.yaml"
        fil.write_text(skriv_skarm(namn, props, kontroller), encoding="utf-8")
        (UT / "kontroller" / f"{i}-{namn}.yaml").write_text(skriv_kontroller(kontroller), encoding="utf-8")
        print("skrev", fil.relative_to(ROT))
    formler = app_formulas()
    (UT / "App.Formulas.txt").write_text(formler, encoding="utf-8")
    sv = (
        "// Svensk version: semikolon mellan argument och dubbelsemikolon mellan formlerna.\n"
        "// Använd den här om Power Apps Studio är på svenska. Annars: App.Formulas.txt.\n"
        + till_svensk_syntax(formler)
    )
    (UT / "App.Formulas.sv.txt").write_text(sv, encoding="utf-8")
    print("skrev powerapps/App.Formulas.txt och App.Formulas.sv.txt")


if __name__ == "__main__":
    main()
