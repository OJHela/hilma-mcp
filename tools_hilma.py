"""
tools_hilma.py – MCP tools for HILMA (hankintailmoitukset.fi).

HILMA is Finland's official public procurement notification channel (Hansel Oy).
All tools return plain strings in Finnish. No API key required.
"""

from hilma_client import (
    fetch_notice,
    format_notice,
    get_statistics,
    search_cpv,
    search_notices,
    search_organisations,
)


def _fmt_notice(n: dict, with_description: bool = True) -> str:
    lines = []
    eu_tag = " [EU]" if n.get("is_eu") else ""
    lines.append(f"[{n['id']}]{eu_tag} {n['title']}")
    lines.append(f"  Organisaatio:  {n['organization']}")
    lines.append(f"  Tyyppi:        {n['notice_type']} / {n['procurement_type']}")
    lines.append(f"  Julkaistu:     {n['date_published']}")
    if n.get("deadline"):
        lines.append(f"  Määräaika:     {n['deadline']}")
    if n.get("contract_value"):
        val = f"{n['contract_value']:,.0f} {n.get('currency', 'EUR')}"
        lines.append(f"  Hankinnan arvo:{val}")
    if n.get("cpv_codes"):
        lines.append(f"  CPV:           {str(n['cpv_codes'])[:80]}")
    if with_description and n.get("description"):
        desc = n["description"][:300]
        if len(n["description"]) > 300:
            desc += "..."
        lines.append(f"  Kuvaus:        {desc}")
    lines.append(f"  URL:           {n['url']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 1: hae_hankintailmoitukset
# ---------------------------------------------------------------------------

async def hae_hankintailmoitukset(
    hakusana: str = "",
    sivu: int = 1,
) -> str:
    """
    Hae julkisia hankintailmoituksia HILMA-portaalista (hankintailmoitukset.fi).

    Args:
        hakusana: Vapaa hakusana (nimi, kuvaus, organisaatio). Esim. "tietojärjestelmä", "siivous"
        sivu:     Sivunumero (oletus 1, 20 ilmoitusta/sivu)

    Esimerkit:
        hae_hankintailmoitukset("koulu")
        hae_hankintailmoitukset("tietojärjestelmä", sivu=2)
        hae_hankintailmoitukset("siivous")
    """
    try:
        raw = search_notices(keyword=hakusana, page=sivu)
    except Exception as e:
        return f"VIRHE: {e}"

    items = raw.get("value", [])
    notices = [format_notice(n) for n in items]

    if not notices:
        return f"Ei hakutuloksia hakusanalla '{hakusana}'."

    start = (sivu - 1) * 20 + 1
    end = start + len(notices) - 1
    lines = [f"Hankintailmoitukset {start}–{end} | HILMA | sivu {sivu}"]
    if hakusana:
        lines[0] += f" | hakusana: '{hakusana}'"
    lines.append("")

    for n in notices:
        lines.append(_fmt_notice(n, with_description=False))
        lines.append("")

    lines.append(f"→ Lisää: hae_hankintailmoitukset(\"{hakusana}\", sivu={sivu + 1})")
    lines.append("→ Tarkemmat tiedot: get_hankintailmoitus(id)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 2: get_hankintailmoitus
# ---------------------------------------------------------------------------

async def get_hankintailmoitus(notice_id: str) -> str:
    """
    Hae yksittäisen hankintailmoituksen täydet tiedot HILMA:sta.

    Args:
        notice_id: Ilmoituksen ID (esim. "EF-450", "OLD-160174", "2024-013439").
                   Löytyy hae_hankintailmoitukset-tuloksista.

    Esimerkit:
        get_hankintailmoitus("EF-450")       → Ylöjärven kaupungin koulukuljetukset
        get_hankintailmoitus("OLD-160174")   → Vanhempi ilmoitus
    """
    notice_id = notice_id.strip()
    try:
        raw = fetch_notice(notice_id)
        notice = format_notice(raw) if raw else None
    except Exception as e:
        return f"VIRHE: {e}"

    if not notice:
        return (
            f"Ilmoitusta '{notice_id}' ei löydy.\n"
            f"Vihje: kokeile hae_hankintailmoitukset('{notice_id}') ensin."
        )

    lines = [f"=== {notice['title']} ===", ""]
    lines.append(f"ID:              {notice['id']}")
    if notice.get("notice_number"):
        lines.append(f"Ilmoitusnumero:  {notice['notice_number']}")
    lines.append(f"Organisaatio:    {notice['organization']}")
    if notice.get("org_id"):
        lines.append(f"Y-tunnus:        {notice['org_id']}")
    lines.append(f"Tyyppi:          {notice['notice_type']}")
    lines.append(f"Hankintalaji:    {notice['procurement_type']}")
    lines.append(f"EU-hankinta:     {'Kyllä' if notice.get('is_eu') else 'Ei'}")
    lines.append(f"Julkaistu:       {notice['date_published']}")
    if notice.get("deadline"):
        lines.append(f"Määräaika:       {notice['deadline']}")
    if notice.get("contract_value"):
        val = f"{notice['contract_value']:,.0f} {notice.get('currency', 'EUR')}"
        lines.append(f"Hankinnan arvo:  {val}")
    if notice.get("cpv_codes"):
        lines.append(f"CPV-koodit:      {notice['cpv_codes']}")
    if notice.get("nuts_codes"):
        lines.append(f"NUTS (alue):     {notice['nuts_codes']}")
    if notice.get("ted_id"):
        lines.append(f"TED-numero:      {notice['ted_id']}")
    lines.append("")
    if notice.get("description"):
        lines.append("Kuvaus:")
        lines.append(notice["description"])
        lines.append("")

    lots = notice.get("lots", [])
    if lots and isinstance(lots, list):
        lines.append(f"Osa-alueet ({len(lots)} kpl):")
        for lot in lots[:5]:
            lot_title = lot.get("titleFi") or lot.get("titleSv") or str(lot.get("id", ""))
            lot_val = lot.get("awardedValue")
            val_str = f" – {lot_val:,.0f} EUR" if lot_val else ""
            lines.append(f"  • {lot_title}{val_str}")
        if len(lots) > 5:
            lines.append(f"  ... ja {len(lots) - 5} muuta osa-aluetta")
        lines.append("")

    lines.append(f"URL: {notice['url']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 3: listaa_hankintayksikot
# ---------------------------------------------------------------------------

async def listaa_hankintayksikot(hakusana: str = "") -> str:
    """
    Listaa HILMA:ssa rekisteröityneet hankintayksiköt (organisaatiot).

    Args:
        hakusana: Suodata nimen perusteella. Esim. "Helsin", "hyvinvointialue", "kunta"
                  Käytä osahakusanaa: "Helsin" löytää sekä "Helsinki" että "Helsingin kaupunki".

    Esimerkit:
        listaa_hankintayksikot("Helsin")      → Helsinki ja Helsingin-alkuiset
        listaa_hankintayksikot("hyvinvointi") → hyvinvointialueet
        listaa_hankintayksikot("Espoo")       → Espoon kaupunki
    """
    try:
        raw = search_organisations(keyword=hakusana)
        orgs = raw.get("value", [])
    except Exception as e:
        return f"VIRHE: {e}"

    if not orgs:
        return (
            f"Ei hankintayksiköitä hakusanalla '{hakusana}'.\n"
            f"Vihje: käytä osahakusanaa, esim. 'Helsin' löytää 'Helsingin kaupunki'."
        )

    lines = [f"Hankintayksiköt ({len(orgs)} kpl)" + (f" – '{hakusana}'" if hakusana else ""), ""]
    for o in orgs[:80]:
        name = o.get("nameFi") or o.get("nameSv") or ""
        org_id = o.get("identifier", "")
        lines.append(f"  {org_id:14s}  {name}")

    if len(orgs) > 80:
        lines.append(f"\n... ja {len(orgs) - 80} muuta. Tarkenna hakusanaa.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 4: hae_cpv_koodit
# ---------------------------------------------------------------------------

async def hae_cpv_koodit(hakusana: str) -> str:
    """
    Hae CPV-koodeja (Common Procurement Vocabulary) hakusanalla.
    CPV-koodit ovat EU:n standardoituja hankintakategorioita.

    Args:
        hakusana: Tuotteen tai palvelun nimi. Esim. "siivous", "tietojärjestelmä", "rakennus"

    Esimerkit:
        hae_cpv_koodit("siivous")          → siivouspalvelujen CPV-koodit
        hae_cpv_koodit("tietojärjestelmä") → IT-järjestelmien CPV-koodit
        hae_cpv_koodit("linja-auto")       → liikennepalvelujen CPV-koodit
    """
    try:
        raw = search_cpv(keyword=hakusana)
        codes = raw.get("value", [])
    except Exception as e:
        return f"VIRHE: {e}"

    if not codes:
        return (
            f"Ei CPV-koodeja hakusanalla '{hakusana}'.\n"
            f"Vihje: kokeile englanniksi (esim. 'cleaning', 'construction') tai CPV-numeron osaa."
        )

    lines = [f"CPV-koodit: '{hakusana}' ({len(codes)} tulosta)", ""]
    for c in codes[:25]:
        code_id = c.get("Id", "")
        label = c.get("LabelFi") or c.get("LabelSv") or c.get("LabelEn") or ""
        lines.append(f"  {code_id}  {label}")

    if len(codes) > 25:
        lines.append(f"\n... ja {len(codes) - 25} muuta. Tarkenna hakusanaa.")

    if codes:
        lines.append(f"\nKäyttö: hae_hankintailmoitukset('{codes[0].get('Id', '')}')")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 5: hilma_tilastot
# ---------------------------------------------------------------------------

async def hilma_tilastot() -> str:
    """
    Hae reaaliaikaiset tilastot HILMA-portaalista.
    Palauttaa tänään julkaistujen ilmoitusten määrän ja avoinna olevien kilpailutusten lukumäärän.
    """
    try:
        stats = get_statistics()
    except Exception as e:
        return f"VIRHE: {e}"

    lines = [
        "HILMA – Julkisten hankintojen tilastot (reaaliaikainen)",
        "",
        f"  Uusia ilmoituksia tänään:     {stats.get('newNotices', '?')}",
        f"  Avoinna olevia kilpailutuksia: {stats.get('openProcurements', '?')}",
        "",
        "Lähde: hankintailmoitukset.fi",
    ]
    return "\n".join(lines)
