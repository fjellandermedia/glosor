#!/usr/bin/env python3
"""Genererar YAML-koden för lärarappen i Power Apps (powerapps/*.yaml).

Kör:  python3 tools/generera_powerapps.py

Varje skärm skrivs i två varianter:
  powerapps/<skärm>.yaml           hela skärmen ("Screens:" ...), klistras in i trädvyn
  powerapps/kontroller/<skärm>.yaml bara kontrollerna, om du hellre klistrar in dem på en tom skärm
"""
from pathlib import Path

ROT = Path(__file__).resolve().parent.parent
UT = ROT / "powerapps"

# ---------- Färger ----------
BG = "RGBA(244, 246, 251, 1)"
ACCENT = "RGBA(47, 91, 211, 1)"
ACCENT_LJUS = "RGBA(231, 237, 252, 1)"
TEXT = "RGBA(28, 35, 51, 1)"
DAMPAD = "RGBA(91, 101, 120, 1)"
VIT = "RGBA(255, 255, 255, 1)"
LINJE = "RGBA(221, 226, 236, 1)"
GRA = "RGBA(230, 233, 240, 1)"
ROD = "RGBA(198, 40, 40, 1)"
GRON = "RGBA(23, 128, 61, 1)"


def genusfarg(uttryck, standard=TEXT):
    return (
        f'Switch({uttryck}, "f", RGBA(211, 47, 47, 1), "m", RGBA(31, 95, 209, 1), '
        f'"n", RGBA(22, 138, 61, 1), {standard})'
    )


def genusknapptext(uttryck):
    return f'Switch({uttryck}, "m", "mask.", "f", "fem.", "n", "neutr.", "genus")'


def nasta_genus(uttryck):
    return f'Switch({uttryck}, "m", "f", "f", "n", "n", "", "m")'


def genusforslag(ord_uttryck, sprak_uttryck):
    return (
        f"Coalesce(LookUp(GenusArtiklar, Sprak = {sprak_uttryck} && "
        f'Artikel = Lower(First(Split(Trim({ord_uttryck}), " ")).Value), Genus), "")'
    )


# ---------- Kontroller ----------


def ctl(namn, typ, props, children=None, variant=None):
    return {"namn": namn, "typ": typ, "variant": variant, "props": props, "children": children or []}


def pos(x, y, w, h):
    return {"X": x, "Y": y, "Width": w, "Height": h}


def label(namn, text, x, y, w, h, **p):
    props = {"Text": text, **pos(x, y, w, h), "Color": TEXT, "Size": 12}
    props.update(p)
    return ctl(namn, "Label@2.5.1", props)


def rubrik(namn, text, x, y, w, h=30, **p):
    return label(namn, text, x, y, w, h, FontWeight="FontWeight.Semibold", Size=13, **p)


def knapp(namn, text, x, y, w, h, onselect, sekundar=False, **p):
    props = {
        "Text": text,
        **pos(x, y, w, h),
        "OnSelect": onselect,
        "Fill": VIT if sekundar else ACCENT,
        "Color": ACCENT if sekundar else VIT,
        "HoverFill": ACCENT_LJUS if sekundar else "ColorFade(Self.Fill, -15%)",
        "HoverColor": ACCENT if sekundar else VIT,
        "PressedFill": ACCENT_LJUS if sekundar else "ColorFade(Self.Fill, -25%)",
        "BorderColor": ACCENT,
        "BorderThickness": 2,
        "RadiusTopLeft": 8,
        "RadiusTopRight": 8,
        "RadiusBottomLeft": 8,
        "RadiusBottomRight": 8,
        "Size": 12,
        "FontWeight": "FontWeight.Semibold",
    }
    props.update(p)
    return ctl(namn, "Classic/Button@2.2.0", props)


def textruta(namn, x, y, w, h, hint="", default='""', **p):
    props = {
        "Default": default,
        "HintText": f'"{hint}"',
        **pos(x, y, w, h),
        "Size": 12,
        "BorderColor": LINJE,
        "RadiusTopLeft": 6,
        "RadiusTopRight": 6,
        "RadiusBottomLeft": 6,
        "RadiusBottomRight": 6,
    }
    props.update(p)
    return ctl(namn, "Classic/TextInput@2.3.2", props)


def kombobox(namn, items, falt, x, y, w, h=40, platshallare="", flera=False, **p):
    props = {
        "Items": items,
        "DisplayFields": f'["{falt}"]',
        "SearchFields": f'["{falt}"]',
        "SelectMultiple": "true" if flera else "false",
        "InputTextPlaceholder": f'"{platshallare}"',
        **pos(x, y, w, h),
    }
    props.update(p)
    return ctl(namn, "Classic/ComboBox@2.4.0", props)


def kryssruta(namn, text, x, y, w, h, **p):
    props = {"Text": text, **pos(x, y, w, h), "Size": 12, "Color": TEXT, "CheckboxBorderColor": ACCENT}
    props.update(p)
    return ctl(namn, "Classic/CheckBox@2.1.0", props)


def rektangel(namn, x, y, w, h, fill, **p):
    props = {**pos(x, y, w, h), "Fill": fill}
    props.update(p)
    return ctl(namn, "Rectangle@2.3.0", props)


def galleri(namn, items, x, y, w, h, mallhojd, children, **p):
    props = {
        "Items": items,
        **pos(x, y, w, h),
        "TemplateSize": mallhojd,
        "TemplatePadding": 0,
        "Fill": VIT,
        "BorderColor": LINJE,
        "BorderThickness": 1,
        "ShowScrollbar": "true",
    }
    props.update(p)
    return ctl(namn, "Gallery@2.15.0", props, children, variant="Vertical")


def sidhuvud(prefix, titel):
    return [
        rektangel(f"rect{prefix}Huvud", 0, 0, "Parent.Width", 64, ACCENT),
        label(f"lbl{prefix}Titel", titel, 24, 0, 800, 64, Color=VIT, Size=20, FontWeight="FontWeight.Bold"),
        knapp(
            f"btn{prefix}Hem",
            '"⌂ Start"',
            "Parent.Width - 150",
            12,
            130,
            40,
            "Navigate(scrStart, ScreenTransition.None)",
            sekundar=True,
        ),
    ]


def rad_separator(namn, w):
    return rektangel(namn, 0, "Parent.TemplateHeight - 1", w, 1, LINJE)


# ---------- Skärm: Start ----------


def skarm_start():
    kort = []
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
            "Set(varRedigeraLista, Blank());\nSet(varMallNamn, \"\");\nClear(colValda);\nNavigate(scrNyLista, ScreenTransition.None)",
        ),
        (
            "Listor",
            '"Gloslistor"',
            '"Se dina och andras gloslistor, kopiera länkar till eleverna, redigera eller dölj listor."',
            "Navigate(scrListor, ScreenTransition.None)",
        ),
    ]
    for i, (n, titel, text, onselect) in enumerate(val):
        x = f"40 + {i} * ((Parent.Width - 120) / 3 + 20)"
        w = "(Parent.Width - 120) / 3"
        kort += [
            rektangel(
                f"rectStart{n}",
                x,
                170,
                w,
                230,
                VIT,
                BorderColor=LINJE,
                BorderThickness=1,
            ),
            label(f"lblStart{n}Rubrik", titel, f"{x} + 24", 190, f"{w} - 48", 40, Size=18, FontWeight="FontWeight.Bold"),
            label(
                f"lblStart{n}Text",
                text,
                f"{x} + 24",
                235,
                f"{w} - 48",
                90,
                Color=DAMPAD,
                VerticalAlign="VerticalAlign.Top",
            ),
            knapp(f"btnStart{n}", '"Öppna"', f"{x} + 24", 335, 150, 44, onselect),
        ]
    kontroller = [
        rektangel("rectStartHuvud", 0, 0, "Parent.Width", 64, ACCENT),
        label("lblStartTitel", '"Glosor – lärarverktyg"', 24, 0, 800, 64, Color=VIT, Size=20, FontWeight="FontWeight.Bold"),
        label(
            "lblStartHej",
            '"Hej " & User().FullName & "! Vad vill du göra?"',
            40,
            100,
            "Parent.Width - 80",
            50,
            Size=16,
        ),
        *kort,
        label(
            "lblStartWebb",
            '"Elevernas övningssida: " & WebbAdress',
            40,
            430,
            "Parent.Width - 80",
            30,
            Color=DAMPAD,
            Size=11,
        ),
    ]
    return "scrStart", {"Fill": BG}, kontroller


# ---------- Skärm: Lägg in glosor ----------

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
        valtSprak: lblGlosSprak.Text
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
)""".replace("%GENUS%", genusforslag("txtMal.Text", "lblGlosSprak.Text"))

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
Clear(colImportTmp)""".replace("%GENUS%", genusforslag("r.Svenska", "lblGlosSprak.Text"))

SPARA_GLOSOR = """With(
    {
        bok: Coalesce(cmbBok.Selected.ID, 0),
        kap: Coalesce(cmbKapitel.Selected.ID, 0),
        valtSprak: lblGlosSprak.Text,
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


def skarm_glosor():
    L, M_, R = 20, 440, 920  # vänster-, mitt- och högerkolumn
    imp_rad = [
        textruta(
            "txtRadMal",
            0,
            4,
            175,
            38,
            default="ThisItem.Mal",
            Color=genusfarg("ThisItem.Genus"),
            FontWeight="FontWeight.Semibold",
            OnChange="Patch(colImport, LookUp(colImport, Nr = ThisItem.Nr), { Mal: Self.Text })",
        ),
        textruta(
            "txtRadSv",
            180,
            4,
            150,
            38,
            default="ThisItem.Svenska",
            OnChange="Patch(colImport, LookUp(colImport, Nr = ThisItem.Nr), { Svenska: Self.Text })",
            BorderColor=f'If(IsBlank(Trim(ThisItem.Svenska)), {ROD}, {LINJE})',
        ),
        knapp(
            "btnRadGenus",
            genusknapptext("ThisItem.Genus"),
            335,
            6,
            75,
            34,
            f"Patch(colImport, LookUp(colImport, Nr = ThisItem.Nr), {{ Genus: {nasta_genus('ThisItem.Genus')} }})",
            Fill=genusfarg("ThisItem.Genus", GRA),
            Color=f'If(IsBlank(ThisItem.Genus), {DAMPAD}, {VIT})',
            BorderThickness=0,
            Size=10,
            HoverFill="ColorFade(Self.Fill, -15%)",
            HoverColor="Self.Color",
            PressedFill="ColorFade(Self.Fill, -25%)",
        ),
        knapp(
            "btnRadTaBort",
            '"✕"',
            415,
            6,
            34,
            34,
            "Remove(colImport, LookUp(colImport, Nr = ThisItem.Nr))",
            sekundar=True,
            BorderThickness=0,
            Color=ROD,
            HoverColor=ROD,
        ),
        rad_separator("rectRadLinje", "Parent.TemplateWidth"),
    ]
    bef_rad = [
        textruta(
            "txtBefMal",
            6,
            4,
            150,
            36,
            default="ThisItem.Title",
            Color=genusfarg("ThisItem.Genus"),
            FontWeight="FontWeight.Semibold",
            OnChange="Patch(Glosor, ThisItem, { Title: Trim(Self.Text) })",
            BorderThickness=0,
        ),
        textruta(
            "txtBefSv",
            160,
            4,
            135,
            36,
            default="ThisItem.Svenska",
            OnChange="Patch(Glosor, ThisItem, { Svenska: Trim(Self.Text) })",
            BorderThickness=0,
        ),
        knapp(
            "btnBefGenus",
            genusknapptext("ThisItem.Genus"),
            298,
            6,
            70,
            32,
            f"Patch(Glosor, ThisItem, {{ Genus: {nasta_genus('ThisItem.Genus')} }})",
            Fill=genusfarg("ThisItem.Genus", GRA),
            Color=f'If(IsBlank(ThisItem.Genus), {DAMPAD}, {VIT})',
            BorderThickness=0,
            Size=10,
            HoverFill="ColorFade(Self.Fill, -15%)",
            HoverColor="Self.Color",
            PressedFill="ColorFade(Self.Fill, -25%)",
        ),
        knapp(
            "btnBefTaBort",
            '"✕"',
            372,
            6,
            32,
            32,
            "Remove(Glosor, ThisItem)",
            sekundar=True,
            BorderThickness=0,
            Color=ROD,
            HoverColor=ROD,
            Visible="ThisItem.SkapadAvEpost = User().Email",
            Tooltip='"Ta bort glosan (bara dina egna)"',
        ),
        rad_separator("rectBefLinje", "Parent.TemplateWidth"),
    ]
    kontroller = [
        *sidhuvud("Glos", '"Lägg in glosor"'),
        # Dold etikett som håller språkkoden för glosorna som läggs in.
        label(
            "lblGlosSprak",
            "If(IsBlank(cmbBok.Selected.ID), cmbSprak.Selected.Kod, cmbBok.Selected.Sprak)",
            0,
            0,
            10,
            10,
            Visible="false",
        ),
        # ----- Vänster: bok, kapitel, språk, tips -----
        rubrik("lblBok", '"1. Bok"', L, 76, 400),
        kombobox(
            "cmbBok",
            "Sort(Bocker, Title)",
            "Title",
            L,
            104,
            400,
            platshallare="Välj bok – lämna tomt för fristående glosor",
            DefaultSelectedItems="Filter(Bocker, ID = varBokID)",
            OnChange="Set(varKapitelID, 0);\nReset(cmbKapitel)",
        ),
        textruta("txtNyBok", L, 150, 175, 36, hint="Ny bok…"),
        kombobox("cmbNyBokSprak", "Sprakval", "Namn", L + 180, 150, 120, h=36, platshallare="Språk"),
        knapp("btnNyBok", '"Skapa bok"', L + 305, 150, 95, 36, SKAPA_BOK, sekundar=True, Size=10),
        label(
            "lblBokSprak",
            '"Språk: " & Coalesce(LookUp(Sprakval, Kod = cmbBok.Selected.Sprak).Namn, cmbBok.Selected.Sprak)',
            L,
            190,
            400,
            26,
            Color=DAMPAD,
            Size=11,
            Visible="!IsBlank(cmbBok.Selected.ID)",
        ),
        rubrik("lblKapitel", '"2. Kapitel"', L, 222, 400),
        kombobox(
            "cmbKapitel",
            "Sort(Filter(Kapitel, BokID = Coalesce(cmbBok.Selected.ID, -1)), Ordning)",
            "Title",
            L,
            250,
            400,
            platshallare="Välj kapitel",
            DefaultSelectedItems="Filter(Kapitel, ID = varKapitelID)",
            DisplayMode="If(IsBlank(cmbBok.Selected.ID), DisplayMode.Disabled, DisplayMode.Edit)",
        ),
        textruta(
            "txtNyttKapitel",
            L,
            296,
            300,
            36,
            hint="Nytt kapitel…",
            DisplayMode="If(IsBlank(cmbBok.Selected.ID), DisplayMode.Disabled, DisplayMode.Edit)",
        ),
        knapp(
            "btnNyttKapitel",
            '"Skapa kapitel"',
            L + 305,
            296,
            95,
            36,
            SKAPA_KAPITEL,
            sekundar=True,
            Size=10,
            DisplayMode="If(IsBlank(cmbBok.Selected.ID), DisplayMode.Disabled, DisplayMode.Edit)",
        ),
        rubrik(
            "lblSprak",
            '"Språk för fristående glosor"',
            L,
            342,
            400,
            Visible="IsBlank(cmbBok.Selected.ID)",
        ),
        kombobox(
            "cmbSprak",
            "Sprakval",
            "Namn",
            L,
            370,
            400,
            platshallare="Välj språk",
            Visible="IsBlank(cmbBok.Selected.ID)",
        ),
        label(
            "lblTips",
            TIPS,
            L,
            425,
            400,
            320,
            Fill=ACCENT_LJUS,
            Size=11,
            VerticalAlign="VerticalAlign.Top",
            PaddingTop=12,
            PaddingLeft=14,
            PaddingRight=14,
        ),
        # ----- Mitten: in-matning -----
        rubrik("lblImport", '"3. Klistra in glosor – en per rad, tabb mellan orden"', M_, 76, 460),
        textruta(
            "txtImport",
            M_,
            104,
            460,
            100,
            Mode="TextMode.MultiLine",
            HintText='"house → hus (tabb mellan orden)" & Char(10) & "dog → hund" & Char(10) & "Fungerar också med ; eller - mellan."',
        ),
        knapp("btnTolka", '"Lägg till raderna ↓"', M_, 210, 220, 38, TOLKA),
        knapp("btnByt", '"⇄ Byt plats på språken"', M_ + 240, 210, 220, 38, BYT, sekundar=True),
        textruta("txtMal", M_, 256, 175, 38, hint="Målspråk, t.ex. la casa"),
        textruta("txtSv", M_ + 180, 256, 200, 38, hint="Svenska, t.ex. huset"),
        knapp("btnLaggTill", '"+ Lägg till"', M_ + 385, 256, 75, 38, LAGG_TILL_EN, Size=10),
        label("lblImpRubMal", '"Målspråk"', M_, 300, 175, 24, Color=DAMPAD, Size=10),
        label("lblImpRubSv", '"Svenska"', M_ + 180, 300, 150, 24, Color=DAMPAD, Size=10),
        label("lblImpRubGenus", '"Genus"', M_ + 335, 300, 75, 24, Color=DAMPAD, Size=10),
        galleri("galImport", "colImport", M_, 324, 460, 340, 46, imp_rad),
        label(
            "lblImportVarning",
            'If(CountRows(Filter(colImport, IsBlank(Trim(Svenska)) || IsBlank(Trim(Mal)))) > 0, "Någon rad saknar ord (röd ram).", '
            'IsBlank(lblGlosSprak.Text), "Välj bok eller språk först.", '
            '!IsBlank(cmbBok.Selected.ID) && IsBlank(cmbKapitel.Selected.ID), "Välj kapitel först.", "")',
            M_,
            668,
            460,
            24,
            Color=ROD,
            Size=10,
        ),
        knapp(
            "btnSparaGlosor",
            '"Spara " & CountRows(colImport) & " glosor"',
            M_,
            694,
            460,
            48,
            SPARA_GLOSOR,
            DisplayMode=(
                "If(CountRows(colImport) > 0 && IsBlank(lblImportVarning.Text), DisplayMode.Edit, DisplayMode.Disabled)"
            ),
        ),
        # ----- Höger: glosor som redan finns -----
        rubrik(
            "lblBefintliga",
            '"Redan inlagda här (" & CountRows(galBefintliga.AllItems) & ")"',
            R,
            76,
            420,
        ),
        label(
            "lblBefintligaInfo",
            '"Alla lärare kan fylla på samma kapitel. Ändringar sparas direkt."',
            R,
            102,
            420,
            24,
            Color=DAMPAD,
            Size=10,
        ),
        galleri("galBefintliga", BEFINTLIGA, R, 130, 420, 612, 44, bef_rad),
    ]
    return "scrGlosor", {"Fill": BG}, kontroller


# ---------- Skärm: Skapa / redigera gloslista ----------

VALD_POST = "{ ID: %s.ID, Title: %s.Title, Svenska: %s.Svenska, Genus: %s.Genus, Sprak: %s.Sprak }"


def vald_post(x):
    return VALD_POST % (x, x, x, x, x)


KALLA = """If(
    chkFristaende.Value,
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
    L, R = 20, 690
    kalla_rad = [
        kryssruta(
            "chkGlosa",
            '""',
            8,
            6,
            40,
            32,
            Default="!IsBlank(LookUp(colValda, ID = ThisItem.ID))",
            OnCheck=f"If(IsBlank(LookUp(colValda, ID = ThisItem.ID)), Collect(colValda, {vald_post('ThisItem')}))",
            OnUncheck="RemoveIf(colValda, ID = ThisItem.ID)",
        ),
        label(
            "lblKMal",
            "ThisItem.Title",
            50,
            0,
            285,
            44,
            Color=genusfarg("ThisItem.Genus"),
            FontWeight="FontWeight.Semibold",
        ),
        label("lblKSv", "ThisItem.Svenska", 340, 0, 290, 44),
        rad_separator("rectKLinje", "Parent.TemplateWidth"),
    ]
    vald_rad = [
        label(
            "lblVMal",
            "ThisItem.Title",
            12,
            0,
            290,
            40,
            Color=genusfarg("ThisItem.Genus"),
            FontWeight="FontWeight.Semibold",
        ),
        label("lblVSv", "ThisItem.Svenska", 310, 0, 280, 40),
        knapp(
            "btnVTaBort",
            '"✕"',
            600,
            4,
            32,
            32,
            "RemoveIf(colValda, ID = ThisItem.ID)",
            sekundar=True,
            BorderThickness=0,
            Color=ROD,
            HoverColor=ROD,
        ),
        rad_separator("rectVLinje", "Parent.TemplateWidth"),
    ]
    lank = 'WebbAdress & "?lista=" & varSparadLista.ID'
    kontroller = [
        *sidhuvud("NyL", 'If(IsBlank(varRedigeraLista), "Skapa gloslista", "Redigera gloslista")'),
        # ----- Vänster: välj glosor -----
        rubrik("lblNyLSteg1", '"1. Välj glosor"', L, 72, 640),
        kombobox(
            "cmbLBok",
            "Sort(Bocker, Title)",
            "Title",
            L,
            102,
            315,
            platshallare="Bok",
            OnChange="Reset(cmbLKapitel)",
            DisplayMode="If(chkFristaende.Value, DisplayMode.Disabled, DisplayMode.Edit)",
        ),
        kombobox(
            "cmbLKapitel",
            "Sort(Filter(Kapitel, BokID = Coalesce(cmbLBok.Selected.ID, -1)), Ordning)",
            "Title",
            L + 325,
            102,
            315,
            platshallare="Kapitel",
            DisplayMode="If(chkFristaende.Value, DisplayMode.Disabled, DisplayMode.Edit)",
        ),
        kryssruta("chkFristaende", '"Visa fristående glosor (utan bok)"', L, 150, 315, 36),
        kombobox(
            "cmbLSprak",
            "Sprakval",
            "Namn",
            L + 325,
            150,
            315,
            h=36,
            platshallare="Språk",
            Visible="chkFristaende.Value",
        ),
        knapp(
            "btnMarkeraAlla",
            '"Markera alla"',
            L,
            196,
            150,
            36,
            f"Collect(colValda, ForAll(Filter(galKalla.AllItems, !(ID in colValda.ID)) As g, {vald_post('g')}))",
            sekundar=True,
            Size=11,
        ),
        knapp(
            "btnAvmarkeraAlla",
            '"Avmarkera alla"',
            L + 160,
            196,
            150,
            36,
            "RemoveIf(colValda, ID in galKalla.AllItems.ID)",
            sekundar=True,
            Size=11,
        ),
        galleri("galKalla", KALLA, L, 240, 640, 330, 44, kalla_rad),
        rubrik("lblNyLListor", '"…eller slå ihop befintliga gloslistor"', L, 584, 640),
        kombobox(
            "cmbListor",
            "Sort(Gloslistor, Title)",
            "Title",
            L,
            614,
            470,
            platshallare="Välj en eller flera listor",
            flera=True,
        ),
        knapp(
            "btnLaggTillListor",
            '"Lägg till glosorna"',
            L + 480,
            614,
            160,
            40,
            LAGG_TILL_LISTOR,
            sekundar=True,
            Size=11,
        ),
        label(
            "lblNyLListorInfo",
            '"Glosorna återanvänds – inget dupliceras. Samma glosa läggs bara till en gång."',
            L,
            660,
            640,
            26,
            Color=DAMPAD,
            Size=10,
        ),
        # ----- Höger: listan -----
        rubrik("lblNyLSteg2", '"2. Din gloslista"', R, 72, 656),
        textruta(
            "txtListNamn",
            R,
            102,
            656,
            40,
            hint="Namn, t.ex. Kapitel 3 glosor",
            default="If(IsBlank(varRedigeraLista), varMallNamn, varRedigeraLista.Title)",
        ),
        textruta(
            "txtListBeskr",
            R,
            148,
            656,
            40,
            hint="Beskrivning (valfri), t.ex. Prov fredag v. 12",
            default='If(IsBlank(varRedigeraLista), "", varRedigeraLista.Beskrivning)',
        ),
        rubrik("lblValda", '"Valda glosor (" & CountRows(colValda) & ")"', R, 196, 500),
        knapp(
            "btnTomLista",
            '"Töm"',
            "Parent.Width - 120",
            194,
            100,
            32,
            "Clear(colValda)",
            sekundar=True,
            Size=10,
        ),
        galleri("galValda", "colValda", R, 232, 656, 350, 40, vald_rad),
        knapp(
            "btnSparaLista",
            'If(IsBlank(varRedigeraLista), "Spara gloslista", "Spara ändringar")',
            R,
            594,
            300,
            48,
            SPARA_LISTA,
            DisplayMode=(
                "If(CountRows(colValda) > 0 && !IsBlank(Trim(txtListNamn.Text)), DisplayMode.Edit, DisplayMode.Disabled)"
            ),
        ),
        label(
            "lblLank",
            '"Länk till eleverna: " & ' + lank,
            R,
            652,
            "Parent.Width - 860",
            40,
            Size=11,
            Color=ACCENT,
            Visible="!IsBlank(varSparadLista)",
        ),
        knapp(
            "btnKopieraLank",
            '"Kopiera länk"',
            "Parent.Width - 160",
            652,
            140,
            40,
            f'Copy({lank});\nNotify("Länken är kopierad.", NotificationType.Success)',
            sekundar=True,
            Visible="!IsBlank(varSparadLista)",
        ),
    ]
    return (
        "scrNyLista",
        {"Fill": BG, "OnVisible": "Set(varSparadLista, varRedigeraLista);\nReset(txtListNamn);\nReset(txtListBeskr)"},
        kontroller,
    )


# ---------- Skärm: Gloslistor ----------

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
    egen = "ThisItem.LarareEpost = User().Email"
    antal = 'CountRows(Filter(Split(ThisItem.GlosaIDs, ";"), !IsBlank(Trim(Value))))'
    lank = 'WebbAdress & "?lista=" & ThisItem.ID'
    rad = [
        label(
            "lblLTitel",
            "ThisItem.Title",
            20,
            10,
            "Parent.TemplateWidth - 720",
            30,
            Size=14,
            FontWeight="FontWeight.Bold",
            Color=f"If(ThisItem.Aktiv, {TEXT}, {DAMPAD})",
        ),
        label(
            "lblLMeta",
            f'ThisItem.LarareNamn & " · " & {antal} & " glosor · " & '
            f'Coalesce(LookUp(Sprakval, Kod = ThisItem.Sprak).Namn, ThisItem.Sprak) & '
            f'If(ThisItem.Aktiv, "", " · DOLD för eleverna")'
            f' & If(IsBlank(ThisItem.Beskrivning), "", " · " & ThisItem.Beskrivning)',
            20,
            40,
            "Parent.TemplateWidth - 720",
            24,
            Color=DAMPAD,
            Size=11,
        ),
        label("lblLLank", lank, 20, 64, "Parent.TemplateWidth - 720", 22, Color=ACCENT, Size=10),
        knapp(
            "btnLKopiera",
            '"Kopiera länk"',
            "Parent.TemplateWidth - 690",
            24,
            125,
            40,
            f'Copy({lank});\nNotify("Länken är kopierad.", NotificationType.Success)',
            sekundar=True,
            Size=10,
        ),
        knapp(
            "btnLRedigera",
            '"Redigera"',
            "Parent.TemplateWidth - 555",
            24,
            105,
            40,
            LADDA_VALDA + "\nSet(varRedigeraLista, ThisItem);\nNavigate(scrNyLista, ScreenTransition.None)",
            sekundar=True,
            Size=10,
            Visible=egen,
        ),
        knapp(
            "btnLMall",
            '"Använd som mall"',
            "Parent.TemplateWidth - 440",
            24,
            140,
            40,
            LADDA_VALDA
            + '\nSet(varRedigeraLista, Blank());\nSet(varMallNamn, "Kopia av " & ThisItem.Title);\n'
            "Navigate(scrNyLista, ScreenTransition.None)",
            sekundar=True,
            Size=10,
        ),
        knapp(
            "btnLAktiv",
            'If(ThisItem.Aktiv, "Dölj", "Visa")',
            "Parent.TemplateWidth - 290",
            24,
            90,
            40,
            "Patch(Gloslistor, ThisItem, { Aktiv: !ThisItem.Aktiv })",
            sekundar=True,
            Size=10,
            Visible=egen,
            Tooltip='"Dolda listor syns inte för eleverna"',
        ),
        knapp(
            "btnLTaBort",
            'If(varTaBortID = ThisItem.ID, "Bekräfta!", "Ta bort")',
            "Parent.TemplateWidth - 190",
            24,
            170,
            40,
            "If(\n    varTaBortID = ThisItem.ID,\n    Remove(Gloslistor, ThisItem);\n    Set(varTaBortID, 0),\n"
            "    Set(varTaBortID, ThisItem.ID)\n)",
            sekundar=True,
            Size=10,
            Color=ROD,
            HoverColor=ROD,
            BorderColor=ROD,
            Visible=egen,
        ),
        rad_separator("rectLLinje", "Parent.TemplateWidth"),
    ]
    kontroller = [
        *sidhuvud("Lis", '"Gloslistor"'),
        kryssruta("chkAllaListor", '"Visa alla lärares listor"', 20, 76, 320, 36),
        knapp(
            "btnLisNy",
            '"+ Ny gloslista"',
            "Parent.Width - 200",
            74,
            180,
            40,
            'Set(varRedigeraLista, Blank());\nSet(varMallNamn, "");\nClear(colValda);\nNavigate(scrNyLista, ScreenTransition.None)',
        ),
        galleri(
            "galListor",
            "Sort(\n    If(chkAllaListor.Value, Gloslistor, Filter(Gloslistor, LarareEpost = User().Email)),\n"
            "    ID,\n    SortOrder.Descending\n)",
            20,
            124,
            "Parent.Width - 40",
            "Parent.Height - 144",
            92,
            rad,
        ),
    ]
    return "scrListor", {"Fill": BG, "OnVisible": "Set(varTaBortID, 0)"}, kontroller


# ---------- YAML-utskrift ----------


def varde(v):
    """Formel -> YAML-värde. Allt skrivs som Power Fx-formel (=...)."""
    if isinstance(v, (int, float)):
        return f"={v}"
    return f"={v}"


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
    def gå(k, skarm):
        if k["namn"] in sedda:
            raise SystemExit(f"Dubbelt kontrollnamn: {k['namn']} ({skarm} och {sedda[k['namn']]})")
        sedda[k["namn"]] = skarm
        for b in k["children"]:
            gå(b, skarm)
    for namn, _, kontroller in skarmar:
        if namn in sedda:
            raise SystemExit(f"Dubbelt namn: {namn}")
        sedda[namn] = namn
        for k in kontroller:
            gå(k, namn)


def main():
    skarmar = [skarm_start(), skarm_glosor(), skarm_ny_lista(), skarm_listor()]
    kontrollera_unika(skarmar)
    (UT / "kontroller").mkdir(parents=True, exist_ok=True)
    for i, (namn, props, kontroller) in enumerate(skarmar, 1):
        fil = UT / f"{i}-{namn}.yaml"
        fil.write_text(skriv_skarm(namn, props, kontroller), encoding="utf-8")
        (UT / "kontroller" / f"{i}-{namn}.yaml").write_text(skriv_kontroller(kontroller), encoding="utf-8")
        print("skrev", fil.relative_to(ROT))


if __name__ == "__main__":
    main()
